from flask import Flask
from flask import render_template, redirect, request, Response, session, url_for, send_file
from flask_mysqldb import MySQL, MySQLdb
import qrcode


app = Flask(__name__, template_folder='template')

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'alexis'
app.config['MYSQL_DB'] = 'login'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def home():
    return render_template('index.html')



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




@app.route('/show_qr/<filename>', methods=['GET'])
def show_qr(filename):
    name1, name2 = filename.split('.')[0].split('_')

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Obtener el estado del voucher
    cur.execute('SELECT estado FROM boucher WHERE name1 = %s AND name2 = %s', (name1, name2))
    result = cur.fetchone()
    estado = result['estado']

    # Generar el código QR
    if estado == 'active':
        data = f"{name1} {name2}"  # Datos para el código QR
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
    img_filename = f'static/qr/{name1}_{name2}.png'
    img.save(img_filename)

    return render_template('show_qr.html', filename=f'{name1}_{name2}.png')

@app.route('/voucher', methods=['GET'])
def voucher():
    return render_template('voucher.html')
    
@app.route('/listado-voucher', methods=['GET'])
def vouchers():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM boucher')
    data = cur.fetchall()
    
    return render_template('listado_voucher.html', boucher=data)



@app.route('/voucher', methods=[ 'POST'])
def boucher():
    if request.method == 'POST':
        name1 = request.form['txtName1']
        name2 = request.form['txtName2']

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('INSERT INTO boucher (name1, name2) VALUES (%s, %s)', (name1, name2))
        mysql.connection.commit()

         # Obtener el estado del voucher
        cur.execute('SELECT estado FROM boucher WHERE name1 = %s AND name2 = %s', (name1, name2))
        result = cur.fetchone()
        estado = result['estado']

        # Generar el código QR
        if estado == 'active':   
         data = f"{name1} {name2}"  # Datos para el código QR
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
        img_filename = f'static/qr/{name1}_{name2}.png'
        img.save(img_filename)

        return redirect(url_for('show_qr', filename=f'{name1}_{name2}.png'))

    return render_template('voucher.html')

@app.route('/listado-voucher', methods=['POST'])
def update_voucher():
    id = request.form.get('id')
    estado = request.form.get('estado')
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('UPDATE boucher SET estado = %s WHERE id = %s', (estado, id))
    mysql.connection.commit()
    return {'message': 'Voucher actualizado correctamente'}


@app.route('/acceso-login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['txtEmail']
        password = request.form['txtPassword']
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SELECT * FROM users WHERE email = %s AND password = %s', (email, password,))
        account = cur.fetchone()
        
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            return render_template('voucher.html')
        else:
            return render_template('index.html', error="Invalid email or password.")
    else:
        # Si el método es GET, simplemente renderizamos el formulario de inicio de sesión.
        return render_template('index.html')
    
@app.route('/users-admin', methods=['GET'])
def users_admin():
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('SELECT * FROM users')
    data = cur.fetchall()
    
    return render_template('users_admin.html', users=data)


@app.route('/users-admin/delete/<int:id>', methods=['POST'])
def delete_user(id):
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute('DELETE FROM users WHERE id = %s', (id,))
    mysql.connection.commit()
    return redirect(url_for('users_admin'))



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
    

@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/register-user', methods=['POST'])
def register_user():
    if request.method == 'POST':
        name = request.form['txtFullName']
        email = request.form['txtEmail']
        password = request.form['txtPassword']
        confirm_password = request.form['txtConfirmPassword']
        branch = request.form['txtBranch']

        if password != confirm_password:
            # Las contraseñas no coinciden
            return "Error: Passwords do not match"

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('INSERT INTO users (name, email, password, branch) VALUES (%s, %s, %s, %s)', (name, email, password, branch))
        mysql.connection.commit()
        return render_template('index.html')
    







   
if __name__ == '__main__':
    app.secret_key = "alexis"
    app.run(debug=True, port=5000, host='0.0.0.0', threaded=True)