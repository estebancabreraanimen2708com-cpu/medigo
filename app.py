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

def columnas_solicitudes():
    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("DESCRIBE solicitudes")
    columnas = [c["Field"] for c in cursor.fetchall()]
    conn.close()
    return columnas

def asegurar_columnas():
    conn = conectar_bd()
    cursor = conn.cursor()

    for nombre, tipo in [
        ("nombre", "VARCHAR(255)"),
        ("curso", "VARCHAR(100)"),
        ("observaciones", "TEXT"),
        ("decision_medico", "VARCHAR(100)")
    ]:
        try:
            cursor.execute(f"ALTER TABLE solicitudes ADD COLUMN {nombre} {tipo}")
            conn.commit()
        except:
            pass

    conn.close()

def asegurar_estado_medico():
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estado_medico(
            id INT PRIMARY KEY,
            disponible TINYINT DEFAULT 1,
            mensaje VARCHAR(255),
            fecha VARCHAR(50)
        )
    """)

    cursor.execute("""
        INSERT IGNORE INTO estado_medico(id, disponible, mensaje, fecha)
        VALUES(1, 1, 'Médico disponible', %s)
    """, (fecha_ecuador(),))

    conn.commit()
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

    if request.method == 'POST':
        curso = request.form.get('curso', '')
        nombre = request.form.get('nombre_manual', '')
        motivo = request.form.get('motivo', '')
        dolor = request.form.get('dolor', '')
        origen = request.form.get('origen', 'profesor')

        cols = columnas_solicitudes()

        conn = conectar_bd()
        cursor = conn.cursor()

        if "id_estudiante" in cols:
            try:
                cursor.execute("INSERT INTO estudiantes(nombre) VALUES(%s)", (nombre,))
                conn.commit()
                id_estudiante = cursor.lastrowid
            except:
                id_estudiante = 1

            cursor.execute("""
                INSERT INTO solicitudes
                (id_estudiante, nombre, motivo, dolor, estado, fecha, curso, observaciones, decision_medico)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                id_estudiante,
                nombre,
                motivo,
                dolor,
                "Pendiente",
                fecha_ecuador(),
                curso,
                "",
                ""
            ))
        else:
            cursor.execute("""
                INSERT INTO solicitudes
                (nombre, motivo, dolor, estado, fecha, curso, observaciones, decision_medico)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                nombre,
                motivo,
                dolor,
                "Pendiente",
                fecha_ecuador(),
                curso,
                "",
                ""
            ))

        conn.commit()
        conn.close()

        if origen == "inspector":
            return redirect('/inspector')

        if origen == "medico":
            return redirect('/medico')

        return redirect('/solicitudes')

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
            COALESCE(decision_medico, '') AS decision_medico,
            fecha
        FROM solicitudes
        ORDER BY id_solicitud DESC
    """)

    datos = cursor.fetchall()
    conn.close()

    for d in datos:
        d["fecha"] = str(d["fecha"]) if d["fecha"] else ""

    return jsonify(datos)

@app.route('/api/estado_medico')
def api_estado_medico():
    asegurar_estado_medico()

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT disponible, mensaje, fecha
        FROM estado_medico
        WHERE id=1
    """)

    estado = cursor.fetchone()
    conn.close()

    return jsonify(estado)

@app.route('/estado_medico/<estado>')
def cambiar_estado_medico(estado):
    asegurar_estado_medico()
    asegurar_columnas()

    id_solicitud = request.args.get("id")

    if estado == "disponible":
        disponible = 1
        mensaje = "Médico disponible"
        decision = "🟢 Puede subir"
    else:
        disponible = 0
        mensaje = "Médico no disponible"
        decision = "🔴 No puede subir"

    conn = conectar_bd()
    cursor = conn.cursor()

    if id_solicitud:
        cursor.execute("""
            UPDATE solicitudes
            SET decision_medico=%s
            WHERE id_solicitud=%s
        """, (decision, id_solicitud))
    else:
        cursor.execute("""
            UPDATE estado_medico
            SET disponible=%s, mensaje=%s, fecha=%s
            WHERE id=1
        """, (disponible, mensaje, fecha_ecuador()))

    conn.commit()
    conn.close()

    return redirect('/medico')

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
            COALESCE(decision_medico, '') AS decision_medico,
            fecha
        FROM solicitudes
        WHERE nombre = %s
        ORDER BY id_solicitud DESC
    """, (nombre,))

    datos = cursor.fetchall()
    conn.close()

    for d in datos:
        d["fecha"] = str(d["fecha"]) if d["fecha"] else ""

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
            COALESCE(decision_medico, '') AS decision_medico,
            fecha
        FROM solicitudes
        ORDER BY id_solicitud DESC
    """)

    datos = cursor.fetchall()
    conn.close()

    pdf = FPDF()
    pdf.add_page()

    pdf.set_fill_color(0, 86, 179)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 18)
    pdf.cell(190, 15, "MediGo - Reporte Medico", 1, 1, "C", True)

    pdf.ln(8)
    pdf.set_text_color(0, 43, 92)

    for d in datos:
        fecha = str(d["fecha"]) if d["fecha"] else ""

        pdf.set_fill_color(56, 189, 248)
        pdf.set_text_color(0, 43, 92)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(190, 10, "Solicitud Medica Escolar", 1, 1, "C", True)

        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(235, 248, 255)

        campos = [
            ("Curso", d["curso"]),
            ("Nombre", d["nombre"]),
            ("Motivo", d["motivo"]),
            ("Dolor", d["dolor"]),
            ("Estado", d["estado"]),
            ("Decision Medico", d["decision_medico"]),
            ("Fecha", fecha),
            ("Observaciones", d["observaciones"])
        ]

        for etiqueta, valor in campos:
            pdf.set_font("Arial", "B", 10)
            pdf.cell(45, 9, etiqueta + ":", 1, 0, "L", True)

            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(145, 9, str(valor), 1, "L")

        pdf.ln(8)

    archivo = "reporte_medigo.pdf"
    pdf.output(archivo)

    return send_file(archivo, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
