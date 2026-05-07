from flask import Flask, render_template, request, redirect, jsonify, send_file
import mysql.connector
from fpdf import FPDF
from datetime import datetime
import pytz

app = Flask(__name__)

# =========================================
# 🔥 MYSQL
# =========================================

def conectar_bd():
    return mysql.connector.connect(
        host="mysql.railway.internal",
        user="root",
        password="wYbBPSlKSxHuYpUKYiYSfWzMnnqUyAVJ",
        database="railway",
        port=3306
    )

# =========================================
# 🔥 HORA ECUADOR
# =========================================

ecuador = pytz.timezone("America/Guayaquil")

def hora_ecuador():
    return datetime.now(ecuador).strftime("%Y-%m-%d %H:%M:%S")

# =========================================
# 🔥 INICIO
# =========================================

@app.route('/')
def inicio():
    return render_template('inicio.html')

# =========================================
# 🔥 ROLES
# =========================================

@app.route('/roles')
def roles():
    return render_template('roles.html')

# =========================================
# 🔥 SOLICITUDES
# =========================================

@app.route('/solicitudes', methods=['GET', 'POST'])
def solicitudes():

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':

        estudiante = request.form['estudiante']
        motivo = request.form['motivo']
        dolor = request.form['dolor']

        cursor.execute("""
        INSERT INTO solicitudes
        (id_estudiante,motivo,dolor,estado,fecha)
        VALUES(%s,%s,%s,%s,%s)
        """, (
            estudiante,
            motivo,
            dolor,
            "pendiente",
            hora_ecuador()
        ))

        conn.commit()

        return redirect('/solicitudes')

    cursor.execute("""
    SELECT DISTINCT id_estudiante,nombre
    FROM estudiantes
    ORDER BY nombre
    """)

    estudiantes = cursor.fetchall()

    return render_template(
        'solicitudes.html',
        estudiantes=estudiantes
    )

# =========================================
# 🔥 API
# =========================================

@app.route('/api/solicitudes')
def api_solicitudes():

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT
        s.id_solicitud,
        e.id_estudiante,
        e.nombre,
        s.motivo,
        s.dolor,
        s.estado,
        s.fecha
    FROM solicitudes s
    JOIN estudiantes e
    ON s.id_estudiante = e.id_estudiante
    ORDER BY s.id_solicitud DESC
    """)

    datos = cursor.fetchall()

    return jsonify(datos)

# =========================================
# 🔥 INSPECTOR
# =========================================

@app.route('/inspector')
def inspector():
    return render_template('inspector.html')

# =========================================
# 🔥 MEDICO
# =========================================

@app.route('/medico')
def medico():
    return render_template('medico.html')

# =========================================
# 🔥 APROBAR
# =========================================

@app.route('/aprobar/<int:id>')
def aprobar(id):

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE solicitudes
    SET estado='aprobado'
    WHERE id_solicitud=%s
    """, (id,))

    conn.commit()

    return redirect('/inspector')

# =========================================
# 🔥 RECHAZAR
# =========================================

@app.route('/rechazar/<int:id>')
def rechazar(id):

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE solicitudes
    SET estado='rechazado'
    WHERE id_solicitud=%s
    """, (id,))

    conn.commit()

    return redirect('/inspector')

# =========================================
# 🔥 ATENDIDO
# =========================================

@app.route('/atendido/<int:id>')
def atendido(id):

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE solicitudes
    SET estado='atendido'
    WHERE id_solicitud=%s
    """, (id,))

    conn.commit()

    return redirect('/medico')

# =========================================
# 🔥 HISTORIAL
# =========================================

@app.route('/historial/<int:id_estudiante>')
def historial(id_estudiante):

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT
        e.nombre,
        s.motivo,
        s.dolor,
        s.estado,
        s.fecha
    FROM solicitudes s
    JOIN estudiantes e
    ON s.id_estudiante = e.id_estudiante
    WHERE e.id_estudiante=%s
    ORDER BY s.fecha DESC
    """, (id_estudiante,))

    historial = cursor.fetchall()

    return render_template(
        'historial.html',
        historial=historial
    )

# =========================================
# 🔥 PDF
# =========================================

@app.route('/descargar_pdf')
def descargar_pdf():

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT
        e.nombre,
        s.motivo,
        s.dolor,
        s.estado,
        s.fecha
    FROM solicitudes s
    JOIN estudiantes e
    ON s.id_estudiante = e.id_estudiante
    ORDER BY s.fecha DESC
    """)

    datos = cursor.fetchall()

    pdf = FPDF()

    pdf.add_page()

    try:
        pdf.image("static/logo.jpg", 70, 8, 70)
    except:
        pass

    pdf.ln(45)

    pdf.set_font("Arial", "B", 20)

    pdf.cell(200, 10, "REPORTE MEDIGO", ln=True, align="C")

    pdf.ln(10)

    pdf.set_font("Arial", "B", 11)

    pdf.cell(40,10,"Nombre",1,0,"C")
    pdf.cell(55,10,"Motivo",1,0,"C")
    pdf.cell(20,10,"Dolor",1,0,"C")
    pdf.cell(30,10,"Estado",1,0,"C")
    pdf.cell(45,10,"Fecha",1,1,"C")

    pdf.set_font("Arial","",10)

    for d in datos:

        pdf.cell(40,10,str(d["nombre"]),1)
        pdf.cell(55,10,str(d["motivo"])[:20],1)
        pdf.cell(20,10,str(d["dolor"]),1)
        pdf.cell(30,10,str(d["estado"]),1)
        pdf.cell(45,10,str(d["fecha"]),1,1)

    archivo = "reporte_medigo.pdf"

    pdf.output(archivo)

    return send_file(
        archivo,
        as_attachment=True
    )

# =========================================
# 🔥 RUN
# =========================================

if __name__ == '__main__':
    app.run(debug=True)
