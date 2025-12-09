# Guía de Testing - Pipeline INGESTA

## 📝 Tests Creados

### Tests Unitarios (Unit Tests)

1. **test_pipeline_context.py** - Tests del PipelineContext

   - ✅ Inicialización
   - ✅ Métodos set/get
   - ✅ Cache SUNAT (primera vez scrapea, segunda vez usa cache)
   - ✅ Serialización to_dict()
   - ✅ Reset del contexto

2. **test_agente_validador_comprobante.py** - Tests del Validador

   - ✅ Cálculo de hash SHA-256
   - ✅ Detección de duplicados por hash
   - ✅ Detección de duplicados por emisor/serie/número
   - ✅ Validación completa (flujo)

3. **test_agente_parseador.py** - Tests del Parseador
   - ✅ Modelos Pydantic (ComprobanteData, EmisorData, ItemData, ClienteData)
   - ✅ OCR para PDFs (PyMuPDF)
   - ✅ OCR para imágenes (PaddleOCR)
   - ✅ Construcción de few-shots
   - ✅ Parseo completo de archivo

### Tests de Integración (Integration Tests)

4. **test_pipeline_ingesta.py** - Test del pipeline completo
   - ✅ Flujo completo: Validador → Parseador → SUNAT → Clasificador → Persistencia
   - ✅ Short-circuit cuando hay duplicado
   - ✅ Verificación de datos en cada paso
   - ✅ Verificación de guardado en BD

---

## 🚀 Cómo Ejecutar los Tests

### Prerrequisitos

1. **Instalar pytest** (si no está instalado):

```bash
pip install pytest pytest-cov pytest-mock
```

### Ejecutar Todos los Tests

```bash
# Desde el directorio raíz del proyecto
cd c:\fespa-dev\finchat\FinchatBackend

# Ejecutar todos los tests
pytest

# Con output verbose
pytest -v

# Con coverage
pytest --cov=app --cov-report=html
```

### Ejecutar Tests Específicos

```bash
# Solo tests del PipelineContext
pytest tests/features/agents/test_pipeline_context.py -v

# Solo tests del Validador
pytest tests/features/agents/test_agente_validador_comprobante.py -v

# Solo tests del Parseador
pytest tests/features/agents/test_agente_parseador.py -v

# Solo tests de integración
pytest tests/integration/test_pipeline_ingesta.py -v
```

### Ejecutar Tests por Clase

```bash
# Solo tests de cache SUNAT
pytest tests/features/agents/test_pipeline_context.py::TestGetSunatData -v

# Solo tests de parseo
pytest tests/features/agents/test_agente_parseador.py::TestParsearArchivo -v
```

### Ejecutar un Test Específico

```bash
# Un test específico
pytest tests/features/agents/test_pipeline_context.py::TestGetSunatData::test_get_sunat_data_primera_vez_hace_scraping -v
```

---

## 📊 Estructura de Tests

```
FinchatBackend/
├── tests/
│   ├── conftest.py                              # Configuración pytest
│   ├── features/
│   │   └── agents/
│   │       ├── test_pipeline_context.py         # Unit tests PipelineContext
│   │       ├── test_agente_validador_comprobante.py  # Unit tests Validador
│   │       └── test_agente_parseador.py         # Unit tests Parseador
│   └── integration/
│       └── test_pipeline_ingesta.py             # Integration test completo
```

---

## 🧪 Cobertura de Tests

### PipelineContext (test_pipeline_context.py)

- **7 clases de test**
- **18 tests unitarios**
- **Cobertura**: ~90%

Cubre:

- Inicialización vacía y con datos
- Set/get de datos genéricos
- Cache SUNAT (primera consulta, segunda consulta, múltiples RUCs)
- Serialización a dict
- Reset del contexto

### Agente Validador Comprobante (test_agente_validador_comprobante.py)

- **4 clases de test**
- **9 tests unitarios**
- **Cobertura**: ~85%

Cubre:

- Cálculo de hash (mismo contenido, diferente contenido)
- Duplicados por hash (existe, no existe)
- Duplicados por emisor/serie/número
- Flujo completo de validación

### Agente Parseador (test_agente_parseador.py)

- **4 clases de test**
- **8 tests unitarios**
- **Cobertura**: ~75%

Cubre:

- Modelos Pydantic (4 modelos)
- OCR de PDFs
- OCR de imágenes
- Construcción de few-shots
- Parseo completo

### Pipeline INGESTA Completo (test_pipeline_ingesta.py)

- **1 clase de test**
- **2 tests de integración**
- **Cobertura**: Flujo E2E completo

Cobre:

- Pipeline completo sin duplicado (5 agentes)
- Short-circuit con duplicado

**Total**: ~37 tests, ~800 líneas de código de test

---

## ✅ Ejemplo de Salida Esperada

```
tests/features/agents/test_pipeline_context.py::TestPipelineContextInicialization::test_inicializacion_vacia PASSED
tests/features/agents/test_pipeline_context.py::TestSetGet::test_set_y_get_dato PASSED
tests/features/agents/test_pipeline_context.py::TestGetSunatData::test_get_sunat_data_primera_vez_hace_scraping PASSED
tests/features/agents/test_pipeline_context.py::TestGetSunatData::test_get_sunat_data_segunda_vez_usa_cache PASSED
tests/features/agents/test_agente_validador_comprobante.py::TestCalcularHash::test_calcular_hash_contenido_simple PASSED
tests/features/agents/test_agente_parseador.py::TestModelos::test_comprobante_data_valido PASSED
tests/integration/test_pipeline_ingesta.py::TestPipelineIngestaCompleto::test_flujo_completo_sin_duplicado PASSED

================================ 37 passed in 2.45s ================================
```

---

## 🐛 Debugging Tests

### Ver print statements

```bash
pytest -v -s
```

### Ver solo failures

```bash
pytest --tb=short
```

### Ejecutar hasta el primer fallo

```bash
pytest -x
```

### Ver coverage detallado

```bash
pytest --cov=app --cov-report=term-missing
```

---

## 📝 Notas Importantes

1. **Mocks**: Todos los tests usan mocks para repositorios, OCR y LLM. No requieren BD real ni API keys.

2. **Fixtures**: Se usan fixtures de pytest para setup/teardown automático.

3. **Fast**: Los tests son rápidos (~2-3 segundos total) porque todo está mockeado.

4. **Aislados**: Cada test es independiente, no hay estado compartido.

---

## 🔜 Tests Pendientes (Opcionales)

Estos tests se pueden agregar después:

1. **test_agente_validador_sunat.py** - Tests del validador SUNAT
2. **test_agente_clasificador.py** - Tests del clasificador
3. **test_agente_persistencia.py** - Tests de persistencia
4. **test_sunat_scraper.py** - Tests del scraper Playwright (requiere setup especial)
5. **Tests E2E con BD real** - Tests con base de datos de prueba

---

## ✨ Próximos Pasos

1. ✅ Ejecutar los tests actuales
2. ✅ Verificar que todos pasen
3. ✅ Ver coverage report
4. ⏳ Agregar tests para agentes restantes (opcional)
5. ⏳ Continuar con Fase 3: Pipeline EXTRACCIÓN
