"""
Stage 3 — Schema Generation: UI Schema
"""

import logging
from backend.llm.client import GeminiClient
from backend.schemas import ArchitectureBlueprint, UISchema

logger = logging.getLogger(__name__)

UI_SCHEMA_PROMPT = """You are an expert Frontend Architect.
Your task is to generate a comprehensive UI Schema based on the provided Architecture Blueprint.

You MUST design:
1. Components: Reusable UI elements (tables, forms, cards) required by the pages.
2. Pages: The concrete layouts for each page defined in the architecture.

Rules:
- You ONLY have access to the ArchitectureBlueprint.
- Ensure every PageDefinition in the blueprint has a corresponding UIPage in your schema.
- Forms should reference fields that logically match the Entities involved.
- Assign standard components (e.g. DATA_TABLE, FORM, DETAIL_VIEW).

ARCHITECTURE BLUEPRINT (JSON):
{blueprint_json}
"""

class UISchemaGenerator:
    """Generates the UI Schema from an Architecture Blueprint."""

    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client

    async def execute(self, blueprint: ArchitectureBlueprint) -> UISchema:
        logger.info("Executing Stage 3: UI Schema Generation")
        
        blueprint_json = blueprint.model_dump_json(indent=2)
        full_prompt = UI_SCHEMA_PROMPT.format(blueprint_json=blueprint_json)
        
        schema = await self.llm.generate_structured(
            prompt=full_prompt,
            response_model=UISchema,
            temperature=0.2,
        )
        
        logger.info(f"Generated UI Schema with {len(schema.pages)} pages and {len(schema.components)} components.")
        return schema
