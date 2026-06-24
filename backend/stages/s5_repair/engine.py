import json
import logging
from typing import List, Tuple

from backend.llm.client import GeminiClient
from backend.schemas import (
    ArchitectureBlueprint,
    StructuredIntent,
    SchemaBundle,
    ValidationReport,
    ValidationIssue,
    UISchema,
    APISchema,
    DatabaseSchema,
    AuthSchema,
    RepairReport,
    RepairAction,
)
from backend.stages.s4_validation.engine import ValidationEngine

logger = logging.getLogger(__name__)

class RepairEngine:
    """
    Stage 5: Repair Engine
    
    Consumes a ValidationReport and performs targeted layer-level LLM repairs.
    """
    def __init__(self, llm_client: GeminiClient):
        self.llm_client = llm_client
        self.validation_engine = ValidationEngine()

    async def execute(self, bundle: SchemaBundle, report: ValidationReport, blueprint: ArchitectureBlueprint, intent: StructuredIntent) -> Tuple[SchemaBundle, ValidationReport, RepairReport]:
        logger.info("Executing Stage 5: Repair Engine (Targeted)")
        
        if report.is_valid or report.total_issues == 0:
            logger.info("No issues to repair.")
            return bundle, report, RepairReport(
                issues_received=0, issues_fixed=0, issues_remaining=0, repair_success_rate=100.0, repair_actions=[]
            )

        # 1. Group issues by layer based on 'source'
        db_issues = []
        api_issues = []
        ui_issues = []
        auth_issues = []

        for issue in report.issues:
            if issue.source.startswith("DBTable"):
                db_issues.append(issue)
            elif issue.source.startswith("APIEndpoint"):
                api_issues.append(issue)
            elif issue.source.startswith("UIPage"):
                ui_issues.append(issue)
            elif issue.source.startswith("AuthSchema"):
                auth_issues.append(issue)
            else:
                # Fallback based on some heuristic or just log it
                logger.warning(f"Could not route issue {issue.id} based on source '{issue.source}'.")

        # Create a working copy of the bundle
        repaired_bundle = bundle.model_copy(deep=True)
        actions: List[RepairAction] = []

        # 2. Perform Targeted Repairs
        if db_issues:
            logger.info(f"Repairing Database Schema ({len(db_issues)} issues)...")
            new_db, layer_actions = await self._repair_layer(
                layer_name="DatabaseSchema",
                schema_model=DatabaseSchema,
                current_schema=repaired_bundle.database,
                issues=db_issues,
                blueprint=blueprint,
                intent=intent
            )
            repaired_bundle.database = new_db
            actions.extend(layer_actions)

        if api_issues:
            logger.info(f"Repairing API Schema ({len(api_issues)} issues)...")
            new_api, layer_actions = await self._repair_layer(
                layer_name="APISchema",
                schema_model=APISchema,
                current_schema=repaired_bundle.api,
                issues=api_issues,
                blueprint=blueprint,
                intent=intent
            )
            repaired_bundle.api = new_api
            actions.extend(layer_actions)

        if ui_issues:
            logger.info(f"Repairing UI Schema ({len(ui_issues)} issues)...")
            new_ui, layer_actions = await self._repair_layer(
                layer_name="UISchema",
                schema_model=UISchema,
                current_schema=repaired_bundle.ui,
                issues=ui_issues,
                blueprint=blueprint,
                intent=intent
            )
            repaired_bundle.ui = new_ui
            actions.extend(layer_actions)

        if auth_issues:
            logger.info(f"Repairing Auth Schema ({len(auth_issues)} issues)...")
            new_auth, layer_actions = await self._repair_layer(
                layer_name="AuthSchema",
                schema_model=AuthSchema,
                current_schema=repaired_bundle.auth,
                issues=auth_issues,
                blueprint=blueprint,
                intent=intent
            )
            repaired_bundle.auth = new_auth
            actions.extend(layer_actions)

        # 3. Rerun Validation
        logger.info("Running post-repair validation...")
        final_report = self.validation_engine.execute(repaired_bundle, blueprint)

        # 4. Evaluate Success
        # An issue is 'fixed' if it's no longer present. For simplicity in the report, 
        # we check the total delta, or specifically look if the target/source pairs are gone.
        remaining_issue_signatures = {f"{i.source}::{i.target}::{i.message}" for i in final_report.issues}
        
        issues_fixed = 0
        for action in actions:
            # We find the original issue
            orig_issue = next((i for i in report.issues if i.id == action.issue_id), None)
            if orig_issue:
                sig = f"{orig_issue.source}::{orig_issue.target}::{orig_issue.message}"
                if sig not in remaining_issue_signatures:
                    action.success = True
                    issues_fixed += 1
                else:
                    action.success = False

        success_rate = (issues_fixed / report.total_issues) * 100.0 if report.total_issues > 0 else 100.0

        repair_report = RepairReport(
            issues_received=report.total_issues,
            issues_fixed=issues_fixed,
            issues_remaining=final_report.total_issues,
            repair_success_rate=round(success_rate, 2),
            repair_actions=actions
        )

        logger.info(f"Repair completed. Fixed: {issues_fixed}/{report.total_issues}. Success rate: {success_rate:.1f}%")
        return repaired_bundle, final_report, repair_report

    async def _repair_layer(
        self,
        layer_name: str,
        schema_model: type,
        current_schema,
        issues: List[ValidationIssue],
        blueprint: ArchitectureBlueprint,
        intent: StructuredIntent
    ) -> Tuple[any, List[RepairAction]]:
        
        issues_json = json.dumps([i.model_dump() for i in issues], indent=2)
        
        prompt = f"""You are repairing the {layer_name} for an application.
The validation engine detected the following issues with the current {layer_name}:

{issues_json}

Here is the existing (flawed) {layer_name}:
{current_schema.model_dump_json(indent=2)}

Here is the Architecture Blueprint for reference:
{blueprint.model_dump_json(indent=2)}

INSTRUCTIONS:
1. Fix the issues mentioned above.
2. DO NOT modify parts of the schema that are unrelated to the issues unless absolutely necessary.
3. Return the fully repaired {layer_name} schema.
"""

        try:
            repaired_schema = await self.llm_client.generate_structured(
                prompt=prompt,
                response_model=schema_model
            )
            
            # Create actions
            actions = []
            for issue in issues:
                actions.append(RepairAction(
                    issue_id=issue.id,
                    component_modified=layer_name,
                    strategy_used="LLM_REGENERATION",
                    success=False, # Evaluated later
                    before_hash=str(hash(current_schema.model_dump_json())),
                    after_hash=str(hash(repaired_schema.model_dump_json()))
                ))
            return repaired_schema, actions
            
        except Exception as e:
            logger.error(f"Failed to repair {layer_name}: {e}")
            # If LLM fails, return the current schema and mark actions as failed
            actions = []
            for issue in issues:
                actions.append(RepairAction(
                    issue_id=issue.id,
                    component_modified=layer_name,
                    strategy_used="LLM_REGENERATION",
                    success=False,
                    before_hash=None,
                    after_hash=None
                ))
            return current_schema, actions
