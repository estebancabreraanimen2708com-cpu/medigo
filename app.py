from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# =========================================
# 🔥 INICIO
# =========================================

@app.route('/')
def inicio():
    return render_template('inicio.html')

# =========================================
# 🔥 ROLES
# =========================================

@app.route('/roles')
def roles():
    return render_template('roles.html')

# =========================================
# 🔥 LOGIN
# =========================================

@app.route('/login/<rol>', methods=['GET', 'POST'])
def login(rol):

    if request.method == 'POST':

        usuario = request.form['usuario']
        password = request.form['password']

        # LOGIN INSPECTOR
        if rol == "inspector":

            if usuario == "inspector" and password == "123":

                return redirect('/inspector')

        # LOGIN MEDICO
        if rol == "medico":

            if usuario == "medico" and password == "123":

                return redirect('/medico')

    return render_template('login.html', rol=rol)

# =========================================
# 🔥 PROFESOR
# =========================================

@app.route('/solicitudes')
def solicitudes():
    return render_template('solicitudes.html')

# =========================================
# 🔥 INSPECTOR
# =========================================

@app.route('/inspector')
def inspector():
    return render_template('inspector.html')

# =========================================
# 🔥 MEDICO
# =========================================

@app.route('/medico')
def medico():
    return render_template('medico.html')

# =========================================
# 🔥 HISTORIAL
# =========================================

@app.route('/historial')
def historial():
    return render_template('historial.html')

# =========================================
# 🔥 RUN
# =========================================

if __name__ == '__main__':
    app.run(debug=True)
