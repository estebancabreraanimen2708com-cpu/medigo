from flask import Flask, render_template, request, redirect, session, jsonify, send_file
import mysql.connector
import os
from datetime import datetime
import pytz
import io

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "medigo_secret"

# 🔥 CONEXIÓN MYSQL
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT"))
    )

# 🔐 PROTECCIÓN
@app.before_request
def proteger():

    ruta = request.path

    # rutas públicas
    publicas = [
        '/',
        '/roles',
        '/solicitudes'
    ]

    if (
        ruta in publicas
        or ruta.startswith('/static')
        or ruta.startswith('/api')
        or ruta.startswith('/login')
    ):
        return

    # inspector
    if ruta.startswith('/inspector'):
        if session.get("rol") != "inspector":
            return redirect('/login/inspector')

    # medico
    if ruta.startswith('/medico'):
        if session.get("rol") != "medico":
            return redirect('/login/medico')

# 🔥 PANTALLA INICIO
@app.route('/')
def inicio():
    return render_template('inicio.html')

# 🔥 ROLES
@app.route('/roles')
def roles():
    return render_template('roles.html')

# 🔥 LOGIN
@app.route('/login/<rol>', methods=['GET', 'POST'])
def login(rol):

    if request.method == 'POST':

        usuario = request.form['user']
        password = request.form['pass']

        # 👮 inspector
        if rol == "inspector":
            if usuario == "admin" and password == "1234":
                session["rol"] = "inspector"
                return redirect('/inspector')

        # 🏥 medico
        if rol == "medico":
            if usuario == "doctor" and password == "1234":
                session["rol"] = "medico"
                return redirect('/medico')

        return render_template(
            'login.html',
            rol=rol,
            error="Credenciales incorrectas"
        )

    return render_template('login.html', rol=rol)

# 🔥 LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# 🔥 OBTENER ESTUDIANTES SIN DUPLICADOS
def obtener_estudiantes():

    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("""
        SELECT MIN(id_estudiante) as id_estudiante, nombre
        FROM estudiantes
        GROUP BY nombre
        ORDER BY nombre
    """)

    estudiantes = cur.fetchall()

    con.close()

    return estudiantes

# 🔥 SOLICITUDES
@app.route('/solicitudes', methods=['GET', 'POST'])
def solicitudes():

    con = get_connection()
    cur = con.cursor()

    # guardar solicitud
    if request.method == 'POST':

        estudiante = request.form['estudiante']
        motivo = request.form['motivo']
        dolor = request.form['dolor']

        fecha = datetime.now(
            pytz.timezone('America/Guayaquil')
        )

        cur.execute("""
            INSERT INTO solicitudes
            (
                id_estudiante,
                id_profesor,
                motivo,
                dolor,
                estado,
                fecha
            )
            VALUES
            (
                %s,
                (SELECT id_profesor FROM profesores LIMIT 1),
                %s,
                %s,
                'pendiente',
                %s
            )
        """, (
            estudiante,
            motivo,
            dolor,
            fecha
        ))

        con.commit()

        con.close()

        return redirect('/solicitudes')

    estudiantes = obtener_estudiantes()

    con.close()

    return render_template(
        'solicitudes.html',
        estudiantes=estudiantes
    )

# 🔥 API SOLICITUDES
@app.route('/api/solicitudes')
def api_solicitudes():

    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("""
        SELECT
            s.id_solicitud,
            e.nombre,
            s.motivo,
            s.estado,
            DATE_FORMAT(
                s.fecha,
                '%Y-%m-%d %H:%i:%s'
            ) as fecha
        FROM solicitudes s
        JOIN estudiantes e
        ON s.id_estudiante = e.id_estudiante
        ORDER BY s.id_solicitud DESC
    """)

    solicitudes = cur.fetchall()

    con.close()

    return jsonify(solicitudes)

# 👮 INSPECTOR
@app.route('/inspector')
def inspector():
    return render_template('inspector.html')

# 🏥 MEDICO
@app.route('/medico')
def medico():
    return render_template('medico.html')

# ✅ APROBAR
@app.route('/aprobar/<int:id>')
def aprobar(id):

    con = get_connection()
    cur = con.cursor()

    cur.execute("""
        UPDATE solicitudes
        SET estado='aprobado'
        WHERE id_solicitud=%s
    """, (id,))

    con.commit()

    con.close()

    return redirect('/inspector')

# ❌ RECHAZAR
@app.route('/rechazar/<int:id>')
def rechazar(id):

    con = get_connection()
    cur = con.cursor()

    cur.execute("""
        UPDATE solicitudes
        SET estado='rechazado'
        WHERE id_solicitud=%s
    """, (id,))

    con.commit()

    con.close()

    return redirect('/inspector')

# 🏥 ATENDIDO
@app.route('/atendido/<int:id>')
def atendido(id):

    con = get_connection()
    cur = con.cursor()

    cur.execute("""
        UPDATE solicitudes
        SET estado='atendido'
        WHERE id_solicitud=%s
    """, (id,))

    con.commit()

    con.close()

    return redirect('/medico')

# 📄 PDF
@app.route('/descargar_pdf')
def descargar_pdf():

    if session.get("rol") != "inspector":
        return redirect('/login/inspector')

    con = get_connection()
    cur = con.cursor(dictionary=True)

    hoy = datetime.now(
        pytz.timezone('America/Guayaquil')
    ).strftime('%Y-%m-%d')

    cur.execute("""
        SELECT
            e.nombre,
            s.motivo,
            s.estado,
            DATE_FORMAT(
                s.fecha,
                '%H:%i'
            ) as hora
        FROM solicitudes s
        JOIN estudiantes e
        ON s.id_estudiante = e.id_estudiante
        WHERE DATE(s.fecha) = %s
        ORDER BY s.fecha DESC
    """, (hoy,))

    datos = cur.fetchall()

    con.close()

    # PDF
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)

    elementos = []

    estilos = getSampleStyleSheet()

    titulo = Paragraph(
        f"<b>Reporte MediGo - {hoy}</b>",
        estilos['Title']
    )

    elementos.append(titulo)
    elementos.append(Spacer(1, 20))

    tabla_data = [
        ['Nombre', 'Motivo', 'Estado', 'Hora']
    ]

    for d in datos:
        tabla_data.append([
            d['nombre'],
            d['motivo'],
            d['estado'],
            d['hora']
        ])

    tabla = Table(tabla_data)

    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),

        ('GRID', (0,0), (-1,-1), 1, colors.black),

        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),

        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#e2e8f0'))
    ]))

    elementos.append(tabla)

    doc.build(elementos)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"Reporte_{hoy}.pdf",
        mimetype='application/pdf'
    )

# 🚀 EJECUTAR
if __name__ == '__main__':
    app.run(debug=True)
