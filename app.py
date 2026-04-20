from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os

app = Flask(__name__, static_folder='static')
app.config["PROPAGATE_EXCEPTIONS"] = True

# CONEXIÓN CORREGIDA PARA TU FOTO DE PHP_MYADMIN
def get_db():
    try:
        # Forzamos los datos exactos de tu XAMPP
        db = mysql.connector.connect(
            host="localhost",       # Cambia a os.getenv si vas a subirlo a internet
            user="root",            # Usuario por defecto de XAMPP
            password="",            # Contraseña por defecto (vacia)
            database="medigo_db",   # El nombre exacto de tu foto
            port=3306
        )
        return db
    except Exception as e:
        # Esto saldrá en tu consola negra cuando intentes entrar a la web
        print("***********************************")
        print(f"ERROR DE CONEXIÓN: {e}")
        print("***********************************")
        return None

# --- RUTA PROFESOR ---
@app.route('/', methods=["GET","POST"])
@app.route('/solicitudes', methods=["GET","POST"])
def solicitudes():
    db = get_db()
    if not db: 
        return "<h1>Error Fatal: No se pudo conectar a 'medigo_db'</h1><p>Revisa que XAMPP tenga MySQL encendido.</p>"
    
    cursor = db.cursor(dictionary=True)
    if request.method == "POST":
        id_est = request.form.get("estudiante")
        mot = request.form.get("motivo")
        # INSERT según tu tabla de la foto (id_profesor es 1 por defecto)
        cursor.execute("INSERT INTO solicitudes (id_estudiante, id_profesor, motivo, estado) VALUES (%s, 1, %s, 'pendiente')", (id_est, mot))
        db.commit()
        return redirect(url_for("solicitudes"))

    cursor.execute("SELECT id_estudiante, nombres FROM estudiantes")
    estudiantes = cursor.fetchall()
    
    cursor.execute("SELECT s.*, e.nombres AS nombre FROM solicitudes s JOIN estudiantes e ON s.id_estudiante = e.id_estudiante ORDER BY s.id_solicitud DESC")
    lista = cursor.fetchall()
    db.close()
    return render_template("solicitudes.html", solicitudes=lista, estudiantes=estudiantes)

# --- LAS DEMÁS RUTAS (Inspector y Médico) SIGUEN IGUAL ---
# (Copia las rutas de Inspector y Médico que te pasé en el mensaje anterior)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
