"""
Demonstration script for Stage 1: Intent Extraction.
"""

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from backend.llm.client import GeminiClient
from backend.stages.s1_intent.extractor import IntentExtractor

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("demo_s1")

async def main():
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        logger.error("Please set GEMINI_API_KEY in your .env file or environment.")
        sys.exit(1)
        
    logger.info("Initializing Gemini Client...")
    client = GeminiClient(api_key=api_key)
    extractor = IntentExtractor(llm_client=client)
    
    prompt = "Build a band management app with members, events, songs and role-based access."
    logger.info(f"Running Intent Extraction with prompt: '{prompt}'")
    
    try:
        intent = await extractor.execute(prompt)
        print("\n" + "="*50)
        print("SUCCESS! Extracted StructuredIntent:")
        print("="*50)
        print(intent.model_dump_json(indent=2))
        print("="*50)
    except Exception as e:
        logger.error(f"Failed to extract intent: {e}")

if __name__ == "__main__":
    asyncio.run(main())
