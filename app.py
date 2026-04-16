from flask import Flask, render_template, request, redirect
import mysql.connector
import os

app = Flask(__name__)

# CONEXIÓN A LA BASE DE DATOS
def get_db():
    conexion = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT")),
        connection_timeout=10
    )
    return conexion, conexion.cursor(dictionary=True)

# PÁGINA PRINCIPAL (FORMULARIO)
@app.route("/")
def inicio():
    return render_template("registro.html")

# REGISTRAR ESTUDIANTE
@app.route("/registrar", methods=["POST"])
def registrar():

    nombre = request.form.get("nombre")
    correo = request.form.get("correo")

    conexion, cursor = get_db()

    cursor.execute("""
        INSERT INTO estudiantes (nombres, correo_institucional)
        VALUES (%s, %s)
    """, (nombre, correo))

    conexion.commit()
    conexion.close()

    return redirect("/inspector")

# MOSTRAR LISTA DE ESTUDIANTES
@app.route("/inspector")
def inspector():

    conexion, cursor = get_db()

    cursor.execute("SELECT * FROM estudiantes")
    estudiantes = cursor.fetchall()

    conexion.close()

    return render_template("inspector.html", estudiantes=estudiantes)

# CONFIGURACIÓN PARA RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
