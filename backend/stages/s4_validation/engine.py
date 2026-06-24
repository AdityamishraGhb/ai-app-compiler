import logging
from typing import List

from backend.schemas import (
    ArchitectureBlueprint,
    SchemaBundle,
    ValidationReport,
    ValidationIssue,
    ValidationSeverity,
    ValidationCategory,
)

logger = logging.getLogger(__name__)

class ValidationEngine:
    """
    Stage 4: Validation Engine
    
    Performs 100% deterministic, zero-LLM checks across the SchemaBundle.
    Collects all validation issues and returns a ValidationReport.
    """
    
    def execute(self, bundle: SchemaBundle, blueprint: ArchitectureBlueprint) -> ValidationReport:
        logger.info("Executing Stage 4: Validation Engine (Deterministic)")
        
        issues: List[ValidationIssue] = []
        
        issues.extend(self._check_database(bundle))
        issues.extend(self._check_api_to_db(bundle))
        issues.extend(self._check_ui_to_api(bundle))
        issues.extend(self._check_auth(bundle, blueprint))
        
        errors = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        warnings = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        infos = sum(1 for i in issues if i.severity == ValidationSeverity.INFO)
        
        report = ValidationReport(
            is_valid=(errors == 0),
            total_issues=len(issues),
            error_count=errors,
            warning_count=warnings,
            info_count=infos,
            issues=sorted(issues, key=lambda i: 0 if i.severity == ValidationSeverity.ERROR else 1)
        )
        
        logger.info(f"Validation completed. Valid: {report.is_valid}, Errors: {errors}, Warnings: {warnings}")
        return report

    def _check_database(self, bundle: SchemaBundle) -> List[ValidationIssue]:
        issues = []
        db_tables = {table.name for table in bundle.database.tables}
        
        for table in bundle.database.tables:
            for column in table.columns:
                if column.foreign_key:
                    ref_table = column.foreign_key.table
                    if ref_table not in db_tables:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            category=ValidationCategory.REFERENTIAL,
                            source=f"DBTable[{table.name}].column[{column.name}].foreign_key",
                            target=f"DBTable[{ref_table}]",
                            message=f"Foreign key '{column.foreign_key.table}.{column.foreign_key.column}' references non-existent table '{ref_table}'.",
                            repair_hint=f"Create a table named '{ref_table}' or correct the foreign key reference in '{table.name}'."
                        ))
        return issues

    def _check_api_to_db(self, bundle: SchemaBundle) -> List[ValidationIssue]:
        issues = []
        db_entities = {table.entity for table in bundle.database.tables}
        db_tables_by_entity = {table.entity: table for table in bundle.database.tables}

        for endpoint in bundle.api.endpoints:
            # Check Response Entity
            if endpoint.response and endpoint.response.entity:
                entity = endpoint.response.entity
                if entity not in db_entities:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.REFERENTIAL,
                        source=f"APIEndpoint[{endpoint.method} {endpoint.path}].response.entity",
                        target=f"DBTable[entity={entity}]",
                        message=f"API endpoint response references entity '{entity}' which does not exist in the Database Schema.",
                        repair_hint=f"Add a Database Schema table for entity '{entity}'."
                    ))

            # Check Request Body Entity and Fields
            if endpoint.request_body and endpoint.request_body.entity:
                entity = endpoint.request_body.entity
                if entity not in db_entities:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.REFERENTIAL,
                        source=f"APIEndpoint[{endpoint.method} {endpoint.path}].request_body.entity",
                        target=f"DBTable[entity={entity}]",
                        message=f"API endpoint request_body references entity '{entity}' which does not exist in the Database Schema.",
                        repair_hint=f"Add a Database Schema table for entity '{entity}'."
                    ))
                else:
                    # Check that fields in request body exist in the DB Table
                    table = db_tables_by_entity[entity]
                    column_names = {col.name for col in table.columns}
                    for field in endpoint.request_body.fields:
                        if field not in column_names:
                            issues.append(ValidationIssue(
                                severity=ValidationSeverity.ERROR,
                                category=ValidationCategory.LOGICAL,
                                source=f"APIEndpoint[{endpoint.method} {endpoint.path}].request_body.fields[{field}]",
                                target=f"DBTable[{table.name}].columns",
                                message=f"API request body accepts field '{field}' but column '{field}' does not exist in table '{table.name}'.",
                                repair_hint=f"Add column '{field}' to DB table '{table.name}' or remove it from the API request body."
                            ))
                            
        return issues

    def _check_ui_to_api(self, bundle: SchemaBundle) -> List[ValidationIssue]:
        issues = []
        api_routes = {f"{ep.method} {ep.path}" for ep in bundle.api.endpoints}
        
        for page in bundle.ui.pages:
            for comp in page.components:
                if comp.data_source and comp.data_source not in api_routes:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.REFERENTIAL,
                        source=f"UIPage[{page.name}].Component[{comp.id}].data_source",
                        target=f"APIEndpoint[{comp.data_source}]",
                        message=f"UI Component '{comp.id}' data_source '{comp.data_source}' maps to a non-existent API endpoint.",
                        repair_hint=f"Create API endpoint '{comp.data_source}' or correct the UI component's data_source."
                    ))
                
                if comp.submit_endpoint and comp.submit_endpoint not in api_routes:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.REFERENTIAL,
                        source=f"UIPage[{page.name}].Component[{comp.id}].submit_endpoint",
                        target=f"APIEndpoint[{comp.submit_endpoint}]",
                        message=f"UI Component '{comp.id}' submit_endpoint '{comp.submit_endpoint}' maps to a non-existent API endpoint.",
                        repair_hint=f"Create API endpoint '{comp.submit_endpoint}' or correct the UI component's submit_endpoint."
                    ))
        return issues

    def _check_auth(self, bundle: SchemaBundle, blueprint: ArchitectureBlueprint) -> List[ValidationIssue]:
        issues = []
        
        # Check Roles match blueprint
        blueprint_roles = {role.name for role in blueprint.roles}
        for role in bundle.auth.roles:
            if role.name not in blueprint_roles:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.LOGICAL,
                    source=f"AuthSchema.Role[{role.name}]",
                    target=f"ArchitectureBlueprint.roles",
                    message=f"Auth Schema defined a role '{role.name}' that does not exist in the Architecture Blueprint.",
                    repair_hint=f"Remove the role '{role.name}' from AuthSchema."
                ))
                
        # Check Credentials map to User DB Table
        user_entity = bundle.auth.user_entity
        db_tables_by_entity = {table.entity: table for table in bundle.database.tables}
        
        if user_entity not in db_tables_by_entity:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                category=ValidationCategory.REFERENTIAL,
                source=f"AuthSchema.user_entity",
                target=f"DBTable[entity={user_entity}]",
                message=f"AuthSchema user_entity '{user_entity}' does not map to any Database Table.",
                repair_hint=f"Create a Database Table for entity '{user_entity}'."
            ))
        else:
            table = db_tables_by_entity[user_entity]
            column_names = {col.name for col in table.columns}
            
            identifier = bundle.auth.credentials.identifier_field
            secret = bundle.auth.credentials.secret_field
            
            if identifier not in column_names:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.REFERENTIAL,
                    source=f"AuthSchema.credentials.identifier_field",
                    target=f"DBTable[{table.name}].columns[{identifier}]",
                    message=f"Auth identifier field '{identifier}' is not a column in the user table '{table.name}'.",
                    repair_hint=f"Add column '{identifier}' to DB table '{table.name}'."
                ))
                
            if secret not in column_names:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category=ValidationCategory.REFERENTIAL,
                    source=f"AuthSchema.credentials.secret_field",
                    target=f"DBTable[{table.name}].columns[{secret}]",
                    message=f"Auth secret field '{secret}' is not a column in the user table '{table.name}'.",
                    repair_hint=f"Add column '{secret}' to DB table '{table.name}'."
                ))

        return issues
