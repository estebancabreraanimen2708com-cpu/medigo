from flask import Flask, render_template, request, redirect, jsonify, send_file
import mysql.connector
from fpdf import FPDF
from datetime import datetime
import pytz

app = Flask(__name__)

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

def asegurar_columnas():
    conn = conectar_bd()
    cursor = conn.cursor()

    columnas = [
        ("nombre", "VARCHAR(255)"),
        ("curso", "VARCHAR(100)"),
        ("observaciones", "TEXT")
    ]

    for nombre, tipo in columnas:
        try:
            cursor.execute(f"ALTER TABLE solicitudes ADD COLUMN {nombre} {tipo}")
            conn.commit()
        except:
            pass

    conn.close()

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/roles')
def roles():
    return render_template('roles.html')

@app.route('/login/<rol>', methods=['GET', 'POST'])
def login(rol):
    error = None

    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']

        if rol == "inspector" and usuario == "inspector" and password == "123":
            return redirect('/inspector')

        if rol == "medico" and usuario == "medico" and password == "123":
            return redirect('/medico')

        error = "Usuario o contraseña incorrectos"

    return render_template('login.html', rol=rol, error=error)

@app.route('/solicitudes', methods=['GET', 'POST'])
def solicitudes():
    asegurar_columnas()

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        curso = request.form.get('curso', '')
        nombre = request.form.get('nombre_manual', '')
        motivo = request.form.get('motivo', '')
        dolor = request.form.get('dolor', '')
        origen = request.form.get('origen', 'profesor')

        cursor.execute("""
            INSERT INTO solicitudes
            (nombre, motivo, dolor, estado, fecha, curso, observaciones)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, (
            nombre,
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
    return render_template('solicitudes.html')

@app.route('/api/solicitudes')
def api_solicitudes():
    asegurar_columnas()

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id_solicitud,
            COALESCE(nombre, '') AS nombre,
            COALESCE(motivo, '') AS motivo,
            COALESCE(dolor, '') AS dolor,
            COALESCE(estado, '') AS estado,
            COALESCE(curso, '') AS curso,
            COALESCE(observaciones, '') AS observaciones,
            fecha
        FROM solicitudes
        ORDER BY id_solicitud DESC
    """)

    datos = cursor.fetchall()
    conn.close()

    for d in datos:
        if d["fecha"]:
            d["fecha"] = str(d["fecha"])
        else:
            d["fecha"] = ""

    return jsonify(datos)

@app.route('/historial/<path:nombre>')
def historial(nombre):
    asegurar_columnas()

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            COALESCE(nombre, '') AS nombre,
            COALESCE(curso, '') AS curso,
            COALESCE(motivo, '') AS motivo,
            COALESCE(dolor, '') AS dolor,
            COALESCE(estado, '') AS estado,
            COALESCE(observaciones, '') AS observaciones,
            fecha
        FROM solicitudes
        WHERE nombre = %s
        ORDER BY id_solicitud DESC
    """, (nombre,))

    datos = cursor.fetchall()
    conn.close()

    for d in datos:
        if d["fecha"]:
            d["fecha"] = str(d["fecha"])
        else:
            d["fecha"] = ""

    return render_template(
        'historial.html',
        historial=datos,
        nombre=nombre,
        total=len(datos)
    )

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
    texto = request.form.get('observaciones', '')

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE solicitudes
        SET observaciones=%s
        WHERE id_solicitud=%s
    """, (texto, id))

    conn.commit()
    conn.close()

    return redirect('/medico')

@app.route('/pdf')
def pdf():
    asegurar_columnas()

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            COALESCE(nombre, '') AS nombre,
            COALESCE(curso, '') AS curso,
            COALESCE(motivo, '') AS motivo,
            COALESCE(dolor, '') AS dolor,
            COALESCE(estado, '') AS estado,
            COALESCE(observaciones, '') AS observaciones,
            fecha
        FROM solicitudes
        ORDER BY id_solicitud DESC
    """)

    datos = cursor.fetchall()
    conn.close()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "Reporte MediGo", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 10)

    for d in datos:
        fecha = str(d["fecha"]) if d["fecha"] else ""

        texto = (
            f"Curso: {d['curso']} | "
            f"Nombre: {d['nombre']} | "
            f"Motivo: {d['motivo']} | "
            f"Dolor: {d['dolor']} | "
            f"Estado: {d['estado']} | "
            f"Fecha: {fecha} | "
            f"Observaciones: {d['observaciones']}"
        )

        pdf.multi_cell(0, 8, texto)

    archivo = "reporte.pdf"
    pdf.output(archivo)

    return send_file(archivo, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
