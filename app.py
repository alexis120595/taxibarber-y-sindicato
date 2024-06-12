from flask import Flask
from flask import render_template, redirect, request, Response, session, url_for, send_file, jsonify
from flask_mysqldb import MySQL, MySQLdb
import qrcode
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime
import re
import unicodedata


app = Flask(__name__, template_folder='template')

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'alexis'
app.config['MYSQL_DB'] = 'login'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

#esta es la ruta de la pagina principal
@app.route('/')
def home():
    return render_template('index.html')

#esta ruta renderiza el formulario de registro de los usuarios
@app.route('/register')
def register():
    return render_template('register.html')

#esta ruta renderiza el formulario del voucher 
@app.route('/voucher', methods=['GET'])
def voucher():
    return render_template('voucher.html')

@app.route('/register_family')
def register_family_form():
    return render_template('register_family.html')

#esta es la ruta del inicio de sesion de los usuarios
@app.route('/acceso-login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['txtEmail']
        password = request.form['txtPassword']

        try:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute('SELECT * FROM users WHERE email = %s', (email,))
            user = cur.fetchone()

            if user is None:
                return render_template('index.html', error="User not registered.")
            
            cur.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password,))
            account = cur.fetchone()
        except Exception as e:
            return render_template('index.html', error="Database error: " + str(e))
        
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            return render_template('voucher.html')
        else:
            return render_template('index.html', error="Invalid password.")
    else:
        # Si el método es GET, simplemente renderizamos el formulario de inicio de sesión.
        return render_template('index.html')
    
#esta ruta crea al usuario una vez completada la informacion que se pide en el formulario 
@app.route('/register-user', methods=['POST'])
def register_user():

    try:
        print(request.form)
        error = None
        if request.method == 'POST':
            name = request.form['txtFullName']
            email = request.form['txtEmail']
            password = request.form['txtPassword']
            confirm_password = request.form['txtConfirmPassword']
            empresa = request.form['txtEmpresa']
            dni = request.form['txtDni']
            celular = request.form['txtCelular']
            familia = request.form['txtFamilia']

            normalized_name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('utf-8')

            if not name:
                 error = "Error: Name is required"
            elif not re.match("^[A-Za-z ]*$", normalized_name):
                error = "Error: Name can only contain letters"
            elif not empresa:
                    error = "Error: empresa is required"
            elif password != confirm_password:
             error = "Error: Passwords do not match"
            elif not dni.isdigit() or len(dni) < 7:
                error = "Error: DNI must be a number and at least 7 digits long"
            elif not celular.isdigit() or len(celular) < 9:
                error = "Error: Celular must be a number and at least 9 digits long"

            if error is None:
              
                cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cur.execute('INSERT INTO users (name, email, password, empresa, dni, celular, familia) VALUES (%s, %s, %s, %s, %s, %s, %s)', (name, email, password, empresa, dni, celular, familia))
                mysql.connection.commit()

               
                return render_template('index.html')
        return render_template('register.html', error=error)
    except Exception as e:
        # Aquí puedes manejar el error como quieras. Por ejemplo, puedes imprimir el error y devolver un mensaje de error al usuario.
        print(e)
        return "An error occurred while processing your request. Please try again later.", 500
    
@app.route('/register_family', methods=['POST'])
def register_family():
    try:
        print(request.form)
        # Obtén los datos del formulario
        nombres = request.form.getlist('nombreHijo[]')
        dnis = request.form.getlist('dniHijo[]')
        relationships = request.form.getlist('relationship[]')
        dni_padre = request.form.getlist('dniPadre[]')
       

        # Crea un cursor
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        for nombre, dni, relationship, user_dni in zip(nombres, dnis, relationships, dni_padre):
        # Ejecuta la consulta SQL para insertar los datos en la base de datos
         cur.execute('INSERT INTO family (nombre, dni, relationship, user_dni) VALUES (%s, %s, %s, %s)', (nombre, dni, relationship, user_dni))

        # Confirma la transacción
        mysql.connection.commit()

        # Redirige al usuario a la página de inicio
        return render_template('index.html')
    except Exception as e:
        # Imprime el error y devuelve un mensaje de error al usuario
        print(e)
        return "An error occurred while processing your request. Please try again later.", 500   
    
#esta ruta crea el voucher una vez completada la informacion que se pide en el formulario 
#tambien genera el qr para que pueda ser escaneado y descargado por el usuario
@app.route('/voucher', methods=[ 'POST'])
def boucher():
    error = None
    if request.method == 'POST':
        name1 = request.form['txtName1']
        dni = request.form['txtDNI']

    if not name1:
        error = "Error: Name is required"
    elif not re.match("^[A-Za-zÑñÁÉÍÓÚáéíóú ]*$", name1):
        error = "Error: Name can only contain letters"
    elif not dni.isdigit() or len(dni) < 7:
        error = "Error: DNI must be a number and at least 7 digits long"

    if error:
        return render_template('voucher.html', error=error)

    try:
        normalized_name = unicodedata.normalize('NFKD', name1).encode('ASCII', 'ignore').decode('utf-8')
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        fecha = datetime.now()
        cur.execute('INSERT INTO boucher (name1, dni, fecha) VALUES (%s, %s, %s)', (normalized_name, dni, fecha))
        mysql.connection.commit()

        # Obtener el estado del voucher
        cur.execute('SELECT estado FROM boucher WHERE name1 = %s AND dni = %s', (normalized_name, dni))
        result = cur.fetchone()
        estado = result['estado']

        # Generar el código QR
        if estado == 'active':   
            data = f"{normalized_name} {dni}"  # Datos para el código QR
        else:
            data = 'qr inactivo, genere uno nuevo'
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill='black', back_color='white')
        img_filename = f'static/qr/{normalized_name}_{dni}.png'
        img.save(img_filename)

        return redirect(url_for('show_qr', filename=f'{normalized_name}_{dni}.png'))
    except Exception as e:
        error = str(e)
        return render_template('voucher.html', error=error)
   

#esta ruta muestra el qr generado una vez es enviado el voucher
# y la informacion es guardada en la base de datos de forma correta 
@app.route('/show_qr/<filename>', methods=['GET'])
def show_qr(filename):
    name1, dni = filename.split('.')[0].split('_')

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Obtener el estado del voucher
    cur.execute('SELECT estado FROM boucher WHERE name1 = %s AND dni = %s', (name1, dni))
    result = cur.fetchone()
    estado = result['estado']

    # Generar el código QR
    if estado == 'active':
        data = f"{name1} {dni}"  # Datos para el código QR
    else:
        data = 'qr inactivo, genere uno nuevo'

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    img_filename = f'static/qr/{name1}_{dni}.png'
    img.save(img_filename)

    return render_template('show_qr.html', filename=f'{name1}_{dni}.png')

    # aca finalizan todas la rutas del lado del usuario 
    # ahora comienzan la rutas de los administradores 

# esta ruta renderiza la plantilla del inicio de sesion de los administradores 
@app.route('/acceso-admin', methods=['GET', 'POST'])
def administrador():
    if request.method == 'POST':
        username = request.form['txtUserName']
        password = request.form['txtPassword']
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM users_admin WHERE username = %s AND password = %s', (username, password,))
        account = cur.fetchone()

        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            return redirect(url_for('users_admin'))
        else:
            return render_template('index_admin.html', error="Invalid username or password.")
    else:
        return render_template('index_admin.html')
    
# esta ruta muestra todos los usuarios que se han registrado en la base de datos
@app.route('/users-admin', methods=['GET'])
def users_admin():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM users')
    data = cur.fetchall()
    
    return render_template('users_admin.html', users=data)

# esta ruta nos perite eliminar usuarios de la base de datos
@app.route('/users-admin/delete/<int:id>', methods=['POST'])
def delete_user(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('DELETE FROM users WHERE id = %s', (id,))
    mysql.connection.commit()
    return redirect(url_for('users_admin'))

@app.route('/users-admin', methods=['POST'])
def update_estado():
    id = request.form.get('id')
    estado = request.form.get('estado')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('UPDATE users SET estado = %s WHERE id = %s', (estado, id))
    mysql.connection.commit()
    return {'message': 'usuario activado'}

# esta ruta nos permite editar los usuarios de la base de datos
@app.route('/users-admin/<int:id>', methods=['PUT'])
def update_user(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Assuming you're receiving JSON data in the form { "name": "new name", "branch": "new branch" }
    data = request.get_json()
    new_name = data['name']
    new_branch = data['branch']

    cur.execute('UPDATE users SET name = %s, branch = %s WHERE id = %s', (new_name, new_branch, id))
    mysql.connection.commit()
    return "User updated"

#esta ruta nos permite buscar por nombre a los usuarios de la base de datos
@app.route('/search', methods=['GET', 'POST'])
def search():
    data = []
    if request.method == 'POST':
        search = request.form['username']
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM users WHERE name = %s', [search])
        data = cur.fetchall()
        cur.close()

    return render_template('search_results.html', users=data)

#esta ruta nos permite ver el listado de los voucher que se han generado
@app.route('/listado-voucher', methods=['GET'])
def vouchers():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM boucher')
    data = cur.fetchall()
    
    return render_template('listado_voucher.html', boucher=data)

#esta ruta nos permite actualizar el estado de los voucher
@app.route('/listado-voucher', methods=['POST'])
def update_voucher():
    id = request.form.get('id')
    estado = request.form.get('estado')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('UPDATE boucher SET estado = %s WHERE id = %s', (estado, id))
    mysql.connection.commit()
    return {'message': 'Voucher actualizado correctamente'}

# esta ruta nos renderiza la plantilla de los graficos
@app.route('/graficos')
def graph():
    return render_template('graficos.html')

# esta ruta nos permite obtener los datos para el grafico
#en este caso se obtiene la cantidad de voucher generados por dia
@app.route('/data_for_graph')
def data_for_graph():
    # Create a cursor
    cur = mysql.connection.cursor()
    
    # Modify the SQL query to group by both date and status
    cur.execute("""
        SELECT DATE_FORMAT(fecha, '%Y-%m-%d') as fecha_formateada, estado, COUNT(*) as count 
        FROM boucher 
        GROUP BY fecha_formateada, estado
    """)
    
    rows = cur.fetchall()

    # Separate the results into lists for each status
    x_data_active = [row['fecha_formateada'] for row in rows if row['estado'] == 'active']
    y_data_active = [row['count'] for row in rows if row['estado'] == 'active']
    x_data_inactive = [row['fecha_formateada'] for row in rows if row['estado'] == 'inactive']
    y_data_inactive = [row['count'] for row in rows if row['estado'] == 'inactive']

    # Create the graph with separate traces for each status
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_data_active, y=y_data_active, name='active'))
    fig.add_trace(go.Bar(x=x_data_inactive, y=y_data_inactive, name='inactive'))

    # Convert the graph to JSON
    graph_json = pio.to_json(fig)

    # Send the graph as JSON
    return jsonify(graph_json=graph_json)
  
if __name__ == '__main__':
    app.secret_key = "alexis"
    app.run(debug=True, port=5000, host='0.0.0.0', threaded=True)