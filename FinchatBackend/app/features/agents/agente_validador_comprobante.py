from __future__ import annotations

import base64
import json
from typing import Dict, Optional

from agno.tools import Toolkit
from agno.agent import Agent

from app.config.settings import settings
from app.db.repositories.comprobante_repositorio import ComprobanteRepositorio
from app.libs.models.model_selector import get_ollama
from app.utils.hashing import calcular_hash_bytes
from app.features.agents.prompts.validador_comprobante import PROMPT_SISTEMA

class ValidationToolkit(Toolkit):
    """
    Toolkit para validación y detección de duplicados.

    Provee herramientas para que el agente decida autónomamente
    la estrategia de validación.
    """

    def __init__(self, comprobante_repo: ComprobanteRepositorio):
        super().__init__(name="validation_tools")
        self.comprobante_repo = comprobante_repo

    def calcular_hash(self, contenido_base64: str) -> str:
        """
        Calcular hash SHA-256 del contenido del archivo.

        Args:
            contenido_base64: Contenido en base64 (para serialización JSON)

        Returns:
            Hash hexadecimal del archivo
        """
        contenido_bytes = base64.b64decode(contenido_base64)
        return calcular_hash_bytes(contenido_bytes)

    def buscar_duplicado_por_hash(
        self,
        usuario_id: int,
        hash_archivo: str
    ) -> str:
        """
        Buscar si existe un comprobante duplicado por hash.

        Args:
            usuario_id: ID del usuario
            hash_archivo: Hash SHA-256 del archivo

        Returns:
            JSON string con info del duplicado o {"es_duplicado": false}
        """
        comprobante_existente = self.comprobante_repo.buscar_por_hash(
            id_usuario=usuario_id,
            hash_archivo=hash_archivo
        )

        if comprobante_existente:
            return json.dumps({
                "es_duplicado": True,
                "tipo_duplicado": "hash",
                "comprobante_id": comprobante_existente.id_comprobante,
                "serie": comprobante_existente.serie,
                "numero": comprobante_existente.numero,
                "fecha_emision": comprobante_existente.fecha_emision.isoformat(),
                "monto_total": float(comprobante_existente.monto_total),
            })

        return json.dumps({"es_duplicado": False})

    def buscar_duplicado_por_metadatos(
        self,
        usuario_id: int,
        emisor_id: int,
        serie: str,
        numero: str,
    ) -> str:
        """
        Buscar duplicado por emisor/serie/número (metadatos).

        Esta validación se usa cuando el hash no encuentra duplicados
        pero queremos verificar por datos del comprobante.

        Args:
            usuario_id: ID del usuario
            emisor_id: ID del emisor
            serie: Serie del comprobante
            numero: Número del comprobante

        Returns:
            JSON string con info del duplicado o {"es_duplicado": false}
        """
        comprobante_existente = self.comprobante_repo.buscar_por_emisor_serie_numero(
            id_usuario=usuario_id,
            id_emisor=emisor_id,
            serie=serie,
            numero=numero,
        )

        if comprobante_existente:
            return json.dumps({
                "es_duplicado": True,
                "tipo_duplicado": "metadatos",
                "comprobante_id": comprobante_existente.id_comprobante,
                "hash_archivo": comprobante_existente.hash_archivo,
                "fecha_emision": comprobante_existente.fecha_emision.isoformat(),
                "monto_total": float(comprobante_existente.monto_total),
            })

        return json.dumps({"es_duplicado": False})


class AgenteValidadorComprobante:
    """
    Agente AGNO autónomo para validación y deduplicación de comprobantes.

    Usa LLM para decidir inteligentemente qué herramientas usar y en qué orden:
    1. Primero valida por hash (más rápido)
    2. Si no es duplicado por hash, puede validar por metadatos si es necesario
    """

    def __init__(self, comprobante_repo: ComprobanteRepositorio):
        """
        Inicializar agente validador.

        Args:
            comprobante_repo: Repositorio de comprobantes
        """
        self.comprobante_repo = comprobante_repo

        # Crear agente AGNO con autonomía
        self.agent = Agent(
            name="ValidadorComprobante",
            model=get_ollama(),
            tools=[ValidationToolkit(comprobante_repo)],
            instructions=[PROMPT_SISTEMA],
            markdown=False,
        )

    def validar_archivo(
        self,
        usuario_id: int,
        contenido: bytes
    ) -> Dict:
        """
        Validar archivo usando agente autónomo.

        El agente decidía la secuencia óptima; ahora priorizamos un flujo
        determinista y rápido: calcular hash localmente y verificar duplicado
        directo por hash. Si no hay duplicado, retornamos de inmediato.

        Args:
            usuario_id: ID del usuario
            contenido: Bytes del archivo

        Returns:
            Dict con hash y si es duplicado
        """
        # 1) Calcular hash local (determinista y rápido)
        hash_archivo = calcular_hash_bytes(contenido)

        # 2) Buscar duplicado por hash en BD
        duplicado_info = self._buscar_duplicado_fallback(usuario_id, hash_archivo)
        if duplicado_info:
            return {
                "hash_archivo": hash_archivo,
                **duplicado_info
            }

        # 3) Sin duplicado: devolvemos resultado inmediato (omitimos LLM)
        return {
            "hash_archivo": hash_archivo,
            "es_duplicado": False,
            "tipo_duplicado": None,
            "comprobante_id": None,
            "motivo": "no_duplicado_hash"
        }

    def _buscar_duplicado_fallback(
        self,
        usuario_id: int,
        hash_archivo: str
    ) -> Optional[Dict]:
        """
        Fallback manual si el LLM falla.

        Args:
            usuario_id: ID del usuario
            hash_archivo: Hash del archivo

        Returns:
            Dict con info de duplicado o None
        """
        comprobante_existente = self.comprobante_repo.buscar_por_hash(
            id_usuario=usuario_id,
            hash_archivo=hash_archivo
        )

        if comprobante_existente:
            return {
                "es_duplicado": True,
                "tipo_duplicado": "hash",
                "comprobante_id": comprobante_existente.id_comprobante,
            }

        return None
