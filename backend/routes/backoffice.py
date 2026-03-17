from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps

from extensions import db
from models.user import User
from models.alert import Alert, WeatherLog, LLMLog
from services.weather_service import get_weather
import json

backoffice_bp = Blueprint("backoffice", __name__)


def admin_required(fn):
    """Decorador que verifica que el usuario es admin."""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if identity.split('|')[1] != "admin":
            return jsonify({"error": "Acceso restringido a administradores"}), 403
        return fn(*args, **kwargs)
    return wrapper


@backoffice_bp.route("/weather/<provincia>", methods=["GET"])
@admin_required
def get_weather_admin(provincia):
    """Obtiene el tiempo para cualquier provincia."""
    identity = get_jwt_identity()
    user = User.query.get(int(identity.split("|")[0]))

    weather = get_weather()

    # Guardar en historial
    log = WeatherLog(
        user_id=user.id,
        provincia=user.provincia,
        datos=json.dumps(weather),
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(weather), 200


@backoffice_bp.route("/alerts", methods=["GET"])
@admin_required
def list_alerts():
    """Lista todas las alertas."""
    alerts = Alert.query.order_by(Alert.creado_en.desc()).all()
    return jsonify([a.to_dict() for a in alerts]), 200


@backoffice_bp.route("/alerts", methods=["POST"])
@admin_required
def create_alert():
    """Crea y emite una alerta a todos los ciudadanos (o de una provincia)."""
    from extensions import socketio

    identity = get_jwt_identity()
    data = request.get_json()

    required = ["titulo", "mensaje", "nivel"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Faltan campos: {', '.join(missing)}"}), 400

    if data["nivel"] not in ["verde", "amarillo", "rojo"]:
        return jsonify({"error": "nivel debe ser: verde, amarillo o rojo"}), 400

    alert = Alert(
        titulo=data["titulo"],
        mensaje=data["mensaje"],
        nivel=data["nivel"],
        provincia=data.get("provincia"),
        creado_por=int(identity.split("|")[0]),
    )
    db.session.add(alert)
    db.session.commit()

    # Contar ciudadanos afectados
    query = User.query.filter_by(rol="ciudadano")
    if alert.provincia:
        query = query.filter_by(provincia=alert.provincia)
    afectados = query.count()

    # ━━━ EMITIR ALERTA EN TIEMPO REAL VÍA WEBSOCKET ━━━
    socketio.emit("nueva_alerta", alert.to_dict(), namespace="/")

    return jsonify({
        "message": f"Alerta emitida a {afectados} ciudadanos",
        "alert": alert.to_dict(),
    }), 201


@backoffice_bp.route("/alerts/<int:alert_id>", methods=["DELETE"])
@admin_required
def deactivate_alert(alert_id):
    """Desactiva una alerta."""
    from extensions import socketio

    alert = Alert.query.get_or_404(alert_id)
    alert.activa = False
    db.session.commit()

    # ━━━ NOTIFICAR DESACTIVACIÓN EN TIEMPO REAL ━━━
    socketio.emit("alerta_desactivada", {"id": alert_id}, namespace="/")

    return jsonify({"message": "Alerta desactivada"}), 200


@backoffice_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    """Lista todos los ciudadanos registrados."""
    users = User.query.filter_by(rol="ciudadano").all()
    return jsonify([u.to_dict() for u in users]), 200


@backoffice_bp.route("/logs/weather", methods=["GET"])
@admin_required
def all_weather_logs():
    """Historial de todas las consultas meteorológicas."""
    logs = WeatherLog.query.order_by(WeatherLog.consultado_en.desc()).limit(50).all()
    return jsonify([l.to_dict() for l in logs]), 200


@backoffice_bp.route("/logs/llm", methods=["GET"])
@admin_required
def all_llm_logs():
    """Historial de todas las consultas al LLM."""
    logs = LLMLog.query.order_by(LLMLog.consultado_en.desc()).limit(50).all()
    return jsonify([l.to_dict() for l in logs]), 200

@backoffice_bp.route("/create-admin", methods=["POST"])
@admin_required
def create_admin():
    """Crea un nuevo usuario administrador."""
    data = request.get_json()

    required = ["email", "password", "nombre"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Faltan campos: {', '.join(missing)}"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Ya existe una cuenta con ese email"}), 409

    admin = User(
        email=data["email"],
        nombre=data["nombre"],
        provincia=data.get("provincia", "Valencia"),
        tipo_vivienda=data.get("tipo_vivienda", "Piso alto"),
        rol="admin",
    )
    admin.set_password(data["password"])

    db.session.add(admin)
    db.session.commit()

    return jsonify({
        "message": f"Admin '{admin.nombre}' creado correctamente",
        "user": admin.to_dict(),
    }), 201