"""Tests de integración del pipeline INGESTA completo."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date

from app.features.agents.pipeline_context import PipelineContext
from app.features.agents.agente_validador_comprobante import AgenteValidadorComprobante
from app.features.agents.agente_parseador import AgenteParseador
from app.features.agents.agente_validador_sunat import AgenteValidadorSunat
from app.features.agents.agente_clasificador import AgenteClasificador
from app.features.agents.agente_persistencia import AgentePersistencia


@pytest.fixture
def mock_repositories():
    """Fixture de repositorios mockeados."""
    return {
        "comprobante": Mock(),
        "emisor": Mock(),
        "detalle": Mock(),
        "validacion": Mock(),
        "clasificacion": Mock(),
        "ocr": Mock(),
    }


@pytest.fixture
def contexto_pipeline():
    """Fixture del contexto del pipeline."""
    return PipelineContext(
        usuario_id=1,
        nombre_archivo="test_boleta.pdf",
        mime_type="application/pdf"
    )


class TestPipelineIngestaCompleto:
    """Tests de integración del pipeline INGESTA completo."""

    @patch('app.features.agents.agente_parseador.extraer_texto_pdf')
    @patch('app.features.agents.agente_parseador.Agent')
    def test_flujo_completo_sin_duplicado(
        self,
        mock_agent_class,
        mock_extraer_pdf,
        mock_repositories,
        contexto_pipeline
    ):
        """Test del flujo completo de INGESTA sin duplicado."""

        # === 1. SETUP: Configurar mocks ===

        # Mock: No hay duplicado
        mock_repositories["comprobante"].buscar_por_hash.return_value = None

        # Mock: OCR extrae texto
        mock_extraer_pdf.return_value = [
            {"numero_pagina": 1, "texto": "BOLETA EB01-4847\nRUC: 10470799531"}
        ]

        #Mock: LLM parsea el texto
        mock_agent = Mock()
        mock_response = Mock()
        mock_response.content = """
        {
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
                "razon_social": "TELLO MENDOZA HUMBELINA"
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
        }
        """
        mock_agent.run.return_value = mock_response
        mock_agent_class.return_value = mock_agent

        # Mock: SUNAT devuelve datos
        contexto_pipeline.sunat_cache["10470799531"] = {
            "razon_social": "TELLO MENDOZA HUMBELINA",
            "nombre_comercial": None,
            "estado_ruc": "ACTIVO",
            "condicion_ruc": "HABIDO",
            "ciiu_principal": "5610"  # Restaurante
        }

        # Mock: Persistencia
        mock_emisor = Mock()
        mock_emisor.id_emisor = 10
        mock_repositories["emisor"].buscar_por_ruc.return_value = None
        mock_repositories["emisor"].crear.return_value = mock_emisor

        mock_comprobante = Mock()
        mock_comprobante.id_comprobante = 100
        mock_repositories["comprobante"].crear.return_value = mock_comprobante

        # === 2. EJECUTAR PIPELINE ===

        contenido = b"PDF content"

        # Paso 1: Validador Comprobante
        validador = AgenteValidadorComprobante(mock_repositories["comprobante"])
        resultado_validacion = validador.validar_archivo(1, contenido)

        assert resultado_validacion["es_duplicado"] is False
        contexto_pipeline.hash_archivo = resultado_validacion["hash_archivo"]

        # Paso 2: Parseador
        parseador = AgenteParseador(contexto_pipeline)
        with patch('tempfile.NamedTemporaryFile'), patch('os.unlink'):
            resultado_parsing = parseador.parsear_archivo(
                contenido,
                "application/pdf",
                "test.pdf"
            )
        contexto_pipeline.comprobante_parseado = resultado_parsing

        # Paso 3: Validador SUNAT
        validador_sunat = AgenteValidadorSunat(contexto_pipeline)
        validacion_sunat = validador_sunat.validar_completo(
            "10470799531",
            "TELLO MENDOZA HUMBELINA"
        )
        contexto_pipeline.validacion_sunat = validacion_sunat

        # Paso 4: Clasificador
        clasificador = AgenteClasificador(contexto_pipeline)
        clasificacion = clasificador.tool_clasificar()
        contexto_pipeline.clasificacion = clasificacion

        # Paso 5: Persistencia
        persistencia = AgentePersistencia(
            contexto_pipeline,
            mock_repositories["emisor"],
            mock_repositories["comprobante"],
            mock_repositories["detalle"],
            mock_repositories["validacion"],
            mock_repositories["clasificacion"],
            mock_repositories["ocr"],
        )
        comprobante_id = persistencia.guardar_todo()

        # === 3. VERIFICACIONES ===

        # Verificar parsing
        assert resultado_parsing["comprobante"]["serie"] == "EB01"
        assert resultado_parsing["emisor"]["ruc"] == "10470799531"
        assert len(resultado_parsing["items"]) == 1

        # Verificar validación SUNAT
        assert validacion_sunat["estado_ruc"] == "ACTIVO"
        assert validacion_sunat["ciiu"] == "5610"
        assert validacion_sunat["pasa_reglas_basicas"] is True

        # Verificar clasificación
        assert clasificacion["categoria_gasto"] ==  "hotelesRestaurantes"
        assert clasificacion["porcentaje_deduccion"] == 15.0
        assert clasificacion["ciiu_utilizado"] == "5610"

        # Verificar persistencia
        assert comprobante_id == 100
        mock_repositories["emisor"].crear.assert_called_once()
        mock_repositories["comprobante"].crear.assert_called_once()
        mock_repositories["detalle"].crear.assert_called_once()
        mock_repositories["validacion"].crear.assert_called_once()
        mock_repositories["clasificacion"].crear.assert_called_once()

    def test_flujo_con_duplicado_short_circuit(
        self,
        mock_repositories,
        contexto_pipeline
    ):
        """Test que el flujo se detiene si hay duplicado (short-circuit)."""

        # Mock: Hay un duplicado
        mock_comprobante_duplicado = Mock()
        mock_comprobante_duplicado.id_comprobante = 999
        mock_comprobante_duplicado.serie = "EB01"
        mock_comprobante_duplicado.numero = "4847"
        mock_comprobante_duplicado.fecha_emision = date(2025, 8, 2)
        mock_comprobante_duplicado.monto_total = 66.00

        mock_repositories["comprobante"].buscar_por_hash.return_value = mock_comprobante_duplicado

        # Ejecutar solo el validador
        validador = AgenteValidadorComprobante(mock_repositories["comprobante"])
        contenido = b"PDF duplicado"
        resultado = validador.validar_archivo(1, contenido)

        # Verificar que se detectó duplicado
        assert resultado["es_duplicado"] is True
        assert resultado["comprobante_id"] == 999

        # El pipeline debería detenerse aquí
        # No se ejecutan: Parseador, SUNAT, Clasificador, ni Persistencia
