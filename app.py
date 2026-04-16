from flask import Flask, render_template, request, redirect
import mysql.connector
import os

app = Flask(__name__)

# CONEXIÓN A LA BD (Railway)
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT")),
        connection_timeout=10
    )

# PÁGINA PRINCIPAL (FORMULARIO + TABLA)
@app.route("/")
def inicio():
    conexion = get_db()
    cursor = conexion.cursor(dictionary=True)

    # obtener estudiantes
    cursor.execute("SELECT id_estudiante, nombres FROM estudiantes")
    estudiantes = cursor.fetchall()

    # obtener solicitudes
    cursor.execute("SELECT id_estudiante, nivel_dolor FROM solicitudes")
    solicitudes = cursor.fetchall()

    conexion.close()

    return render_template("solicitudes.html",
                           estudiantes=estudiantes,
                           solicitudes=solicitudes)

# GUARDAR SOLICITUD
@app.route("/guardar_solicitud", methods=["POST"])
def guardar_solicitud():

    estudiante = request.form.get("estudiante")
    dolor = request.form.get("dolor")

    if not estudiante or not dolor:
        return "Faltan datos"

    conexion = get_db()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO solicitudes (id_estudiante, nivel_dolor)
        VALUES (%s, %s)
    """, (estudiante, dolor))

    conexion.commit()
    conexion.close()

    return redirect("/")

# CONFIGURACIÓN RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
