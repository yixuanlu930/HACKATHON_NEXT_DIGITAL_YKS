from datetime import datetime
# from flask_sqlalchemy import SQLAlchemy
# db = SQLAlchemy()
from extensions import db

class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    nivel = db.Column(db.String(20), nullable=False, default="amarillo")  # verde | amarillo | rojo
    provincia = db.Column(db.String(100), nullable=True)  # None = todas las provincias
    creado_por = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)
    activa = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "mensaje": self.mensaje,
            "nivel": self.nivel,
            "provincia": self.provincia,
            "creado_por": self.creado_por,
            "creado_en": self.creado_en.isoformat(),
            "activa": self.activa,
        }


class WeatherLog(db.Model):
    __tablename__ = "weather_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    provincia = db.Column(db.String(100), nullable=False)
    datos = db.Column(db.Text, nullable=False)  # JSON como string
    consultado_en = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "user_id": self.user_id,
            "provincia": self.provincia,
            "datos": json.loads(self.datos),
            "consultado_en": self.consultado_en.isoformat(),
        }


class LLMLog(db.Model):
    __tablename__ = "llm_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    system_prompt = db.Column(db.Text, nullable=False)
    user_prompt = db.Column(db.Text, nullable=False)
    respuesta = db.Column(db.Text, nullable=False)
    consultado_en = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        respuesta = self.respuesta
        try:
            respuesta = json.loads(respuesta)
        except (json.JSONDecodeError, TypeError):
            pass
        return {
            "id": self.id,
            "user_id": self.user_id,
            "respuesta": respuesta,
            "consultado_en": self.consultado_en.isoformat(),
        }