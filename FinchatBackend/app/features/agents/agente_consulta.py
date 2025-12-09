from __future__ import annotations

import json
from datetime import date, datetime
from typing import Dict, List, Optional

from agno.tools import Toolkit
from agno.agent import Agent
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.db.models import Comprobante, Emisor, Clasificacion
from app.db.repositories.comprobante_repositorio import ComprobanteRepositorio
from app.db.repositories.emisor_repositorio import EmisorRepositorio
from app.libs.models.model_selector import get_ollama
from app.features.agents.prompts.consulta import PROMPT_SISTEMA

class QueryToolkit(Toolkit):
    def __init__(self, session: Session, usuario_id: int):
        super().__init__(
            name="query_tools",
            tools=[
                self.buscar_comprobantes,
                self.obtener_totales,
                self.buscar_por_emisor,
            ],
        )
        self.session = session
        self.usuario_id = usuario_id
        self.comprobante_repo = ComprobanteRepositorio(session)
        self.emisor_repo = EmisorRepositorio(session)

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
        """
        Buscar comprobantes con filtros múltiples.

        Args:
            ruc_emisor: RUC del emisor (11 dígitos)
            fecha_desde: Fecha desde (formato YYYY-MM-DD)
            fecha_hasta: Fecha hasta (formato YYYY-MM-DD)
            categoria: Categoría de gasto
            monto_min: Monto mínimo
            monto_max: Monto máximo
            limit: Límite de resultados (default 50)

        Returns:
            JSON con lista de comprobantes encontrados
        """
        query = (
            self.session.query(Comprobante)
            .join(Emisor, Comprobante.id_emisor == Emisor.id_emisor)
            .outerjoin(Clasificacion, Comprobante.id_comprobante == Clasificacion.id_comprobante)
            .filter(Comprobante.id_usuario == self.usuario_id)
        )

        # Aplicar filtros
        if ruc_emisor:
            query = query.filter(Emisor.ruc == ruc_emisor)

        if fecha_desde:
            try:
                fecha_d = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
                query = query.filter(Comprobante.fecha_emision >= fecha_d)
            except ValueError:
                pass

        if fecha_hasta:
            try:
                fecha_h = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
                query = query.filter(Comprobante.fecha_emision <= fecha_h)
            except ValueError:
                pass

        if categoria:
            query = query.filter(Clasificacion.categoria_gasto.ilike(f"%{categoria}%"))

        if monto_min is not None:
            query = query.filter(Comprobante.monto_total >= monto_min)

        if monto_max is not None:
            query = query.filter(Comprobante.monto_total <= monto_max)

        # Limitar resultados
        comprobantes = query.limit(limit).all()

        # Formatear respuesta
        resultados = []
        for comp in comprobantes:
            resultados.append({
                "id_comprobante": comp.id_comprobante,
                "serie": comp.serie,
                "numero": comp.numero,
                "fecha_emision": comp.fecha_emision.isoformat(),
                "monto_total": float(comp.monto_total),
                "moneda": comp.moneda,
                "emisor_ruc": comp.emisor.ruc if comp.emisor else None,
                "emisor_nombre": comp.emisor.razon_social if comp.emisor else None,
                "categoria": comp.clasificacion[0].categoria_gasto if comp.clasificacion else None,
            })

        return json.dumps({
            "total_encontrados": len(resultados),
            "comprobantes": resultados,
            "limit": limit
        }, ensure_ascii=False)

    def obtener_totales(
        self,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        agrupar_por: Optional[str] = None,
    ) -> str:
        """
        Obtener totales y agregaciones de comprobantes.

        Args:
            fecha_desde: Fecha desde (formato YYYY-MM-DD)
            fecha_hasta: Fecha hasta (formato YYYY-MM-DD)
            agrupar_por: Campo para agrupar ('categoria', 'emisor', 'mes')

        Returns:
            JSON con totales calculados
        """
        query = (
            self.session.query(Comprobante)
            .filter(Comprobante.id_usuario == self.usuario_id)
        )

        # Aplicar filtros de fecha
        if fecha_desde:
            try:
                fecha_d = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
                query = query.filter(Comprobante.fecha_emision >= fecha_d)
            except ValueError:
                pass

        if fecha_hasta:
            try:
                fecha_h = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
                query = query.filter(Comprobante.fecha_emision <= fecha_h)
            except ValueError:
                pass

        # Agregaciones básicas
        total_gastado = query.with_entities(
            func.sum(Comprobante.monto_total)
        ).scalar() or 0.0

        promedio = query.with_entities(
            func.avg(Comprobante.monto_total)
        ).scalar() or 0.0

        cantidad = query.count()

        resultado = {
            "total_gastado": float(total_gastado),
            "promedio_comprobante": float(promedio),
            "cantidad_comprobantes": cantidad,
        }

        # Agrupación opcional
        if agrupar_por == "categoria":
            query_cat = (
                self.session.query(
                    Clasificacion.categoria_gasto,
                    func.sum(Comprobante.monto_total).label("total"),
                    func.count(Comprobante.id_comprobante).label("cantidad")
                )
                .join(Comprobante, Clasificacion.id_comprobante == Comprobante.id_comprobante)
                .filter(Comprobante.id_usuario == self.usuario_id)
            )

            if fecha_desde:
                fecha_d = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
                query_cat = query_cat.filter(Comprobante.fecha_emision >= fecha_d)

            if fecha_hasta:
                fecha_h = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
                query_cat = query_cat.filter(Comprobante.fecha_emision <= fecha_h)

            por_categoria = []
            for cat, total, cant in query_cat.group_by(Clasificacion.categoria_gasto).all():
                por_categoria.append({
                    "categoria": cat,
                    "total": float(total),
                    "cantidad": cant
                })

            resultado["por_categoria"] = por_categoria

        return json.dumps(resultado, ensure_ascii=False)

    def buscar_por_emisor(
        self,
        texto_busqueda: str,
    ) -> str:
        """
        Buscar comprobantes por RUC o nombre del emisor.

        Args:
            texto_busqueda: RUC (11 dígitos) o nombre parcial del emisor

        Returns:
            JSON con comprobantes del emisor + totales
        """
        # Buscar emisor
        emisores = (
            self.session.query(Emisor)
            .filter(
                or_(
                    Emisor.ruc == texto_busqueda,
                    Emisor.razon_social.ilike(f"%{texto_busqueda}%"),
                    Emisor.nombre_comercial.ilike(f"%{texto_busqueda}%")
                )
            )
            .all()
        )

        if not emisores:
            return json.dumps({
                "encontrado": False,
                "mensaje": f"No se encontró emisor con '{texto_busqueda}'"
            }, ensure_ascii=False)

        # Tomar el primer emisor (o todos si hay múltiples)
        emisor = emisores[0]

        # Buscar comprobantes de este emisor
        comprobantes = (
            self.session.query(Comprobante)
            .filter(
                and_(
                    Comprobante.id_usuario == self.usuario_id,
                    Comprobante.id_emisor == emisor.id_emisor
                )
            )
            .order_by(Comprobante.fecha_emision.desc())
            .limit(50)
            .all()
        )

        # Calcular totales
        total = sum(float(c.monto_total) for c in comprobantes)

        resultados = []
        for comp in comprobantes:
            resultados.append({
                "serie": comp.serie,
                "numero": comp.numero,
                "fecha": comp.fecha_emision.isoformat(),
                "monto": float(comp.monto_total),
                "moneda": comp.moneda,
            })

        return json.dumps({
            "encontrado": True,
            "emisor": {
                "ruc": emisor.ruc,
                "razon_social": emisor.razon_social,
                "nombre_comercial": emisor.nombre_comercial,
            },
            "cantidad_comprobantes": len(comprobantes),
            "total_gastado": total,
            "comprobantes": resultados,
        }, ensure_ascii=False)

# intpreta -> LLM capturar campos TOOLS SELECT -> GENERAR informacion
class AgenteConsulta:
    def __init__(self, session: Session, usuario_id: int):
        self.session = session
        self.usuario_id = usuario_id

        self.agent = Agent(
            name="AgenteConsulta",
            model=get_ollama(),
            tools=[QueryToolkit(session, usuario_id)],
            instructions=[PROMPT_SISTEMA],
            markdown=True,
            add_datetime_to_context=True,
            tool_call_limit=2,
            tool_choice="required",
            debug_mode=True,
            debug_level=2,
        )

    def consultar(self, query: str) -> Dict:
        """
        Procesar consulta en lenguaje natural.

        Args:
            query: Pregunta del usuario

        Returns:
            Dict con respuesta y datos estructurados
        """
        response = self.agent.run(query)

        return {
            "respuesta": response.content,
            "tipo": "consulta",
        }
