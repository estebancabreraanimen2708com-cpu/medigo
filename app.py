from flask import Flask, render_template, request, redirect, jsonify, send_file
import mysql.connector
from fpdf import FPDF
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# =========================================
# MYSQL
# =========================================

def conectar_bd():
    return mysql.connector.connect(
        host="roundhouse.proxy.rlwy.net",
        user="root",
        password="wYbBPSlKSxHuYpUKYiYSfWzMnnqUyAVJ",
        database="railway",
        port=21196
    )

ecuador = pytz.timezone("America/Guayaquil")

def fecha_ecuador():
    return datetime.now(ecuador).strftime("%Y-%m-%d %H:%M:%S")

# =========================================
# INICIO
# =========================================

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/roles')
def roles():
    return render_template('roles.html')

# =========================================
# LOGIN
# =========================================

@app.route('/login/<rol>', methods=['GET', 'POST'])
def login(rol):

    error = None

    if request.method == 'POST':

        usuario = request.form['usuario']
        password = request.form['password']

        if rol == "inspector":

            if usuario == "inspector" and password == "123":
                return redirect('/inspector')

        if rol == "medico":

            if usuario == "medico" and password == "123":
                return redirect('/medico')

        error = "Usuario o contraseña incorrectos"

    return render_template(
        'login.html',
        rol=rol,
        error=error
    )

# =========================================
# SOLICITUDES
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
        (
            id_estudiante,
            motivo,
            dolor,
            estado,
            fecha
        )

        VALUES(%s,%s,%s,%s,%s)

        """, (
            estudiante,
            motivo,
            dolor,
            "Pendiente",
            fecha_ecuador()
        ))

        conn.commit()

        conn.close()

        return redirect('/solicitudes')

    cursor.execute("""

    SELECT
    MIN(id_estudiante) AS id_estudiante,
    nombre

    FROM estudiantes

    GROUP BY nombre

    ORDER BY nombre

    """)

    estudiantes = cursor.fetchall()

    conn.close()

    return render_template(
        'solicitudes.html',
        estudiantes=estudiantes
    )

# =========================================
# API
# =========================================

@app.route('/api/solicitudes')
def api_solicitudes():

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""

    SELECT

    s.id_solicitud,
    e.nombre,
    s.motivo,
    s.dolor,
    s.estado,

    DATE_FORMAT(
        s.fecha,
        '%Y-%m-%d %H:%i:%s'
    ) AS fecha

    FROM solicitudes s

    JOIN estudiantes e
    ON s.id_estudiante = e.id_estudiante

    ORDER BY s.id_solicitud DESC

    """)

    solicitudes = cursor.fetchall()

    conn.close()

    return jsonify(solicitudes)

# =========================================
# INSPECTOR
# =========================================

@app.route('/inspector')
def inspector():
    return render_template('inspector.html')

# =========================================
# MEDICO
# =========================================

@app.route('/medico')
def medico():
    return render_template('medico.html')

# =========================================
# APROBAR
# =========================================

@app.route('/aprobar/<int:id>')
def aprobar(id):

    conn = conectar_bd()
    cursor = conn.cursor()

    texto = (
        "Estudiante yendo al medico | "
        + fecha_ecuador()
    )

    cursor.execute("""

    UPDATE solicitudes

    SET estado=%s

    WHERE id_solicitud=%s

    """, (
        texto,
        id
    ))

    conn.commit()

    conn.close()

    return redirect('/inspector')

# =========================================
# RECHAZAR
# =========================================

@app.route('/rechazar/<int:id>')
def rechazar(id):

    conn = conectar_bd()
    cursor = conn.cursor()

    texto = (
        "Estudiante se queda en clases | "
        + fecha_ecuador()
    )

    cursor.execute("""

    UPDATE solicitudes

    SET estado=%s

    WHERE id_solicitud=%s

    """, (
        texto,
        id
    ))

    conn.commit()

    conn.close()

    return redirect('/inspector')

# =========================================
# LLEGO AL MEDICO
# =========================================

@app.route('/llego/<int:id>')
def llego(id):

    conn = conectar_bd()
    cursor = conn.cursor()

    texto = (
        "Estudiante llego al medico | "
        + fecha_ecuador()
    )

    cursor.execute("""

    UPDATE solicitudes

    SET estado=%s

    WHERE id_solicitud=%s

    """, (
        texto,
        id
    ))

    conn.commit()

    conn.close()

    return redirect('/medico')

# =========================================
# PDF
# =========================================

@app.route('/pdf')
def pdf():

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""

    SELECT

    e.nombre,
    s.motivo,
    s.dolor,
    s.estado,

    DATE_FORMAT(
        s.fecha,
        '%Y-%m-%d %H:%i:%s'
    ) AS fecha

    FROM solicitudes s

    JOIN estudiantes e
    ON s.id_estudiante = e.id_estudiante

    ORDER BY s.id_solicitud DESC

    """)

    datos = cursor.fetchall()

    conn.close()

    archivo = "reporte_medigo.pdf"

    pdf = FPDF()

    pdf.add_page()

    if os.path.exists("static/logo.jpg"):
        pdf.image("static/logo.jpg", 75, 8, 60)

    pdf.ln(45)

    pdf.set_font("Arial", "B", 18)

    pdf.cell(
        0,
        10,
        "Reporte MediGo",
        ln=True,
        align="C"
    )

    pdf.ln(10)

    pdf.set_font("Arial", "", 10)

    for d in datos:

        texto = (
            f"{d['nombre']} | "
            f"{d['motivo']} | "
            f"Dolor: {d['dolor']} | "
            f"{d['estado']} | "
            f"{d['fecha']}"
        )

        pdf.multi_cell(0, 8, texto)

    pdf.output(archivo)

    return send_file(
        archivo,
        as_attachment=True
    )

# =========================================
# RUN
# =========================================

if __name__ == '__main__':
    app.run(debug=True)
