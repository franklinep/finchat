import argparse
import json
import time
import asyncio
import sys
from typing import Dict, List, Any
from unittest.mock import MagicMock, AsyncMock

# --- MOCKING DEPENDENCIES BEFORE IMPORTS ---
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# We mock 'playwright' and 'playwright.async_api' to avoid ModuleNotFoundError
# when importing PipelineContext -> SunatRucScraper
mock_playwright = MagicMock()
sys.modules["playwright"] = mock_playwright
sys.modules["playwright.async_api"] = mock_playwright

# We also need to mock SunatRucScraper if it's imported at top level
# But PipelineContext imports it. Let's see if we can just mock PipelineContext's dependency.
# Actually, if we mock playwright, SunatRucScraper import might succeed (if it only imports playwright).
# Let's assume mocking playwright is enough.

# Now we can import the actual app modules
try:
    from app.features.agents.pipeline_context import PipelineContext
    from app.features.agents.agente_validador_sunat import AgenteValidadorSunat, SunatToolkit
    from agno.models.ollama import Ollama
except ImportError as e:
    print(f"CRITICAL IMPORT ERROR: {e}")
    print("Ensure you are running this script with the project's virtual environment activated.")
    sys.exit(1)

# Hardcoded RUC data for mocking the tool response
RUC_DATA = {
    "10199483761": {"estado": "ACTIVO", "condicion": "HABIDO", "ciiu": "5610", "razon_social": "CAMARENA APOLINARIO MARIA ROSALINA", "nombre_comercial": "CAMARENA APOLINARIO MARIA ROSALINA"},
    "20556519065": {"estado": "ACTIVO", "condicion": "HABIDO", "ciiu": "5610", "razon_social": "TEAM SABOR S.A.C", "nombre_comercial": "TEAM SABOR S.A.C"},
    "20612675521": {"estado": "ACTIVO", "condicion": "HABIDO", "ciiu": "5610", "razon_social": "ASTO & BAUER CORPORATION SOCIEDAD ANONIMA CERRADA", "nombre_comercial": "ASTO & BAUER CORPORATION SOCIEDAD ANONIMA CERRADA"},
    "10080581578": {"estado": "ACTIVO", "condicion": "HABIDO", "ciiu": "5610", "razon_social": "SOTO PEREZ NICOLAS", "nombre_comercial": "SOTO PEREZ NICOLAS"},
    "20509076945": {"estado": "ACTIVO", "condicion": "HABIDO", "ciiu": "5610", "razon_social": "CINCO MILLAS SAC", "nombre_comercial": "CINCO MILLAS SAC"}
}

# Subclass PipelineContext to override get_sunat_data
class MockPipelineContext(PipelineContext):
    def __init__(self):
        # Skip super().__init__ if it does heavy setup
        pass

    async def get_sunat_data(self, ruc: str) -> Dict:
        return RUC_DATA.get(ruc, None)

async def run_benchmark(models: List[str]):
    results = {}

    test_cases = [
        ("10199483761", "CAMARENA APOLINARIO MARIA ROSALINA"),
        ("20556519065", "TEAM SABOR S.A.C"),
        ("20612675521", "ASTO & BAUER CORPORATION SOCIEDAD ANONIMA CERRADA"),
        ("10080581578", "SOTO PEREZ NICOLAS"),
        ("20509076945", "CINCO MILLAS SAC")
    ]

    for model_id in models:
        print(f"Benchmarking Validator with model: {model_id}...")

        metrics = {
            "latencies": [],
            "tool_calls": 0,
            "correct_status": 0,
            "correct_condicion": 0,
            "correct_ciiu": 0,
            "errors": 0
        }

        # Setup Agent with Mock Context
        ctx = MockPipelineContext()

        # We need to inject the specific model into the agent.
        # AgenteValidadorSunat initializes Agent in __init__ using get_ollama().
        # We can monkeypatch get_ollama or modify the agent instance after creation.

        # Option 1: Monkeypatch get_ollama
        # from app.libs.models.model_selector import get_ollama
        # But we want to change it per loop iteration.

        # Option 2: Modify agent instance
        agent_wrapper = AgenteValidadorSunat(ctx)
        # The underlying AGNO agent is at agent_wrapper.agent
        # We can swap its model.
        agent_wrapper.agent.model = Ollama(id=model_id)

        for ruc, nombre in test_cases:
            t0 = time.perf_counter()
            try:
                # The agent uses 'consultar_ruc' tool which calls ctx.get_sunat_data
                # Our MockPipelineContext handles that.

                res = await agent_wrapper.validar_completo(ruc, nombre)
                dt = time.perf_counter() - t0
                metrics["latencies"].append(dt)

                expected = RUC_DATA[ruc]

                # Validation Logic
                if res.get("estado_ruc") == expected["estado"]:
                    metrics["correct_status"] += 1

                if res.get("condicion_ruc") == expected["condicion"]:
                    metrics["correct_condicion"] += 1

                if str(res.get("ciiu")) == str(expected["ciiu"]):
                    metrics["correct_ciiu"] += 1

                # Heuristic: if we got a valid razon_social (not DESCONOCIDO), the tool was likely called and parsed
                if res.get("razon_social") != "DESCONOCIDO":
                    metrics["tool_calls"] += 1

            except Exception as e:
                print(f"Error validating {ruc}: {e}")
                metrics["errors"] += 1

        avg_latency = sum(metrics["latencies"]) / len(metrics["latencies"]) if metrics["latencies"] else 0

        results[model_id] = {
            "avg_latency_sec": round(avg_latency, 4),
            "accuracy": {
                "tool_usage": metrics["tool_calls"] / len(test_cases),
                "status": metrics["correct_status"] / len(test_cases),
                "condicion": metrics["correct_condicion"] / len(test_cases),
                "ciiu": metrics["correct_ciiu"] / len(test_cases)
            },
            "total_samples": len(test_cases),
            "errors": metrics["errors"]
        }

    print("\n=== VALIDATOR BENCHMARK RESULTS ===")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["llama3.1:8b", "gemma3:12b", "qwen3:4b"], help="List of Ollama models to test")
    args = parser.parse_args()

    asyncio.run(run_benchmark(args.models))
