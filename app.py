from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os

app = Flask(__name__)

# =========================
# CONEXIÓN SEGURA
# =========================
def get_connection():
    try:
        conexion = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            database=os.environ.get("DB_NAME"),
            port=int(os.environ.get("DB_PORT", 3306))
        )
        return conexion
    except Exception as e:
        print("ERROR CONEXIÓN:", e)
        return None


# =========================
# PROFESOR
# =========================
@app.route('/', methods=["GET", "POST"])
@app.route('/solicitudes', methods=["GET", "POST"])
def solicitudes():

    conexion = get_connection()
    if conexion is None:
        return "Error conectando a la base de datos"

    cursor = conexion.cursor(dictionary=True)

    if request.method == "POST":
        try:
            estudiante = request.form["estudiante"]
            motivo = request.form["motivo"]
            dolor = request.form["dolor"]

            cursor.execute("""
            INSERT INTO solicitudes (id_estudiante, id_profesor, motivo, dolor, estado)
            VALUES (%s, 1, %s, %s, 'pendiente')
            """, (estudiante, motivo, dolor))

            conexion.commit()

        except Exception as e:
            return f"Error al insertar: {e}"

        finally:
            cursor.close()
            conexion.close()

        return redirect(url_for("solicitudes"))

    # GET
    try:
        cursor.execute("SELECT * FROM estudiantes")
        estudiantes = cursor.fetchall()

        cursor.execute("""
        SELECT s.id_solicitud, e.nombre, s.motivo, s.estado, s.fecha, s.dolor
        FROM solicitudes s
        JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
        ORDER BY s.id_solicitud DESC
        """)
        solicitudes = cursor.fetchall()

    except Exception as e:
        return f"Error consultando: {e}"

    finally:
        cursor.close()
        conexion.close()

    return render_template("solicitudes.html", solicitudes=solicitudes, estudiantes=estudiantes)


# =========================
# INSPECTOR
# =========================
@app.route('/inspector')
def inspector():

    conexion = get_connection()
    if conexion is None:
        return "Error DB"

    cursor = conexion.cursor(dictionary=True)

    try:
        cursor.execute("""
        SELECT s.id_solicitud, e.nombre, s.motivo, s.estado, s.fecha, s.dolor
        FROM solicitudes s
        JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
        ORDER BY s.id_solicitud DESC
        """)
        solicitudes = cursor.fetchall()

    except Exception as e:
        return f"Error: {e}"

    finally:
        cursor.close()
        conexion.close()

    return render_template("inspector.html", solicitudes=solicitudes)


# =========================
# APROBAR / RECHAZAR
# =========================
@app.route('/aprobar/<int:id>')
def aprobar(id):

    conexion = get_connection()
    cursor = conexion.cursor()

    try:
        cursor.execute("UPDATE solicitudes SET estado='aprobado' WHERE id_solicitud=%s", (id,))
        conexion.commit()
    except Exception as e:
        return f"Error: {e}"
    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for("inspector"))


@app.route('/rechazar/<int:id>')
def rechazar(id):

    conexion = get_connection()
    cursor = conexion.cursor()

    try:
        cursor.execute("UPDATE solicitudes SET estado='rechazado' WHERE id_solicitud=%s", (id,))
        conexion.commit()
    except Exception as e:
        return f"Error: {e}"
    finally:
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

    try:
        cursor.execute("""
        SELECT s.id_solicitud, e.nombre, s.motivo, s.dolor
        FROM solicitudes s
        JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
        WHERE s.estado='aprobado'
        """)
        solicitudes = cursor.fetchall()

    except Exception as e:
        return f"Error: {e}"

    finally:
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

    try:
        cursor.execute("UPDATE solicitudes SET estado='atendido' WHERE id_solicitud=%s", (id,))
        conexion.commit()
    except Exception as e:
        return f"Error: {e}"
    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for("medico"))


# =========================
# ERROR GLOBAL
# =========================
@app.errorhandler(500)
def error_500(e):
    return f"Error interno del servidor: {e}", 500


# =========================
# RUN
# =========================
if __name__ == '__main__':
    app.run(debug=True)
