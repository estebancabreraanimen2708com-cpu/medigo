from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os

app = Flask(__name__, static_folder='static')
app.config["PROPAGATE_EXCEPTIONS"] = True

# CONEXIÓN A MEDIGO_DB
def get_db():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "medigo_db"), # Nombre de tu foto
            port=int(os.getenv("DB_PORT", "3306")),
            connection_timeout=5
        )
    except Exception as e:
        print(f"Error: {e}")
        return None

# --- RUTA PROFESOR ---
@app.route('/', methods=["GET","POST"])
@app.route('/solicitudes', methods=["GET","POST"])
def solicitudes():
    db = get_db()
    if not db: return "Error de conexión a medigo_db"
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        id_est = request.form.get("estudiante")
        mot = request.form.get("motivo")
        # En tu tabla no veo columna 'dolor', si no existe, la quitamos del insert
        cursor.execute("""
            INSERT INTO solicitudes (id_estudiante, id_profesor, motivo, estado) 
            VALUES (%s, 1, %s, 'pendiente')
        """, (id_est, mot))
        db.commit()
        return redirect(url_for("solicitudes"))

    cursor.execute("SELECT id_estudiante, nombres FROM estudiantes")
    estudiantes = cursor.fetchall()
    
    cursor.execute("""
        SELECT s.*, e.nombres AS nombre 
        FROM solicitudes s 
        JOIN estudiantes e ON s.id_estudiante = e.id_estudiante 
        ORDER BY s.id_solicitud DESC
    """)
    lista = cursor.fetchall()
    db.close()
    return render_template("solicitudes.html", solicitudes=lista, estudiantes=estudiantes)

# --- RUTA INSPECTOR ---
@app.route('/inspector')
def inspector():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.*, e.nombres AS nombre 
        FROM solicitudes s 
        JOIN estudiantes e ON s.id_estudiante = e.id_estudiante 
        WHERE s.estado = 'pendiente'
    """)
    lista = cursor.fetchall()
    db.close()
    return render_template("inspector.html", solicitudes=lista)

@app.route('/aprobar/<int:id>')
def aprobar(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE solicitudes SET estado='aprobado' WHERE id_solicitud=%s", (id,))
    db.commit()
    db.close()
    return redirect(url_for("inspector"))

@app.route('/rechazar/<int:id>')
def rechazar(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE solicitudes SET estado='rechazado' WHERE id_solicitud=%s", (id,))
    db.commit()
    db.close()
    return redirect(url_for("inspector"))

# --- RUTA MÉDICO ---
@app.route('/medico')
def medico():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.*, e.nombres AS nombre 
        FROM solicitudes s 
        JOIN estudiantes e ON s.id_estudiante = e.id_estudiante 
        WHERE s.estado = 'aprobado'
    """)
    lista = cursor.fetchall()
    db.close()
    return render_template("medico.html", solicitudes=lista)

@app.route('/atendido/<int:id>')
def atendido(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE solicitudes SET estado='atendido' WHERE id_solicitud=%s", (id,))
    db.commit()
    db.close()
    return redirect(url_for("medico"))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
