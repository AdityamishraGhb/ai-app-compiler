"""
Stage 3 — Schema Generation: Auth Schema
"""

import logging
from backend.llm.client import GeminiClient
from backend.schemas import ArchitectureBlueprint, AuthSchema

logger = logging.getLogger(__name__)

AUTH_SCHEMA_PROMPT = """You are an expert Security Architect.
Your task is to generate a comprehensive Auth Schema based on the provided Architecture Blueprint.

You MUST design:
1. Roles: Map all roles from the blueprint.
2. Route Guards: Define protection rules mapping API endpoints and Pages to roles.
3. Credentials: Define the credential requirements.

Rules:
- You ONLY have access to the ArchitectureBlueprint.
- Ensure every Role defined in the blueprint is included.
- Assign appropriate permissions based on the blueprint roles and features.
- Define basic AuthStrategy (e.g., JWT).

ARCHITECTURE BLUEPRINT (JSON):
{blueprint_json}
"""

class AuthSchemaGenerator:
    """Generates the Auth Schema from an Architecture Blueprint."""

    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client

    async def execute(self, blueprint: ArchitectureBlueprint) -> AuthSchema:
        logger.info("Executing Stage 3: Auth Schema Generation")
        
        blueprint_json = blueprint.model_dump_json(indent=2)
        full_prompt = AUTH_SCHEMA_PROMPT.format(blueprint_json=blueprint_json)
        
        schema = await self.llm.generate_structured(
            prompt=full_prompt,
            response_model=AuthSchema,
            temperature=0.2,
        )
        
        logger.info(f"Generated Auth Schema with {len(schema.roles)} roles and {len(schema.guards)} route guards.")
        return schema
