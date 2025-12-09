"""Tests unitarios para PipelineContext."""

import pytest
from unittest.mock import patch, Mock

from app.features.agents.pipeline_context import PipelineContext


class TestPipelineContextInicialization:
    """Tests para inicialización del contexto."""

    def test_inicializacion_vacia(self):
        """Test que el contexto se inicializa vacío."""
        contexto = PipelineContext()

        assert contexto.usuario_id is None
        assert contexto.hash_archivo is None
        assert contexto.es_duplicado is False
        assert contexto.comprobante_parseado is None
        assert contexto.validacion_sunat is None
        assert contexto.clasificacion is None
        assert contexto.comprobante_id is None
        assert len(contexto.sunat_cache) == 0
        assert len(contexto.datos) == 0

    def test_inicializacion_con_datos(self):
        """Test inicialización con datos."""
        contexto = PipelineContext(
            usuario_id=1,
            nombre_archivo="test.pdf",
            mime_type="application/pdf"
        )

        assert contexto.usuario_id == 1
        assert contexto.nombre_archivo == "test.pdf"
        assert contexto.mime_type == "application/pdf"


class TestSetGet:
    """Tests para métodos set/get genéricos."""

    def test_set_y_get_dato(self):
        """Test guardar y recuperar dato genérico."""
        contexto = PipelineContext()

        contexto.set("clave_test", "valor_test")
        valor = contexto.get("clave_test")

        assert valor == "valor_test"

    def test_get_con_default(self):
        """Test get con valor por defecto."""
        contexto = PipelineContext()

        valor = contexto.get("clave_inexistente", "default")

        assert valor == "default"

    def test_set_sobrescribe(self):
        """Test que set sobrescribe valores."""
        contexto = PipelineContext()

        contexto.set("clave", "valor1")
        contexto.set("clave", "valor2")

        assert contexto.get("clave") == "valor2"


class TestGetSunatData:
    """Tests para cache de datos SUNAT."""

    @patch('app.features.agents.pipeline_context.SunatRucScraper')
    def test_get_sunat_data_primera_vez_hace_scraping(self, mock_scraper_class):
        """Test que la primera consulta hace scraping."""
        # Mock del scraper
        mock_scraper = Mock()
        mock_scraper.consultar_ruc.return_value = {
            "razon_social": "TEST SAC",
            "estado_ruc": "ACTIVO"
        }
        mock_scraper_class.return_value = mock_scraper

        contexto = PipelineContext()
        resultado = contexto.get_sunat_data("10470799531")

        assert resultado["razon_social"] == "TEST SAC"
        assert resultado["estado_ruc"] == "ACTIVO"
        mock_scraper.consultar_ruc.assert_called_once_with("10470799531")

        # Verificar que se guardó en cache
        assert "10470799531" in contexto.sunat_cache

    @patch('app.features.agents.pipeline_context.SunatRucScraper')
    def test_get_sunat_data_segunda_vez_usa_cache(self, mock_scraper_class):
        """Test que la segunda consulta usa cache (no hace scraping)."""
        mock_scraper = Mock()
        mock_scraper.consultar_ruc.return_value = {
            "razon_social": "TEST SAC",
            "estado_ruc": "ACTIVO"
        }
        mock_scraper_class.return_value = mock_scraper

        contexto = PipelineContext()

        # Primera llamada
        resultado1 = contexto.get_sunat_data("10470799531")

        # Segunda llamada (debe usar cache)
        resultado2 = contexto.get_sunat_data("10470799531")

        # Verificar que solo se llamó una vez al scraper
        assert mock_scraper.consultar_ruc.call_count == 1

        # Verificar que ambos resultados son iguales
        assert resultado1 == resultado2

    @patch('app.features.agents.pipeline_context.SunatRucScraper')
    def test_get_sunat_data_multiples_rucs(self, mock_scraper_class):
        """Test que diferentes RUCs se cachean independientemente."""
        mock_scraper = Mock()

        def consultar_mock(ruc):
            return {"razon_social": f"EMPRESA {ruc}"}

        mock_scraper.consultar_ruc.side_effect = consultar_mock
        mock_scraper_class.return_value = mock_scraper

        contexto = PipelineContext()

        # Consultar diferentes RUCs
        resultado1 = contexto.get_sunat_data("11111111111")
        resultado2 = contexto.get_sunat_data("22222222222")

        assert resultado1["razon_social"] == "EMPRESA 11111111111"
        assert resultado2["razon_social"] == "EMPRESA 22222222222"

        # Verificar cache
        assert len(contexto.sunat_cache) == 2
        assert "11111111111" in contexto.sunat_cache
        assert "22222222222" in contexto.sunat_cache


class TestToDict:
    """Tests para serialización del contexto."""

    def test_to_dict_basico(self):
        """Test serialización básica."""
        contexto = PipelineContext(
            usuario_id=1,
            nombre_archivo="test.pdf",
            hash_archivo="abc123"
        )

        dict_result = contexto.to_dict()

        assert dict_result["usuario_id"] == 1
        assert dict_result["nombre_archivo"] == "test.pdf"
        assert dict_result["hash_archivo"] == "abc123"
        assert dict_result["es_duplicado"] is False

    def test_to_dict_con_cache_sunat(self):
        """Test que muestra keys del cache SUNAT."""
        contexto = PipelineContext()
        contexto.sunat_cache["10470799531"] = {"razon_social": "TEST"}
        contexto.sunat_cache["20123456789"] = {"razon_social": "OTHER"}

        dict_result = contexto.to_dict()

        assert len(dict_result["sunat_cache_keys"]) == 2
        assert "10470799531" in dict_result["sunat_cache_keys"]
        assert "20123456789" in dict_result["sunat_cache_keys"]

    def test_to_dict_flags_de_datos(self):
        """Test flags de presencia de datos."""
        contexto = PipelineContext()

        dict_result = contexto.to_dict()
        assert dict_result["tiene_parseado"] is False
        assert dict_result["tiene_validacion"] is False
        assert dict_result["tiene_clasificacion"] is False

        # Agregar datos
        contexto.comprobante_parseado = {"serie": "EB01"}
        contexto.validacion_sunat = {"estado": "ACTIVO"}
        contexto.clasificacion = {"categoria": "test"}

        dict_result = contexto.to_dict()
        assert dict_result["tiene_parseado"] is True
        assert dict_result["tiene_validacion"] is True
        assert dict_result["tiene_clasificacion"] is True


class TestReset:
    """Tests para reset del contexto."""

    def test_reset_limpia_datos(self):
        """Test que reset limpia los datos del comprobante."""
        contexto = PipelineContext()

        # Llenar con datos
        contexto.hash_archivo = "abc123"
        contexto.es_duplicado = True
        contexto.comprobante_parseado = {"test": "data"}
        contexto.validacion_sunat = {"estado": "ACTIVO"}
        contexto.clasificacion = {"categoria": "test"}
        contexto.comprobante_id = 123
        contexto.set("custom_data", "value")

        # Reset
        contexto.reset()

        # Verificar que se limpió
        assert contexto.hash_archivo is None
        assert contexto.es_duplicado is False
        assert contexto.comprobante_parseado is None
        assert contexto.validacion_sunat is None
        assert contexto.clasificacion is None
        assert contexto.comprobante_id is None
        assert len(contexto.datos) == 0

    def test_reset_mantiene_cache_sunat(self):
        """Test que reset mantiene el cache SUNAT."""
        contexto = PipelineContext()

        # Agregar al cache
        contexto.sunat_cache["10470799531"] = {"razon_social": "TEST"}

        # Reset
        contexto.reset()

        # Verificar que el cache se mantiene
        assert "10470799531" in contexto.sunat_cache
        assert contexto.sunat_cache["10470799531"]["razon_social"] == "TEST"
