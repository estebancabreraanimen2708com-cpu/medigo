from flask import Flask, render_template, request, redirect, session, jsonify, send_file
import mysql.connector
import os
from datetime import datetime
import pytz
import io

# PDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = "supersecreto123"

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT"))
    )

def proteger(rol):
    if "rol" not in session:
        return False
    return session["rol"] == rol

# API
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

# LOGIN
@app.route('/login/<rol>', methods=["GET","POST"])
def login(rol):
    if request.method == "POST":
        user = request.form["user"]
        password = request.form["pass"]

        if rol == "inspector" and user == "admin" and password == "1234":
            session["rol"] = "inspector"
            return redirect("/inspector")

        elif rol == "medico" and user == "doctor" and password == "1234":
            session["rol"] = "medico"
            return redirect("/medico")

        return render_template("login.html", error="Credenciales incorrectas", rol=rol)

    return render_template("login.html", rol=rol)

@app.route('/logout')
def logout():
    session.clear()
    return redirect("/solicitudes")

# SOLICITUDES
@app.route('/', methods=["GET","POST"])
@app.route('/solicitudes', methods=["GET","POST"])
def solicitudes():
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    if request.method == "POST":
        estudiante = request.form["estudiante"]
        motivo = request.form["motivo"]
        dolor = request.form["dolor"]

        # 🇪🇨 HORA ECUADOR CORREGIDA
        fecha = datetime.now(pytz.timezone('America/Guayaquil')).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("""
        INSERT INTO solicitudes (id_estudiante, id_profesor, motivo, dolor, estado, fecha)
        VALUES (%s,(SELECT id_profesor FROM profesores LIMIT 1),%s,%s,'pendiente',%s)
        """,(estudiante, motivo, dolor, fecha))

        conexion.commit()
        return redirect("/solicitudes")

    cursor.execute("SELECT * FROM estudiantes")
    estudiantes = cursor.fetchall()

    conexion.close()
    return render_template("solicitudes.html", estudiantes=estudiantes)

# INSPECTOR
@app.route('/inspector')
def inspector():
    if not proteger("inspector"):
        return redirect("/login/inspector")
    return render_template("inspector.html")

# MEDICO
@app.route('/medico')
def medico():
    if not proteger("medico"):
        return redirect("/login/medico")
    return render_template("medico.html")

# ACCIONES
@app.route('/aprobar/<int:id>')
def aprobar(id):
    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("UPDATE solicitudes SET estado='aprobado' WHERE id_solicitud=%s",(id,))
    conexion.commit()
    conexion.close()
    return redirect("/inspector")

@app.route('/rechazar/<int:id>')
def rechazar(id):
    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("UPDATE solicitudes SET estado='rechazado' WHERE id_solicitud=%s",(id,))
    conexion.commit()
    conexion.close()
    return redirect("/inspector")

@app.route('/atendido/<int:id>')
def atendido(id):
    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("UPDATE solicitudes SET estado='atendido' WHERE id_solicitud=%s",(id,))
    conexion.commit()
    conexion.close()
    return redirect("/medico")

# PDF
@app.route('/descargar_pdf')
def descargar_pdf():
    if not proteger("inspector"):
        return redirect("/login/inspector")

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute("""
    SELECT e.nombre, s.motivo, s.estado, s.fecha
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    ORDER BY s.fecha DESC
    """)

    datos = cursor.fetchall()
    conexion.close()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)

    tabla_data = [["Nombre", "Motivo", "Estado", "Fecha"]]

    for fila in datos:
        tabla_data.append([fila[0], fila[1], fila[2], str(fila[3])])

    tabla = Table(tabla_data)

    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))

    doc.build([tabla])
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="solicitudes.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(debug=True)
