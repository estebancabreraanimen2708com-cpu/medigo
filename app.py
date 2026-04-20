from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os

app = Flask(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = True

# =========================
# CONEXIÓN CORREGIDA
# =========================
def get_db():
    try:
        # IMPORTANTE: En producción, estas variables NO deben ser 'localhost'
        # Si usas Render/Railway, asegúrate de que DB_HOST sea la URL que te dan ellos.
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "tu_base_de_datos"),
            port=int(os.getenv("DB_PORT", "3306")),
            connection_timeout=5
        )
    except mysql.connector.Error as err:
        print(f"Error de conexión: {err}")
        return None

# =========================
# PROFESOR / SOLICITUDES
# =========================
@app.route('/', methods=["GET","POST"])
@app.route('/solicitudes', methods=["GET","POST"])
def solicitudes():
    conexion = get_db()
    if not conexion:
        return "ERROR: No se pudo conectar a la base de datos. Verifica si el servidor MySQL está encendido."

    try:
        cursor = conexion.cursor(dictionary=True)

        if request.method == "POST":
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

        cursor.execute("SELECT id_estudiante, nombres FROM estudiantes")
        estudiantes = cursor.fetchall()

        cursor.execute("""
            SELECT s.id_solicitud, e.nombres AS nombre, s.motivo, s.estado, s.fecha, s.dolor
            FROM solicitudes s
            JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
            ORDER BY s.id_solicitud DESC
        """)
        lista_solicitudes = cursor.fetchall()

        cursor.close()
        conexion.close()
        return render_template("solicitudes.html", solicitudes=lista_solicitudes, estudiantes=estudiantes)

    except Exception as e:
        if conexion: conexion.close()
        return f"ERROR EN /solicitudes: {str(e)}"

# =========================
# INSPECTOR
# =========================
@app.route('/inspector')
def inspector():
    conexion = get_db()
    if not conexion: return "Error de DB"
    
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.id_solicitud, e.nombres AS nombre, s.motivo, s.estado, s.fecha, s.dolor
            FROM solicitudes s
            JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
        """)
        solicitudes = cursor.fetchall()
        cursor.close()
        conexion.close()
        return render_template("inspector.html", solicitudes=solicitudes)
    except Exception as e:
        return f"ERROR: {str(e)}"

# =========================
# APROBAR / RECHAZAR
# =========================
@app.route('/aprobar/<int:id>')
def aprobar(id):
    conexion = get_db()
    if conexion:
        cursor = conexion.cursor()
        cursor.execute("UPDATE solicitudes SET estado='aprobado' WHERE id_solicitud=%s",(id,))
        conexion.commit()
        conexion.close()
    return redirect(url_for("inspector"))

@app.route('/rechazar/<int:id>')
def rechazar(id):
    conexion = get_db()
    if conexion:
        cursor = conexion.cursor()
        cursor.execute("UPDATE solicitudes SET estado='rechazado' WHERE id_solicitud=%s",(id,))
        conexion.commit()
        conexion.close()
    return redirect(url_for("inspector"))

# =========================
# MÉDICO
# =========================
@app.route('/medico')
def medico():
    conexion = get_db()
    if not conexion: return "Error de DB"
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.id_solicitud, e.nombres AS nombre, s.motivo, s.dolor
            FROM solicitudes s
            JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
            WHERE s.estado='aprobado'
        """)
        solicitudes = cursor.fetchall()
        conexion.close()
        return render_template("medico.html", solicitudes=solicitudes)
    except Exception as e:
        return f"ERROR: {str(e)}"

@app.route('/atendido/<int:id>')
def atendido(id):
    conexion = get_db()
    if conexion:
        cursor = conexion.cursor()
        cursor.execute("UPDATE solicitudes SET estado='atendido' WHERE id_solicitud=%s",(id,))
        conexion.commit()
        conexion.close()
    return redirect(url_for("medico"))

# =========================
# RUN
# =========================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
