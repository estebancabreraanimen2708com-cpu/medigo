from flask import Flask, render_template, request, redirect, session, jsonify, send_file
import mysql.connector
import os
from datetime import datetime
import pytz
import io

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

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

# 🔐 PROTEGER RUTAS
@app.before_request
def proteger():
    ruta = request.path

    if ruta.startswith("/static") or ruta.startswith("/login") or ruta.startswith("/api"):
        return

    if ruta.startswith("/inspector"):
        if "rol" not in session or session["rol"] != "inspector":
            return redirect("/login/inspector")

    if ruta.startswith("/medico"):
        if "rol" not in session or session["rol"] != "medico":
            return redirect("/login/medico")

# 🔥 API SOLICITUDES
@app.route('/api/solicitudes')
def api_solicitudes():
    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("""
    SELECT s.id_solicitud, e.id_estudiante, e.nombre,
           s.motivo, s.estado,
           DATE_FORMAT(s.fecha, '%Y-%m-%d %H:%i:%s') as fecha
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    ORDER BY s.id_solicitud DESC
    """)

    data = cur.fetchall()
    con.close()
    return jsonify(data)

# 🔥 API ESTUDIANTES
@app.route('/api/estudiantes')
def api_estudiantes():
    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("SELECT id_estudiante, nombre FROM estudiantes ORDER BY nombre")

    data = cur.fetchall()
    con.close()
    return jsonify(data)

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

        return render_template("login.html", error="Credenciales incorrectas", rol=rol)

    return render_template("login.html", rol=rol)

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/solicitudes")

# 📋 SOLICITUDES
@app.route('/', methods=["GET","POST"])
@app.route('/solicitudes', methods=["GET","POST"])
def solicitudes():
    con = get_connection()
    cur = con.cursor(dictionary=True)

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

    # 🔥 TODOS LOS ESTUDIANTES (SIN ERROR)
    cur.execute("SELECT id_estudiante, nombre FROM estudiantes ORDER BY nombre")
    estudiantes = cur.fetchall()

    con.close()
    return render_template("solicitudes.html", estudiantes=estudiantes)

# 👮 INSPECTOR
@app.route('/inspector')
def inspector():
    return render_template("inspector.html")

# 🏥 MEDICO
@app.route('/medico')
def medico():
    return render_template("medico.html")

# 📊 HISTORIAL
@app.route('/historial/<int:id>')
def historial(id):
    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("""
    SELECT e.nombre, s.motivo, s.estado, s.fecha, s.dolor
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    WHERE e.id_estudiante = %s
    ORDER BY s.fecha DESC
    """,(id,))

    data = cur.fetchall()
    con.close()

    return render_template("historial.html", data=data)

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

# 📄 PDF DEL DÍA
@app.route('/pdf_hoy')
def pdf_hoy():
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
    SELECT e.nombre, s.motivo, s.estado, s.fecha
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    WHERE DATE(s.fecha) = CURDATE()
    """)

    datos = cur.fetchall()
    con.close()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)

    tabla_data = [["Nombre","Motivo","Estado","Fecha"]]
    for f in datos:
        tabla_data.append([f[0],f[1],f[2],str(f[3])])

    tabla = Table(tabla_data)
    tabla.setStyle(TableStyle([('GRID',(0,0),(-1,-1),1,colors.black)]))

    doc.build([tabla])
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="hoy.pdf")

if __name__ == '__main__':
    app.run(debug=True)
