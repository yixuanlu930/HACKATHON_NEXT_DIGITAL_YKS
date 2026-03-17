from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from extensions import db
from models.user import User

auth_bp = Blueprint("auth", __name__)

TIPOS_VIVIENDA = [
    "Sótano",
    "Semisótano",
    "Planta baja",
    "Bajo con patio/jardín",
    "Piso alto",
    "Casa de campo",
    "Urbanización cerrada",
]
ROLES_VALIDOS = ["ciudadano", "admin"]


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # Campos obligatorios
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
        rol=data.get("rol", "ciudadano") if data.get("rol") in ROLES_VALIDOS else "ciudadano",
        # Ubicación
        provincia=data["provincia"],
        municipio=data.get("municipio", ""),
        codigo_postal=data.get("codigo_postal", ""),
        cerca_cauce=data.get("cerca_cauce", False),
        # Vivienda
        tipo_vivienda=data["tipo_vivienda"],
        numero_planta=int(data.get("numero_planta") or 0),
        num_personas=int(data.get("num_personas") or 1),
        # Vehículo
        tiene_vehiculo=data.get("tiene_vehiculo", False),
        garaje_subterraneo=data.get("garaje_subterraneo", False),
        planta_garaje=data.get("planta_garaje", ""),
        # Necesidades
        necesidades_especiales=data.get("necesidades_especiales", ""),
        detalle_mascotas=data.get("detalle_mascotas", ""),
        # Contacto
        telefono_emergencia=data.get("telefono_emergencia", ""),
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

    # Campos editables
    if "nombre" in data:
        user.nombre = data["nombre"]
    if "provincia" in data:
        user.provincia = data["provincia"]
    if "municipio" in data:
        user.municipio = data["municipio"]
    if "codigo_postal" in data:
        user.codigo_postal = data["codigo_postal"]
    if "cerca_cauce" in data:
        user.cerca_cauce = data["cerca_cauce"]
    if "tipo_vivienda" in data:
        if data["tipo_vivienda"] not in TIPOS_VIVIENDA:
            return jsonify({"error": "tipo_vivienda inválido"}), 400
        user.tipo_vivienda = data["tipo_vivienda"]
    if "numero_planta" in data:
        user.numero_planta = int(data["numero_planta"] or 0)
    if "num_personas" in data:
        user.num_personas = int(data["num_personas"] or 1)
    if "tiene_vehiculo" in data:
        user.tiene_vehiculo = data["tiene_vehiculo"]
    if "garaje_subterraneo" in data:
        user.garaje_subterraneo = data["garaje_subterraneo"]
    if "planta_garaje" in data:
        user.planta_garaje = data["planta_garaje"]
    if "necesidades_especiales" in data:
        user.necesidades_especiales = data["necesidades_especiales"]
    if "detalle_mascotas" in data:
        user.detalle_mascotas = data["detalle_mascotas"]
    if "telefono_emergencia" in data:
        user.telefono_emergencia = data["telefono_emergencia"]

    db.session.commit()
    return jsonify({"message": "Perfil actualizado", "user": user.to_dict()}), 200
