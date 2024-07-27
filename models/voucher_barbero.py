from db.db import db
from sqlalchemy import Date


class voucher_barbero(db.Model):
    __tablename__ = 'voucher_barbero'   
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cliente = db.Column(db.String(100), nullable=False)
    barbero = db.Column(db.String(100), nullable=False)
    dni = db.Column(db.Integer, nullable=False)
    fecha = db.Column(Date)
  

    def __init__(self, cliente, barbero, dni, fecha):
        self.cliente = cliente
        self.barbero = barbero
        self.dni = dni
        self.fecha = fecha
        


