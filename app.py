from flask import Flask, render_template, request, redirect, jsonify, send_file
import mysql.connector
from fpdf import FPDF
from datetime import datetime
import pytz
import os

app = Flask(__name__)

# ===== CONEXIÓN RAILWAY =====
def conectar_bd():
    return mysql.connector.connect(
        host=os.environ.get("MYSQLHOST"),
        user=os.environ.get("MYSQLUSER"),
        password=os.environ.get("MYSQLPASSWORD"),
        database=os.environ.get("MYSQLDATABASE"),
        port=int(os.environ.get("MYSQLPORT"))
    )

ecuador = pytz.timezone("America/Guayaquil")

def fecha_ecuador():
    return datetime.now(ecuador).strftime("%Y-%m-%d %H:%M:%S")


def asegurar_columnas():
    conn = conectar_bd()
    cursor = conn.cursor()

    columnas = [
        ("nombre","VARCHAR(255)"),
        ("curso","VARCHAR(100)"),
        ("observaciones","TEXT"),
        ("decision_medico","VARCHAR(100)")
    ]

    for nombre,tipo in columnas:
        try:
            cursor.execute(
                f"ALTER TABLE solicitudes ADD COLUMN {nombre} {tipo}"
            )
            conn.commit()
        except:
            pass

    conn.close()


@app.route('/')
def inicio():
    return render_template("inicio.html")


@app.route('/roles')
def roles():
    return render_template("roles.html")


@app.route('/login/<rol>', methods=["GET","POST"])
def login(rol):

    error=None

    if request.method=="POST":

        usuario=request.form["usuario"]
        password=request.form["password"]

        if(
            rol=="inspector"
            and usuario=="inspector"
            and password=="123"
        ):

            return redirect("/inspector")


        if(
            rol=="medico"
            and usuario=="medico"
            and password=="123"
        ):

            return redirect("/medico")


        error="Usuario o contraseña incorrectos"


    return render_template(
        "login.html",
        rol=rol,
        error=error
    )


@app.route('/solicitudes',methods=["GET","POST"])
def solicitudes():

    asegurar_columnas()

    if request.method=="POST":

        curso=request.form.get("curso","")
        nombre=request.form.get(
            "nombre_manual",""
        )

        motivo=request.form.get(
            "motivo",""
        )

        dolor=request.form.get(
            "dolor",""
        )

        origen=request.form.get(
            "origen",
            "profesor"
        )

        conn=conectar_bd()
        cursor=conn.cursor()

        cursor.execute("""

        INSERT INTO solicitudes

        (
        nombre,
        motivo,
        dolor,
        estado,
        fecha,
        curso,
        observaciones,
        decision_medico
        )

        VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s)

        """,

        (
        nombre,
        motivo,
        dolor,
        "Pendiente",
        fecha_ecuador(),
        curso,
        "",
        "Sin revisar"
        )
        )

        conn.commit()
        conn.close()

        if origen=="inspector":

            return redirect(
            "/inspector"
            )

        return redirect(
        "/solicitudes"
        )


    return render_template(
    "solicitudes.html"
    )


@app.route('/api/solicitudes')
def api_solicitudes():

    conn=conectar_bd()

    cursor=conn.cursor(
    dictionary=True
    )

    cursor.execute("""

    SELECT *

    FROM solicitudes

    ORDER BY
    id_solicitud DESC

    """)

    datos=cursor.fetchall()

    conn.close()

    return jsonify(datos)


@app.route('/inspector')
def inspector():

    return render_template(
    "inspector.html"
    )


@app.route('/medico')
def medico():

    return render_template(
    "medico.html"
    )


@app.route(
'/decision_medico/<int:id>/<decision>'
)

def decision_medico(
id,
decision
):

    if decision=="subir":

        texto="🟢 Puede subir"

    else:

        texto="🔴 No puede subir"


    conn=conectar_bd()

    cursor=conn.cursor(
    dictionary=True
    )


    cursor.execute("""

    SELECT
    decision_medico

    FROM solicitudes

    WHERE
    id_solicitud=%s

    """,

    (id,)
    )

    fila=cursor.fetchone()


    if fila:

        actual=fila[
        "decision_medico"
        ]

        if(
            actual
            and
            actual!="Sin revisar"
        ):

            conn.close()

            return redirect(
            "/medico"
            )


    cursor=conn.cursor()

    cursor.execute("""

    UPDATE solicitudes

    SET
    decision_medico=%s

    WHERE
    id_solicitud=%s

    """,

    (
    texto,
    id
    )
    )

    conn.commit()
    conn.close()

    return redirect(
    "/medico"
    )


@app.route('/aprobar/<int:id>')
def aprobar(id):

    conn=conectar_bd()

    cursor=conn.cursor()

    cursor.execute("""

    UPDATE solicitudes

    SET estado='Aprobado'

    WHERE
    id_solicitud=%s

    """,

    (id,)
    )

    conn.commit()
    conn.close()

    return redirect(
    "/inspector"
    )


@app.route('/rechazar/<int:id>')
def rechazar(id):

    conn=conectar_bd()

    cursor=conn.cursor()

    cursor.execute("""

    UPDATE solicitudes

    SET estado='Rechazado'

    WHERE
    id_solicitud=%s

    """,

    (id,)
    )

    conn.commit()
    conn.close()

    return redirect(
    "/inspector"
    )


@app.route('/atendido/<int:id>')
def atendido(id):

    conn=conectar_bd()

    cursor=conn.cursor()

    cursor.execute("""

    UPDATE solicitudes

    SET estado='Atendido'

    WHERE
    id_solicitud=%s

    """,

    (id,)
    )

    conn.commit()

    conn.close()

    return redirect(
    "/medico"
    )


@app.route(
'/observacion/<int:id>',
methods=["POST"]
)

def observacion(id):

    texto=request.form.get(
    "observaciones",""
    )

    conn=conectar_bd()

    cursor=conn.cursor()

    cursor.execute("""

    UPDATE solicitudes

    SET
    observaciones=%s

    WHERE
    id_solicitud=%s

    """,

    (
    texto,
    id
    )
    )

    conn.commit()

    conn.close()

    return redirect(
    "/medico"
    )


if __name__=="__main__":
    app.run(debug=True)
