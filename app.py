from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os

app = Flask(__name__)

# =========================
# CONEXIÓN A MYSQL (RAILWAY)
# =========================
try:
    conexion = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT"))
    )
    cursor = conexion.cursor(dictionary=True)
    print("✅ Conexión exitosa a la base de datos")

except Exception as e:
    print("❌ Error conectando a la base de datos:", e)


# =========================
# PROFESOR (CREAR Y VER)
# =========================
@app.route('/', methods=["GET", "POST"])
@app.route('/solicitudes', methods=["GET", "POST"])
def solicitudes():

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

        return redirect(url_for("solicitudes"))

    # 🔥 OBTENER ESTUDIANTES (IMPORTANTE)
    cursor.execute("SELECT * FROM estudiantes")
    estudiantes = cursor.fetchall()

    # 🔥 OBTENER SOLICITUDES
    cursor.execute("""
    SELECT s.id_solicitud, e.nombre, s.motivo, s.estado, s.fecha, s.dolor
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    ORDER BY s.id_solicitud DESC
    """)
    solicitudes = cursor.fetchall()

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

    cursor.execute("""
    SELECT s.id_solicitud, e.nombre, s.motivo, s.estado, s.fecha, s.dolor
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    ORDER BY s.id_solicitud DESC
    """)

    solicitudes = cursor.fetchall()

    return render_template("inspector.html", solicitudes=solicitudes)


# =========================
# APROBAR
# =========================
@app.route('/aprobar/<int:id>')
def aprobar(id):

    cursor.execute(
        "UPDATE solicitudes SET estado='aprobado' WHERE id_solicitud=%s", (id,)
    )
    conexion.commit()

    return redirect(url_for("inspector"))


# =========================
# RECHAZAR
# =========================
@app.route('/rechazar/<int:id>')
def rechazar(id):

    cursor.execute(
        "UPDATE solicitudes SET estado='rechazado' WHERE id_solicitud=%s", (id,)
    )
    conexion.commit()

    return redirect(url_for("inspector"))


# =========================
# MÉDICO
# =========================
@app.route('/medico')
def medico():

    cursor.execute("""
    SELECT s.id_solicitud, e.nombre, s.motivo, s.dolor
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    WHERE s.estado='aprobado'
    """)

    solicitudes = cursor.fetchall()

    return render_template("medico.html", solicitudes=solicitudes)


# =========================
# ATENDIDO
# =========================
@app.route('/atendido/<int:id>')
def atendido(id):

    cursor.execute(
        "UPDATE solicitudes SET estado='atendido' WHERE id_solicitud=%s", (id,)
    )
    conexion.commit()

    return redirect(url_for("medico"))


# =========================
# EJECUTAR APP
# =========================
if __name__ == '__main__':
    app.run(debug=True)
