from flask import Flask, jsonify, render_template
import psycopg2
import os

app = Flask(__name__)

DB = {
    "host": os.getenv("NEON_HOST"),
    "port": "5432",
    "dbname": os.getenv("NEON_DB"),
    "user": os.getenv("NEON_USER"),
    "password": os.getenv("NEON_PASSWORD"),
    "sslmode": "require"
}

TABLE_DETECCIONES = "detecciones"
TABLE_PEDIDOS = "pedidos"

def get_connection():
    return psycopg2.connect(**DB)

# ==========================
#   RUTAS PARA TU DASHBOARD
# ==========================

@app.route("/")
def index():
    return render_template("index.html")

# 1️⃣ RESUMEN ACEPTADOS / RECHAZADOS
@app.route("/resumen")
def resumen():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT resultado FROM {TABLE_DETECCIONES}")
    rows = cursor.fetchall()

    aceptados = sum(1 for r in rows if r[0] == "aceptado")
    rechazados = sum(1 for r in rows if r[0] == "rechazado")

    cursor.close()
    conn.close()

    return jsonify({
        "aceptados": aceptados,
        "rechazados": rechazados
    })

# 2️⃣ PROMEDIO DE CONFIANZA POR COLOR
@app.route("/promedio_confianza_colores")
def promedio_confianza():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT 
            AVG(confianza) FILTER (WHERE gpio_activado = 17),
            AVG(confianza) FILTER (WHERE gpio_activado = 22),
            AVG(confianza) FILTER (WHERE gpio_activado = 27)
        FROM {TABLE_DETECCIONES};
    """)

    rojo, verde, azul = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({
        "rojo": rojo,
        "verde": verde,
        "azul": azul
    })

# 3️⃣ TIEMPO PROMEDIO DE PEDIDOS
@app.route("/promedio_tiempo_piezas")
def tiempo_promedio():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT 
            rojos_solicitados + verdes_solicitados + azules_solicitados AS piezas,
            EXTRACT(EPOCH FROM (fecha_hora_finalizado - fecha_hora_inicio)) AS segundos
        FROM {TABLE_PEDIDOS}
        WHERE fecha_hora_finalizado IS NOT NULL;
    """)

    rows = cursor.fetchall()

    tiempos = {}
    conteo = {}

    for piezas, segundos in rows:
        if piezas not in tiempos:
            tiempos[piezas] = 0
            conteo[piezas] = 0
        tiempos[piezas] += segundos
        conteo[piezas] += 1

    promedio = {p: tiempos[p] / conteo[p] for p in tiempos}

    cursor.close()
    conn.close()

    return jsonify(promedio)

# 4️⃣ PEDIDOS MÁS POPULARES (PASTEL)
@app.route("/pedidos_populares")
def pedidos_populares():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT 
            rojos_solicitados + verdes_solicitados + azules_solicitados AS piezas,
            COUNT(*)
        FROM {TABLE_PEDIDOS}
        GROUP BY piezas
        ORDER BY piezas;
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({str(p): c for p, c in rows})

# ==========================
#   INICIAR SERVIDOR
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
