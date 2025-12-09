from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime
from typing import Dict, Tuple

from agno.agent import Agent

from app.features.agents.models import ComprobanteParsed
from app.features.agents.prompts import PROMPT_SISTEMA
from app.features.agents.pipeline_context import PipelineContext
from app.libs.models.model_selector import get_ollama
from app.libs.ocr.imagen_ocr import extraer_texto_img
from app.libs.ocr.pdf_extractor import extraer_texto_pdf

class AgenteParseador:
    def __init__(self, contexto: PipelineContext):
        self.contexto = contexto
        self.agent = Agent(
            name="ParseadorComprobantes",
            model=get_ollama(),
            instructions=[PROMPT_SISTEMA],
            markdown=False,
        )

    def _ejecutar_ocr(self, ruta_archivo: str, mime_type: str) -> tuple[str, float]:
        if mime_type == "application/pdf":
            paginas = extraer_texto_pdf(ruta_archivo)
            textos = [p["texto"] for p in paginas]
            texto_completo = "\n===PÁGINA===\n".join(textos)
            return texto_completo, 1.0  # PDFs digitales tienen confianza alta
        else:
            resultado = extraer_texto_img(ruta_archivo)
            return resultado["texto"], resultado.get("confianza_promedio", 0.0)

    def _fallback_parse(self, texto_ocr: str, confianza_ocr: float) -> Dict:
        lines = [ln.strip() for ln in texto_ocr.splitlines() if ln.strip()]
        norm_text = texto_ocr.upper()
        norm_ruc_text = texto_ocr.translate(str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "B": "8", "S": "5", "Z": "2"}))

        # RUC
        ruc_match = re.search(r"\b\d{11}\b", norm_ruc_text)
        ruc = ruc_match.group(0) if ruc_match else "00000000000"

        # Emisor
        razon_social = ""
        if ruc_match:
            pos = norm_ruc_text.find(ruc)
            for idx, ln in enumerate(lines):
                if ruc in ln.replace(" ", ""):
                    razon_social = lines[idx - 1] if idx > 0 else ""
                    break
        if not razon_social and lines:
            razon_social = lines[0]

        # Serie y número
        serie_numero_match = re.search(r"\b([A-Z]{1,4}\d{0,3})[-\s]*0*([0-9]{1,8})\b", norm_text)
        serie = serie_numero_match.group(1) if serie_numero_match else "SIN_SERIE"
        numero = serie_numero_match.group(2) if serie_numero_match else "0"

        # Fecha
        fecha_match = re.search(r"(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})", texto_ocr)
        fecha_norm = datetime(1970, 1, 1).date()
        if fecha_match:
            fecha_raw = fecha_match.group(1)
            try:
                if "-" in fecha_raw and fecha_raw[4] == "-":
                    fecha_norm = datetime.strptime(fecha_raw, "%Y-%m-%d").date()
                else:
                    fecha_norm = datetime.strptime(fecha_raw.replace("/", "-"), "%d-%m-%Y").date()
            except Exception:
                pass

        # Totales
        total_patterns = [
            r"TOTAL\s*[:]?\s*([0-9]+[\.,][0-9]{2})",
            r"TOTAL\s+[A-Z/]*\s*([0-9]+[\.,][0-9]{2})",
            r"IMPORTE\s*[:]?\s*([0-9]+[\.,][0-9]{2})",
        ]
        monto_total = 0.0
        for pat in total_patterns:
            m = re.search(pat, norm_text)
            if m:
                try:
                    monto_total = float(m.group(1).replace(",", "."))
                    break
                except Exception:
                    continue

        # limitar a 10 caracteres por esquema BD: usar defaults cortos
        if "FACTURA" in norm_text:
            tipo = "factura"
        elif "BOLETA" in norm_text:
            tipo = "boleta"
        else:
            tipo = "boleta"
        origen = "electronico" if "ELECTRONIC" in norm_text else "fisico"

        # Items heurísticos
        items = []
        item_lines = []
        for ln in lines:
            if re.search(r"(TOTAL|IGV|SUB\s*TOTAL)", ln.upper()):
                continue
            nums = re.findall(r"[0-9]+[\.,]?[0-9]*", ln)
            if len(nums) >= 2:
                item_lines.append(ln)

        for ln in item_lines:
            nums = re.findall(r"[0-9]+[\.,]?[0-9]*", ln)
            desc = re.sub(r"[0-9]+[\.,]?[0-9]*", "", ln).strip(" -:\t")
            qty = 1.0
            precio_unit = 0.0
            monto_item = 0.0
            try:
                if len(nums) >= 3:
                    qty = float(nums[0].replace(",", "."))
                    precio_unit = float(nums[1].replace(",", "."))
                    monto_item = float(nums[2].replace(",", "."))
                elif len(nums) == 2:
                    qty = 1.0
                    precio_unit = float(nums[0].replace(",", "."))
                    monto_item = float(nums[1].replace(",", "."))
            except Exception:
                pass

            if desc == "":
                desc = "ITEM"

            items.append({
                "descripcion": desc,
                "cantidad": qty,
                "precio_unitario": precio_unit,
                "monto_item": monto_item if monto_item else precio_unit,
            })

        if not items:
            items.append({
                "descripcion": "CONSUMO",
                "cantidad": 1.0,
                "precio_unitario": monto_total,
                "monto_item": monto_total,
            })

        fallback = {
            "comprobante": {
                "tipo_comprobante": tipo,
                "serie": serie,
                "numero": numero,
                "fecha_emision": fecha_norm.isoformat(),
                "moneda": "PEN",
                "monto_total": monto_total if monto_total else sum(i["monto_item"] for i in items),
                "origen": origen,
            },
            "emisor": {
                "ruc": ruc,
                "razon_social": razon_social,
                "nombre_comercial": None,
            },
            "items": items,
            "cliente": {
                "nombre_cliente": None,
                "doc_cliente": None,
                "tipo_doc_cliente": None,
            },
            "confianza_parsing": confianza_ocr,
            "texto_completo_ocr": texto_ocr,
        }
        return fallback

    def _extraer_json_desde_respuesta(self, response) -> Tuple[Dict, str]:
        if hasattr(response, "content"):
            raw_content = response.content
        else:
            raw_content = str(response)

        cleaned_content = raw_content.replace("```json", "").replace("```", "").strip()

        if not cleaned_content:
            raise ValueError("Respuesta vacía del LLM")

        try:
            resultado_json = json.loads(cleaned_content)
            return resultado_json, raw_content
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned_content, flags=re.DOTALL)
            if not match:
                raise
            bloque = match.group(0)
            resultado_json = json.loads(bloque)
            return resultado_json, raw_content

    def parsear_archivo(self, contenido: bytes, mime_type: str, nombre_archivo: str) -> Dict:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{nombre_archivo}") as tmp:
            tmp.write(contenido)
            tmp.flush()
            ruta_tmp = tmp.name

        try:
            texto_ocr, confianza_ocr = self._ejecutar_ocr(ruta_tmp, mime_type)

            self.contexto.set("texto_ocr", texto_ocr)
            self.contexto.set("confianza_ocr", confianza_ocr)

            response = self.agent.run(f"TEXTO OCR A PROCESAR:\n{texto_ocr}")

            parsed_dict = None
            raw_content = ""

            try:
                parsed_dict, raw_content = self._extraer_json_desde_respuesta(response)
            except Exception as e:
                print(f"Error decodificando JSON del LLM: {e}")
                print(f"Contenido recibido: {raw_content}")
                parsed_dict = self._fallback_parse(texto_ocr, confianza_ocr)

            parsed_dict["confianza_parsing"] = parsed_dict.get("confianza_parsing", confianza_ocr)
            parsed_dict["texto_completo_ocr"] = texto_ocr

            try:
                parsed = ComprobanteParsed(**parsed_dict)
            except Exception as e:
                print(f"Error validando ComprobanteParsed: {e}")
                parsed = ComprobanteParsed(**self._fallback_parse(texto_ocr, confianza_ocr))

            self.contexto.comprobante_parseado = parsed.model_dump()
            return self.contexto.comprobante_parseado

        finally:
            try:
                if os.path.exists(ruta_tmp):
                    os.unlink(ruta_tmp)
            except Exception:
                pass
