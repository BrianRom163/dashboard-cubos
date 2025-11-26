from flask import Flask, jsonify, render_template
import os
import psycopg2

app = Flask(__name__)

DB = {
    "host": os.getenv("NEON_HOST"),
    "port": "5432",
    "dbname": os.getenv("NEON_DB"),
    "user": os.getenv("NEON_USER"),
    "password": os.getenv("NEON_PASSWORD"),
    "sslmode": "require",
}

def get_conn():
    return psycopg2.connect(**DB)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/resumen")
def resumen():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT resultado, COUNT(*)
        FROM detecciones
        WHERE resultado IN ('aceptado','rechazado')
        GROUP BY resultado;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    total = sum(r[1] for r in rows) or 1
    aceptados = next((c for res, c in rows if res == "aceptado"), 0)
    rechazados = next((c for res, c in rows if res == "rechazado"), 0)
    return jsonify({
        "aceptados": aceptados,
        "rechazados": rechazados,
        "porcentaje_aceptados": round(aceptados * 100 / total, 2),
        "porcentaje_rechazados": round(rechazados * 100 / total, 2),
    })

@app.route("/promedio_confianza_colores")
def promedio_confianza_colores():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            CASE
                WHEN gpio_activado = 17 THEN 'rojo'
                WHEN gpio_activado = 27 THEN 'verde'
                WHEN gpio_activado = 22 THEN 'azul'
                ELSE 'otro'
            END AS color,
            AVG(_confianza)
        FROM detecciones
        WHERE resultado = 'aceptado'
        GROUP BY color
        HAVING color IN ('rojo','verde','azul');
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    data = {c: float(v) for c, v in rows}
    for c in ["rojo","verde","azul"]:
        data.setdefault(c, 0.0)
    return jsonify(data)

@app.route("/promedio_tiempo_piezas")
def promedio_tiempo_piezas():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            (rojos_solicitados + verdes_solicitados + azules_solicitados) AS cantidad,
            AVG(fecha_hora_finalizada - fecha_hora_inicio)
        FROM pedidos
        WHERE fecha_hora_inicio IS NOT NULL
          AND fecha_hora_finalizada IS NOT NULL
        GROUP BY cantidad
        ORDER BY cantidad;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    cantidades=[]
    promedios=[]
    for cant, interval in rows:
        segundos = interval.total_seconds() if interval else 0
        cantidades.append(int(cant))
        promedios.append(segundos)
    return jsonify({"cantidades": cantidades,"promedios_segundos": promedios})

@app.route("/pedidos_populares")
def pedidos_populares():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        WITH t AS (
            SELECT
                (rojos_solicitados + verdes_solicitados + azules_solicitados) AS cantidad,
                COUNT(*) AS veces
            FROM pedidos
            GROUP BY cantidad
        )
        SELECT cantidad, veces,
               ROUND(100.0 * veces / SUM(veces) OVER(), 2)
        FROM t
        ORDER BY cantidad;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify({
        "cantidades":[int(r[0]) for r in rows],
        "veces":[int(r[1]) for r in rows],
        "porcentajes":[float(r[2]) for r in rows]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)