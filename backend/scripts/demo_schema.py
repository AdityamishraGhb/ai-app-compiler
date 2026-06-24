import asyncio
import os
import json
from dotenv import load_dotenv

from backend.llm.client import GeminiClient
from backend.stages.s1_intent.extractor import IntentExtractor
from backend.stages.s2_architecture.designer import ArchitectureDesigner
from backend.stages.s3_schema.bundler import SchemaBundler, BundleValidationError

load_dotenv()

async def run_demo():
    print("=" * 60)
    print("SCHEMA GENERATOR - LIVE DEMO")
    print("=" * 60)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in environment.")
        return

    client = GeminiClient(api_key=api_key)
    
    # Run Stage 1
    print("\nRunning Stage 1: Intent Extraction...")
    s1 = IntentExtractor(client)
    intent = await s1.execute("Build a to-do list app with users, tasks, categories, and priority levels.")
    print(f"Success! Extracted intent for: {intent.app_type}")
    
    # Run Stage 2
    print("\nRunning Stage 2: Architecture Generation...")
    s2 = ArchitectureDesigner(client)
    blueprint = await s2.execute(intent)
    print(f"Success! Generated {len(blueprint.entities)} Entities, {len(blueprint.pages)} Pages.")
    
    # Run Stage 3
    print("\nRunning Stage 3: Schema Generation (UI, API, DB, Auth concurrently)...")
    s3 = SchemaBundler(client)
    
    try:
        bundle = await s3.execute(blueprint)
        print("\nSuccess! SchemaBundle generated and validated.")
        print("\nSUMMARY TABLE:")
        print("-" * 40)
        print(f"DB Tables       : {len(bundle.database.tables)}")
        print(f"API Endpoints   : {len(bundle.api.endpoints)}")
        print(f"UI Pages        : {len(bundle.ui.pages)}")
        print(f"Auth Roles      : {len(bundle.auth.roles)}")
        print("-" * 40)
        
        # Save output to a file for inspection
        with open("demo_schema_output.json", "w") as f:
            f.write(bundle.model_dump_json(indent=2))
        print("\nFull SchemaBundle written to demo_schema_output.json")
        
    except BundleValidationError as e:
        print(f"\n[!] VALIDATION FAILED WITH {len(e.issues)} ISSUES:")
        for issue in e.issues:
            print(f"  - [{issue.severity.upper()}] {issue.location.schema_layer}.{issue.location.field}: {issue.message}")
            if issue.suggestion:
                print(f"    Suggestion: {issue.suggestion}")

if __name__ == "__main__":
    asyncio.run(run_demo())
