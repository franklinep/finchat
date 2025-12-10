from __future__ import annotations

import logging
from typing import Dict

from app.db.repositories import (
    ClasificacionRepositorio,
    ComprobanteRepositorio,
    DetalleComprobanteRepositorio,
    EmisorRepositorio,
    OcrPaginaRepositorio,
    ValidacionRepositorio,
)
from app.features.agents.pipeline_context import PipelineContext

logger = logging.getLogger(__name__)


from sqlalchemy.orm import Session

class AgentePersistencia:
    def __init__(
        self,
        contexto: PipelineContext,
        session: Session,
        emisor_repo: EmisorRepositorio,
        comprobante_repo: ComprobanteRepositorio,
        detalle_repo: DetalleComprobanteRepositorio,
        validacion_repo: ValidacionRepositorio,
        clasificacion_repo: ClasificacionRepositorio,
        ocr_repo: OcrPaginaRepositorio,
    ):
        self.contexto = contexto
        self.session = session
        self.emisor_repo = emisor_repo
        self.comprobante_repo = comprobante_repo
        self.detalle_repo = detalle_repo
        self.validacion_repo = validacion_repo
        self.clasificacion_repo = clasificacion_repo
        self.ocr_repo = ocr_repo

    def guardar_todo(self) -> int:
        try:
            # Guardar o actualizar emisor
            emisor = self._guardar_emisor()
            emisor_id = emisor.id_emisor

            # Guardar comprobante
            comprobante = self._guardar_comprobante(emisor_id)
            comprobante_id = comprobante.id_comprobante

            # Guardar items del detalle
            self._guardar_items(comprobante_id)

            # Guardar validación SUNAT
            self._guardar_validacion(comprobante_id)

            # Guardar clasificación
            self._guardar_clasificacion(comprobante_id)

            # Guardar páginas OCR (si hay)
            self._guardar_ocr_paginas(comprobante_id)

            logger.info(f"Comprobante {comprobante_id} guardado exitosamente")
            return comprobante_id

        except Exception as e:
            logger.error(f"Error guardando comprobante: {e}")
            raise

    def _guardar_emisor(self):
        emisor_data = self.contexto.comprobante_parseado["emisor"]
        validacion = self.contexto.validacion_sunat

        ruc = "".join(filter(str.isdigit, emisor_data["ruc"]))[:11]

        # Buscar si ya existe
        emisor_existente = self.emisor_repo.buscar_por_ruc(ruc)

        if emisor_existente:
            # Actualizar datos de SUNAT si los tenemos
            if validacion and not validacion.get("fallback"):
                emisor_existente.razon_social = validacion.get("razon_social") or emisor_data["razon_social"]
                emisor_existente.nombre_comercial = validacion.get("nombre_comercial_sunat")
                emisor_existente.ciiu_principal = validacion.get("ciiu")
                emisor_existente.estado_ruc = validacion.get("estado_ruc")
                emisor_existente.condicion_ruc = validacion.get("condicion_ruc")

            logger.info(f"Emisor RUC {ruc} actualizado")
            return emisor_existente
        else:
            # Crear nuevo emisor
            nuevo_emisor = self.emisor_repo.crear(
                ruc=ruc,
                razon_social=validacion.get("razon_social") if validacion else emisor_data["razon_social"],
                nombre_comercial=validacion.get("nombre_comercial_sunat") if validacion else emisor_data.get("nombre_comercial"),
                ciiu_principal=validacion.get("ciiu") if validacion else None,
                estado_ruc=validacion.get("estado_ruc") if validacion else None,
                condicion_ruc=validacion.get("condicion_ruc") if validacion else None,
            )
            self.session.flush()  # Generar ID
            logger.info(f"Nuevo emisor RUC {ruc} creado")
            return nuevo_emisor

    def _guardar_comprobante(self, emisor_id: int):
        comp_data = self.contexto.comprobante_parseado["comprobante"]
        validacion = self.contexto.validacion_sunat

        # Determinar si es deducible
        es_deducible = None
        if validacion:
            es_deducible = validacion.get("pasa_reglas_basicas", False)

        comprobante = self.comprobante_repo.crear(
            id_usuario=self.contexto.usuario_id,
            id_emisor=emisor_id,
            tipo_comprobante=comp_data["tipo_comprobante"],
            serie=comp_data["serie"],
            numero=comp_data["numero"],
            fecha_emision=comp_data["fecha_emision"],
            monto_total=comp_data["monto_total"],
            moneda=comp_data["moneda"],
            origen=comp_data["origen"],
            hash_archivo=self.contexto.hash_archivo,
            estado_procesamiento="procesado",
            es_deducible=es_deducible,
            es_duplicado=False,
            ruta_archivo=None,  # Se puede agregar después
            mime_type=self.contexto.mime_type,
        )

        self.session.flush()  # Generar ID
        return comprobante

    def _guardar_items(self, comprobante_id: int):
        items = self.contexto.comprobante_parseado.get("items", [])

        for item in items:
            self.detalle_repo.crear(
                id_comprobante=comprobante_id,
                descripcion=item["descripcion"],
                cantidad=item.get("cantidad", 1.0),
                precio_unitario=item.get("precio_unitario", 0.0),
                monto_item=item["monto_item"],
            )

        logger.info(f"{len(items)} ítems guardados para comprobante {comprobante_id}")

    def _guardar_validacion(self, comprobante_id: int):
        validacion = self.contexto.validacion_sunat

        if not validacion:
            logger.warning("No hay datos de validación SUNAT para guardar")
            return

        emisor_data = self.contexto.comprobante_parseado["emisor"]

        self.validacion_repo.crear(
            id_comprobante=comprobante_id,
            estado_ruc=validacion.get("estado_ruc"),
            condicion_ruc=validacion.get("condicion_ruc"),
            ciiu_detectado=validacion.get("ciiu"),
            nombre_comercial_sunat=validacion.get("nombre_comercial_sunat"),
            nombre_emisor_ocr=emisor_data.get("razon_social"),
            coincide_nombre=validacion.get("coincide_nombre"),
            pasa_reglas=validacion.get("pasa_reglas_basicas"),
            motivo_no_deducible=validacion.get("motivo_no_deducible"),
        )

    def _guardar_clasificacion(self, comprobante_id: int):
        clasificacion = self.contexto.clasificacion

        if not clasificacion:
            logger.warning("No hay datos de clasificación para guardar")
            return

        self.clasificacion_repo.crear(
            id_comprobante=comprobante_id,
            categoria_gasto=clasificacion["categoria_gasto"],
            porcentaje_deduccion=clasificacion["porcentaje_deduccion"],
            ciiu_utilizado=clasificacion.get("ciiu_utilizado"),
            version_regla=clasificacion.get("version_regla", "v1.0"),
            fuente_clasificacion=clasificacion.get("fuente_clasificacion", "automatico"),
        )

    def _guardar_ocr_paginas(self, comprobante_id: int):
        texto_ocr = self.contexto.get("texto_ocr")
        confianza_ocr = self.contexto.get("confianza_ocr")

        if not texto_ocr:
            return

        self.ocr_repo.crear(
            id_comprobante=comprobante_id,
            numero_pagina=1,
            texto_pagina=texto_ocr,
            confianza_promedio=confianza_ocr,
        )

        logger.info(f"Página OCR guardada para comprobante {comprobante_id}")
