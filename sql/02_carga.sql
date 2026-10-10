-- 02_carga.sql · Transformación y carga: staging -> lectura_demo
-- Extrae los atributos del JSONB con ->> y los convierte al tipo correcto.
-- ON CONFLICT hace la carga idempotente: una lectura que ya existe
-- (misma clave primaria dispositivo_id + ts) se omite sin error.
INSERT INTO lectura_demo (dispositivo_id, ts, p_ac, irradiancia, temp_modulo, payload)
SELECT
    (payload ->> 'device_id')::int,
    (payload ->> 'ts')::timestamptz,
    (payload ->> 'p_ac')::numeric(10,3),
    (payload ->> 'irradiancia')::numeric(8,1),
    (payload ->> 'temp_modulo')::numeric(5,1),
    payload
FROM stg_lectura_raw
ORDER BY id
ON CONFLICT (dispositivo_id, ts) DO NOTHING;
