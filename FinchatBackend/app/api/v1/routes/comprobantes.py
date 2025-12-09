from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session

from app.db.sesion import get_db
from app.api.v1.schemas.comprobantes import (
    ComprobanteResumen,
    CrearComprobanteRequest,
    ExtraccionRequest,
    SubirComprobantesResponse,
)
from app.api.v1.schemas.consultas import ConsultaRequest, ConsultaResponse
from app.features.agents.pipeline_ingesta import IngestaWorkflow
from app.features.agents.agente_consulta import AgenteConsulta

comprobantes_router = APIRouter()

@comprobantes_router.post(
    "/comprobantes/subir", response_model=SubirComprobantesResponse
)
async def subir_comprobantes(
    archivos: List[UploadFile] = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    usuarioId = request.state.user.get("sub") if hasattr(request.state, "user") else None
    if usuarioId is None:
        raise HTTPException(status_code=401, detail="Token sin usuario")

    pipeline = IngestaWorkflow(db)

    procesados = []
    for archivo in archivos:
        contenido = await archivo.read()

        # Procesar con pipeline de 5 agentes
        resultado = await pipeline.run(
            input_data={
                "usuario_id": usuarioId,
                "nombre_archivo": archivo.filename or "",
                "mime_type": archivo.content_type or "application/pdf",
                "contenido": contenido,
            }
        )

        # Formatear respuesta
        procesado = {
            "nombreArchivo": archivo.filename or "",
            "hashArchivo": resultado.get("hash_archivo"),
            "esDuplicado": resultado.get("duplicado", False),
            "idComprobante": resultado.get("comprobante_id"),
        }

        # Agregar campos parseados si existen
        if resultado.get("campos_parseados"):
            campos = resultado["campos_parseados"]
            procesado["camposClave"] = {
                "ruc_emisor": campos.get("ruc_emisor"),
                "serie_numero": f"{campos.get('serie')}-{campos.get('numero')}",
                "fecha_emision": campos.get("fecha_emision"),
                "moneda": campos.get("moneda"),
                "monto_total": campos.get("monto_total"),
                "tipo_comprobante": campos.get("tipo_comprobante"),
            }

        # Agregar validación SUNAT si existe
        if resultado.get("validacion_sunat"):
            val = resultado["validacion_sunat"]
            procesado["validacionSunat"] = {
                "ruc": resultado.get("campos_parseados", {}).get("ruc_emisor"),
                "estadoRuc": val.get("estado_ruc"),
                "condicionRuc": val.get("condicion_ruc"),
                "ciiuPrincipal": val.get("ciiu"),
                "pasaReglasBasicas": val.get("pasa_reglas"),
                "motivoNoDeducible": None,
            }

        # Agregar clasificación si existe
        if resultado.get("clasificacion"):
            clas = resultado["clasificacion"]
            procesado["clasificacion"] = {
                "categoriaGasto": clas.get("categoria_gasto"),
                "porcentajeDeduccion": clas.get("porcentaje_deduccion"),
                "versionRegla": "v1.0",
            }

        procesados.append(procesado)

    return {
        "usuarioId": usuarioId,
        "totalArchivos": len(archivos),
        "procesados": procesados,
    }

@comprobantes_router.post("/comprobantes/consultar", response_model=ConsultaResponse)
def consultar_comprobantes(
    payload: ConsultaRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    usuarioId = request.state.user.get("sub") if hasattr(request.state, "user") else None
    if usuarioId is None:
        raise HTTPException(status_code=401, detail="Token sin usuario")

    agente_consulta = AgenteConsulta(db, usuarioId)
    resultado = agente_consulta.consultar(payload.mensaje)

    return resultado
