"""
ClimAlert Valencia — FRONTEND
Hackatón Campus Sostenible UPM 2026

Flask que sirve HTML. Llama al BACKEND API para todo.
Guarda el JWT en session de Flask.
"""

import os
import requests as http
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "frontend-secret-2026")

# URL del backend (tu compañero)
BACKEND = os.environ.get("BACKEND_URL", "http://localhost:5000")


# ─── Helper: llamar al backend ───────────────────────────────────────────

def api(method, path, json=None, token=None):
    """Hace una petición al backend y devuelve (data, status_code)."""
    url = f"{BACKEND}{path}"
    headers = {"Content-Type": "application/json"}
    tk = token or session.get("token")
    if tk:
        headers["Authorization"] = f"Bearer {tk}"
    try:
        r = http.request(method, url, json=json, headers=headers, timeout=15)
        if r.status_code == 401 and tk:
            session.clear()
        return r.json(), r.status_code
    except http.exceptions.JSONDecodeError:
        return {"error": "Respuesta no válida del backend"}, 502
    except Exception as e:
        return {"error": str(e)}, 500


def logged_in():
    return "token" in session and "user" in session


def is_admin():
    return logged_in() and session.get("user", {}).get("rol") == "admin"


# ─── Decoradores ─────────────────────────────────────────────────────────

from functools import wraps

def login_required(f):
    @wraps(f)
    def w(*a, **kw):
        if not logged_in():
            flash("Inicia sesión para continuar.", "warning")
            return redirect(url_for("login"))
        return f(*a, **kw)
    return w

def admin_required(f):
    @wraps(f)
    def w(*a, **kw):
        if not is_admin():
            flash("Acceso restringido a administradores.", "danger")
            return redirect(url_for("login"))
        return f(*a, **kw)
    return w


# ─── Context processor: alertas en todas las páginas ─────────────────────

@app.context_processor
def inject_globals():
    alertas = []
    if logged_in():
        if is_admin():
            data, code = api("GET", "/api/backoffice/alerts")
        else:
            data, code = api("GET", "/api/citizen/alerts")
        if code == 200 and isinstance(data, list):
            alertas = [a for a in data if a.get("activa", True)]
    return {
        "alertas_activas": alertas,
        "current_user": session.get("user"),
        "is_admin": is_admin(),
    }


# ═════════════════════════════════════════════════════════════════════════
# RUTAS — AUTH
# ═════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    if not logged_in():
        return redirect(url_for("login"))
    if is_admin():
        return redirect(url_for("bo_dashboard"))
    return redirect(url_for("citizen_dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        data, code = api("POST", "/api/auth/login", json={
            "email": email,
            "password": password,
        })

        if code == 200 and "token" in data:
            session["token"] = data["token"]
            session["user"] = data["user"]
            flash(f"¡Bienvenido/a, {data['user']['nombre']}!", "success")
            if data["user"]["rol"] == "admin":
                return redirect(url_for("bo_dashboard"))
            return redirect(url_for("citizen_dashboard"))
        else:
            flash(data.get("error", "Credenciales incorrectas."), "danger")

    return render_template("auth/login.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        f = request.form
        body = {
            "email": f.get("email", "").strip(),
            "password": f.get("password", ""),
            "nombre": f.get("nombre", "").strip(),
            "rol": "ciudadano",
            # Ubicación
            "provincia": f.get("provincia", "Valencia"),
            "municipio": f.get("municipio", "").strip(),
            "codigo_postal": f.get("codigo_postal", "").strip(),
            "cerca_cauce": f.get("cerca_cauce") == "true",
            # Vivienda
            "tipo_vivienda": f.get("tipo_vivienda", ""),
            "numero_planta": int(f.get("numero_planta") or 0),
            "num_personas": int(f.get("num_personas") or 1),
            # Vehículo
            "tiene_vehiculo": f.get("tiene_vehiculo") == "true",
            "garaje_subterraneo": f.get("garaje_subterraneo") == "true",
            "planta_garaje": f.get("planta_garaje", ""),
            # Necesidades
            "necesidades_especiales": ",".join(f.getlist("necesidades_especiales")),
            "detalle_mascotas": f.get("detalle_mascotas", "").strip(),
            # Contacto
            "telefono_emergencia": f.get("telefono_emergencia", "").strip(),
        }

        data, code = api("POST", "/api/auth/register", json=body)

        if code == 201 and "token" in data:
            session["token"] = data["token"]
            session["user"] = data["user"]
            flash("¡Cuenta creada!", "success")
            return redirect(url_for("citizen_dashboard"))
        else:
            flash(data.get("error", "Error al registrarse."), "danger")

    return render_template("auth/registro.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))


# ═════════════════════════════════════════════════════════════════════════
# RUTAS — PERFIL
# ═════════════════════════════════════════════════════════════════════════

@app.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    if request.method == "POST":
        f = request.form
        body = {
            "nombre": f.get("nombre", "").strip(),
            "provincia": f.get("provincia", ""),
            "municipio": f.get("municipio", "").strip(),
            "codigo_postal": f.get("codigo_postal", "").strip(),
            "cerca_cauce": f.get("cerca_cauce") == "true",
            "tipo_vivienda": f.get("tipo_vivienda", ""),
            "numero_planta": int(f.get("numero_planta") or 0),
            "num_personas": int(f.get("num_personas") or 1),
            "tiene_vehiculo": f.get("tiene_vehiculo") == "true",
            "garaje_subterraneo": f.get("garaje_subterraneo") == "true",
            "planta_garaje": f.get("planta_garaje", ""),
            "necesidades_especiales": ",".join(f.getlist("necesidades_especiales")),
            "detalle_mascotas": f.get("detalle_mascotas", "").strip(),
            "telefono_emergencia": f.get("telefono_emergencia", "").strip(),
        }
        data, code = api("PUT", "/api/auth/me", json=body)
        if code == 200:
            session["user"] = data.get("user", session["user"])
            flash("Perfil actualizado.", "success")
        else:
            flash(data.get("error", "Error al actualizar."), "danger")
        return redirect(url_for("perfil"))

    # GET: obtener perfil fresco del backend
    data, code = api("GET", "/api/auth/me")
    user = data if code == 200 else session.get("user", {})
    return render_template("perfil.html", user=user)


# ═════════════════════════════════════════════════════════════════════════
# RUTAS — CIUDADANO
# ═════════════════════════════════════════════════════════════════════════

@app.route("/ciudadano")
@login_required
def citizen_dashboard():
    alertas, _ = api("GET", "/api/citizen/alerts")
    if not isinstance(alertas, list):
        alertas = []
    return render_template("ciudadano/dashboard.html", alertas=alertas)


@app.route("/ciudadano/clima")
@login_required
def citizen_weather():
    data, code = api("GET", "/api/citizen/weather")
    error = data.get("error") if code != 200 else None
    return render_template("ciudadano/clima.html", weather=data, error=error)


@app.route("/ciudadano/recomendaciones")
@login_required
def citizen_recommendations():
    data, code = api("GET", "/api/citizen/recommendations")
    error = data.get("error") if code != 200 else None
    return render_template("ciudadano/recomendaciones.html", data=data, error=error)


@app.route("/ciudadano/historial")
@login_required
def citizen_historial():
    weather_logs, _ = api("GET", "/api/citizen/history/weather")
    llm_logs, _ = api("GET", "/api/citizen/history/llm")
    if not isinstance(weather_logs, list):
        weather_logs = []
    if not isinstance(llm_logs, list):
        llm_logs = []
    return render_template("ciudadano/historial.html", weather_logs=weather_logs, llm_logs=llm_logs)


# ═════════════════════════════════════════════════════════════════════════
# RUTAS — BACKOFFICE
# ═════════════════════════════════════════════════════════════════════════

@app.route("/backoffice")
@admin_required
def bo_dashboard():
    alertas, _ = api("GET", "/api/backoffice/alerts")
    users, _ = api("GET", "/api/backoffice/users")
    if not isinstance(alertas, list):
        alertas = []
    if not isinstance(users, list):
        users = []
    return render_template(
        "backoffice/dashboard.html",
        alertas=alertas, users=users,
        n_ciudadanos=len(users),
        n_activas=len([a for a in alertas if a.get("activa")]),
    )


@app.route("/backoffice/clima")
@admin_required
def bo_weather():
    provincia = request.args.get("provincia", "Valencia")
    data, code = api("GET", f"/api/backoffice/weather/{provincia}")
    error = data.get("error") if code != 200 else None
    return render_template("backoffice/clima.html", weather=data, error=error, provincia=provincia)


@app.route("/backoffice/alertas/crear", methods=["POST"])
@admin_required
def bo_crear_alerta():
    f = request.form
    body = {
        "titulo": f.get("titulo", "").strip(),
        "mensaje": f.get("mensaje", "").strip(),
        "nivel": f.get("nivel", "amarillo"),
        "provincia": f.get("provincia", "").strip() or None,
    }
    data, code = api("POST", "/api/backoffice/alerts", json=body)
    if code == 201:
        flash(data.get("message", "Alerta emitida."), "success")
    else:
        flash(data.get("error", "Error al crear alerta."), "danger")
    return redirect(url_for("bo_dashboard"))


@app.route("/backoffice/alertas/<int:aid>/desactivar", methods=["POST"])
@admin_required
def bo_desactivar_alerta(aid):
    data, code = api("DELETE", f"/api/backoffice/alerts/{aid}")
    if code == 200:
        flash("Alerta desactivada.", "info")
    else:
        flash(data.get("error", "Error."), "danger")
    return redirect(url_for("bo_dashboard"))

@app.route("/backoffice/crear-admin", methods=["POST"])
@admin_required
def bo_crear_admin():
    f = request.form
    body = {
        "email": f.get("email", "").strip(),
        "password": f.get("password", ""),
        "nombre": f.get("nombre", "").strip(),
        "provincia": f.get("provincia", "Valencia").strip(),
    }
    data, code = api("POST", "/api/backoffice/create-admin", json=body)
    if code == 201:
        flash(data.get("message", "Admin creado."), "success")
    else:
        flash(data.get("error", "Error al crear admin."), "danger")
    return redirect(url_for("bo_dashboard"))

@app.route("/backoffice/historial")
@admin_required
def bo_historial():
    weather_logs, _ = api("GET", "/api/backoffice/logs/weather")
    llm_logs, _ = api("GET", "/api/backoffice/logs/llm")
    if not isinstance(weather_logs, list):
        weather_logs = []
    if not isinstance(llm_logs, list):
        llm_logs = []
    return render_template("backoffice/historial.html", weather_logs=weather_logs, llm_logs=llm_logs)


# ─── API interna: polling alertas desde JS ───────────────────────────────

@app.route("/api/alertas-poll")
def alertas_poll():
    if not logged_in():
        return jsonify([]), 401
    if is_admin():
        data, code = api("GET", "/api/backoffice/alerts")
    else:
        data, code = api("GET", "/api/citizen/alerts")
    if code == 200 and isinstance(data, list):
        return jsonify([a for a in data if a.get("activa", True)])
    return jsonify([])


# ─── Errores ─────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# ─── Run ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)