from db.db import db
from sqlalchemy import Date

class boucher (db.Model):
    __tablename__ = 'boucher'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name1 = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.String(50), nullable=False, default='active') 
    fecha = db.Column(Date)
    dni = db.Column(db.Integer, nullable=False)

    def __init__(self, name1, fecha, dni, estado='active'):
        self.name1 = name1
        self.estado = estado
        self.fecha = fecha
        self.dni = dni

 