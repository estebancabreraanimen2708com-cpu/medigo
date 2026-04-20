from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os

app = Flask(__name__)

# Función para conectar: esto evita el "Internal Server Error"
def get_conexion():
    return mysql.connector.connect(
        host="localhost", # Si subes a Render, aquí va la variable de entorno
        user="root",
        password="",
        database="medigo_db"
    )

# =========================
# PROFESOR
# =========================
@app.route('/', methods=["GET","POST"])
@app.route('/solicitudes', methods=["GET","POST"])
def solicitudes():
    try:
        conexion = get_conexion()
        cursor = conexion.cursor(dictionary=True)

        if request.method == "POST":
            estudiante = request.form["estudiante"]
            motivo = request.form["motivo"]
            # En tu foto de MySQL no hay columna 'dolor', la quitamos para que no falle
            sql = "INSERT INTO solicitudes (id_estudiante, id_profesor, motivo, estado) VALUES (%s, 1, %s, 'pendiente')"
            cursor.execute(sql, (estudiante, motivo))
            conexion.commit()
            return redirect(url_for("solicitudes"))

        # OBTENER ESTUDIANTES
        cursor.execute("SELECT id_estudiante, nombres FROM estudiantes")
        estudiantes = cursor.fetchall()

        # OBTENER SOLICITUDES (Cambiado 'e.nombre' por 'e.nombres' según tu foto)
        cursor.execute("""
            SELECT s.id_solicitud, e.nombres as nombre, s.motivo, s.estado, s.fecha
            FROM solicitudes s
            JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
            ORDER BY s.id_solicitud DESC
        """)
        solicitudes_lista = cursor.fetchall()
        
        return render_template("solicitudes.html", solicitudes=solicitudes_lista, estudiantes=estudiantes)
    
    except Exception as e:
        return f"Error detallado: {e}"
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            cursor.close()
            conexion.close()

# =========================
# INSPECTOR
# =========================
@app.route('/inspector')
def inspector():
    try:
        conexion = get_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.id_solicitud, e.nombres as nombre, s.motivo, s.estado, s.fecha
            FROM solicitudes s
            JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
            WHERE s.estado = 'pendiente'
        """)
        solicitudes_lista = cursor.fetchall()
        return render_template("inspector.html", solicitudes=solicitudes_lista)
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

@app.route('/aprobar/<int:id>')
def aprobar(id):
    conexion = get_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE solicitudes SET estado='aprobado' WHERE id_solicitud=%s", (id,))
    conexion.commit()
    conexion.close()
    return redirect(url_for("inspector"))

@app.route('/rechazar/<int:id>')
def rechazar(id):
    conexion = get_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE solicitudes SET estado='rechazado' WHERE id_solicitud=%s", (id,))
    conexion.commit()
    conexion.close()
    return redirect(url_for("inspector"))

# =========================
# MÉDICO
# =========================
@app.route('/medico')
def medico():
    try:
        conexion = get_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT s.id_solicitud, e.nombres as nombre, s.motivo
            FROM solicitudes s
            JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
            WHERE s.estado='aprobado'
        """)
        solicitudes_lista = cursor.fetchall()
        return render_template("medico.html", solicitudes=solicitudes_lista)
    finally:
        if 'conexion' in locals() and conexion.is_connected():
            conexion.close()

@app.route('/atendido/<int:id>')
def atendido(id):
    conexion = get_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE solicitudes SET estado='atendido' WHERE id_solicitud=%s", (id,))
    conexion.commit()
    conexion.close()
    return redirect(url_for("medico"))

if __name__ == '__main__':
    app.run(debug=True)
