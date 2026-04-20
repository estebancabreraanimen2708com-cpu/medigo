from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os

app = Flask(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = True

# =========================
# CONEXIÓN SEGURA CORREGIDA
# =========================
def get_db():
    # El error ocurría aquí porque os.getenv devolvía None y int(None) falla.
    # Usamos valores por defecto por si las variables no están configuradas.
    try:
        db_port = os.getenv("DB_PORT", "3306")
        return mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(db_port),
            connection_timeout=10
        )
    except Exception as e:
        print(f"Error crítico de conexión: {e}")
        raise e

# =========================
# PROFESOR / SOLICITUDES
# =========================
@app.route('/', methods=["GET","POST"])
@app.route('/solicitudes', methods=["GET","POST"])
def solicitudes():
    try:
        conexion = get_db()
        cursor = conexion.cursor(dictionary=True)

        if request.method == "POST":
            # Validamos que los datos no lleguen vacíos
            estudiante = request.form.get("estudiante")
            motivo = request.form.get("motivo")
            dolor = request.form.get("dolor")

            cursor.execute("""
                INSERT INTO solicitudes (id_estudiante, id_profesor, motivo, dolor, estado)
                VALUES (%s, 1, %s, %s, 'pendiente')
            """, (estudiante, motivo, dolor))

            conexion.commit()
            cursor.close()
            conexion.close()
            return redirect(url_for("solicitudes"))

        # Obtener lista de estudiantes para el formulario
        cursor.execute("SELECT id_estudiante, nombres FROM estudiantes")
        estudiantes = cursor.fetchall()

        # Obtener historial de solicitudes
        cursor.execute("""
            SELECT s.id_solicitud,
                   e.nombres AS nombre,
                   s.motivo,
                   s.estado,
                   s.fecha,
                   s.dolor
            FROM solicitudes s
            JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
            ORDER BY s.id_solicitud DESC
        """)
        lista_solicitudes = cursor.fetchall()

        cursor.close()
        conexion.close()

        return render_template("solicitudes.html",
                               solicitudes=lista_solicitudes,
                               estudiantes=estudiantes)

    except Exception as e:
        return f"ERROR EN /solicitudes: {str(e)}"

# =========================
# INSPECTOR
# =========================
@app.route('/inspector')
def inspector():
    try:
        conexion = get_db()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT s.id_solicitud,
                   e.nombres AS nombre,
                   s.motivo,
                   s.estado,
                   s.fecha,
                   s.dolor
            FROM solicitudes s
            JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
            ORDER BY s.fecha DESC
        """)

        lista_solicitudes = cursor.fetchall()
        cursor.close()
        conexion.close()

        return render_template("inspector.html", solicitudes=lista_solicitudes)

    except Exception as e:
        return f"ERROR EN /inspector: {str(e)}"

# =========================
# ACCIONES (APROBAR/RECHAZAR)
# =========================
@app.route('/aprobar/<int:id>')
def aprobar(id):
    try:
        conexion = get_db()
        cursor = conexion.cursor()
        cursor.execute("UPDATE solicitudes SET estado='aprobado' WHERE id_solicitud=%s", (id,))
        conexion.commit()
        conexion.close()
        return redirect(url_for("inspector"))
    except Exception as e:
        return f"ERROR EN aprobar: {str(e)}"

@app.route('/rechazar/<int:id>')
def rechazar(id):
    try:
        conexion = get_db()
        cursor = conexion.cursor()
        cursor.execute("UPDATE solicitudes SET estado='rechazado' WHERE id_solicitud=%s", (id,))
        conexion.commit()
        conexion.close()
        return redirect(url_for("inspector"))
    except Exception as e:
        return f"ERROR EN rechazar: {str(e)}"

# =========================
# MÉDICO
# =========================
@app.route('/medico')
def medico():
    try:
        conexion = get_db()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.id_solicitud,
                   e.nombres AS nombre,
                   s.motivo,
                   s.dolor
            FROM solicitudes s
            JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
            WHERE s.estado='aprobado'
        """)
        lista_solicitudes = cursor.fetchall()
        conexion.close()
        return render_template("medico.html", solicitudes=lista_solicitudes)
    except Exception as e:
        return f"ERROR EN /medico: {str(e)}"

@app.route('/atendido/<int:id>')
def atendido(id):
    try:
        conexion = get_db()
        cursor = conexion.cursor()
        cursor.execute("UPDATE solicitudes SET estado='atendido' WHERE id_solicitud=%s", (id,))
        conexion.commit()
        conexion.close()
        return redirect(url_for("medico"))
    except Exception as e:
        return f"ERROR EN atendido: {str(e)}"

# =========================
# CONFIGURACIÓN DE ARRANQUE
# =========================
if __name__ == '__main__':
    # Obtenemos el puerto de la variable de entorno, si no existe usamos 5000
    port_env = os.environ.get("PORT", 5000)
    app.run(host="0.0.0.0", port=int(port_env))
