"""
Scraper de RUC de SUNAT usando Playwright (Async).

Módulo encargado de interactuar con la web de SUNAT para extraer información
de contribuyentes (Razón Social, Estado, Condición, CIIU).
"""

from __future__ import annotations

import logging
import re
from typing import Dict, Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class SunatRucScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.url_consulta = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"

    async def consultar_ruc(self, ruc: str) -> Optional[Dict[str, str]]:
        logger.info(f"Iniciando scraping async SUNAT para RUC: {ruc}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()

            try:
                # Navegar a la página
                await page.goto(self.url_consulta, timeout=30000)

                # Llenar formulario
                await page.wait_for_selector("#txtRuc", state="visible", timeout=10000)
                await page.fill("#txtRuc", ruc)

                # Click en Buscar
                await page.click("#btnAceptar", timeout=5000)

                # Esperar resultados
                await page.wait_for_timeout(5000)

                # Extraer datos
                datos = await self._extraer_datos(page)

                if datos:
                    logger.info(f"✓ RUC {ruc}: {datos.get('razon_social')} - Estado: {datos.get('estado_ruc')} - Condición: {datos.get('condicion_ruc')} - CIIU: {datos.get('ciiu')}")
                else:
                    logger.warning(f"No se pudieron extraer datos para RUC {ruc}")
 
                return datos

            except PlaywrightTimeoutError:
                logger.error(f"Timeout scrapeando SUNAT para RUC {ruc}")
                return None
            except Exception as e:
                logger.error(f"Error scrapeando SUNAT: {e}")
                return None
            finally:
                await browser.close()

    async def _extraer_datos(self, page) -> Optional[Dict[str, str]]:
        try:
            texto_body = await page.inner_text("body")

            if "No se encontraron resultados" in texto_body:
                return None

            resultado = {
                "ruc": "",
                "razon_social": "",
                "nombre_comercial": None,
                "estado_ruc": "",
                "condicion_ruc": "",
                "ciiu": None,
            }

            # Parsing línea por línea
            lines = texto_body.split('\n')

            for i, line in enumerate(lines):
                line = line.strip()

                # RUC y Razón Social
                if "Número de RUC:" in line and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if "-" in next_line:
                        parts = next_line.split("-", 1)
                        if len(parts) == 2:
                            resultado["ruc"] = parts[0].strip()
                            resultado["razon_social"] = parts[1].strip()

                # Nombre Comercial
                if "Nombre Comercial:" in line and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and next_line != "-":
                        resultado["nombre_comercial"] = next_line

                # Estado del Contribuyente
                if "Estado del Contribuyente:" in line:
                    for j in range(i + 1, min(i + 3, len(lines))):
                        next_line = lines[j].strip()
                        if next_line:
                            resultado["estado_ruc"] = next_line
                            break

                # Condición del Contribuyente
                if "Condición del Contribuyente:" in line:
                    for j in range(i + 1, min(i + 3, len(lines))):
                        next_line = lines[j].strip()
                        if next_line:
                            resultado["condicion_ruc"] = next_line
                            break

                # Actividad Económica (CIIU)
                if "Actividad(es) Económica(s):" in line:
                    # Buscar en las próximas líneas
                    for j in range(i + 1, min(i + 10, len(lines))):
                        actividad_line = lines[j].strip()
                        if actividad_line and "Principal" in actividad_line:
                            # Extraer CIIU con regex
                            match = re.search(r'Principal\s*-\s*(\d{4})', actividad_line)
                            if match:
                                resultado["ciiu"] = match.group(1)
                                break
                            # Intento alternativo: cualquier 4 dígitos
                            match = re.search(r'(\d{4})', actividad_line)
                            if match:
                                resultado["ciiu"] = match.group(1)
                                break

            return resultado

        except Exception as e:
            logger.error(f"Error extrayendo datos del DOM: {e}")
            return None
