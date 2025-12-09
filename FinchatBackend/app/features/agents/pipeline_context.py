from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.libs.sunat_scraper.ruc_scraper import SunatRucScraper
# GrapState (LangGraph)

@dataclass
class PipelineContext:
    usuario_id: Optional[int] = None
    nombre_archivo: Optional[str] = None
    mime_type: Optional[str] = None

    hash_archivo: Optional[str] = None
    es_duplicado: bool = False
    comprobante_parseado: Optional[Dict] = None
    validacion_sunat: Optional[Dict] = None
    clasificacion: Optional[Dict] = None
    comprobante_id: Optional[int] = None

    # cache para los datos de sunat extraidos
    sunat_cache: Dict[str, Dict] = field(default_factory=dict)

    datos: Dict[str, Any] = field(default_factory=dict) # datos extra

    def set(self, key: str, value: Any) -> None:
        self.datos[key] = value

    def get(self, key: str, default=None) -> Any:
        return self.datos.get(key, default)

    async def get_sunat_data(self, ruc: str) -> Optional[Dict]:
        if ruc not in self.sunat_cache:
            scraper = SunatRucScraper()
            self.sunat_cache[ruc] = await scraper.consultar_ruc(ruc)

        return self.sunat_cache[ruc]

    def to_dict(self) -> Dict:
        return {
            "usuario_id": self.usuario_id,
            "nombre_archivo": self.nombre_archivo,
            "mime_type": self.mime_type,
            "hash_archivo": self.hash_archivo,
            "es_duplicado": self.es_duplicado,
            "comprobante_id": self.comprobante_id,
            "sunat_cache_keys": list(self.sunat_cache.keys()),
            "tiene_parseado": self.comprobante_parseado is not None,
            "tiene_validacion": self.validacion_sunat is not None,
            "tiene_clasificacion": self.clasificacion is not None,
        }

    def reset(self) -> None:
        self.hash_archivo = None
        self.es_duplicado = False
        self.comprobante_parseado = None
        self.validacion_sunat = None
        self.clasificacion = None
        self.comprobante_id = None
        self.datos.clear()
