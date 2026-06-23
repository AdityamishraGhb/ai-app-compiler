import asyncio
import os
import json
from dotenv import load_dotenv

from backend.llm.client import GeminiClient
from backend.stages.s1_intent.extractor import IntentExtractor
from backend.schemas import StructuredIntent

async def main():
    load_dotenv()
    
    env_var_name = "GEMINI_API_KEY"
    api_key = os.getenv(env_var_name)
    
    # User requested: "gemini-2.5-flash" based on their successful test
    model_name = "gemini-2.5-flash"
    
    print("=" * 60)
    print("INTENT EXTRACTOR - LIVE TEST")
    print("=" * 60)
    print(f"API Key Source : Environment variable '{env_var_name}'")
    print(f"Model Name     : {model_name}")
    print("=" * 60)
    
    client = GeminiClient(api_key=api_key, model_name=model_name)
    extractor = IntentExtractor(llm_client=client)
    
    prompt = "Build a band management app with members, events, songs and role-based access."
    print(f"\nPROMPT:\n{prompt}\n")
    
    print("Running extraction... (This may take a few seconds)\n")
    
    # We will temporarily monkeypatch the client's generate_structured to capture the raw text
    original_generate_structured = client.generate_structured
    
    raw_json_captured = []
    
    async def patched_generate_structured(prompt, response_model, temperature=0.0):
        # We manually do the generation here to capture raw text easily for the printout
        schema_json = response_model.model_json_schema()
        enhanced_prompt = (
            f"{prompt}\n\n"
            f"IMPORTANT: You MUST return ONLY a valid JSON object that exactly matches this schema. "
            f"Do not wrap the response in markdown code blocks like ```json. Return raw JSON.\n"
            f"Schema: {json.dumps(schema_json)}\n"
        )
        response = await client.model.generate_content_async(
            contents=enhanced_prompt,
        )
        raw_text = response.text
        raw_json_captured.append(raw_text)
        
        # Strip markdown
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"): cleaned = cleaned[7:]
        elif cleaned.startswith("```"): cleaned = cleaned[3:]
        if cleaned.endswith("```"): cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        return response_model.model_validate_json(cleaned)
        
    # Replace the method for this run
    client.generate_structured = patched_generate_structured
    
    try:
        intent = await extractor.execute(prompt)
        
        print("=" * 60)
        print("RAW LLM JSON OUTPUT")
        print("=" * 60)
        print(raw_json_captured[0])
        
        print("\n" + "=" * 60)
        print("VALIDATION RESULT")
        print("=" * 60)
        print("Pydantic Validation: SUCCESS (No validation errors raised)")
        
        print("\n" + "=" * 60)
        print("PARSED STRUCTURED INTENT")
        print("=" * 60)
        print(intent.model_dump_json(indent=2))
        print("=" * 60)
        
    except Exception as e:
        print("\nEXTRACTION FAILED")
        print(f"Error: {e}")
        if raw_json_captured:
            print("\nRaw Output that caused failure:")
            print(raw_json_captured[0])

if __name__ == "__main__":
    asyncio.run(main())
