from db.db import db

class barbero (db.Model):
    __tablename__ = 'barbero'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.Integer, nullable=False)

    def __init__(self, name, password):
        self.name = name
        self.password = password
    
 