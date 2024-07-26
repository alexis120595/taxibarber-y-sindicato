from db.db import db


class TablaPrueba(db.Model):
    __tablename__ = 'tabla_prueba'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
  

    def __init__(self, nombre):
        self.nombre = nombre
        


