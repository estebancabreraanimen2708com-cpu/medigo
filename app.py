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

# INICIO
@app.route("/")
def inicio():
    return render_template("registro.html")

# REGISTRAR (NO TOCA TU HTML)
@app.route("/registrar", methods=["POST"])
def registrar():

    nombre = request.form.get("nombre")
    correo = request.form.get("correo")

    conexion = get_db()
    cursor = conexion.cursor()

    cursor.execute(
        "INSERT INTO estudiantes (nombres, correo_institucional) VALUES (%s,%s)",
        (nombre, correo)
    )

    conexion.commit()
    conexion.close()

    return redirect("/inspector")

# MOSTRAR LISTA SIN CAMBIAR DISEÑO
@app.route("/inspector")
def inspector():

    conexion = get_db()
    cursor = conexion.cursor(dictionary=True)

    cursor.execute("SELECT * FROM estudiantes")
    estudiantes = cursor.fetchall()

    conexion.close()

    # 👇 IMPORTANTE: esto manda los datos a tu HTML
    return render_template("inspector.html", estudiantes=estudiantes)


# PUERTO
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
