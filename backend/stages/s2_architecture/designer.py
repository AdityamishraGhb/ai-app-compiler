"""
Stage 2 — Architecture Generation

Converts a validated StructuredIntent into an ArchitectureBlueprint.
Designs Entities, Roles, Pages, and Flows.
"""

import logging
import json

from backend.llm.client import GeminiClient
from backend.schemas import StructuredIntent, ArchitectureBlueprint

logger = logging.getLogger(__name__)

ARCHITECTURE_DESIGN_PROMPT = """You are an expert Software Architect.
Your task is to design a complete system architecture blueprint based on a validated Application Intent.

You MUST design:
1. Entities: The core data models (e.g., User, Product, Order). Include relationships and attributes. Entity names MUST be PascalCase.
2. Roles: The distinct user permission roles in the system.
3. Pages: The high-level UI views required.
4. Features: The specific functionalities needed.
5. Flows: The user workflows mapping features to pages and roles.

Rules:
- You ONLY have access to the StructuredIntent. Do not make assumptions outside of it.
- Ensure cross-layer consistency: Roles mentioned in Flows must exist in the Roles definition. Entities mentioned in relationships must exist in the Entities list.
- Keep definitions clean, minimal, and highly structured.
- Use logical names for pages (e.g., 'dashboard', 'user_settings').

STRUCTURED INTENT (JSON):
{intent_json}
"""

class ArchitectureDesigner:
    """Pipeline Stage 2: Designs system architecture from structured intent."""

    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client

    async def execute(self, intent: StructuredIntent) -> ArchitectureBlueprint:
        """
        Execute the architecture design stage.
        
        Args:
            intent: The validated StructuredIntent from Stage 1.
            
        Returns:
            A validated ArchitectureBlueprint.
        """
        logger.info(f"Executing Stage 2: Architecture Design for app '{intent.app_name}'")
        
        # Serialize the input intent to JSON to feed into the prompt
        intent_json = intent.model_dump_json(indent=2)
        full_prompt = ARCHITECTURE_DESIGN_PROMPT.format(intent_json=intent_json)
        
        blueprint = await self.llm.generate_structured(
            prompt=full_prompt,
            response_model=ArchitectureBlueprint,
            temperature=0.2,  # Low temperature for consistency, but slightly higher than extraction
        )
        
        logger.info(f"Successfully designed architecture: {len(blueprint.entities)} entities, {len(blueprint.roles)} roles.")
        return blueprint
