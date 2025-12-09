from __future__ import annotations

import json
import logging
from typing import Dict, Optional

from agno.tools import Toolkit
from agno.agent import Agent
from pydantic import BaseModel, Field

from app.config.settings import settings
from app.features.agents.pipeline_context import PipelineContext
from app.libs.models.model_selector import get_ollama
from app.features.agents.prompts.validador_sunat import PROMPT_SISTEMA

logger = logging.getLogger(__name__)


class SunatToolkit(Toolkit):
    """Toolkit para consultas a SUNAT."""

    def __init__(self, contexto: PipelineContext):
        super().__init__(name="sunat_tools")
        self.contexto = contexto
        # self.register(self.consultar_ruc) # Methods are auto-registered by default

    async def consultar_ruc(self, ruc: str) -> str:
        """
        Consulta información de un RUC en SUNAT.

        Args:
            ruc: Número de RUC de 11 dígitos.

        Returns:
            JSON string con datos del contribuyente (razón social, estado, condición, CIIU).
        """
        datos = await self.contexto.get_sunat_data(ruc)
        if not datos:
            return json.dumps({"error": "No se encontraron datos", "fallback": True})
        return json.dumps(datos, ensure_ascii=False)


class AgenteValidadorSunat:
    def __init__(self, contexto: PipelineContext):
        """
        Inicializar agente validador SUNAT.

        Args:
            contexto: Contexto compartido del pipeline
        """
        self.contexto = contexto

        # Crear agente AGNO con modelo dual (Ollama/OpenAI)
        self.agent = Agent(
            name="ValidadorSUNAT",
            model=get_ollama(),
            tools=[SunatToolkit(contexto)],
            instructions=[PROMPT_SISTEMA],
            markdown=False,
        )

    async def validar_completo(self, ruc: str, nombre_emisor_ocr: str) -> Dict:
        try:
            prompt = f"""
            Valida el siguiente emisor:
            RUC: {ruc}
            Nombre OCR: {nombre_emisor_ocr}

            Responde SOLO con el JSON estructurado.
            """

            response = await self.agent.arun(prompt)

            try:
                content = response.content.replace("```json", "").replace("```", "").strip() #  limpia los bloques de codigo si el llm lo incluye
                resultado = json.loads(content)
                return resultado
            except json.JSONDecodeError:
                logger.error(f"Error parseando respuesta JSON del agente: {response.content}")
                return self._fallback_response(ruc)

        except Exception as e:
            logger.error(f"Error en AgenteValidadorSunat: {e}")
            return self._fallback_response(ruc)

    def _fallback_response(self, ruc: str) -> Dict:
        return {
            "estado_ruc": "DESCONOCIDO",
            "condicion_ruc": "DESCONOCIDO",
            "ciiu": None,
            "razon_social": "DESCONOCIDO",
            "nombre_comercial_sunat": None,
            "coincide_nombre": False,
            "pasa_reglas_basicas": False,
            "motivo_no_deducible": "Error interno en agente de validación",
            "fallback": True
        }
