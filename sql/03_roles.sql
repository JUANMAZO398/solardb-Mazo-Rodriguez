-- 03_roles.sql · Gobernanza aplicada: principio de mínimo privilegio
-- Tres roles (ver respuesta G5). Se crean sin contraseña y sin LOGIN;
-- para usarlos como usuarios reales se les asigna LOGIN y una contraseña
-- fuera del repositorio (nunca se versionan credenciales).
--   solar_ingesta : proceso ETL (escribe)
--   solar_lector  : consulta (solo lectura)  <- rol del Paso 6
--   solar_admin   : administración

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'solar_ingesta') THEN
        CREATE ROLE solar_ingesta NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'solar_lector') THEN
        CREATE ROLE solar_lector NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'solar_admin') THEN
        CREATE ROLE solar_admin NOLOGIN;
    END IF;
END
$$;

-- Punto de partida: nadie fuera del dueño tiene acceso.
REVOKE ALL ON stg_lectura_raw, lectura_demo, etl_log FROM PUBLIC;
REVOKE ALL ON stg_lectura_raw, lectura_demo, etl_log
    FROM solar_ingesta, solar_lector, solar_admin;

-- Ingesta: solo lo que necesita el ETL.
GRANT SELECT, INSERT, DELETE, TRUNCATE ON stg_lectura_raw TO solar_ingesta;
GRANT SELECT, INSERT                   ON lectura_demo    TO solar_ingesta;
GRANT SELECT, INSERT, UPDATE           ON etl_log         TO solar_ingesta;
GRANT USAGE ON SEQUENCE stg_lectura_raw_id_seq, etl_log_id_seq TO solar_ingesta;

-- Lector: solo lectura sobre los datos finales.
GRANT SELECT ON lectura_demo TO solar_lector;

-- Administración: todo sobre las tres tablas.
GRANT ALL ON stg_lectura_raw, lectura_demo, etl_log TO solar_admin;
GRANT ALL ON SEQUENCE stg_lectura_raw_id_seq, etl_log_id_seq TO solar_admin;
