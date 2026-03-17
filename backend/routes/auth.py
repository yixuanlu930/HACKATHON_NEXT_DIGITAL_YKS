from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from extensions import db
from models.user import User

auth_bp = Blueprint("auth", __name__)

TIPOS_VIVIENDA = ["Sótano", "Planta baja", "Piso alto", "Casa de campo"]
ROLES_VALIDOS = ["ciudadano", "admin"]


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # Validar campos obligatorios
    required = ["email", "password", "nombre", "provincia", "tipo_vivienda"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Faltan campos obligatorios: {', '.join(missing)}"}), 400

    if data["tipo_vivienda"] not in TIPOS_VIVIENDA:
        return jsonify({"error": f"tipo_vivienda debe ser uno de: {TIPOS_VIVIENDA}"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Ya existe una cuenta con ese email"}), 409

    user = User(
        email=data["email"],
        nombre=data["nombre"],
        provincia=data["provincia"],
        tipo_vivienda=data["tipo_vivienda"],
        necesidades_especiales=data.get("necesidades_especiales", ""),
        rol=data.get("rol", "ciudadano") if data.get("rol") in ROLES_VALIDOS else "ciudadano",
    )
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity={"id": user.id, "rol": user.rol})
    return jsonify({"message": "Usuario registrado correctamente", "token": token, "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email y contraseña son obligatorios"}), 400

    user = User.query.filter_by(email=data["email"]).first()

    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    token = create_access_token(identity={"id": user.id, "rol": user.rol})
    return jsonify({"token": token, "user": user.to_dict()}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user.to_dict()), 200


@auth_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_profile():
    identity = get_jwt_identity()
    user = User.query.get(identity["id"])
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json()
    if "provincia" in data:
        user.provincia = data["provincia"]
    if "tipo_vivienda" in data:
        if data["tipo_vivienda"] not in TIPOS_VIVIENDA:
            return jsonify({"error": f"tipo_vivienda inválido"}), 400
        user.tipo_vivienda = data["tipo_vivienda"]
    if "necesidades_especiales" in data:
        user.necesidades_especiales = data["necesidades_especiales"]
    if "nombre" in data:
        user.nombre = data["nombre"]

    db.session.commit()
    return jsonify({"message": "Perfil actualizado", "user": user.to_dict()}), 200
