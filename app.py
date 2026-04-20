from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os

app = Flask(__name__)

# =========================
# CONEXIÓN A MYSQL (RENDER)
# =========================
def get_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME"),
        port=int(os.environ.get("DB_PORT", 3306))
    )


# =========================
# PROFESOR (CREAR Y VER)
# =========================
@app.route('/', methods=["GET", "POST"])
@app.route('/solicitudes', methods=["GET", "POST"])
def solicitudes():
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)

    if request.method == "POST":
        estudiante = request.form["estudiante"]
        motivo = request.form["motivo"]
        dolor = request.form["dolor"]

        sql = """
        INSERT INTO solicitudes (id_estudiante, id_profesor, motivo, dolor, estado)
        VALUES (%s, 1, %s, %s, 'pendiente')
        """

        cursor.execute(sql, (estudiante, motivo, dolor))
        conexion.commit()

        cursor.close()
        conexion.close()

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

    cursor.close()
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

    cursor.close()
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

    cursor.close()
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

    cursor.close()
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

    cursor.close()
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

    cursor.close()
    conexion.close()

    return redirect(url_for("medico"))


# =========================
# EJECUTAR APP
# =========================
if __name__ == '__main__':
    app.run(debug=True)
