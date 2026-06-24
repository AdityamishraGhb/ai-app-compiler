import asyncio
import json
import logging
import time
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load .env explicitly from the project root
root = Path(__file__).resolve().parents[2]
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

logger = logging.getLogger(__name__)

class Evaluator:
    def __init__(self, api_key: str):
        self.llm_client = GeminiClient(api_key=api_key)
        self.intent_extractor = IntentExtractor(self.llm_client)
        self.arch_generator = ArchitectureDesigner(self.llm_client)
        self.schema_bundler = SchemaBundler(self.llm_client)
        self.validation_engine = ValidationEngine()
        self.repair_engine = RepairEngine(self.llm_client)
        self.runtime_simulator = RuntimeSimulator()

    async def run_single_prompt(self, prompt: str, category: str) -> Dict[str, Any]:
        result = {
            "prompt": prompt,
            "category": category,
            "success": False,
            "latency": 0.0,
            "stages": {},
            "errors": []
        }

        start_time = time.time()
        
        try:
            # Stage 1: Intent
            s1_start = time.time()
            intent = await self.intent_extractor.execute(prompt)
            result["stages"]["intent"] = {"success": True, "latency": time.time() - s1_start}

            # Stage 2: Architecture
            s2_start = time.time()
            blueprint = await self.arch_generator.execute(intent)
            result["stages"]["architecture"] = {"success": True, "latency": time.time() - s2_start}

            # Stage 3: Schema
            s3_start = time.time()
            bundle = await self.schema_bundler.execute(blueprint, intent)
            result["stages"]["schema"] = {"success": True, "latency": time.time() - s3_start}

            # Stage 4: Validation
            s4_start = time.time()
            validation_report = self.validation_engine.execute(bundle, blueprint)
            result["stages"]["validation"] = {
                "success": validation_report.is_valid,
                "issues": validation_report.total_issues,
                "latency": time.time() - s4_start
            }

            # Stage 5: Repair (if needed)
            s5_start = time.time()
            if not validation_report.is_valid:
                repaired_bundle, final_validation, repair_report = await self.repair_engine.execute(
                    bundle, validation_report, blueprint, intent
                )
                result["stages"]["repair"] = {
                    "executed": True,
                    "success": final_validation.is_valid,
                    "issues_fixed": repair_report.issues_fixed,
                    "issues_received": repair_report.issues_received,
                    "latency": time.time() - s5_start
                }
                bundle = repaired_bundle
            else:
                result["stages"]["repair"] = {
                    "executed": False,
                    "success": True,
                    "latency": time.time() - s5_start
                }

            # Stage 6: Runtime
            s6_start = time.time()
            runtime_result = self.runtime_simulator.execute(bundle.database)
            result["stages"]["runtime"] = {
                "success": runtime_result.success,
                "tables_created": len(runtime_result.tables_created),
                "execution_errors": len(runtime_result.execution_errors),
                "latency": time.time() - s6_start
            }

            # Overall Success
            result["success"] = result["stages"]["runtime"]["success"]

        except Exception as e:
            logger.error(f"Error processing prompt '{prompt}': {e}", exc_info=True)
            result["errors"].append(str(e))
        finally:
            result["latency"] = time.time() - start_time

        return result

    async def run_evaluation(self, prompts: List[Dict[str, str]]) -> Dict[str, Any]:
        total_runs = 0
        successful_runs = 0
        failed_runs = 0
        total_latency = 0.0
        total_validation_failures = 0
        
        repair_attempts = 0
        repair_successes = 0
        
        runtime_attempts = 0
        runtime_successes = 0

        results = []

        for p in prompts:
            prompt_text = p["prompt"]
            category = p["category"]
            logger.info(f"Evaluating: [{category}] {prompt_text}")
            
            res = await self.run_single_prompt(prompt_text, category)
            results.append(res)
            
            total_runs += 1
            total_latency += res["latency"]
            
            if res["success"]:
                successful_runs += 1
            else:
                failed_runs += 1
                
            # Track validation failures
            val_stage = res["stages"].get("validation")
            if val_stage and not val_stage.get("success", False):
                total_validation_failures += 1
                
            # Track repairs
            rep_stage = res["stages"].get("repair")
            if rep_stage and rep_stage.get("executed", False):
                repair_attempts += 1
                if rep_stage.get("success", False):
                    repair_successes += 1
                    
            # Track runtime
            rt_stage = res["stages"].get("runtime")
            if rt_stage:
                runtime_attempts += 1
                if rt_stage.get("success", False):
                    runtime_successes += 1

        # Calculate metrics
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
        avg_latency = (total_latency / total_runs) if total_runs > 0 else 0
        repair_success_rate = (repair_successes / repair_attempts * 100) if repair_attempts > 0 else 100.0
        runtime_success_rate = (runtime_successes / runtime_attempts * 100) if runtime_attempts > 0 else 0.0

        report = {
            "metrics": {
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "success_rate": round(success_rate, 2),
                "average_latency": round(avg_latency, 2),
                "validation_failures": total_validation_failures,
                "repair_success_rate": round(repair_success_rate, 2),
                "runtime_success_rate": round(runtime_success_rate, 2)
            },
            "detailed_results": results
        }

        return report

