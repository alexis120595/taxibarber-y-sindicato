from db.db import db
from sqlalchemy import Date

class corte (db.Model):
    __tablename__ = 'corte'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cliente = db.Column(db.String(50), nullable=False)
    barbero = db.Column(db.String(50), nullable=False)
    fecha = db.Column(Date)

    def __init__(self, cliente, barbero, fecha):
        self.cliente = cliente
        self.barbero = barbero
        self.fecha = fecha