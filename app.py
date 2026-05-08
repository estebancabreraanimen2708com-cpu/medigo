from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

# =========================================
# 🔥 MYSQL RAILWAY PUBLIC NETWORK
# =========================================

def conectar_bd():
    return mysql.connector.connect(
        host="roundhouse.proxy.rlwy.net",
        user="root",
        password="wYbBPSlKSxHuYpUKYiYSfWzMnnqUyAVJ",
        database="railway",
        port=21196
    )

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
# 🔥 LOGIN ÚNICO
# =========================================

@app.route('/login/<rol>', methods=['GET', 'POST'])
def login(rol):

    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']

        if rol == "inspector" and usuario == "inspector" and password == "123":
            return redirect('/inspector')

        if rol == "medico" and usuario == "medico" and password == "123":
            return redirect('/medico')

    return render_template('login.html', rol=rol)

# =========================================
# 🔥 PROFESOR / SOLICITUDES
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
            INSERT INTO solicitudes (id_estudiante, motivo, dolor, estado)
            VALUES (%s, %s, %s, %s)
        """, (estudiante, motivo, dolor, "Pendiente"))

        conn.commit()
        conn.close()

        return redirect('/solicitudes')

    cursor.execute("""
        SELECT DISTINCT id_estudiante, nombre
        FROM estudiantes
        ORDER BY nombre
    """)

    estudiantes = cursor.fetchall()
    conn.close()

    return render_template('solicitudes.html', estudiantes=estudiantes)

# =========================================
# 🔥 INSPECTOR
# =========================================

@app.route('/inspector')
def inspector():

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.id_solicitud,
            e.nombre,
            s.motivo,
            s.dolor,
            s.estado
        FROM solicitudes s
        JOIN estudiantes e
        ON s.id_estudiante = e.id_estudiante
        ORDER BY s.id_solicitud DESC
    """)

    solicitudes = cursor.fetchall()
    conn.close()

    return render_template('inspector.html', solicitudes=solicitudes)

# =========================================
# 🔥 MÉDICO
# =========================================

@app.route('/medico')
def medico():

    conn = conectar_bd()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.id_solicitud,
            e.nombre,
            s.motivo,
            s.dolor,
            s.estado
        FROM solicitudes s
        JOIN estudiantes e
        ON s.id_estudiante = e.id_estudiante
        ORDER BY s.id_solicitud DESC
    """)

    solicitudes = cursor.fetchall()
    conn.close()

    return render_template('medico.html', solicitudes=solicitudes)

# =========================================
# 🔥 APROBAR / RECHAZAR
# =========================================

@app.route('/aprobar/<int:id>')
def aprobar(id):

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE solicitudes
        SET estado = 'Aprobado'
        WHERE id_solicitud = %s
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
        SET estado = 'Rechazado'
        WHERE id_solicitud = %s
    """, (id,))

    conn.commit()
    conn.close()

    return redirect('/inspector')

# =========================================
# 🔥 PDF
# =========================================

@app.route('/pdf')
def pdf():
    return "PDF próximamente"

# =========================================
# 🔥 RUN
# =========================================

if __name__ == '__main__':
    app.run(debug=True)
