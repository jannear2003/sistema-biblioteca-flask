from database import db
from datetime import datetime, timedelta

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)


class Libro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    disponible = db.Column(db.Boolean, default=True)


class Prestamo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    libro_id = db.Column(db.Integer, db.ForeignKey('libro.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))

    fecha_prestamo = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_devolucion_estimada = db.Column(
        db.DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=7)
    )

    libro = db.relationship('Libro')
    usuario = db.relationship('Usuario')