from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "clave_secreta"

# CONEXIÓN A LA BASE DE DATOS (RAILWAY)
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


# INICIO (usa registro.html como página principal)
@app.route("/")
def inicio():
    return render_template("registro.html")


# FORMULARIO (también usa registro.html)
@app.route("/formulario")
def formulario():
    return render_template("registro.html")


# REGISTRO (ejemplo básico)
@app.route("/registrar", methods=["POST"])
def registrar():
    nombre = request.form.get("nombre")
    correo = request.form.get("correo")

    conexion, cursor = get_db()

    cursor.execute("""
    INSERT INTO estudiantes (nombres, correo_institucional)
    VALUES (%s,%s)
    """,(nombre,correo))

    conexion.commit()
    conexion.close()

    return "Registro guardado"


# PANEL INSPECTOR
@app.route("/inspector")
def inspector():
    return render_template("inspector.html")


# PANEL MÉDICO
@app.route("/medico")
def medico():
    return render_template("medico.html")


# SOLICITUDES
@app.route("/solicitudes")
def solicitudes():
    return render_template("solicitudes.html")


# PUERTO PARA RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
