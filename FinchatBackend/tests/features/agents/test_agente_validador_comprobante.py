"""Tests unitarios para Agente Validador de Comprobante."""

import pytest
from unittest.mock import Mock, MagicMock

from app.features.agents.agente_validador_comprobante import AgenteValidadorComprobante
from app.db.models import Comprobante
from datetime import date


@pytest.fixture
def mock_comprobante_repo():
    """Mock del repositorio de comprobantes."""
    return Mock()


@pytest.fixture
def agente_validador(mock_comprobante_repo):
    """Fixture del agente validador."""
    return AgenteValidadorComprobante(mock_comprobante_repo)


class TestCalcularHash:
    """Tests para cálculo de hash."""

    def test_calcular_hash_contenido_simple(self, agente_validador):
        """Test que el hash se calcula correctamente."""
        contenido = b"Test content"
        hash_result = agente_validador.tool_calcular_hash(contenido)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 64  # SHA-256 produce 64 caracteres hex

    def test_calcular_hash_mismo_contenido_mismo_hash(self, agente_validador):
        """Test que el mismo contenido produce el mismo hash."""
        contenido = b"Test content"
        hash1 = agente_validador.tool_calcular_hash(contenido)
        hash2 = agente_validador.tool_calcular_hash(contenido)

        assert hash1 == hash2

    def test_calcular_hash_diferente_contenido_diferente_hash(self, agente_validador):
        """Test que diferente contenido produce diferente hash."""
        contenido1 = b"Content 1"
        contenido2 = b"Content 2"

        hash1 = agente_validador.tool_calcular_hash(contenido1)
        hash2 = agente_validador.tool_calcular_hash(contenido2)

        assert hash1 != hash2


class TestValidarDuplicadoPorHash:
    """Tests para validación de duplicados por hash."""

    def test_no_duplicado_cuando_no_existe(self, agente_validador, mock_comprobante_repo):
        """Test que retorna None cuando no hay duplicado."""
        mock_comprobante_repo.buscar_por_hash.return_value = None

        resultado = agente_validador.tool_validar_duplicado_por_hash(
            usuario_id=1,
            hash_archivo="abc123"
        )

        assert resultado is None
        mock_comprobante_repo.buscar_por_hash.assert_called_once_with(
            id_usuario=1,
            hash_archivo="abc123"
        )

    def test_duplicado_cuando_existe(self, agente_validador, mock_comprobante_repo):
        """Test que identifica duplicado correctamente."""
        # Mock de comprobante existente
        mock_comprobante = MagicMock(spec=Comprobante)
        mock_comprobante.id_comprobante = 123
        mock_comprobante.serie = "EB01"
        mock_comprobante.numero = "4847"
        mock_comprobante.fecha_emision = date(2025, 8, 2)
        mock_comprobante.monto_total = 66.00

        mock_comprobante_repo.buscar_por_hash.return_value = mock_comprobante

        resultado = agente_validador.tool_validar_duplicado_por_hash(
            usuario_id=1,
            hash_archivo="abc123"
        )

        assert resultado is not None
        assert resultado["es_duplicado"] is True
        assert resultado["tipo_duplicado"] == "hash"
        assert resultado["comprobante_id"] == 123
        assert resultado["serie"] == "EB01"
        assert resultado["numero"] == "4847"
        assert resultado["fecha_emision"] == "2025-08-02"
        assert resultado["monto_total"] == 66.00


class TestValidarDuplicadoPorEmisorSerieNumero:
    """Tests para validación de duplicados por emisor/serie/número."""

    def test_no_duplicado_cuando_no_existe(self, agente_validador, mock_comprobante_repo):
        """Test que retorna None cuando no hay duplicado."""
        mock_comprobante_repo.buscar_por_emisor_serie_numero.return_value = None

        resultado = agente_validador.tool_validar_duplicado_por_emisor_serie_numero(
            usuario_id=1,
            emisor_id=10,
            serie="EB01",
            numero="4847"
        )

        assert resultado is None

    def test_duplicado_cuando_existe(self, agente_validador, mock_comprobante_repo):
        """Test que identifica duplicado correctamente."""
        mock_comprobante = MagicMock(spec=Comprobante)
        mock_comprobante.id_comprobante = 456
        mock_comprobante.hash_archivo = "xyz789"
        mock_comprobante.fecha_emision = date(2025, 7, 15)
        mock_comprobante.monto_total = 120.50

        mock_comprobante_repo.buscar_por_emisor_serie_numero.return_value = mock_comprobante

        resultado = agente_validador.tool_validar_duplicado_por_emisor_serie_numero(
            usuario_id=1,
            emisor_id=10,
            serie="F001",
            numero="123"
        )

        assert resultado is not None
        assert resultado["es_duplicado"] is True
        assert resultado["tipo_duplicado"] == "emisor_serie_numero"
        assert resultado["comprobante_id"] == 456
        assert resultado["hash_archivo"] == "xyz789"


class TestValidarArchivo:
    """Tests para validación completa de archivo."""

    def test_validar_archivo_no_duplicado(self, agente_validador, mock_comprobante_repo):
        """Test flujo completo cuando no hay duplicado."""
        mock_comprobante_repo.buscar_por_hash.return_value = None

        contenido = b"Test PDF content"
        resultado = agente_validador.validar_archivo(
            usuario_id=1,
            contenido=contenido
        )

        assert resultado["es_duplicado"] is False
        assert "hash_archivo" in resultado
        assert len(resultado["hash_archivo"]) == 64

    def test_validar_archivo_duplicado(self, agente_validador, mock_comprobante_repo):
        """Test flujo completo cuando hay duplicado (short-circuit)."""
        mock_comprobante = MagicMock(spec=Comprobante)
        mock_comprobante.id_comprobante = 999
        mock_comprobante.serie = "B002"
        mock_comprobante.numero = "45"
        mock_comprobante.fecha_emision = date(2025, 9, 15)
        mock_comprobante.monto_total = 250.75

        mock_comprobante_repo.buscar_por_hash.return_value = mock_comprobante

        contenido = b"Duplicate PDF content"
        resultado = agente_validador.validar_archivo(
            usuario_id=1,
            contenido=contenido
        )

        assert resultado["es_duplicado"] is True
        assert resultado["tipo_duplicado"] == "hash"
        assert resultado["comprobante_id"] == 999
        assert "hash_archivo" in resultado
