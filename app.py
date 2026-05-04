from flask import Flask, render_template, request, redirect, session, jsonify
import mysql.connector
import os
from datetime import datetime
import pytz

app = Flask(__name__)
app.secret_key = "secreto"

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT"))
    )

# 🔐 PROTECCIÓN DE RUTAS
@app.before_request
def proteger():
    ruta = request.path

    if ruta.startswith("/static") or ruta.startswith("/login") or ruta.startswith("/api"):
        return

    if ruta.startswith("/inspector"):
        if session.get("rol") != "inspector":
            return redirect("/login/inspector")

    if ruta.startswith("/medico"):
        if session.get("rol") != "medico":
            return redirect("/login/medico")

# 🔥 API SOLICITUDES (SIN DUPLICADOS)
@app.route('/api/solicitudes')
def api_solicitudes():
    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("""
    SELECT s.id_solicitud, e.nombre,
           s.motivo, s.estado,
           DATE_FORMAT(s.fecha, '%Y-%m-%d %H:%i:%s') as fecha
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    ORDER BY s.id_solicitud DESC
    """)

    data = cur.fetchall()
    con.close()
    return jsonify(data)

# 🔥 LISTA DE ESTUDIANTES SIN DUPLICADOS
def obtener_estudiantes():
    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("""
    SELECT MIN(id_estudiante) as id_estudiante, nombre
    FROM estudiantes
    GROUP BY nombre
    ORDER BY nombre
    """)

    data = cur.fetchall()
    con.close()
    return data

# 🔐 LOGIN
@app.route('/login/<rol>', methods=["GET","POST"])
def login(rol):
    if request.method == "POST":
        user = request.form["user"]
        password = request.form["pass"]

        if rol == "inspector" and user == "admin" and password == "1234":
            session["rol"] = "inspector"
            return redirect("/inspector")

        if rol == "medico" and user == "doctor" and password == "1234":
            session["rol"] = "medico"
            return redirect("/medico")

        return render_template("login.html", rol=rol, error="Credenciales incorrectas")

    return render_template("login.html", rol=rol)

# 📋 SOLICITUDES
@app.route('/', methods=["GET","POST"])
@app.route('/solicitudes', methods=["GET","POST"])
def solicitudes():
    con = get_connection()
    cur = con.cursor()

    if request.method == "POST":
        est = request.form["estudiante"]
        mot = request.form["motivo"]
        dolor = request.form["dolor"]

        fecha = datetime.now(pytz.timezone('America/Guayaquil'))

        cur.execute("""
        INSERT INTO solicitudes (id_estudiante, id_profesor, motivo, dolor, estado, fecha)
        VALUES (%s,(SELECT id_profesor FROM profesores LIMIT 1),%s,%s,'pendiente',%s)
        """,(est,mot,dolor,fecha))

        con.commit()
        return redirect("/solicitudes")

    estudiantes = obtener_estudiantes()
    return render_template("solicitudes.html", estudiantes=estudiantes)

# 👮 INSPECTOR
@app.route('/inspector')
def inspector():
    return render_template("inspector.html")

# 🏥 MEDICO
@app.route('/medico')
def medico():
    return render_template("medico.html")

# ACCIONES
@app.route('/aprobar/<int:id>')
def aprobar(id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("UPDATE solicitudes SET estado='aprobado' WHERE id_solicitud=%s",(id,))
    con.commit()
    con.close()
    return redirect("/inspector")

@app.route('/rechazar/<int:id>')
def rechazar(id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("UPDATE solicitudes SET estado='rechazado' WHERE id_solicitud=%s",(id,))
    con.commit()
    con.close()
    return redirect("/inspector")

@app.route('/atendido/<int:id>')
def atendido(id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("UPDATE solicitudes SET estado='atendido' WHERE id_solicitud=%s",(id,))
    con.commit()
    con.close()
    return redirect("/medico")

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/solicitudes")

if __name__ == '__main__':
    app.run(debug=True)
