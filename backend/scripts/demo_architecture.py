import os
import sys
import asyncio
import json

from dotenv import load_dotenv
load_dotenv()

from backend.llm.client import GeminiClient
from backend.stages.s1_intent.extractor import IntentExtractor
from backend.stages.s2_architecture.designer import ArchitectureDesigner

async def main():
    print("=" * 60)
    print("ARCHITECTURE GENERATOR - LIVE DEMO")
    print("=" * 60)
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)
        
    model_name = "gemini-2.5-flash"
    client = GeminiClient(api_key=api_key, model_name=model_name)
    
    # We run Stage 1 to get a valid intent
    extractor = IntentExtractor(llm_client=client)
    prompt = "Build a band management app with members, events, songs and role-based access."
    
    print("\nRunning Stage 1: Intent Extraction...")
    try:
        intent = await extractor.execute(prompt)
        print(f"Success! Extracted intent for: {intent.app_name}")
    except Exception as e:
        print(f"Failed Stage 1: {e}")
        sys.exit(1)
        
    # We run Stage 2 to get the architecture blueprint
    designer = ArchitectureDesigner(llm_client=client)
    
    print("\nRunning Stage 2: Architecture Generation...")
    print("(This involves reasoning about entities, roles, pages, and flows. It may take 10-15 seconds)\n")
    
    try:
        blueprint = await designer.execute(intent)
        
        print("=" * 60)
        print("VALIDATION RESULT")
        print("=" * 60)
        print("Pydantic Validation: SUCCESS (ArchitectureBlueprint conforms to schema)")
        
        print("\n" + "=" * 60)
        print("ARCHITECTURE BLUEPRINT")
        print("=" * 60)
        print(blueprint.model_dump_json(indent=2))
        print("=" * 60)
        
        # Summary
        print(f"\nGenerated:")
        print(f"- {len(blueprint.entities)} Entities")
        print(f"- {len(blueprint.roles)} Roles")
        print(f"- {len(blueprint.pages)} Pages")
        print(f"- {len(blueprint.features)} Features")
        print(f"- {len(blueprint.flows)} Flows")
        
    except Exception as e:
        print(f"\nARCHITECTURE GENERATION FAILED")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
