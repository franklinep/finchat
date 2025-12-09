"""Repositorios para acceso a datos."""

from app.db.repositories.base_repository import BaseRepository
from app.db.repositories.comprobante_repositorio import ComprobanteRepositorio
from app.db.repositories.detalle_comprobante_repositorio import DetalleComprobanteRepositorio
from app.db.repositories.emisor_repositorio import EmisorRepositorio
from app.db.repositories.usuario_repositorio import UsuarioRepositorio
from app.db.repositories.validacion_repositorio import ValidacionRepositorio
from app.db.repositories.clasificacion_repositorio import ClasificacionRepositorio
from app.db.repositories.ocr_pagina_repositorio import OcrPaginaRepositorio

__all__ = [
    "BaseRepository",
    "ComprobanteRepositorio",
    "DetalleComprobanteRepositorio",
    "EmisorRepositorio",
    "UsuarioRepositorio",
    "ValidacionRepositorio",
    "ClasificacionRepositorio",
    "OcrPaginaRepositorio",
]
