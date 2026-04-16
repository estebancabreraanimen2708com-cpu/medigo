from flask import Flask, render_template, request, redirect
import mysql.connector
import os

app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT"))
    )

# FORMULARIO + TABLA
@app.route("/")
def inicio():

    conexion = get_db()
    cursor = conexion.cursor(dictionary=True)

    # estudiantes para el dropdown
    cursor.execute("SELECT * FROM estudiantes")
    estudiantes = cursor.fetchall()

    # solicitudes para la tabla
    cursor.execute("SELECT * FROM solicitudes")
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

    conexion = get_db()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO solicitudes (id_estudiante, nivel_dolor)
        VALUES (%s, %s)
    """, (estudiante, dolor))

    conexion.commit()
    conexion.close()

    return redirect("/")


# PUERTO
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
