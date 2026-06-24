"""
Stage 3 — Schema Generation: Database Schema
"""

import logging
from backend.llm.client import GeminiClient
from backend.schemas import ArchitectureBlueprint, DatabaseSchema

logger = logging.getLogger(__name__)

DB_SCHEMA_PROMPT = """You are an expert Database Architect.
Your task is to generate a comprehensive Database Schema (SQLite compatible) based on the provided Architecture Blueprint.

You MUST design:
1. Tables: One for each entity defined.
2. Columns: Mapped from the entity attributes. Ensure correct SQLiteColumnType.
3. Foreign Keys: Proper constraints based on entity relationships.
4. Indexes: Add indexes for foreign keys and frequently queried fields.

Rules:
- You ONLY have access to the ArchitectureBlueprint.
- Ensure every Entity in the blueprint becomes a DBTable.
- Translate logical field types (e.g. 'string', 'uuid') to SQLite column types (e.g. 'TEXT').
- Explicitly map foreign key relationships.

ARCHITECTURE BLUEPRINT (JSON):
{blueprint_json}
"""

class DatabaseSchemaGenerator:
    """Generates the Database Schema from an Architecture Blueprint."""

    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client

    async def execute(self, blueprint: ArchitectureBlueprint) -> DatabaseSchema:
        logger.info("Executing Stage 3: Database Schema Generation")
        
        blueprint_json = blueprint.model_dump_json(indent=2)
        full_prompt = DB_SCHEMA_PROMPT.format(blueprint_json=blueprint_json)
        
        schema = await self.llm.generate_structured(
            prompt=full_prompt,
            response_model=DatabaseSchema,
            temperature=0.2,
        )
        
        logger.info(f"Generated Database Schema with {len(schema.tables)} tables.")
        return schema
