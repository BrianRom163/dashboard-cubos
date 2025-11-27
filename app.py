from flask import Flask, jsonify, render_template
import psycopg2
import os

app = Flask(__name__)

# -------------------------------
#   CONFIG DB DESDE VARIABLES
# -------------------------------
DB = {
    "host": os.getenv("NEON_HOST"),
    "port": 5432,
    "dbname": os.getenv("NEON_DB"),
    "user": os.getenv("NEON_USER"),
    "password": os.getenv("NEON_PASSWORD"),
    "sslmode": "require"
}

def get_connection():
    return psycopg2.connect(**DB)

# -------------------------------
#      RUTA PRINCIPAL HTML
# -------------------------------
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

# ------------------------------------------------
#   1️⃣ ACEPTADOS VS RECHAZADOS (tabla detecciones)
# ------------------------------------------------
@app.route("/resumen")
def resumen():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT resultado, COUNT(*) 
        FROM detecciones 
        GROUP BY resultado;
    """)
    data = cur.fetchall()
    conn.close()

    return jsonify({
        "aceptado": next((r[1] for r in data if r[0] == "aceptado"), 0),
        "rechazado": next((r[1] for r in data if r[0] == "rechazado"), 0),
    })

# --------------------------------------------------------
#  2️⃣ PROMEDIO DE CONFIANZA POR COLOR (tabla detecciones)
# --------------------------------------------------------
@app.route("/confianza")
def confianza():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT color_detectado, AVG(nivel_confianza)
        FROM detecciones
        GROUP BY color_detectado;
    """)
    data = cur.fetchall()
    conn.close()

    return jsonify({color: float(avg) for color, avg in data})

# --------------------------------------------------------
# 3️⃣ TIEMPO PROMEDIO DE ENTREGA POR CANTIDAD (tabla pedidos)
# --------------------------------------------------------
@app.route("/tiempos")
def tiempos():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            (rojos_solicitados + verdes_solicitados + azules_solicitados) AS cantidad,
            AVG(EXTRACT(EPOCH FROM (fecha_hora_finalizacion - fecha_creacion))/60) AS minutos
        FROM pedidos
        WHERE fecha_hora_finalizacion IS NOT NULL
        GROUP BY cantidad
        ORDER BY cantidad;
    """)

    data = cur.fetchall()
    conn.close()

    return jsonify({
        str(cant): float(mins)
        for cant, mins in data
    })

# --------------------------------------------------------
# 4️⃣ GRAFICA PASTEL — Pedidos más populares (tabla pedidos)
# --------------------------------------------------------
@app.route("/populares")
def populares():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            (rojos_solicitados + verdes_solicitados + azules_solicitados) AS cantidad,
            COUNT(*) 
        FROM pedidos
        GROUP BY cantidad
        ORDER BY cantidad;
    """)

    data = cur.fetchall()
    conn.close()

    return jsonify({
        str(cant): count for cant, count in data
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5
