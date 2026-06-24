"""
Stage 3 — Schema Generation: API Schema
"""

import logging
from backend.llm.client import GeminiClient
from backend.schemas import ArchitectureBlueprint, APISchema

logger = logging.getLogger(__name__)

API_SCHEMA_PROMPT = """You are an expert Backend API Architect.
Your task is to generate a comprehensive API Schema based on the provided Architecture Blueprint.

You MUST design:
1. Endpoints: RESTful API endpoints covering the features and entities defined.
2. Request/Response Bodies: Schema definitions for payloads.

Rules:
- You ONLY have access to the ArchitectureBlueprint.
- Generate endpoints matching the required features (CRUD operations).
- Every endpoint should logically map to the entities in the blueprint.
- Ensure proper HTTP methods and URL paths (e.g. GET /users, POST /tasks).
- Include appropriate authentication flags.

ARCHITECTURE BLUEPRINT (JSON):
{blueprint_json}
"""

class APISchemaGenerator:
    """Generates the API Schema from an Architecture Blueprint."""

    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client

    async def execute(self, blueprint: ArchitectureBlueprint) -> APISchema:
        logger.info("Executing Stage 3: API Schema Generation")
        
        blueprint_json = blueprint.model_dump_json(indent=2)
        full_prompt = API_SCHEMA_PROMPT.format(blueprint_json=blueprint_json)
        
        schema = await self.llm.generate_structured(
            prompt=full_prompt,
            response_model=APISchema,
            temperature=0.2,
        )
        
        logger.info(f"Generated API Schema with {len(schema.endpoints)} endpoints.")
        return schema
