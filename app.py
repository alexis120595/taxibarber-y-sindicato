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

@app.route('/estadisticas-empresas')
def estadisticas_empresas():
    return render_template('estadisticas_por_empresas.html')    

@app.route('/detalle-voucher')
def detalle_voucher():
    return render_template('detalle_voucher.html')

#esta es la ruta del inicio de sesion de los usuarios
@app.route('/acceso-login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['txtEmail']
        password = request.form['txtPassword']

        try:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            # Actualizar la consulta para incluir el estado del usuario
            cur.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password,))
            account = cur.fetchone()

            if account is None:
                return render_template('index.html', mensaje="User not registered or invalid password.")

            # Verificar si el estado del usuario es 'inactive'
            if account['estado'] == 'inactive':
                return render_template('index.html', mensaje="This account is inactive.")
            
        except Exception as e:
            return render_template('index.html', mensaje="Database error: " + str(e))
        
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            return render_template('voucher.html')
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
           # url_base = 'https://87f7-45-189-217-93.ngrok-free.app'
            #ruta = '/buscador-dni'  
            #data = f"{url_base}{ruta}"  # Datos para el código QR
                data = f"{name1}_{dni}"
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
        url_base = 'https://87f7-45-189-217-93.ngrok-free.app'
        ruta = '/buscador-dni'
        data = f"{url_base}{ruta}"   # Datos para el código QR
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

#esta ruta nos permite buscar por dni a los voucher de la base de datos
@app.route('/search-voucher', methods=['GET', 'POST'])
def search_voucher():
    data = []
    if request.method == 'POST':
        search_dni = request.form.get('dni', None)
        if search_dni:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute('SELECT * FROM boucher WHERE dni = %s', [search_dni])
            data = cur.fetchall()
            print(data)
            cur.close()

        else:    
              return {'error': 'El campo DNI es requerido'}, 400
        
    return render_template('detalle_voucher.html', boucher=data)

#esta ruta nos va a renderizar la plantilla del buscador de dni desde el qr 
@app.route('/buscador-dni', methods=['GET', 'POST'])
def buscador_dni():
    if request.method == 'POST':
        dni = request.form.get('dni', None)
        if dni:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cur.execute('SELECT * FROM boucher WHERE dni = %s', [dni])
            data = cur.fetchone()
            cur.close()
           
    return render_template('buscador_dni.html')

#esta ruta nos permite actualizar el estado de los voucher
@app.route('/listado-voucher', methods=['POST'])
def update_voucher():
    id = request.form.get('id')
    estado = request.form.get('estado')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('UPDATE boucher SET estado = %s WHERE id = %s', (estado, id))
    mysql.connection.commit()
    return {'message': 'Voucher actualizado correctamente'}



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
            return render_template('index_admin.html', mensaje="Invalid username or password.")
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

# esta ruta nos permite actualizar el estado de los usuarios de la base de datos
@app.route('/users-admin', methods=['POST'])
def update_estado():
    id = request.form.get('id')
    estado = request.form.get('estado')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('UPDATE users SET estado = %s WHERE id = %s', (estado, id))
    mysql.connection.commit()
    
    if estado == 'active':
        message = 'Usuario activado correctamente'
    elif estado == 'inactive':
        message = 'Usuario desactivado correctamente'
    return {'message': message}

# esta ruta nos permite editar los usuarios de la base de datos, ests ruta no esta implementada en el front
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

#esta ruta nos permite obtener los datos de las empresas para el grafico
@app.route('/companies')
def companies():
    # Create a cursor
    cur = mysql.connection.cursor()
    
    # Execute a SQL query to count users by company
    cur.execute("""
        SELECT empresa, COUNT(*) as user_count 
        FROM users 
        GROUP BY empresa 
        ORDER BY user_count DESC
    """)
    
    rows = cur.fetchall()

    # Prepare the data for the graph
    empresas = [row['empresa'] for row in rows]
    user_counts = [row['user_count'] for row in rows]

    # Create the graph
    fig = go.Figure(data=[go.Bar(x=empresas, y=user_counts)])

    # Convert the graph to JSON
    graph_json = pio.to_json(fig)

    # Send the graph as JSON
    return jsonify(graph_json=graph_json)

#esta ruta nos renderiza la plantilla para el registro de los barberos
@app.route('/register-barbero')
def register_barbero():
    return render_template('register_barbero.html') 

#esta ruta nos permite registrar a los barberos en la base de datos
@app.route('/register-barbero', methods=['POST'])
def register_barbero_data():
    name = request.form['txtBarberoName']
    password = request.form['txtPassword']

    #if not re.match("^[A-Za-z]+$", name):
        # Si el nombre no es válido, retorna a la plantilla con un mensaje de error
        #return render_template('register_barbero.html', mensaje="El nombre solo debe contener letras.")
    try:
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO barbero (name, password) VALUES (%s, %s)", (name, password))
        mysql.connection.commit()
        cur.close()
        return render_template('register_barbero.html', mensaje="Datos ingresados correctamente.")
    except Exception as e:
        print("Error al insertar en la base de datos:", e)
        return render_template('register_barbero.html', mensaje="Error al ingresar los datos: " + str(e))
    

#esta ruta nos renderiza la plantilla para  el inicio de sesion de los barberos
@app.route('/acceso-barbero')
def barbero():
    return render_template('login_barbero.html')

#esta ruta nos renderiza la plantilla del inicio del menu principal de los barberos
@app.route('/inicio-barbero')
def inicio_barbero():
    return render_template('inicio_barbero.html')

#esta ruta nos permite acceder con el nombre y la contraseña a la pagina principal de los barberos
@app.route('/acceso-barbero', methods=['GET', 'POST'])
def login_barbero():
    if request.method == 'POST':
        name = request.form.get('txtBarberoName')
        password = request.form.get('txtPassword')
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM barbero WHERE name = %s AND password = %s', (name, password,))
        account = cur.fetchone()

        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            return redirect(url_for('inicio_barbero'))
        else:
            return render_template('login_barbero.html', mensaje="Invalid username or password.")
    else:
        return render_template('login_barbero.html')

#esta ruta nos renderiza la plantilla para el registro de los cortes de los barberos    
@app.route('/corte-barberia')
def corte_barbero():
    return render_template('corte_barberia.html')

#esta ruta nos permite registrar los cortes de los barberos en la base de datos
@app.route('/corte-barberia', methods=['POST'])
def ingresar_nombres():
    cliente = request.form['txtCliente']
    barbero = request.form['txtBarbero']
    fecha_actual = datetime.now().strftime('%Y-%m-%d')  # Obtiene la fecha actual en formato YYYY-MM-DD
    print("Cliente:", cliente)
    print("Barbero:", barbero)
    print("Fecha:", fecha_actual)
    
    patron = re.compile('^[A-Za-z\s]+$')

    if not patron.match(cliente) or not patron.match(barbero):
        # Si la validación falla, retorna al formulario con un mensaje de error
        return render_template('corte_barberia.html', mensaje="Error: Los campos solo deben contener letras y espacios.")  # Imprime la fecha actual para verificar
    try:
        cur = mysql.connection.cursor()
        # Asegúrate de ajustar tu consulta SQL para incluir la columna de fecha
        cur.execute("INSERT INTO corte (cliente, barbero, fecha) VALUES (%s, %s, %s)", (cliente, barbero, fecha_actual))
        mysql.connection.commit()
        cur.close()
        return render_template('corte_barberia.html', mensaje="Datos ingresados correctamente.")
    except Exception as e:
        print("Error al insertar en la base de datos:", e)
        return render_template('corte_barberia.html', mensaje="Error al ingresar los datos: " + str(e))
  

#esta ruta nos renderiza la plantilla para el registro de los voucher de los barberos
@app.route('/voucher-barberia')
def voucher_barberia():
    return render_template('voucher_barberia.html')

#esta ruta nos permite registrar los voucher de los barberos en la base de datos
@app.route('/voucher-barberia', methods=['POST'])
def ingresar_datos():
    cliente = request.form['txtCliente1']
    barbero = request.form['txtBarbero1']
    dni = request.form['txtDni1']
    fecha_actual = datetime.now().strftime('%Y-%m-%d')  # Obtiene la fecha actual en formato YYYY-MM-DD
    print("Cliente:", cliente)
    print("Barbero:", barbero)
    print("Dni:", dni)
    print("Fecha:", fecha_actual) 
    if not re.match('^[A-Za-z\s]+$', cliente):
        return render_template('voucher_barberia.html', mensaje="Error: El nombre del cliente solo puede contener letras.")
    if not re.match('^[A-Za-z\s]+$', barbero):
        return render_template('voucher_barberia.html', mensaje="Error: El nombre del barbero solo puede contener letras.")
    if not re.match('^\d+$', dni):
        return render_template('voucher_barberia.html', mensaje="Error: El DNI solo puede contener números.")
 # Imprime la fecha actual para verificar
    try:
        cur = mysql.connection.cursor()
        # Asegúrate de ajustar tu consulta SQL para incluir la columna de fecha
        cur.execute("INSERT INTO voucher_barbero (cliente, barbero, dni, fecha) VALUES (%s, %s, %s, %s)", (cliente, barbero, dni, fecha_actual))
        mysql.connection.commit()
        cur.close()
        return render_template('voucher_barberia.html', mensaje="Datos ingresados correctamente.")
    except Exception as e:
        print("Error al insertar en la base de datos:", e)
        return render_template('voucher_barberia.html', mensaje="Error al ingresar los datos.")    

#esta ruta nos renderiza la plantilla para el listado de los cortes de los barberos    
@app.route('/listado-cortes', methods=['GET'])
def lista_cortes():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM corte')
    data = cur.fetchall()
    
    return render_template('listado_cortes.html', corte=data)

#esta ruta nos renderiza la plantilla para el listado de los voucher de los barberos
@app.route('/listado-voucher-barbero', methods=['GET'])
def lista_voucher_barbero():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM voucher_barbero')
    data = cur.fetchall()
    
    return render_template('listado_voucher_barbero.html', voucher_barbero=data)

#esta ruta nos renderiza la plantilla para poder ver las estadisticas de los cortes
@app.route('/estadisticas-cortes')
def estadisticas_cortes():
    return render_template('estadisticas_cortes.html')    

#esta ruta nos permite obtener los datos para el grafico de los cortes
@app.route('/corte')
def corte():
    # Create a cursor
    cur = mysql.connection.cursor()
    
    # Execute a SQL query to count users by company and include the date of the cut
    cur.execute("""
        SELECT barbero, DATE_FORMAT(fecha, '%Y-%m-%d') as fecha, COUNT(*) as user_count 
        FROM corte
        GROUP BY barbero, fecha
        ORDER BY fecha, user_count DESC
    """)
    
    rows = cur.fetchall()

    # Prepare the data for the graph
    labels = [f"{row['barbero']} ({row['fecha']})" for row in rows]
    user_counts = [row['user_count'] for row in rows]

    # Create the graph
    fig = go.Figure(data=[go.Bar(x=labels, y=user_counts)])

    # Convert the graph to JSON
    graph_json = pio.to_json(fig)

    # Send the graph as JSON
    return jsonify(graph_json=graph_json)

#esta ruta nos renderiza la plantilla para poder ver las estadisticas de los voucher
@app.route('/estadisticas-voucher-barbero')
def estadisticas_voucher_barbero():
    return render_template('estadisticas_voucher_barbero.html') 

#esta ruta nos permite obtener los datos para el grafico de los voucher
@app.route('/estadisticas-barbero')
def estadisticas_barbero():
    # Create a cursor
    cur = mysql.connection.cursor()
    
    # Execute a SQL query to count users by company
    cur.execute("""
        SELECT barbero, DATE(fecha) as fecha, COUNT(*) as voucher_count 
        FROM voucher_barbero
        GROUP BY barbero, DATE(fecha)
        ORDER BY fecha DESC, voucher_count DESC
    """)
    
    rows = cur.fetchall()

    # Prepare the data for the graph
    labels = [f"{row['fecha']} - {row['barbero']}" for row in rows]
    voucher_counts = [row['voucher_count'] for row in rows]

    # Create the graph
    fig = go.Figure(data=[go.Bar(x=labels, y=voucher_counts)])

    # Convert the graph to JSON
    graph_json = pio.to_json(fig)

    # Send the graph as JSON
    return jsonify(graph_json=graph_json)
 
if __name__ == '__main__':
    app.secret_key = "alexis"
    app.run(debug=True, port=5000, host='0.0.0.0', threaded=True)