"""
Stage 1 — Intent Extraction

Converts a natural language software requirement prompt into a structured intent.
"""

import logging

from backend.llm.client import GeminiClient
from backend.schemas import StructuredIntent

logger = logging.getLogger(__name__)

INTENT_EXTRACTION_PROMPT = """You are an expert software architect and product manager.
Your task is to analyze the user's natural language software requirements and extract a highly structured application intent.

You MUST extract:
1. A concise, PascalCase application name.
2. The type of application. Reduce generic classifications (like 'web_application' or 'dashboard'). Prefer domain-specific app types (like 'music_management_system' or 'healthcare_erp') when confidence is high. Use snake_case.
3. A clear description of the application's purpose.
4. A list of distinct target user roles (e.g., admin, guest, customer) in snake_case.
5. The core functional features required, ordered by priority (critical, high, medium, low).
6. Non-functional constraints (e.g., does it require auth? realtime?).

Be objective and comprehensive. If the user doesn't explicitly mention constraints like auth, infer them from the context (e.g., a "dashboard" or "user management" implies auth_required=true).

USER PROMPT:
{user_prompt}
"""

class IntentExtractor:
    """Pipeline Stage 1: Extracts structured intent from a raw prompt."""

    def __init__(self, llm_client: GeminiClient):
        self.llm = llm_client

    async def execute(self, prompt: str) -> StructuredIntent:
        """
        Execute the intent extraction stage.
        
        Args:
            prompt: The raw natural language requirement from the user.
            
        Returns:
            A validated StructuredIntent.
        """
        logger.info("Executing Stage 1: Intent Extraction")
        
        full_prompt = INTENT_EXTRACTION_PROMPT.format(user_prompt=prompt)
        
        intent = await self.llm.generate_structured(
            prompt=full_prompt,
            response_model=StructuredIntent,
            temperature=0.1,  # Low temperature for analytical extraction
        )
        
        logger.info(f"Successfully extracted intent for app: {intent.app_name}")
        return intent
