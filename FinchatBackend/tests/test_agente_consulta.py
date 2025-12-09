"""Tests unitarios para QueryToolkit del Agente Consulta."""

import pytest
from datetime import date, datetime
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from app.features.agents.agente_consulta import QueryToolkit
from app.db.models import Comprobante, Emisor, Clasificacion


class TestQueryToolkit:
    """Tests para QueryToolkit."""

    @pytest.fixture
    def mock_session(self):
        """Crear session mock."""
        session = Mock(spec=Session)
        return session

    @pytest.fixture
    def toolkit(self, mock_session):
        """Crear toolkit con session mock."""
        return QueryToolkit(session=mock_session, usuario_id=1)

    def test_init(self, toolkit):
        """Test inicialización del toolkit."""
        assert toolkit.usuario_id == 1
        assert toolkit.name == "query_tools"

    def test_buscar_comprobantes_sin_filtros(self, toolkit, mock_session):
        """Test búsqueda sin filtros."""
        # Mock query builder
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query

        # Mock resultados
        mock_comprobante = Mock(spec=Comprobante)
        mock_comprobante.id_comprobante = 1
        mock_comprobante.serie = "F001"
        mock_comprobante.numero = "123"
        mock_comprobante.fecha_emision = date(2025, 12, 1)
        mock_comprobante.monto_total = 100.0
        mock_comprobante.moneda = "PEN"
        mock_comprobante.emisor = Mock(ruc="20123456789", razon_social="Test SAC")
        mock_comprobante.clasificacion = []

        mock_query.all.return_value = [mock_comprobante]

        # Ejecutar
        resultado = toolkit.buscar_comprobantes()

        # Verificar
        assert "total_encontrados" in resultado
        assert "comprobantes" in resultado

    def test_buscar_comprobantes_con_ruc(self, toolkit, mock_session):
        """Test búsqueda filtrando por RUC."""
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        resultado = toolkit.buscar_comprobantes(ruc_emisor="20123456789")

        # Verificar que se llamó filter (por RUC)
        assert mock_query.filter.called

    def test_obtener_totales_basico(self, toolkit, mock_session):
        """Test obtener totales sin agrupación."""
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query

        # Mock agregaciones
        mock_query.with_entities.return_value.scalar.side_effect = [1000.0, 250.0]
        mock_query.count.return_value = 4

        resultado = toolkit.obtener_totales()

        # Verificar estructura
        assert "total_gastado" in resultado
        assert "promedio_comprobante" in resultado
        assert "cantidad_comprobantes" in resultado

    def test_buscar_por_emisor_encontrado(self, toolkit, mock_session):
        """Test búsqueda por emisor exitosa."""
        # Mock emisor
        mock_emisor = Mock(spec=Emisor)
        mock_emisor.id_emisor = 1
        mock_emisor.ruc = "20123456789"
        mock_emisor.razon_social = "Test SAC"
        mock_emisor.nombre_comercial = "Test"

        # Mock query emisor
        mock_query_emisor = MagicMock()
        mock_session.query.return_value = mock_query_emisor
        mock_query_emisor.filter.return_value = mock_query_emisor
        mock_query_emisor.all.return_value = [mock_emisor]

        # Mock comprobantes
        mock_comprobante = Mock(spec=Comprobante)
        mock_comprobante.serie = "F001"
        mock_comprobante.numero = "123"
        mock_comprobante.fecha_emision = date(2025, 12, 1)
        mock_comprobante.monto_total = 100.0
        mock_comprobante.moneda = "PEN"

        mock_query_comp = MagicMock()
        mock_session.query.side_effect = [mock_query_emisor, mock_query_comp]
        mock_query_comp.filter.return_value = mock_query_comp
        mock_query_comp.order_by.return_value = mock_query_comp
        mock_query_comp.limit.return_value = mock_query_comp
        mock_query_comp.all.return_value = [mock_comprobante]

        resultado = toolkit.buscar_por_emisor("20123456789")

        # Verificar
        assert "encontrado" in resultado
        assert "emisor" in resultado

    def test_buscar_por_emisor_no_encontrado(self, toolkit, mock_session):
        """Test búsqueda por emisor sin resultados."""
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []

        resultado = toolkit.buscar_por_emisor("99999999999")

        # Verificar mensaje de no encontrado
        assert "encontrado" in resultado
        assert '"encontrado": false' in resultado.lower()


class TestAgenteConsulta:
    """Tests para AgenteConsulta (integración con Ollama)."""

    @pytest.fixture
    def mock_session(self):
        """Crear session mock."""
        return Mock(spec=Session)

    @pytest.mark.skip("Requiere Ollama corriendo")
    def test_consulta_simple(self, mock_session):
        """Test consulta simple (requiere Ollama)."""
        from app.features.agents.agente_consulta import AgenteConsulta

        agente = AgenteConsulta(session=mock_session, usuario_id=1)
        resultado = agente.consultar("¿Cuánto gasté en total?")

        assert "respuesta" in resultado
        assert "tipo" in resultado
        assert resultado["tipo"] == "consulta"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
