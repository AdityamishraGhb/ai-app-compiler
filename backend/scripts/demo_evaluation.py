import asyncio
import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

from backend.scripts.evaluation import Evaluator

# Load .env explicitly from the project root
root = Path(__file__).resolve().parents[2]
load_dotenv(root / ".env")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

async def run_demo():
    print("=" * 60)
    print("EVALUATION FRAMEWORK - PIPELINE BENCHMARK")
    print("=" * 60)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable is required.")
        return

    evaluator = Evaluator(api_key=api_key)

    # Dataset: 10 normal prompts, 10 edge cases
    prompts = [
        # Normal Prompts
        {"category": "Normal", "prompt": "Build a CRM application with users, contacts, and deals."},
        {"category": "Normal", "prompt": "Create a hospital management system for doctors, patients, and appointments."},
        {"category": "Normal", "prompt": "Build a school portal for teachers, students, and grades."},
        {"category": "Normal", "prompt": "Create an ecommerce app with products, categories, and shopping carts."},
        {"category": "Normal", "prompt": "Build an inventory management system with products, warehouses, and stock levels."},
        {"category": "Normal", "prompt": "Create an HRMS for employees, leaves, and payroll."},
        {"category": "Normal", "prompt": "Build a gym management app for members, trainers, and classes."},
        {"category": "Normal", "prompt": "Create a band management app with members, events, songs, and roles."},
        {"category": "Normal", "prompt": "Build a hotel booking system with rooms, guests, and reservations."},
        {"category": "Normal", "prompt": "Create a task manager for teams, projects, and tasks."},
        
        # Edge Cases
        {"category": "Edge", "prompt": "Build something."},
        {"category": "Edge", "prompt": "Build a CRM without any users."},
        {"category": "Edge", "prompt": "Create a school portal without students."},
        {"category": "Edge", "prompt": "Build an app without a database."},
        {"category": "Edge", "prompt": "Build a CRM but it shouldn't have any customer data."},
        {"category": "Edge", "prompt": "Build an app with no authentication or login."},
        {"category": "Edge", "prompt": "Create a thing that does things."},
        {"category": "Edge", "prompt": "Build a system where admins have no permissions but guests have all permissions."},
        {"category": "Edge", "prompt": "Create an app."},
        {"category": "Edge", "prompt": "Build an application but I will not tell you the business requirements."}
    ]

    print(f"Starting evaluation of {len(prompts)} prompts...")
    
    report = await evaluator.run_evaluation(prompts)
    
    # Save the report
    with open("evaluation_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    metrics = report["metrics"]
    print(f"Total Runs:            {metrics['total_runs']}")
    print(f"Successful Runs:       {metrics['successful_runs']}")
    print(f"Failed Runs:           {metrics['failed_runs']}")
    print(f"Success Rate:          {metrics['success_rate']}%")
    print(f"Average Latency:       {metrics['average_latency']}s")
    print(f"Validation Failures:   {metrics['validation_failures']}")
    print(f"Repair Success Rate:   {metrics['repair_success_rate']}%")
    print(f"Runtime Success Rate:  {metrics['runtime_success_rate']}%")
    print("=" * 60)
    print("Detailed report saved to evaluation_report.json")


if __name__ == "__main__":
    asyncio.run(run_demo())
