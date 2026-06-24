"""
LLM Client wrapper for Google Gemini API.

Provides structured JSON output generation with exponential backoff retries.
"""

import asyncio
import json
import logging
from typing import TypeVar, Type, Any

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from google.api_core.exceptions import ResourceExhausted, RetryError, GoogleAPIError
from pydantic import BaseModel, ValidationError

from backend.llm.errors import LLMCommunicationError, LLMRateLimitError, LLMValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

def async_retry(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
    """
    Decorator for async exponential backoff retries.
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except (ResourceExhausted, LLMRateLimitError) as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts.")
                        raise LLMRateLimitError("Rate limit exceeded") from e
                    logger.warning(f"Rate limit hit. Retrying in {delay}s... (Attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, max_delay)
                except (GoogleAPIError, RetryError) as e:
                    if attempt == max_retries - 1:
                        logger.error(f"API communication error after {max_retries} attempts: {e}")
                        raise LLMCommunicationError(f"API communication error: {e}") from e
                    logger.warning(f"API Error. Retrying in {delay}s... (Attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, max_delay)
        return wrapper
    return decorator


import os

class GeminiClient:
    """Client for interacting with the Google Gemini API."""

    def __init__(self, api_key: str, model_name: str = None):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: The Google Gemini API key.
            model_name: The name of the model to use. Defaults to GEMINI_MODEL env var or gemini-2.5-flash.
        """
        genai.configure(api_key=api_key)
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.model = genai.GenerativeModel(self.model_name)

    @async_retry(max_retries=3, base_delay=2.0)
    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        temperature: float = 0.0,
    ) -> T:
        """
        Generate a structured JSON response from the LLM parsed into a Pydantic model.
        
        Args:
            prompt: The full prompt string (system instructions + user input).
            response_model: The Pydantic model class to validate and return.
            temperature: Sampling temperature. 0.0 is best for structured tasks.
            
        Returns:
            An instance of `response_model` populated with the LLM's output.
            
        Raises:
            LLMValidationError: If the LLM output is not valid JSON or fails schema validation.
            LLMRateLimitError: If API limits are hit.
            LLMCommunicationError: On network or provider errors.
        """
        try:
            # We explicitly ask the model to return JSON matching the schema
            schema_json = response_model.model_json_schema()
            
            enhanced_prompt = (
                f"{prompt}\n\n"
                f"IMPORTANT: You MUST return ONLY a valid JSON object that exactly matches this schema. "
                f"Do not wrap the response in markdown code blocks like ```json. Return raw JSON.\n"
                f"Schema: {json.dumps(schema_json)}\n"
            )

            response = await self.model.generate_content_async(
                contents=enhanced_prompt,
                generation_config=GenerationConfig(
                    temperature=temperature,
                    response_mime_type="application/json",
                ),
            )
            
            response_text = response.text.strip()
            
            # Sometimes models still wrap in markdown despite instructions
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            elif response_text.startswith("```"):
                response_text = response_text[3:]
            
            if response_text.endswith("```"):
                response_text = response_text[:-3]
                
            response_text = response_text.strip()
            
            return response_model.model_validate_json(response_text)
            
        except ValidationError as e:
            # Pydantic v2 throws ValidationError with 'json_invalid' type for bad JSON strings
            errors = e.errors()
            if errors and errors[0].get("type") == "json_invalid":
                raise LLMValidationError(f"LLM did not return valid JSON: {e}") from e
                
            # Deterministic Pre-Validation Repair for UISchema
            if response_model.__name__ == "UISchema":
                try:
                    data = json.loads(response_text)
                    repaired = False
                    for page in data.get("pages", []):
                        for comp in page.get("components", []):
                            actions = comp.get("actions")
                            if isinstance(actions, list):
                                new_actions = []
                                for action in actions:
                                    if isinstance(action, dict) and "label" in action:
                                        new_actions.append(str(action["label"]))
                                        repaired = True
                                    elif isinstance(action, dict):
                                        # Fallback to stringifying the dict if no label
                                        new_actions.append(str(action))
                                        repaired = True
                                    else:
                                        new_actions.append(action)
                                comp["actions"] = new_actions
                    if repaired:
                        logger.info("Auto-repaired UISchema actions dictionary mismatch.")
                        return response_model.model_validate(data)
                except Exception as repair_err:
                    logger.debug(f"Deterministic repair failed: {repair_err}")
            
            logger.error(f"Pydantic validation failed: {e}")
            logger.debug(f"Raw LLM output: {response_text}")
            raise LLMValidationError(f"Failed to validate LLM output against {response_model.__name__}: {e}") from e
