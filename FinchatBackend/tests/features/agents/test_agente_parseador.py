"""Tests unitarios para Agente Parseador."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from app.features.agents.agente_parseador import (
    AgenteParseador,
    ComprobanteParsed,
    ComprobanteData,
    EmisorData,
    ItemData,
    ClienteData,
)
from app.features.agents.pipeline_context import PipelineContext


@pytest.fixture
def contexto():
    """Fixture del contexto del pipeline."""
    return PipelineContext(
        usuario_id=1,
        nombre_archivo="test.pdf",
        mime_type="application/pdf"
    )


@pytest.fixture
def agente_parseador(contexto):
    """Fixture del agente parseador."""
    with patch('app.features.agents.agente_parseador.Agent'):
        return AgenteParseador(contexto)


class TestModelos:
    """Tests para modelos Pydantic."""

    def test_comprobante_data_valido(self):
        """Test que ComprobanteData valida correctamente."""
        data = ComprobanteData(
            tipo_comprobante="boleta",
            serie="EB01",
            numero="4847",
            fecha_emision="2025-08-02",
            moneda="PEN",
            monto_total=66.00,
            origen="electronico"
        )

        assert data.tipo_comprobante == "boleta"
        assert data.serie == "EB01"
        assert data.monto_total == 66.00

    def test_emisor_data_valido(self):
        """Test que EmisorData valida correctamente."""
        data = EmisorData(
            ruc="10470799531",
            razon_social="TELLO MENDOZA HUMBELINA"
        )

        assert data.ruc == "10470799531"
        assert data.nombre_comercial is None

    def test_item_data_valido(self):
        """Test que ItemData valida correctamente."""
        data = ItemData(
            descripcion="CONSUMO",
            cantidad=1.0,
            precio_unitario=60.00,
            monto_item=66.00
        )

        assert data.descripcion == "CONSUMO"
        assert data.cantidad == 1.0

    def test_comprobante_parsed_completo(self):
        """Test que ComprobanteParsed valida estructura completa."""
        data = ComprobanteParsed(
            comprobante=ComprobanteData(
                tipo_comprobante="boleta",
                serie="EB01",
                numero="4847",
                fecha_emision="2025-08-02",
                moneda="PEN",
                monto_total=66.00,
                origen="electronico"
            ),
            emisor=EmisorData(
                ruc="10470799531",
                razon_social="TELLO MENDOZA HUMBELINA"
            ),
            items=[
                ItemData(
                    descripcion="CONSUMO",
                    cantidad=1.0,
                    precio_unitario=60.00,
                    monto_item=66.00
                )
            ],
            cliente=ClienteData(),
            confianza_parsing=0.95,
            texto_completo_ocr="..."
        )

        assert len(data.items) == 1
        assert data.comprobante.serie == "EB01"
        assert data.emisor.ruc == "10470799531"


class TestEjecutarOCR:
    """Tests para ejecución de OCR."""

    @patch('app.features.agents.agente_parseador.extraer_texto_pdf')
    def test_ejecutar_ocr_pdf(self, mock_extraer_pdf, agente_parseador):
        """Test OCR para archivos PDF."""
        mock_extraer_pdf.return_value = [
            {"numero_pagina": 1, "texto": "Página 1"},
            {"numero_pagina": 2, "texto": "Página 2"}
        ]

        texto, confianza = agente_parseador._ejecutar_ocr(
            "test.pdf",
            "application/pdf"
        )

        assert "Página 1" in texto
        assert "Página 2" in texto
        assert confianza == 1.0  # PDFs tienen confianza 100%
        mock_extraer_pdf.assert_called_once_with("test.pdf")

    @patch('app.features.agents.agente_parseador.extraer_texto_img')
    def test_ejecutar_ocr_imagen(self, mock_extraer_img, agente_parseador):
        """Test OCR para imágenes."""
        mock_extraer_img.return_value = {
            "texto": "Texto de imagen",
            "confianza_promedio": 0.85
        }

        texto, confianza = agente_parseador._ejecutar_ocr(
            "test.jpg",
            "image/jpeg"
        )

        assert texto == "Texto de imagen"
        assert confianza == 0.85
        mock_extraer_img.assert_called_once_with("test.jpg")


class TestBuildFewShots:
    """Tests para construcción de few-shots."""

    def test_build_few_shots_tiene_ejemplos(self, agente_parseador):
        """Test que se construyen mensajes few-shot."""
        mensajes = agente_parseador._build_few_shots()

        # Debe tener pares de user/assistant
        assert len(mensajes) > 0
        assert len(mensajes) % 2 == 0  # Pares

        # Verificar formato
        for i in range(0, len(mensajes), 2):
            assert mensajes[i]["role"] == "user"
            assert mensajes[i+1]["role"] == "assistant"
            assert "TEXTO OCR" in mensajes[i]["content"]


class TestParsearArchivo:
    """Tests para parseo completo de archivo."""

    @patch('app.features.agents.agente_parseador.extraer_texto_pdf')
    @patch('tempfile.NamedTemporaryFile')
    @patch('os.unlink')
    def test_parsear_archivo_pdf_exitoso(
        self,
        mock_unlink,
        mock_tempfile,
        mock_extraer_pdf,
        agente_parseador,
        contexto
    ):
        """Test parseo exitoso de PDF."""
        # Mock tempfile
        mock_tmp = MagicMock()
        mock_tmp.name = "/tmp/test.pdf"
        mock_tmp.__enter__.return_value = mock_tmp
        mock_tempfile.return_value = mock_tmp

        # Mock OCR
        mock_extraer_pdf.return_value = [
            {"numero_pagina": 1, "texto": "BOLETA EB01-4847"}
        ]

        # Mock respuesta del LLM
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "comprobante": {
                "tipo_comprobante": "boleta",
                "serie": "EB01",
                "numero": "4847",
                "fecha_emision": "2025-08-02",
                "moneda": "PEN",
                "monto_total": 66.00,
                "origen": "electronico"
            },
            "emisor": {
                "ruc": "10470799531",
                "razon_social": "TEST EMISOR"
            },
            "items": [
                {
                    "descripcion": "CONSUMO",
                    "cantidad": 1.0,
                    "precio_unitario": 60.00,
                    "monto_item": 66.00
                }
            ],
            "cliente": {}
        })

        agente_parseador.agent.run = MagicMock(return_value=mock_response)

        # Ejecutar
        contenido = b"PDF content"
        resultado = agente_parseador.parsear_archivo(
            contenido=contenido,
            mime_type="application/pdf",
            nombre_archivo="test.pdf"
        )

        # Verificar
        assert resultado["comprobante"]["serie"] == "EB01"
        assert resultado["emisor"]["ruc"] == "10470799531"
        assert len(resultado["items"]) == 1
        assert resultado["confianza_parsing"] == 1.0  # PDF

        # Verificar que se guardó en contexto
        assert contexto.get("texto_ocr") is not None
        assert contexto.get("confianza_ocr") == 1.0
