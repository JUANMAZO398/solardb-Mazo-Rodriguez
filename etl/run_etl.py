import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PROCESO = "carga_lecturas_demo"


def cargar_env():
    """Lee un .env sencillo (CLAVE=valor) sin pisar variables ya definidas."""
    env = RAIZ / ".env"
    if env.exists():
        for linea in env.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def psql(*args, entrada=None):
    """Ejecuta psql y devuelve la salida estándar; lanza error si falla."""
    cmd = ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", *args]
    res = subprocess.run(cmd, input=entrada, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.strip() or "psql falló")
    return res.stdout


def sql(consulta):
    """Ejecuta una sentencia y devuelve el resultado como texto sin formato."""
    return psql("-A", "-t", "-c", consulta).strip()


def validar(linea):
    """Devuelve el dict si la línea es un mensaje válido; si no, None."""
    try:
        m = json.loads(linea)
        int(m["device_id"])
        datetime.fromisoformat(m["ts"])
        if float(m["p_ac"]) < 0:
            return None
        if not 0 <= float(m["irradiancia"]) <= 1500:
            return None
        float(m["temp_modulo"])
        return m
    except (ValueError, KeyError, TypeError):
        return None


def main():
    cargar_env()
    archivo = Path(sys.argv[1] if len(sys.argv) > 1 else RAIZ / "data" / "lecturas.jsonl")
    if not archivo.exists():
        sys.exit(f"No existe el archivo de lecturas: {archivo}")

    psql("-f", str(RAIZ / "sql" / "01_tablas.sql"))
    log_id = sql(
        "INSERT INTO etl_log (proceso, archivo_origen) "
        f"VALUES ('{PROCESO}', '{archivo.name}') RETURNING id"
    ).splitlines()[0]

    leidas = rechazadas = cargadas = 0
    try:
        validas = []
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            if not linea.strip():
                continue
            leidas += 1
            m = validar(linea)
            if m is None:
                rechazadas += 1
            else:
                validas.append(json.dumps(m))

        # Staging transitorio: se vacía y se recarga en cada ejecución.
        sql("TRUNCATE stg_lectura_raw")
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8") as tmp:
            tmp.write("\n".join(validas) + "\n")
            ruta_tmp = tmp.name
        try:
            # Formato CSV con delimitador/comilla improbables: cada línea JSON entra
            # intacta (sin que COPY interprete comillas ni barras invertidas).
            psql("-c", f"\\copy stg_lectura_raw (payload) FROM '{ruta_tmp}' "
                       "WITH (FORMAT csv, QUOTE E'\\x01', DELIMITER E'\\x02')")
        finally:
            os.unlink(ruta_tmp)

        antes = int(sql("SELECT count(*) FROM lectura_demo"))
        psql("-f", str(RAIZ / "sql" / "02_carga.sql"))
        despues = int(sql("SELECT count(*) FROM lectura_demo"))
        cargadas = despues - antes
        duplicadas = len(validas) - cargadas
        estado, error = "OK", "NULL"
    except Exception as exc:  # se registra el fallo en la bitácora y se propaga
        duplicadas = 0
        estado = "ERROR"
        error = "'" + str(exc).replace("'", "''")[:500] + "'"
        print(f"ERROR: {exc}", file=sys.stderr)

    sql(
        f"UPDATE etl_log SET fin = now(), filas_leidas = {leidas}, "
        f"filas_cargadas = {cargadas}, filas_duplicadas = {duplicadas}, "
        f"filas_rechazadas = {rechazadas}, estado = '{estado}', error = {error} "
        f"WHERE id = {log_id}"
    )
    print(f"[{estado}] leídas={leidas} cargadas={cargadas} "
          f"duplicadas={duplicadas} rechazadas={rechazadas} (etl_log id={log_id})")
    sys.exit(0 if estado == "OK" else 1)


if __name__ == "__main__":
    main()
