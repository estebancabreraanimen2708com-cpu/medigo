from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/roles')
def roles():
    return render_template('roles.html')

@app.route('/solicitudes')
def solicitudes():
    return render_template('solicitudes.html')

@app.route('/inspector')
def inspector():
    return render_template('inspector.html')

@app.route('/medico')
def medico():
    return render_template('medico.html')

@app.route('/historial')
def historial():
    return render_template('historial.html')

if __name__ == '__main__':
    app.run(debug=True)
