from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os

app = Flask(__name__, static_folder='static')
app.config["PROPAGATE_EXCEPTIONS"] = True

# CONEXIÓN A LA BASE DE DATOS CORREGIDA
def get_db():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "medigo_db"), # <-- CAMBIADO AQUÍ
            port=int(os.getenv("DB_PORT", "3306")),
            connection_timeout=10
        )
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

# --- PROFESOR ---
@app.route('/', methods=["GET","POST"])
@app.route('/solicitudes', methods=["GET","POST"])
def solicitudes():
    conexion = get_db()
    if not conexion: return "Error: No se pudo conectar a medigo_db. Verifica XAMPP."
    
    try:
        cursor = conexion.cursor(dictionary=True)
        if request.method == "POST":
            estudiante = request.form.get("estudiante")
            motivo = request.form.get("motivo")
            dolor = request.form.get("dolor")
            cursor.execute("INSERT INTO solicitudes (id_estudiante, id_profesor, motivo, dolor, estado) VALUES (%s, 1, %s, %s, 'pendiente')", (estudiante, motivo, dolor))
            conexion.commit()
            return redirect(url_for("solicitudes"))

        cursor.execute("SELECT id_estudiante, nombres FROM estudiantes")
        estudiantes = cursor.fetchall()
        cursor.execute("SELECT s.*, e.nombres AS nombre FROM solicitudes s JOIN estudiantes e ON s.id_estudiante = e.id_estudiante ORDER BY s.id_solicitud DESC")
        lista = cursor.fetchall()
        return render_template("solicitudes.html", solicitudes=lista, estudiantes=estudiantes)
    finally:
        conexion.close()

# --- INSPECTOR ---
@app.route('/inspector')
def inspector():
    conexion = get_db()
    if not conexion: return "Error de DB"
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT s.*, e.nombres AS nombre FROM solicitudes s JOIN estudiantes e ON s.id_estudiante = e.id_estudiante ORDER BY s.fecha DESC")
        lista = cursor.fetchall()
        return render_template("inspector.html", solicitudes=lista)
    finally:
        conexion.close()

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

# --- MÉDICO ---
@app.route('/medico')
def medico():
    conexion = get_db()
    if not conexion: return "Error de DB"
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT s.*, e.nombres AS nombre FROM solicitudes s JOIN estudiantes e ON s.id_estudiante = e.id_estudiante WHERE s.estado='aprobado'")
        lista = cursor.fetchall()
        return render_template("medico.html", solicitudes=lista)
    finally:
        conexion.close()

@app.route('/atendido/<int:id>')
def atendido(id):
    conexion = get_db()
    if conexion:
        cursor = conexion.cursor()
        cursor.execute("UPDATE solicitudes SET estado='atendido' WHERE id_solicitud=%s",(id,))
        conexion.commit()
        conexion.close()
    return redirect(url_for("medico"))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
