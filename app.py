from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
import mysql.connector
import os
from datetime import datetime
import pytz
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "secreto123"  # 🔥 necesario para login

# =========================
# LOGIN CREDENCIALES
# =========================
USUARIOS = {
    "inspector": {"user": "admin", "pass": "1234"},
    "medico": {"user": "doctor", "pass": "1234"}
}

# =========================
# DB
# =========================
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT"))
    )

# =========================
# API
# =========================
@app.route('/api/solicitudes')
def api_solicitudes():
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
    SELECT s.id_solicitud, e.nombre, s.motivo, s.estado, s.fecha, s.dolor
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    ORDER BY s.id_solicitud DESC
    """)

    data = cursor.fetchall()
    conexion.close()
    return jsonify(data)

# =========================
# LOGIN
# =========================
@app.route('/login/<rol>', methods=["GET", "POST"])
def login(rol):

    if request.method == "POST":
        user = request.form["user"]
        password = request.form["pass"]

        if rol in USUARIOS and user == USUARIOS[rol]["user"] and password == USUARIOS[rol]["pass"]:
            session["rol"] = rol
            return redirect(url_for(rol))
        else:
            return render_template("login.html", error="Credenciales incorrectas", rol=rol)

    return render_template("login.html", rol=rol)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("solicitudes"))

# =========================
# PROTECCIÓN
# =========================
def proteger(rol):
    if "rol" not in session or session["rol"] != rol:
        return False
    return True

# =========================
# VISTAS
# =========================
@app.route('/', methods=["GET", "POST"])
@app.route('/solicitudes', methods=["GET", "POST"])
def solicitudes():

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    if request.method == "POST":
        estudiante = request.form["estudiante"]
        motivo = request.form["motivo"]
        dolor = request.form["dolor"]

        ecuador = pytz.timezone('America/Guayaquil')
        fecha = datetime.now(ecuador)

        cursor.execute("""
        INSERT INTO solicitudes (id_estudiante, id_profesor, motivo, dolor, estado, fecha)
        VALUES (%s, (SELECT id_profesor FROM profesores LIMIT 1), %s, %s, 'pendiente', %s)
        """, (estudiante, motivo, dolor, fecha))

        conexion.commit()
        return redirect(url_for("solicitudes"))

    cursor.execute("SELECT * FROM estudiantes")
    estudiantes = cursor.fetchall()

    conexion.close()
    return render_template("solicitudes.html", estudiantes=estudiantes)


@app.route('/inspector')
def inspector():
    if not proteger("inspector"):
        return redirect(url_for("login", rol="inspector"))
    return render_template("inspector.html")


@app.route('/medico')
def medico():
    if not proteger("medico"):
        return redirect(url_for("login", rol="medico"))
    return render_template("medico.html")


# =========================
# ACCIONES
# =========================
@app.route('/aprobar/<int:id>')
def aprobar(id):
    if not proteger("inspector"):
        return redirect(url_for("login", rol="inspector"))

    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("UPDATE solicitudes SET estado='aprobado' WHERE id_solicitud=%s", (id,))
    conexion.commit()
    conexion.close()
    return redirect(url_for("inspector"))


@app.route('/rechazar/<int:id>')
def rechazar(id):
    if not proteger("inspector"):
        return redirect(url_for("login", rol="inspector"))

    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("UPDATE solicitudes SET estado='rechazado' WHERE id_solicitud=%s", (id,))
    conexion.commit()
    conexion.close()
    return redirect(url_for("inspector"))


@app.route('/atendido/<int:id>')
def atendido(id):
    if not proteger("medico"):
        return redirect(url_for("login", rol="medico"))

    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("UPDATE solicitudes SET estado='atendido' WHERE id_solicitud=%s", (id,))
    conexion.commit()
    conexion.close()
    return redirect(url_for("medico"))


if __name__ == '__main__':
    app.run(debug=True)
