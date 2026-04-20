from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# FUNCIÓN PARA CONECTAR (Para evitar que la conexión se pierda)
def conectar_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="medigo_db"
    )

# =========================
# PROFESOR (SOLICITUDES)
# =========================
@app.route('/', methods=["GET","POST"])
@app.route('/solicitudes', methods=["GET","POST"])
def solicitudes():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)

    if request.method == "POST":
        estudiante = request.form["estudiante"]
        motivo = request.form["motivo"]
        # Nota: En tu foto no veo la columna 'dolor', si te da error, quítala de aquí:
        sql = "INSERT INTO solicitudes (id_estudiante, id_profesor, motivo, estado) VALUES (%s, 1, %s, 'pendiente')"
        cursor.execute(sql, (estudiante, motivo))
        conexion.commit()
        conexion.close()
        return redirect(url_for("solicitudes"))

    # OBTENER ESTUDIANTES (Columna 'nombres' según tu foto)
    cursor.execute("SELECT id_estudiante, nombres FROM estudiantes")
    estudiantes = cursor.fetchall()

    # OBTENER SOLICITUDES (Cambiado 'e.nombre' por 'e.nombres')
    cursor.execute("""
    SELECT s.id_solicitud, e.nombres as nombre, s.motivo, s.estado, s.fecha
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    ORDER BY s.id_solicitud DESC
    """)
    solicitudes_lista = cursor.fetchall()
    
    conexion.close()
    return render_template("solicitudes.html", solicitudes=solicitudes_lista, estudiantes=estudiantes)

# =========================
# INSPECTOR
# =========================
@app.route('/inspector')
def inspector():
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
    SELECT s.id_solicitud, e.nombres as nombre, s.motivo, s.estado, s.fecha
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    WHERE s.estado = 'pendiente'
    ORDER BY s.id_solicitud DESC
    """)
    solicitudes_lista = cursor.fetchall()
    conexion.close()
    return render_template("inspector.html", solicitudes=solicitudes_lista)

@app.route('/aprobar/<int:id>')
def aprobar(id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("UPDATE solicitudes SET estado='aprobado' WHERE id_solicitud=%s", (id,))
    conexion.commit()
    conexion.close()
    return redirect(url_for("inspector"))

@app.route('/rechazar/<int:id>')
def rechazar(id):
    conexion = conectar_db()
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
    conexion = conectar_db()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
    SELECT s.id_solicitud, e.nombres as nombre, s.motivo
    FROM solicitudes s
    JOIN estudiantes e ON s.id_estudiante = e.id_estudiante
    WHERE s.estado='aprobado'
    """)
    solicitudes_lista = cursor.fetchall()
    conexion.close()
    return render_template("medico.html", solicitudes=solicitudes_lista)

@app.route('/atendido/<int:id>')
def atendido(id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("UPDATE solicitudes SET estado='atendido' WHERE id_solicitud=%s", (id,))
    conexion.commit()
    conexion.close()
    return redirect(url_for("medico"))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
