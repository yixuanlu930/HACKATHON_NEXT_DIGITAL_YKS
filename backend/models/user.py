from werkzeug.security import generate_password_hash, check_password_hash
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()
from extensions import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default="ciudadano")  # ciudadano | admin

    # Campos del perfil para personalizar alertas
    provincia = db.Column(db.String(100), nullable=False)
    tipo_vivienda = db.Column(db.String(50), nullable=False)   # Sótano, Planta baja, Piso alto, Casa de campo
    necesidades_especiales = db.Column(db.String(200), nullable=True)  # Silla de ruedas, persona dependiente, mascotas

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "nombre": self.nombre,
            "rol": self.rol,
            "provincia": self.provincia,
            "tipo_vivienda": self.tipo_vivienda,
            "necesidades_especiales": self.necesidades_especiales,
        }
