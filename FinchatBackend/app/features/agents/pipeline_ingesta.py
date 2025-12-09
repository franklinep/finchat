from __future__ import annotations

import logging
from typing import Dict, Optional, Any

from sqlalchemy.orm import Session
from agno.workflow import Workflow

from app.db.repositories import (
    ClasificacionRepositorio,
    ComprobanteRepositorio,
    DetalleComprobanteRepositorio,
    EmisorRepositorio,
    OcrPaginaRepositorio,
    ValidacionRepositorio,
)
from app.features.agents.agente_clasificador import AgenteClasificador
from app.features.agents.agente_parseador import AgenteParseador
from app.features.agents.agente_persistencia import AgentePersistencia
from app.features.agents.agente_validador_comprobante import AgenteValidadorComprobante
from app.features.agents.agente_validador_sunat import AgenteValidadorSunat
from app.features.agents.pipeline_context import PipelineContext

logger = logging.getLogger(__name__)


class IngestaWorkflow(Workflow):
    def __init__(self, session: Session, **kwargs):
        super().__init__(**kwargs)
        self.session = session

        self.comprobante_repo = ComprobanteRepositorio(session)
        self.emisor_repo = EmisorRepositorio(session)
        self.detalle_repo = DetalleComprobanteRepositorio(session)
        self.validacion_repo = ValidacionRepositorio(session)
        self.clasificacion_repo = ClasificacionRepositorio(session)
        self.ocr_repo = OcrPaginaRepositorio(session)

    async def run(self, input_data: Dict[str, Any], **kwargs) -> Dict:
        usuario_id = input_data["usuario_id"]
        nombre_archivo = input_data["nombre_archivo"]
        mime_type = input_data["mime_type"]
        contenido = input_data["contenido"]

        contexto = None
        try:
            logger.info(f"[Workflow] Iniciando procesamiento de {nombre_archivo} para usuario {usuario_id}")
            contexto = PipelineContext(
                usuario_id=usuario_id,
                nombre_archivo=nombre_archivo,
                mime_type=mime_type,
            )

            # Agente validador del comprobante
            logger.info(f"[Workflow] Paso 1/5: Validando archivo {nombre_archivo}")
            validador = AgenteValidadorComprobante(self.comprobante_repo)
            resultado_validacion = validador.validar_archivo(usuario_id, contenido)
            logger.info(f"[Workflow] Validación completada: hash={resultado_validacion['hash_archivo'][:8]}..., duplicado={resultado_validacion['es_duplicado']}")

            contexto.hash_archivo = resultado_validacion["hash_archivo"]
            contexto.es_duplicado = resultado_validacion["es_duplicado"]

            # si es duplicado entonces
            if resultado_validacion["es_duplicado"]:
                logger.info(f"[Workflow] Archivo duplicado detectado: {nombre_archivo}")
                return {
                    "exito": True,
                    "duplicado": True,
                    "comprobante_id": resultado_validacion["comprobante_id"],
                    "hash_archivo": resultado_validacion["hash_archivo"],
                    "tipo_duplicado": resultado_validacion["tipo_duplicado"],
                    "mensaje": "Archivo duplicado - workflow detenido"
                }

            # Agente parseador
            logger.info(f"[Workflow] Paso 2/5: Parseando archivo {nombre_archivo}")
            try:
                parseador = AgenteParseador(contexto)
                resultado_parsing = parseador.parsear_archivo(
                    contenido=contenido,
                    mime_type=mime_type,
                    nombre_archivo=nombre_archivo,
                )
                contexto.comprobante_parseado = resultado_parsing
                logger.info(f"[Workflow] Parsing completado: tipo={resultado_parsing['comprobante']['tipo_comprobante']}, serie={resultado_parsing['comprobante']['serie']}")
            except Exception as e:
                logger.error(f"[Workflow] Error en Parseador: {e}", exc_info=True)
                raise Exception(f"Error en parsing: {str(e)}") from e

            # Agente validador SUNAT
            logger.info(f"[Workflow] Paso 3/5: Validando en SUNAT")
            try:
                ruc_emisor = resultado_parsing["emisor"]["ruc"]
                nombre_emisor_ocr = resultado_parsing["emisor"]["razon_social"]
                logger.info(f"[Workflow] Validando RUC {ruc_emisor}")

                validador_sunat = AgenteValidadorSunat(contexto)
                validacion_sunat = await validador_sunat.validar_completo(ruc_emisor, nombre_emisor_ocr)
                contexto.validacion_sunat = validacion_sunat
                logger.info(f"[Workflow] SUNAT completado: estado={validacion_sunat.get('estado_ruc')}")
            except Exception as e:
                logger.error(f"[Workflow] Error en Validador SUNAT: {e}", exc_info=True)
                raise Exception(f"Error en validación SUNAT: {str(e)}") from e

            # Agente clasificador
            logger.info(f"[Workflow] Paso 4/5: Clasificando comprobante")
            try:
                clasificador = AgenteClasificador(contexto)
                clasificacion = clasificador.tool_clasificar()
                contexto.clasificacion = clasificacion
                logger.info(f"[Workflow] Clasificación completada: categoria={clasificacion['categoria_gasto']}")
            except Exception as e:
                logger.error(f"[Workflow] Error en Clasificador: {e}", exc_info=True)
                raise Exception(f"Error en clasificación: {str(e)}") from e

            # Agente persistencia
            logger.info(f"[Workflow] Paso 5/5: Guardando en BD")
            try:
                persistencia = AgentePersistencia(
                    contexto=contexto,
                    session=self.session,
                    emisor_repo=self.emisor_repo,
                    comprobante_repo=self.comprobante_repo,
                    detalle_repo=self.detalle_repo,
                    validacion_repo=self.validacion_repo,
                    clasificacion_repo=self.clasificacion_repo,
                    ocr_repo=self.ocr_repo,
                )

                comprobante_id = persistencia.guardar_todo()
                self.session.commit()
                logger.info(f"[Workflow] Commit exitoso, comprobante_id={comprobante_id}")
            except Exception as e:
                logger.error(f"[Workflow] Error en Persistencia: {e}", exc_info=True)
                self.session.rollback()
                raise Exception(f"Error en persistencia: {str(e)}") from e

            logger.info(f"[Workflow] ✓ Completado exitosamente: comprobante_id={comprobante_id}")

            # Retornar resultado completo
            return {
                "exito": True,
                "duplicado": False,
                "comprobante_id": comprobante_id,
                "hash_archivo": contexto.hash_archivo,
                "campos_parseados": {
                    "tipo_comprobante": resultado_parsing["comprobante"]["tipo_comprobante"],
                    "serie": resultado_parsing["comprobante"]["serie"],
                    "numero": resultado_parsing["comprobante"]["numero"],
                    "fecha_emision": resultado_parsing["comprobante"]["fecha_emision"],
                    "monto_total": resultado_parsing["comprobante"]["monto_total"],
                    "moneda": resultado_parsing["comprobante"]["moneda"],
                    "ruc_emisor": ruc_emisor,
                    "razon_social_emisor": nombre_emisor_ocr,
                    "num_items": len(resultado_parsing["items"]),
                },
                "validacion_sunat": {
                    "estado_ruc": validacion_sunat.get("estado_ruc"),
                    "condicion_ruc": validacion_sunat.get("condicion_ruc"),
                    "ciiu": validacion_sunat.get("ciiu"),
                    "pasa_reglas": validacion_sunat.get("pasa_reglas_basicas"),
                    "coincide_nombre": validacion_sunat.get("coincide_nombre"),
                },
                "clasificacion": {
                    "categoria_gasto": clasificacion["categoria_gasto"],
                    "porcentaje_deduccion": clasificacion["porcentaje_deduccion"],
                    "ciiu_utilizado": clasificacion.get("ciiu_utilizado"),
                },
                "mensaje": "Archivo procesado exitosamente"
            }

        except Exception as e:
            logger.error(f"[Workflow] ERROR procesando {nombre_archivo}: {type(e).__name__}: {str(e)}", exc_info=True)
            try:
                self.session.rollback()
            except Exception:
                pass

            return {
                "exito": False,
                "duplicado": False,
                "comprobante_id": None,
                "hash_archivo": contexto.hash_archivo if contexto and hasattr(contexto, 'hash_archivo') else None,
                "error": str(e),
                "error_tipo": type(e).__name__,
                "mensaje": f"Error en workflow: {str(e)}"
            }
