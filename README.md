# SolarDB Pascual · Consulta de gobernanza, ETL e IoT

**Curso:** Bases de Datos I (SD1006) · **Grupo:** 811 · **Semestre:** 2026-II
**Docente:** Ramiro Grisales Montoya · **Institución:** Institución Universitaria Pascual Bravo

**Integrante: Juan José Mazo Rodríguez

> An idempotent ETL pipeline that loads simulated IoT telemetry into a governed PostgreSQL repository, versioned on GitHub.

## Descripción

Consulta sobre gobernanza de datos, automatización ETL e Internet de las Cosas
aplicada a SolarDB, más una práctica guiada: un simulador genera mensajes JSON de
dos inversores, se cargan a una tabla de *staging* (`stg_lectura_raw`, JSONB) y
de allí a una tabla relacional (`lectura_demo`) con una carga **idempotente**
(`INSERT ... ON CONFLICT DO NOTHING`). Cada ejecución queda registrada en
`etl_log`, y el rol `solar_lector` solo puede leer.

## Estructura

```
├── README.md
├── .gitignore
├── .env.example      plantilla de conexión (sin credenciales reales)
├── docs/             PDF de la consulta
├── data/             lecturas.jsonl de muestra
├── etl/              simulador.py, run_etl.py
└── sql/              01_tablas.sql, 02_carga.sql, 03_roles.sql
```

## Cómo reproducir la práctica

Requisitos: PostgreSQL 15 o superior, cliente `psql` en el PATH y Python 3.9+
(solo biblioteca estándar, no hay que instalar paquetes).

```bash
# 1. Crear la base y configurar la conexión (sin subir credenciales)
createdb solardb
cp .env.example .env        # editar PGUSER / PGPASSWORD si hace falta

# 2. Generar los datos simulados (data/lecturas.jsonl)
python etl/simulador.py

# 3. Ejecutar todo el flujo con un único comando (crea tablas, carga, registra bitácora)
python etl/run_etl.py

# 4. Prueba de idempotencia: repetir y comparar el conteo
python etl/run_etl.py
psql -c "SELECT COUNT(*) FROM lectura_demo;"      # sigue siendo 288

# 5. Bitácora
psql -c "SELECT * FROM etl_log ORDER BY id;"

# 6. Roles y prueba del rol de solo lectura
psql -f sql/03_roles.sql
psql -c "SET ROLE solar_lector; SELECT COUNT(*) FROM lectura_demo;"                 # permitido
psql -c "SET ROLE solar_lector; INSERT INTO lectura_demo (dispositivo_id, ts) VALUES (9, now());"  # rechazado
```

### Automatización (cada hora)

Expresión cron (no implementada): `0 * * * * cd /ruta/solardb && python etl/run_etl.py >> etl.log 2>&1`


## Seguridad

Las credenciales se pasan por variables de entorno o por `.env`, que está excluido
en `.gitignore`. Nunca se suben contraseñas ni cadenas de conexión.
