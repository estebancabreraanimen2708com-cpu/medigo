from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os
from datetime import datetime
import pytz

app = Flask(__name__)

# =========================
# CONEXIÓN A MYSQL
# =========================
def get_connection():
    try:
        conexion = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT"))
        )
        return conexion
    except Exception as e:
        print("❌ Error DB:", e)
        return None


# =========================
# PROFESOR (CREAR Y VER)
# =========================
@app.route('/', methods=["GET", "POST"])
@app.route('/solicitudes', methods=["GET", "POST"])
def solicitudes():

    conexion = get_connection()
    if conexion is None:
        return "Error de conexión a la base de datos"

    cursor = conexion.cursor(dictionary=True)

    if request.method == "POST":
        estudiante = request.form["estudiante"]
        motivo = request.form["motivo"]
        dolor = request.form["dolor"]

        # 🔥 Hora Ecuador
        ecuador = pytz.timezone('America/Guayaquil')
        fecha_ecuador = datetime.now(ecuador)

        sql = """
        INSERT INTO solicitudes (id_estudiante, id_profesor, motivo, dolor, estado, fecha)
        VALUES (%s, (SELECT id_profesor FROM profesores LIMIT 1), %s, %s, 'pendiente', %s)
        """

        try:
            cursor.execute(sql, (estudiante, motivo, dolor, fecha_ecuador))
            conexion.commit()
        except Exception as e:
            return "Error al insertar: " + str(e)

        return redirect(url_for("solicitudes"))

    # OBTENER ESTUDIANTES
    cursor.execute("SELECT * FROM estudiantes")
    estudiantes = cursor.fetchall()

    # OBTENER SOLICITUDES
    cursor.execute("""
    SELECT s.id_solicitud, e.nombre, s.motivo, s.estado, s.fecha, s.dolor
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    ORDER BY s.id_solicitud DESC
    """)
    solicitudes = cursor.fetchall()

    conexion.close()

    return render_template(
        "solicitudes.html",
        solicitudes=solicitudes,
        estudiantes=estudiantes
    )


# =========================
# INSPECTOR
# =========================
@app.route('/inspector')
def inspector():

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
    SELECT s.id_solicitud, e.nombre, s.motivo, s.estado, s.fecha, s.dolor
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    ORDER BY s.id_solicitud DESC
    """)

    solicitudes = cursor.fetchall()
    conexion.close()

    return render_template("inspector.html", solicitudes=solicitudes)


# =========================
# APROBAR
# =========================
@app.route('/aprobar/<int:id>')
def aprobar(id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute(
        "UPDATE solicitudes SET estado='aprobado' WHERE id_solicitud=%s", (id,)
    )
    conexion.commit()
    conexion.close()

    return redirect(url_for("inspector"))


# =========================
# RECHAZAR
# =========================
@app.route('/rechazar/<int:id>')
def rechazar(id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute(
        "UPDATE solicitudes SET estado='rechazado' WHERE id_solicitud=%s", (id,)
    )
    conexion.commit()
    conexion.close()

    return redirect(url_for("inspector"))


# =========================
# MÉDICO
# =========================
@app.route('/medico')
def medico():

    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("""
    SELECT s.id_solicitud, e.nombre, s.motivo, s.dolor
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    WHERE s.estado='aprobado'
    """)

    solicitudes = cursor.fetchall()
    conexion.close()

    return render_template("medico.html", solicitudes=solicitudes)


# =========================
# ATENDIDO
# =========================
@app.route('/atendido/<int:id>')
def atendido(id):

    conexion = get_connection()
    cursor = conexion.cursor()

    cursor.execute(
        "UPDATE solicitudes SET estado='atendido' WHERE id_solicitud=%s", (id,)
    )
    conexion.commit()
    conexion.close()

    return redirect(url_for("medico"))


if __name__ == '__main__':
    app.run(debug=True)
