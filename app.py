from flask import Flask, render_template, request, redirect
import mysql.connector

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
# 🔥 LOGIN INSPECTOR
# =========================================

@app.route('/login/inspector', methods=['GET', 'POST'])
def login_inspector():

    if request.method == 'POST':

        usuario = request.form['usuario']
        password = request.form['password']

        if usuario == "inspector" and password == "123":

            return redirect('/inspector')

    return render_template(
        'login.html',
        rol="inspector"
    )

# =========================================
# 🔥 LOGIN MEDICO
# =========================================

@app.route('/login/medico', methods=['GET', 'POST'])
def login_medico():

    if request.method == 'POST':

        usuario = request.form['usuario']
        password = request.form['password']

        if usuario == "medico" and password == "123":

            return redirect('/medico')

    return render_template(
        'login.html',
        rol="medico"
    )

# =========================================
# 🔥 SOLICITUDES
# =========================================

@app.route('/solicitudes', methods=['GET', 'POST'])
def solicitudes():

    try:

        conn = conectar_bd()

        cursor = conn.cursor(dictionary=True)

        # GUARDAR SOLICITUD
        if request.method == 'POST':

            estudiante = request.form['estudiante']

            motivo = request.form['motivo']

            dolor = request.form['dolor']

            cursor.execute("""

            INSERT INTO solicitudes
            (id_estudiante,motivo,dolor,estado)

            VALUES(%s,%s,%s,%s)

            """, (
                estudiante,
                motivo,
                dolor,
                "Pendiente"
            ))

            conn.commit()

            return redirect('/solicitudes')

        # ESTUDIANTES
        cursor.execute("""

        SELECT
        id_estudiante,
        nombre

        FROM estudiantes

        ORDER BY nombre

        """)

        estudiantes = cursor.fetchall()

        return render_template(
            'solicitudes.html',
            estudiantes=estudiantes
        )

    except Exception as e:

        return f"ERROR PROFESOR: {e}"

# =========================================
# 🔥 INSPECTOR
# =========================================

@app.route('/inspector')
def inspector():

    try:

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

        return render_template(
            'inspector.html',
            solicitudes=solicitudes
        )

    except Exception as e:

        return f"ERROR INSPECTOR: {e}"

# =========================================
# 🔥 APROBAR
# =========================================

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
    SET estado='Rechazado'

    WHERE id_solicitud=%s

    """, (id,))

    conn.commit()

    return redirect('/inspector')

# =========================================
# 🔥 MEDICO
# =========================================

@app.route('/medico')
def medico():

    try:

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

        return render_template(
            'medico.html',
            solicitudes=solicitudes
        )

    except Exception as e:

        return f"ERROR MEDICO: {e}"

# =========================================
# 🔥 RUN
# =========================================

if __name__ == '__main__':

    app.run(debug=True)
