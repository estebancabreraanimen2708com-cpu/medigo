from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
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

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT"))
    )

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

# SOLICITUDES
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

# INSPECTOR
@app.route('/inspector')
def inspector():
    return render_template("inspector.html")

# MEDICO
@app.route('/medico')
def medico():
    return render_template("medico.html")

# ACCIONES
@app.route('/aprobar/<int:id>')
def aprobar(id):
    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("UPDATE solicitudes SET estado='aprobado' WHERE id_solicitud=%s", (id,))
    conexion.commit()
    conexion.close()
    return redirect(url_for("inspector"))

@app.route('/rechazar/<int:id>')
def rechazar(id):
    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("UPDATE solicitudes SET estado='rechazado' WHERE id_solicitud=%s", (id,))
    conexion.commit()
    conexion.close()
    return redirect(url_for("inspector"))

@app.route('/atendido/<int:id>')
def atendido(id):
    conexion = get_connection()
    cursor = conexion.cursor()
    cursor.execute("UPDATE solicitudes SET estado='atendido' WHERE id_solicitud=%s", (id,))
    conexion.commit()
    conexion.close()
    return redirect(url_for("medico"))

# PDF
@app.route('/reporte_pdf')
def reporte_pdf():

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    ecuador = pytz.timezone('America/Guayaquil')
    hoy = datetime.now(ecuador).date()

    cursor.execute("""
    SELECT e.nombre, s.motivo, s.estado, s.fecha
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    WHERE DATE(s.fecha) = %s
    """, (hoy,))

    datos = cursor.fetchall()
    conexion.close()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    elementos = [Paragraph("Reporte del Día", styles['Title'])]

    tabla = [["Estudiante", "Motivo", "Estado", "Fecha"]]

    for d in datos:
        tabla.append([
            d["nombre"],
            d["motivo"],
            d["estado"],
            d["fecha"].strftime('%d/%m/%Y %H:%M')
        ])

    t = Table(tabla)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.blue),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))

    elementos.append(t)
    doc.build(elementos)

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="reporte.pdf")

if __name__ == '__main__':
    app.run(debug=True)
