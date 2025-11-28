from flask import Flask, jsonify, render_template
import psycopg2
import os
import urllib.parse as urlparse


#       CONFIGURACIÓN DE FLASK

app = Flask(__name__)


#       CONEXIÓN A NeonDB usando DATABASE_URL

url = urlparse.urlparse(os.environ["DATABASE_URL"])

DB = {
    "dbname": url.path[1:],
    "user": url.username,
    "password": url.password,
    "host": url.hostname,
    "port": url.port,
    "sslmode": "require"
}

def get_connection():
    return psycopg2.connect(**DB)

#   DASHBOARD
@app.route("/")
def dashboard():
    return render_template("dashboard.html")



#  RESUMEN: Aceptados vs Rechazados
@app.route("/api/resumen")
def resumen():
    try:
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

    except Exception as e:
        return jsonify({"error": str(e)}), 500


#   PROMEDIO DE CONFIANZA POR COLOR
@app.route("/api/confianza")
def confianza():
    try:
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

    except Exception as e:
        return jsonify({"error": str(e)}), 500


#  TIEMPO PROMEDIO POR CANTIDAD
@app.route("/api/tiempos")
def tiempos():
    try:
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
            str(cant): float(mins) for cant, mins in data
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


#   PEDIDOS MÁS POPULARES
@app.route("/api/populares")
def populares():
    try:
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

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# -------------------------------------------------------------
#       EJECUCIÓN LOCAL (Render ignora esto por Gunicorn)
# -------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
