from flask import Flask, render_template, request, redirect, jsonify, send_file
import mysql.connector
from fpdf import FPDF
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# =========================
# CONEXIÓN MYSQL
# =========================

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


# =========================
# CREAR COLUMNAS SI NO EXISTEN
# =========================

def asegurar_columnas():

    conn = conectar_bd()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        ALTER TABLE solicitudes
        ADD COLUMN curso VARCHAR(50)
        """)
        conn.commit()
    except:
        pass

    try:
        cursor.execute("""
        ALTER TABLE solicitudes
        ADD COLUMN observaciones TEXT
        """)
        conn.commit()
    except:
        pass

    conn.close()


# =========================
# INICIO
# =========================

@app.route('/')
def inicio():
    return render_template('inicio.html')


@app.route('/roles')
def roles():
    return render_template('roles.html')


# =========================
# LOGIN
# =========================

@app.route('/login/<rol>', methods=['GET', 'POST'])
def login(rol):

    error = None

    if request.method == 'POST':

        usuario = request.form['usuario']
        password = request.form['password']

        if rol == "inspector":

            if usuario == "inspector" and password == "123":
                return redirect('/inspector')

            else:
                error = "Usuario o contraseña incorrectos"

        if rol == "medico":

            if usuario == "medico" and password == "123":
                return redirect('/medico')

            else:
                error = "Usuario o contraseña incorrectos"

    return render_template(
        'login.html',
        rol=rol,
        error=error
    )


# =========================
# PROFESOR
# =========================

@app.route('/solicitudes', methods=['GET', 'POST'])
def solicitudes():

    asegurar_columnas()

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':

        curso = request.form['curso']
        nombre = request.form['nombre_manual']
        motivo = request.form['motivo']
        dolor = request.form['dolor']

        origen = request.form.get(
            'origen',
            'profesor'
        )

        # CREAR ESTUDIANTE
        cursor.execute("""
        INSERT INTO estudiantes(nombre)
        VALUES(%s)
        """, (nombre,))

        conn.commit()

        id_estudiante = cursor.lastrowid

        # CREAR SOLICITUD
        cursor.execute("""
        INSERT INTO solicitudes
        (
            id_estudiante,
            motivo,
            dolor,
            estado,
            fecha,
            curso,
            observaciones
        )
        VALUES(%s,%s,%s,%s,%s,%s,%s)
        """, (
            id_estudiante,
            motivo,
            dolor,
            "Pendiente",
            fecha_ecuador(),
            curso,
            ""
        ))

        conn.commit()
        conn.close()

        if origen == "inspector":
            return redirect('/inspector')

        if origen == "medico":
            return redirect('/medico')

        return redirect('/solicitudes')

    conn.close()

    return render_template(
        'solicitudes.html'
    )


# =========================
# API SOLICITUDES
# =========================

@app.route('/api/solicitudes')
def api_solicitudes():

    asegurar_columnas()

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""

    SELECT

        s.id_solicitud,
        s.id_estudiante,

        e.nombre,

        s.motivo,
        s.dolor,
        s.estado,

        COALESCE(s.curso,'') AS curso,

        COALESCE(
            s.observaciones,
            ''
        ) AS observaciones,

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

    return jsonify(datos)


# =========================
# HISTORIAL
# =========================

@app.route('/historial/<int:id_estudiante>')
def historial(id_estudiante):

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    # DATOS ESTUDIANTE
    cursor.execute("""

    SELECT nombre

    FROM estudiantes

    WHERE id_estudiante=%s

    """, (id_estudiante,))

    estudiante = cursor.fetchone()

    if not estudiante:

        conn.close()

        return "Estudiante no encontrado"

    # HISTORIAL
    cursor.execute("""

    SELECT

        e.nombre,

        COALESCE(
            s.curso,
            ''
        ) AS curso,

        s.motivo,
        s.dolor,
        s.estado,

        COALESCE(
            s.observaciones,
            ''
        ) AS observaciones,

        DATE_FORMAT(
            s.fecha,
            '%Y-%m-%d %H:%i:%s'
        ) AS fecha

    FROM solicitudes s

    JOIN estudiantes e
    ON s.id_estudiante = e.id_estudiante

    WHERE s.id_estudiante=%s

    ORDER BY s.id_solicitud DESC

    """, (id_estudiante,))

    historial = cursor.fetchall()

    conn.close()

    return render_template(
        'historial.html',
        historial=historial,
        nombre=estudiante["nombre"],
        total=len(historial)
    )


# =========================
# INSPECTOR
# =========================

@app.route('/inspector')
def inspector():
    return render_template('inspector.html')


@app.route('/aprobar/<int:id>')
def aprobar(id):

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE solicitudes
    SET estado='Aprobado'
    WHERE id_solicitud=%s
    """, (id,))

    conn.commit()
    conn.close()

    return redirect('/inspector')


@app.route('/rechazar/<int:id>')
def rechazar(id):

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE solicitudes
    SET estado='Rechazado'
    WHERE id_solicitud=%s
    """, (id,))

    conn.commit()
    conn.close()

    return redirect('/inspector')


# =========================
# MÉDICO
# =========================

@app.route('/medico')
def medico():
    return render_template('medico.html')


@app.route('/atendido/<int:id>')
def atendido(id):

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE solicitudes
    SET estado='Atendido'
    WHERE id_solicitud=%s
    """, (id,))

    conn.commit()
    conn.close()

    return redirect('/medico')


@app.route('/observacion/<int:id>', methods=['POST'])
def observacion(id):

    texto = request.form.get(
        'observaciones',
        ''
    )

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE solicitudes
    SET observaciones=%s
    WHERE id_solicitud=%s
    """, (
        texto,
        id
    ))

    conn.commit()
    conn.close()

    return redirect('/medico')


# =========================
# PDF
# =========================

@app.route('/pdf')
def pdf():

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""

    SELECT

        e.nombre,

        COALESCE(
            s.curso,
            ''
        ) AS curso,

        s.motivo,
        s.dolor,
        s.estado,

        COALESCE(
            s.observaciones,
            ''
        ) AS observaciones,

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

    try:

        if os.path.exists("static/logo.jpg"):

            pdf.image(
                "static/logo.jpg",
                75,
                8,
                60
            )

            pdf.ln(45)

    except:
        pdf.ln(10)

    pdf.set_font("Arial", "B", 18)

    pdf.cell(
        0,
        10,
        "Reporte MediGo",
        ln=True,
        align="C"
    )

    pdf.set_font("Arial", "", 11)

    pdf.cell(
        0,
        8,
        "Fecha: " + fecha_ecuador(),
        ln=True,
        align="C"
    )

    pdf.ln(8)

    pdf.set_font("Arial", "", 10)

    for d in datos:

        texto = (
            f"Curso: {d['curso']} | "
            f"Nombre: {d['nombre']} | "
            f"Motivo: {d['motivo']} | "
            f"Dolor: {d['dolor']} | "
            f"Estado: {d['estado']} | "
            f"Fecha: {d['fecha']} | "
            f"Observaciones: {d['observaciones']}"
        )

        pdf.multi_cell(
            0,
            8,
            texto
        )

    pdf.output(archivo)

    return send_file(
        archivo,
        as_attachment=True
    )


# =========================
# RUN
# =========================

if __name__ == '__main__':
    app.run(debug=True)
