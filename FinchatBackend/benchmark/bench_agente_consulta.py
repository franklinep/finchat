import argparse
import json
import time
import asyncio
import sys
from typing import Dict, List, Any, Optional
from unittest.mock import MagicMock

# --- MOCKING DEPENDENCIES ---
mock_session = MagicMock()
mock_repo_comp = MagicMock()
mock_repo_emisor = MagicMock()

# Mock sys.modules to avoid importing full app dependencies if they fail
# But we try to import first. If it fails, we might need more aggressive mocking.
# For now, let's assume we can import AgenteConsulta if we mock the DB stuff it uses.

# We need to mock the repositories used in QueryToolkit if we use the real QueryToolkit.
# Or we can just mock QueryToolkit entirely.
# Let's mock QueryToolkit entirely since we want to control the output for the benchmark
# and we are testing the AGENT'S ability to call the tool, not the tool's DB logic.

# However, AgenteConsulta imports QueryToolkit. We can monkeypatch it.

import sys
from pathlib import Path
# Add project root to Python path to allow imports from 'app'
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from agno.agent import Agent
from agno.tools import Toolkit
from agno.models.ollama import Ollama

# Mock Toolkit
class MockQueryToolkit(Toolkit):
    def __init__(self):
        super().__init__(name="query_tools")
        self.register(self.buscar_comprobantes)
        self.register(self.obtener_totales)
        self.register(self.buscar_por_emisor)
        self.calls = []

    def buscar_comprobantes(
        self,
        ruc_emisor: Optional[str] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        categoria: Optional[str] = None,
        monto_min: Optional[float] = None,
        monto_max: Optional[float] = None,
        limit: int = 50,
    ) -> str:
        """Buscar comprobantes con filtros múltiples."""
        self.calls.append({
            "tool": "buscar_comprobantes",
            "args": {
                "ruc_emisor": ruc_emisor,
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
                "categoria": categoria,
                "monto_min": monto_min,
                "monto_max": monto_max
            }
        })
        return json.dumps({"total_encontrados": 2, "comprobantes": [{"id": 1, "monto": 100}, {"id": 2, "monto": 200}]})

    def obtener_totales(
        self,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        agrupar_por: Optional[str] = None,
    ) -> str:
        """Obtener totales y agregaciones de comprobantes."""
        self.calls.append({
            "tool": "obtener_totales",
            "args": {
                "fecha_desde": fecha_desde,
                "fecha_hasta": fecha_hasta,
                "agrupar_por": agrupar_por
            }
        })
        return json.dumps({"total_gastado": 300.0, "cantidad_comprobantes": 2})

    def buscar_por_emisor(
        self,
        texto_busqueda: str,
    ) -> str:
        """Buscar comprobantes por RUC o nombre del emisor."""
        self.calls.append({
            "tool": "buscar_por_emisor",
            "args": {"texto_busqueda": texto_busqueda}
        })
        return json.dumps({"encontrado": True, "emisor": {"razon_social": "TEST EMISOR"}, "total_gastado": 150.0})

# Import PROMPT
from app.features.agents.prompts.consulta import PROMPT_SISTEMA

class BenchmarkAgenteConsulta:
    def __init__(self, model_id: str):
        self.toolkit = MockQueryToolkit()
        self.agent = Agent(
            name="AgenteConsultaBench",
            model=Ollama(id=model_id),
            tools=[self.toolkit],
            instructions=[PROMPT_SISTEMA],
            markdown=True,
            tool_choice="required",
        )

    def run(self, query: str):
        # Clear previous calls
        self.toolkit.calls = []
        try:
            resp = self.agent.run(query)
            return {
                "response": resp.content,
                "calls": self.toolkit.calls
            }
        except Exception as e:
            print(f"Error running agent: {e}")
            return {"response": str(e), "calls": []}

async def run_benchmark(models: List[str]):
    results = {}

    # Test Queries and Expected Tools/Args
    test_cases = [
        {
            "query": "¿Cuánto gasté en total?",
            "expected_tool": "obtener_totales",
            "expected_args": {} # Loose check
        },
        {
            "query": "Gastos de Polleria Soto",
            "expected_tool": "buscar_por_emisor",
            "expected_args": {"texto_busqueda": "Polleria Soto"} # Partial match check
        },
        {
            "query": "Comprobantes de diciembre 2024",
            "expected_tool": "buscar_comprobantes",
            "expected_args": {"fecha_desde": "2024-12-01"} # Check if date logic works (agent might infer dates)
        },
        {
            "query": "¿Cuánto gasté en restaurantes?",
            "expected_tool": "obtener_totales",
            "expected_args": {"agrupar_por": "categoria"}
        }
    ]

    for model_id in models:
        print(f"Benchmarking Consulta Agent with model: {model_id}...")

        metrics = {
            "latencies": [],
            "correct_tool": 0,
            "correct_args": 0,
            "errors": 0
        }

        agent = BenchmarkAgenteConsulta(model_id)

        for case in test_cases:
            t0 = time.perf_counter()
            res = agent.run(case["query"])
            dt = time.perf_counter() - t0
            metrics["latencies"].append(dt)

            calls = res["calls"]
            if not calls:
                print(f"  Failed: No tool called for '{case['query']}'")
                metrics["errors"] += 1
                continue

            # Check first call (usually sufficient)
            call = calls[0]

            # Tool Check
            if call["tool"] == case["expected_tool"]:
                metrics["correct_tool"] += 1

                # Args Check (Heuristic)
                args_ok = True
                for k, v in case["expected_args"].items():
                    if k not in call["args"]:
                        args_ok = False
                        break
                    # Simple string containment for values
                    if isinstance(v, str) and v.lower() not in str(call["args"][k]).lower():
                        args_ok = False
                        break

                if args_ok:
                    metrics["correct_args"] += 1
                else:
                    print(f"  Args Mismatch for '{case['query']}': Expected {case['expected_args']}, Got {call['args']}")
            else:
                print(f"  Wrong Tool for '{case['query']}': Expected {case['expected_tool']}, Got {call['tool']}")

        avg_latency = sum(metrics["latencies"]) / len(metrics["latencies"]) if metrics["latencies"] else 0

        results[model_id] = {
            "avg_latency_sec": round(avg_latency, 4),
            "accuracy": {
                "tool_selection": metrics["correct_tool"] / len(test_cases),
                "argument_extraction": metrics["correct_args"] / len(test_cases)
            },
            "total_samples": len(test_cases)
        }

    print("\n=== CONSULTA AGENT BENCHMARK RESULTS ===")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["qwen3:4b", "llama3.1:8b", "gemma3:12b"], help="List of Ollama models to test")
    args = parser.parse_args()

    asyncio.run(run_benchmark(args.models))
