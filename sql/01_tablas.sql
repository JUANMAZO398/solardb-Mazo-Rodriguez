-- 01_tablas.sql · Tablas de la práctica (PostgreSQL 15 o superior)
-- Se puede ejecutar varias veces sin error (IF NOT EXISTS).

-- Staging: guarda el mensaje crudo del gateway, sin transformar (enfoque ELT).
CREATE TABLE IF NOT EXISTS stg_lectura_raw (
    id         BIGSERIAL PRIMARY KEY,
    payload    JSONB       NOT NULL,
    cargado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Destino relacional simplificado (en la Fase 1 se usará el modelo oficial).
CREATE TABLE IF NOT EXISTS lectura_demo (
    dispositivo_id INT          NOT NULL,
    ts             TIMESTAMPTZ  NOT NULL,
    p_ac           NUMERIC(10,3) CHECK (p_ac >= 0),
    irradiancia    NUMERIC(8,1)  CHECK (irradiancia BETWEEN 0 AND 1500),
    temp_modulo    NUMERIC(5,1),
    payload        JSONB,
    PRIMARY KEY (dispositivo_id, ts)
);

-- Bitácora del proceso ETL (trazabilidad / data lineage), ver respuesta E4.
CREATE TABLE IF NOT EXISTS etl_log (
    id                BIGSERIAL PRIMARY KEY,
    proceso           TEXT        NOT NULL,
    archivo_origen    TEXT        NOT NULL,
    inicio            TIMESTAMPTZ NOT NULL DEFAULT now(),
    fin               TIMESTAMPTZ,
    filas_leidas      INT,
    filas_cargadas    INT,
    filas_duplicadas  INT,
    filas_rechazadas  INT,
    estado            TEXT        NOT NULL DEFAULT 'EN_CURSO'
                      CHECK (estado IN ('EN_CURSO', 'OK', 'ERROR')),
    error             TEXT
);
