from __future__ import annotations

import json
import logging
from typing import Dict, Optional

from agno.tools import Toolkit

from agno.agent import Agent

from app.config.settings import settings
from app.features.agents.pipeline_context import PipelineContext
from app.libs.models.model_selector import get_ollama
from app.features.agents.prompts.clasificador import PROMPT_SISTEMA

logger = logging.getLogger(__name__)

MAPEO_CIIU_CATEGORIAS = {
    # ===============================
    #  A) RESTAURANTES, BARES Y HOTELES (15%)
    # ===============================
    "5510": {
        "categoria": "Hoteles y alojamientos similares",
        "deduccion": 15,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Restaurantes, bares y hoteles",
        "nota": "Alojamiento temporal tipo hotel; CIIU división 55."
    },
    "5590": {
        "categoria": "Otros tipos de alojamiento",
        "deduccion": 15,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Restaurantes, bares y hoteles",
        "nota": "Otros servicios de alojamiento (hostales, residencias, etc.)."
    },
    "5610": {
        "categoria": "Restaurantes y servicios de comidas",
        "deduccion": 15,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Restaurantes, bares y hoteles",
        "nota": "Restaurantes, cafeterías, comida rápida, comida para llevar, etc."
    },
    "5630": {
        "categoria": "Servicios de bebidas (bares, tabernas, pubs)",
        "deduccion": 15,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Restaurantes, bares y hoteles",
        "nota": "Bares, tabernas, expendio de bebidas para consumo en el local."
    },

    # ===============================
    #  B) SERVICIOS MÉDICOS Y ODONTÓLOGOS (30%)
    # ===============================
    "8620": {
        "categoria": "Actividades de médicos y odontólogos",
        "deduccion": 30,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Servicios de médicos y odontólogos",
        "requiere_renta_cuarta": True,
        "nota": "Consultas y tratamientos médicos/odontológicos; validar que el comprobante sea RHE."
    },

    # ===============================
    #  C) SERVICIOS PROFESIONALES Y OFICIOS (4TA CATEGORÍA – 30%)
    # ===============================
    "5811": {
        "categoria": "Servicios editoriales (edición de libros)",
        "deduccion": 30,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Servicios profesionales y oficios (4ta)",
        "requiere_renta_cuarta": True,
        "nota": "Servicio profesional cuando el emisor sea persona natural con RHE."
    },
    "6201": {
        "categoria": "Programación informática / desarrollo de software",
        "deduccion": 30,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Servicios profesionales y oficios (4ta)",
        "requiere_renta_cuarta": True,
        "nota": "Desarrollo de software, programación a medida, etc."
    },
    "6202": {
        "categoria": "Consultoría informática y gestión de TI",
        "deduccion": 30,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Servicios profesionales y oficios (4ta)",
        "requiere_renta_cuarta": True,
        "nota": "Consultoría informática, soporte, gestión de sistemas."
    },
    "7020": {
        "categoria": "Consultoría en gestión empresarial",
        "deduccion": 30,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Servicios profesionales y oficios (4ta)",
        "requiere_renta_cuarta": True,
        "nota": "Consultores de negocio, estrategia, gestión."
    },
    "6910": {
        "categoria": "Servicios jurídicos (abogados, notarios, etc.)",
        "deduccion": 30,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Servicios profesionales y oficios (4ta)",
        "requiere_renta_cuarta": True,
        "nota": "Abogados y actividades jurídicas; usualmente 4ta si emisor es P.N."
    },
    "6920": {
        "categoria": "Contabilidad, auditoría y asesoría fiscal",
        "deduccion": 30,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Servicios profesionales y oficios (4ta)",
        "requiere_renta_cuarta": True,
        "nota": "Contadores, auditores, asesores tributarios."
    },
    "7110": {
        "categoria": "Arquitectura e ingeniería y consultoría técnica",
        "deduccion": 30,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Servicios profesionales y oficios (4ta)",
        "requiere_renta_cuarta": True,
        "nota": "Servicios de arquitectura, planos, ingeniería, inspecciones técnicas."
    },
    "7310": {
        "categoria": "Servicios de publicidad y marketing",
        "deduccion": 30,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Servicios profesionales y oficios (4ta)",
        "requiere_renta_cuarta": True,
        "nota": "Agencias de publicidad, creativos, campañas, medios."
    },

    # ===============================
    #  D) COMERCIO MINORISTA (NO DEDUCIBLE 3 UIT)
    # ===============================
    "4711": {
        "categoria": "Comercio minorista no especializado (supermercados)",
        "deduccion": 0,
        "tipo_regla": "no_deducible_3UIT",
        "grupo_sunat": "Fuera de 3UIT",
        "nota": "Consumidor puede deducir solo dentro de 7 UIT generales, no en la bolsa adicional."
    },
    "4722": {
        "categoria": "Comercio minorista de productos farmacéuticos (farmacias)",
        "deduccion": 0,
        "tipo_regla": "no_deducible_3UIT",
        "grupo_sunat": "Fuera de 3UIT",
        "nota": "Boletas de farmacia no suman a las 3 UIT adicionales."
    },

    # ===============================
    #  E) ES SALUD TRABAJADOR DEL HOGAR (100%)
    # ===============================
    "9700": {
        "categoria": "Hogares como empleadores de personal doméstico",
        "deduccion": 100,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Aportaciones a EsSalud por trabajadoras/es del hogar",
        "nota": "Aporte EsSalud (Form. 1676), no por la CIIU en sí."
    },
}

# ===============================
# REGLAS CIIU POR PREFIJO
# ===============================
REGLAS_CIIU_PREFIJO = [
    # Restaurantes, bares y hoteles: cualquier CIIU que empiece en 55 o 56
    {
        "prefijo": "55",
        "categoria": "Hoteles y otros alojamientos",
        "deduccion": 15,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Restaurantes, bares y hoteles"
    },
    {
        "prefijo": "56",
        "categoria": "Restaurantes, bares y servicios de comidas/bebidas",
        "deduccion": 15,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Restaurantes, bares y hoteles"
    },

    # Servicios médicos / salud humana
    {
        "prefijo": "86",
        "categoria": "Servicios de salud humana",
        "deduccion": 30,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Servicios de médicos y odontólogos",
        "requiere_renta_cuarta": True,
        "nota": "Aplicar sólo si profesión es médico/odontólogo y comprobante es RHE."
    },

    # Servicios profesionales
    {
        "prefijo": "69",
        "categoria": "Servicios jurídicos y contables",
        "deduccion": 30,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Servicios profesionales y oficios (4ta)",
        "requiere_renta_cuarta": True
    },
    {
        "prefijo": "70",
        "categoria": "Servicios de gestión empresarial",
        "deduccion": 30,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Servicios profesionales y oficios (4ta)",
        "requiere_renta_cuarta": True
    },
    {
        "prefijo": "71",
        "categoria": "Servicios de arquitectura e ingeniería",
        "deduccion": 30,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Servicios profesionales y oficios (4ta)",
        "requiere_renta_cuarta": True
    },
    {
        "prefijo": "73",
        "categoria": "Publicidad y estudios de mercado",
        "deduccion": 30,
        "tipo_regla": "3UIT_adicional",
        "grupo_sunat": "Servicios profesionales y oficios (4ta)",
        "requiere_renta_cuarta": True
    },
]


class ClasificacionToolkit(Toolkit):

    def __init__(self, contexto: PipelineContext):
        super().__init__(name="clasificacion_tools")
        self.contexto = contexto

    def mapear_ciiu(self, ciiu: str) -> str:
        """
        Mapea un código CIIU a categoría y % deducción según SUNAT 2025.

        Lógica de búsqueda:
        1. Búsqueda exacta en MAPEO_CIIU_CATEGORIAS
        2. Búsqueda por prefijo en REGLAS_CIIU_PREFIJO
        3. Default si no hay coincidencia

        Args:
            ciiu: Código CIIU de 4 dígitos

        Returns:
            JSON string con categoría, porcentaje, tipo_regla, etc.
        """
        if not ciiu:
            return json.dumps({
                "categoria": "gastoGeneral",
                "porcentaje": 0.0,
                "tipo_regla": "sin_ciiu",
                "fuente": "sin_ciiu"
            })

        # Búsqueda exacta
        if ciiu in MAPEO_CIIU_CATEGORIAS:
            datos = MAPEO_CIIU_CATEGORIAS[ciiu]
            return json.dumps({
                "categoria": datos["categoria"],
                "porcentaje": datos["deduccion"],
                "tipo_regla": datos.get("tipo_regla", "general"),
                "grupo_sunat": datos.get("grupo_sunat", ""),
                "requiere_renta_cuarta": datos.get("requiere_renta_cuarta", False),
                "nota": datos.get("nota", ""),
                "fuente": "ciiu_exacto"
            })

        # Búsqueda por prefijo
        for regla in REGLAS_CIIU_PREFIJO:
            if ciiu.startswith(regla["prefijo"]):
                return json.dumps({
                    "categoria": regla["categoria"],
                    "porcentaje": regla["deduccion"],
                    "tipo_regla": regla.get("tipo_regla", "general"),
                    "grupo_sunat": regla.get("grupo_sunat", ""),
                    "requiere_renta_cuarta": regla.get("requiere_renta_cuarta", False),
                    "nota": regla.get("nota", ""),
                    "fuente": f"ciiu_prefijo_{regla['prefijo']}"
                })

        # CIIU no mapeado
        logger.warning(f"CIIU no mapeado: {ciiu}, usando clasificación default")
        return json.dumps({
            "categoria": "gastoGeneral",
            "porcentaje": 0.0,
            "tipo_regla": "general_7UIT",
            "grupo_sunat": "No clasificado",
            "fuente": "default_ciiu_no_mapeado"
        })


class AgenteClasificador:
    def __init__(self, contexto: PipelineContext):
        self.contexto = contexto
        self.agent = Agent(
            name="ClasificadorGastos",
            model=get_ollama(),
            tools=[ClasificacionToolkit(contexto)],
            instructions=[PROMPT_SISTEMA],
            markdown=False,
        )

    def tool_clasificar(self) -> Dict:
        """
        Ejecuta la clasificación usando el agente.
        """
        # Obtener CIIU del contexto
        validacion = self.contexto.validacion_sunat or {}
        ciiu = validacion.get("ciiu")

        try:
            prompt = f"Clasifica el comprobante con CIIU: {ciiu or 'null'}"
            response = self.agent.run(prompt)

            # Parsear respuesta
            try:
                content = response.content.replace("```json", "").replace("```", "").strip()
                resultado = json.loads(content)
                return resultado
            except json.JSONDecodeError:
                logger.error(f"Error parseando respuesta JSON del clasificador: {response.content}")
                return self._clasificacion_default()

        except Exception as e:
            logger.error(f"Error en AgenteClasificador: {e}")
            return self._clasificacion_default()

    def _clasificacion_default(self) -> Dict:
        """Clasificación por defecto en caso de error."""
        return {
            "categoria_gasto": "gastoGeneral",
            "porcentaje_deduccion": 0.0,
            "ciiu_utilizado": None,
            "version_regla": "v1.0",
            "fuente_clasificacion": "error_fallback"
        }
