from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import json

from app import db
from models.user import User
from models.alert import Alert, WeatherLog, LLMLog
from services.weather_service import get_weather
from services.llm_service import ask_llm, build_system_prompt, build_user_prompt

citizen_bp = Blueprint("citizen", __name__)


@citizen_bp.route("/weather", methods=["GET"])
@jwt_required()
def get_my_weather():
    """Obtiene el tiempo actual para la provincia del ciudadano."""
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])

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


@citizen_bp.route("/recommendations", methods=["GET"])
@jwt_required()
def get_recommendations():
    """Obtiene recomendaciones personalizadas del LLM según tiempo + perfil."""
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])

    weather = get_weather()
    if "error" in weather:
        return jsonify({"error": "No se pudo obtener el tiempo"}), 503

    system_prompt = build_system_prompt(user)
    user_prompt = build_user_prompt(weather)

    respuesta = ask_llm(system_prompt, user_prompt)

    # Guardar consulta LLM en historial
    llm_log = LLMLog(
        user_id=user.id,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        respuesta=respuesta,
    )
    db.session.add(llm_log)
    db.session.commit()

    return jsonify({
        "weather": weather,
        "recomendacion": respuesta,
        "nivel_alerta": weather.get("nivel_alerta"),
    }), 200


@citizen_bp.route("/alerts", methods=["GET"])
@jwt_required()
def get_my_alerts():
    """Devuelve alertas activas para la provincia del ciudadano."""
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])

    alerts = Alert.query.filter(
        Alert.activa == True,
        (Alert.provincia == user.provincia) | (Alert.provincia == None)
    ).order_by(Alert.creado_en.desc()).all()

    return jsonify([a.to_dict() for a in alerts]), 200


@citizen_bp.route("/history/weather", methods=["GET"])
@jwt_required()
def weather_history():
    """Historial de consultas meteorológicas del ciudadano."""
    identity = get_jwt_identity()
    logs = WeatherLog.query.filter_by(user_id=identity["id"]).order_by(WeatherLog.consultado_en.desc()).limit(20).all()
    return jsonify([l.to_dict() for l in logs]), 200


@citizen_bp.route("/history/llm", methods=["GET"])
@jwt_required()
def llm_history():
    """Historial de consultas al LLM del ciudadano."""
    identity = get_jwt_identity()
    logs = LLMLog.query.filter_by(user_id=identity["id"]).order_by(LLMLog.consultado_en.desc()).limit(20).all()
    return jsonify([l.to_dict() for l in logs]), 200
