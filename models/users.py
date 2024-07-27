from db.db import db

class users (db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.String(50), nullable=False, default='inactive')
    empresa = db.Column(db.String(50), nullable=False)
    dni = db.Column(db.Integer, nullable=False)
    celular = db.Column(db.String(25), nullable=False)
    familia = db.Column(db.String(300), nullable=False)
    

def __init__(self, name, email, password, empresa, dni, celular, familia, estado='inactive'):
        self.name = name
        self.email = email
        self.password = password
        self.estado = estado
        self.empresa = empresa
        self.dni = dni
        self.celular = celular
        self.familia = familia
        