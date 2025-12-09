CREATE TABLE usuario (
  id_usuario SERIAL PRIMARY KEY,
  nombre_mostrar VARCHAR(120) NOT NULL,
  correo_electronico VARCHAR(255) UNIQUE,
  password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE emisor (
  id_emisor SERIAL PRIMARY KEY,
  ruc CHAR(11) NOT NULL UNIQUE,
  razon_social VARCHAR(255) NOT NULL,
  nombre_comercial VARCHAR(255),
  ciiu_principal VARCHAR(10),
  estado_ruc VARCHAR(30),
  condicion_ruc VARCHAR(30)
);

CREATE TABLE comprobante (
  id_comprobante BIGSERIAL PRIMARY KEY,
  id_usuario INTEGER REFERENCES usuario(id_usuario),
  id_emisor INTEGER REFERENCES emisor(id_emisor),
  tipo_comprobante VARCHAR(10) NOT NULL, -- 'boleta', 'factura', etc.
  serie VARCHAR(8) NOT NULL,
  numero VARCHAR(20) NOT NULL,
  fecha_emision DATE NOT NULL,
  monto_total NUMERIC(12,2) NOT NULL,
  moneda CHAR(3) NOT NULL DEFAULT 'PEN',
  origen VARCHAR(15) NOT NULL, -- 'fisico' | 'electronico'
  hash_archivo CHAR(64) NOT NULL,
  estado_procesamiento VARCHAR(20) NOT NULL DEFAULT 'pendiente',
  es_deducible BOOLEAN,
  es_duplicado BOOLEAN DEFAULT FALSE,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ruta_archivo TEXT,
  mime_type VARCHAR(100),

  CONSTRAINT comprobante_unq_usuario_emisor_serie_numero
    UNIQUE (id_usuario, id_emisor, serie, numero),

  CONSTRAINT comprobante_unq_usuario_hash
    UNIQUE (id_usuario, hash_archivo)
);

CREATE TABLE detalle_comprobante (
  id_detalle BIGSERIAL PRIMARY KEY,
  id_comprobante BIGINT NOT NULL
    REFERENCES comprobante(id_comprobante) ON DELETE CASCADE,
  descripcion TEXT NOT NULL,
  cantidad NUMERIC(10,2),
  precio_unitario NUMERIC(12,2),
  monto_item NUMERIC(12,2)
);

CREATE TABLE validacion (
  id_comprobante BIGINT PRIMARY KEY
    REFERENCES comprobante(id_comprobante) ON DELETE CASCADE,
  estado_ruc VARCHAR(30),
  condicion_ruc VARCHAR(30),
  ciiu_detectado VARCHAR(10),
  nombre_comercial_sunat VARCHAR(255),
  nombre_emisor_ocr VARCHAR(255),
  coincide_nombre BOOLEAN,
  pasa_reglas BOOLEAN,
  motivo_no_deducible TEXT
);

CREATE TABLE clasificacion (
  id_comprobante BIGINT PRIMARY KEY
    REFERENCES comprobante(id_comprobante) ON DELETE CASCADE,
  categoria_gasto VARCHAR(60),
  porcentaje_deduccion NUMERIC(5,2),
  version_regla VARCHAR(20) DEFAULT 'v1'
);

CREATE TABLE ocr_pagina (
  id_ocr_pagina BIGSERIAL PRIMARY KEY,
  id_comprobante BIGINT NOT NULL
    REFERENCES comprobante(id_comprobante) ON DELETE CASCADE,
  numero_pagina INTEGER NOT NULL,
  texto_pagina TEXT,
  confianza_promedio NUMERIC(5,2)
);

CREATE UNIQUE INDEX idx_ocr_pagina_comprobante_pagina
  ON ocr_pagina(id_comprobante, numero_pagina);

CREATE TABLE estado_trabajo (
  id_trabajo UUID PRIMARY KEY,
  id_usuario INTEGER REFERENCES usuario(id_usuario),
  tipo_trabajo VARCHAR(20) NOT NULL, -- 'ingesta' | 'consulta'
  estado VARCHAR(20) NOT NULL, -- 'pendiente', 'en_proceso', 'completado', 'error'
  id_comprobante BIGINT REFERENCES comprobante(id_comprobante),
  codigo_error VARCHAR(50),
  intentos INTEGER NOT NULL DEFAULT 0,
  mensaje TEXT,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE historial_chat (
  id_mensaje BIGSERIAL PRIMARY KEY,
  id_usuario INTEGER REFERENCES usuario(id_usuario),
  rol VARCHAR(20) NOT NULL, -- 'user' | 'assistant' | 'system'
  contenido TEXT NOT NULL,
  creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
