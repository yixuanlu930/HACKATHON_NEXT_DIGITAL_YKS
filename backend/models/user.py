#from app import db
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
    rol = db.Column(db.String(20), nullable=False, default="ciudadano")

    # ── Ubicación ────────────────────────────────────────
    provincia = db.Column(db.String(100), nullable=False)
    municipio = db.Column(db.String(100), nullable=True, default="")
    codigo_postal = db.Column(db.String(10), nullable=True, default="")
    cerca_cauce = db.Column(db.Boolean, nullable=True, default=False)

    # ── Vivienda ─────────────────────────────────────────
    tipo_vivienda = db.Column(db.String(50), nullable=False)
    numero_planta = db.Column(db.Integer, nullable=True, default=0)
    num_personas = db.Column(db.Integer, nullable=True, default=1)

    # ── Vehículo ─────────────────────────────────────────
    tiene_vehiculo = db.Column(db.Boolean, nullable=True, default=False)
    garaje_subterraneo = db.Column(db.Boolean, nullable=True, default=False)
    planta_garaje = db.Column(db.String(10), nullable=True, default="")

    # ── Necesidades especiales ───────────────────────────
    necesidades_especiales = db.Column(db.String(500), nullable=True)
    detalle_mascotas = db.Column(db.String(200), nullable=True, default="")

    # ── Contacto de emergencia ───────────────────────────
    telefono_emergencia = db.Column(db.String(20), nullable=True, default="")

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
            "municipio": self.municipio or "",
            "codigo_postal": self.codigo_postal or "",
            "cerca_cauce": self.cerca_cauce or False,
            "tipo_vivienda": self.tipo_vivienda,
            "numero_planta": self.numero_planta or 0,
            "num_personas": self.num_personas or 1,
            "tiene_vehiculo": self.tiene_vehiculo or False,
            "garaje_subterraneo": self.garaje_subterraneo or False,
            "planta_garaje": self.planta_garaje or "",
            "necesidades_especiales": self.necesidades_especiales or "",
            "detalle_mascotas": self.detalle_mascotas or "",
            "telefono_emergencia": self.telefono_emergencia or "",
        }
