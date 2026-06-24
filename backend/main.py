import os
import traceback
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Load .env explicitly from the project root
root = Path(__file__).resolve().parents[1]
load_dotenv(root / ".env")

from backend.llm.client import GeminiClient
from backend.stages import (
    IntentExtractor,
    ArchitectureDesigner,
    SchemaBundler,
    ValidationEngine,
    RepairEngine,
    RuntimeSimulator
)
from backend.schemas import (
    StructuredIntent,
    ArchitectureBlueprint,
    SchemaBundle,
    ValidationReport,
    RepairReport,
    RuntimeResult
)

app = FastAPI(title="AI App Compiler")

class CompileRequest(BaseModel):
    prompt: str

class CompileResponse(BaseModel):
    intent: StructuredIntent
    architecture: ArchitectureBlueprint
    schema_bundle: SchemaBundle
    validation_report: ValidationReport
    repair_report: Optional[RepairReport] = None
    runtime_result: RuntimeResult

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/compile", response_model=CompileResponse)
async def compile_app(req: CompileRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is missing")

    try:
        llm_client = GeminiClient(api_key=api_key)
        
        # Stage 1: Intent Extraction
        intent_extractor = IntentExtractor(llm_client)
        intent = await intent_extractor.execute(req.prompt)
        
        # Stage 2: Architecture Generation
        arch_designer = ArchitectureDesigner(llm_client)
        blueprint = await arch_designer.execute(intent)
        
        # Stage 3: Schema Generation
        schema_bundler = SchemaBundler(llm_client)
        bundle = await schema_bundler.execute(blueprint)
        
        # Stage 4: Validation
        validation_engine = ValidationEngine()
        val_report = validation_engine.execute(bundle, blueprint)
        
        # Stage 5: Repair
        repair_report = None
        if not val_report.is_valid:
            repair_engine = RepairEngine(llm_client)
            bundle, val_report, repair_report = await repair_engine.execute(
                bundle, val_report, blueprint, intent
            )
            
        # Stage 6: Runtime Simulation
        runtime_simulator = RuntimeSimulator()
        runtime_result = runtime_simulator.execute(bundle.database)
        
        return CompileResponse(
            intent=intent,
            architecture=blueprint,
            schema_bundle=bundle,
            validation_report=val_report,
            repair_report=repair_report,
            runtime_result=runtime_result
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


