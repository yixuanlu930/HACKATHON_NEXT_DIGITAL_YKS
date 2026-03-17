"""
ClimAlert Valencia — Frontend Flask
Hackatón Campus Sostenible UPM 2026
Aplicación Web para la Gestión de Emergencias Climáticas
"""

import os
import json
import sqlite3
from datetime import datetime
from functools import wraps

import requests
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, g
)
from werkzeug.security import generate_password_hash, check_password_hash

# ═══════════════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════════════

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "climalert-vlc-2026-secret")

API_BASE = "http://ec2-54-171-51-31.eu-west-1.compute.amazonaws.com"
WEATHER_TOKEN = os.environ.get(
    "WEATHER_TOKEN",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiJZU0siLCJleHAiOjE3NzM4MjM4MTd9"
    ".huTUc3BVNqpdRaijUhq3QpKq3QjyPtTeiPVfzaDr3m0",
)

DATABASE = os.path.join(os.path.dirname(__file__), "climalert.db")


# ═══════════════════════════════════════════════════════════════════════
# Database helpers (raw sqlite3 — zero extra deps)
# ═══════════════════════════════════════════════════════════════════════

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        email       TEXT UNIQUE NOT NULL,
        password    TEXT NOT NULL,
        nombre      TEXT NOT NULL,
        rol         TEXT NOT NULL DEFAULT 'ciudadano',
        provincia   TEXT DEFAULT 'Valencia',
        municipio   TEXT DEFAULT '',
        tipo_vivienda TEXT DEFAULT '',
        piso_numero INTEGER DEFAULT 0,
        necesidades TEXT DEFAULT '',
        num_personas INTEGER DEFAULT 1,
        tiene_vehiculo INTEGER DEFAULT 0,
        telefono_emergencia TEXT DEFAULT '',
        created_at  TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS alertas (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo      TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        nivel       TEXT NOT NULL DEFAULT 'amarilla',
        zona        TEXT DEFAULT 'Valencia',
        activa      INTEGER DEFAULT 1,
        created_by  INTEGER REFERENCES usuarios(id),
        created_at  TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS historial_meteo (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        datos       TEXT NOT NULL,
        disaster    INTEGER DEFAULT 0,
        usuario_id  INTEGER REFERENCES usuarios(id),
        created_at  TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS historial_llm (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        system_p    TEXT NOT NULL,
        user_p      TEXT NOT NULL,
        respuesta   TEXT NOT NULL,
        usuario_id  INTEGER REFERENCES usuarios(id),
        created_at  TEXT DEFAULT (datetime('now'))
    );
    """)

    # Admin por defecto
    cur = db.execute("SELECT id FROM usuarios WHERE rol='backoffice' LIMIT 1")
    if cur.fetchone() is None:
        db.execute(
            "INSERT INTO usuarios (email,password,nombre,rol,provincia,municipio) VALUES (?,?,?,?,?,?)",
            ("admin@emergencias.es", generate_password_hash("admin2026"),
             "Administrador", "backoffice", "Valencia", "Valencia"),
        )
        print("✅  Admin creado → admin@emergencias.es / admin2026")
    db.commit()
    db.close()


init_db()


# ═══════════════════════════════════════════════════════════════════════
# Auth decorators
# ═══════════════════════════════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if "uid" not in session:
            flash("Inicia sesión para continuar.", "warning")
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if "uid" not in session:
            return redirect(url_for("login"))
        if session.get("rol") != "backoffice":
            flash("Acceso restringido a administradores.", "danger")
            return redirect(url_for("citizen_dashboard"))
        return f(*a, **kw)
    return wrapper


def current_user():
    if "uid" not in session:
        return None
    return get_db().execute("SELECT * FROM usuarios WHERE id=?", (session["uid"],)).fetchone()


# ═══════════════════════════════════════════════════════════════════════
# API helpers
# ═══════════════════════════════════════════════════════════════════════

def api_weather(disaster=False):
    try:
        r = requests.get(
            f"{API_BASE}/weather",
            params={"disaster": str(disaster).lower()},
            headers={"Authorization": f"Bearer {WEATHER_TOKEN}"},
            timeout=12,
        )
        return r.json() if r.ok else {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}


def api_llm(system_prompt, user_prompt):
    try:
        r = requests.post(
            f"{API_BASE}/prompt",
            headers={
                "Authorization": f"Bearer {WEATHER_TOKEN}",
                "Content-Type": "application/json",
            },
            json={"system_prompt": system_prompt, "user_prompt": user_prompt},
            timeout=30,
        )
        if r.ok:
            d = r.json()
            if isinstance(d, dict):
                return d.get("response") or d.get("message") or d.get("output") or json.dumps(d)
            return str(d)
        return f"Error {r.status_code}: {r.text}"
    except Exception as e:
        return f"Error de conexión: {e}"


# ═══════════════════════════════════════════════════════════════════════
# Prompt Engineering
# ═══════════════════════════════════════════════════════════════════════

VIVIENDA_LABELS = {
    "sotano": "un sótano / semisótano",
    "planta_baja": "una planta baja",
    "piso_alto": "un piso alto (planta {piso})",
    "casa_campo": "una casa de campo / chalet",
}

NECESIDAD_LABELS = {
    "silla_ruedas": "persona en silla de ruedas",
    "movilidad_reducida": "persona con movilidad reducida",
    "persona_dependiente": "persona dependiente",
    "persona_mayor": "persona mayor",
    "ninos": "niños pequeños",
    "mascotas": "mascotas",
    "embarazada": "persona embarazada",
}


def perfil_texto(u):
    """Devuelve un resumen en lenguaje natural del perfil del usuario."""
    viv = VIVIENDA_LABELS.get(u["tipo_vivienda"], u["tipo_vivienda"] or "vivienda no especificada")
    if "{piso}" in viv:
        viv = viv.format(piso=u["piso_numero"] or "?")

    necs = [NECESIDAD_LABELS.get(n.strip(), n.strip())
            for n in (u["necesidades"] or "").split(",") if n.strip()]
    nec_txt = (". En el hogar hay: " + ", ".join(necs) + ".") if necs else ""
    veh = "Dispone de vehículo." if u["tiene_vehiculo"] else "No dispone de vehículo."

    return (
        f"{u['nombre']} vive en {u['municipio'] or u['provincia']}, "
        f"provincia de {u['provincia']}, en {viv}. "
        f"Son {u['num_personas']} persona(s) en el hogar{nec_txt} {veh}"
    )


def sp_ciudadano(u):
    return (
        "Eres un experto en protección civil y gestión de emergencias climáticas "
        "en la Comunidad Valenciana (España). Tu misión es dar instrucciones "
        "CLARAS, CONCRETAS y PERSONALIZADAS para proteger la vida del ciudadano.\n\n"
        f"PERFIL DEL USUARIO:\n{perfil_texto(u)}\n\n"
        "REGLAS:\n"
        "1. Sé directo. Usa lenguaje sencillo pero firme.\n"
        "2. Prioriza la seguridad de las personas sobre bienes materiales.\n"
        "3. Si vive en sótano o planta baja y hay riesgo de inundación, "
        "indica SIEMPRE subir a un piso superior.\n"
        "4. Si hay personas con movilidad reducida, dependientes o mascotas, "
        "da instrucciones específicas para cada caso.\n"
        "5. Incluye siempre: 112 (emergencias), 085 (bomberos Valencia).\n"
        "6. Da pasos numerados y concretos.\n"
        "7. Si no hay riesgo grave, tranquiliza pero da precauciones preventivas.\n"
        "8. Responde SIEMPRE en español.\n"
        "9. Indica nivel de urgencia: BAJO / MODERADO / ALTO / MUY ALTO.\n"
    )


def sp_backoffice():
    return (
        "Eres un analista experto en meteorología y gestión de emergencias "
        "climáticas en la Comunidad Valenciana. Analizas datos meteorológicos "
        "y recomiendas al equipo de protección civil si emitir alerta.\n\n"
        "REGLAS:\n"
        "1. Indica claramente si recomiendas emitir alerta y de qué nivel "
        "(amarilla / naranja / roja).\n"
        "2. Justifica con datos concretos.\n"
        "3. Sugiere el texto de la alerta si la recomiendas.\n"
        "4. Considera riesgos de DANA, lluvias torrenciales e inundaciones.\n"
        "5. Responde en español. Sé técnico pero comprensible.\n"
    )


# ═══════════════════════════════════════════════════════════════════════
# Jinja filters
# ═══════════════════════════════════════════════════════════════════════

@app.template_filter("dt")
def _filter_dt(val):
    if not val:
        return ""
    try:
        d = datetime.fromisoformat(val)
        return d.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(val)


@app.template_filter("json_pretty")
def _filter_json(val):
    try:
        return json.dumps(json.loads(val), indent=2, ensure_ascii=False)
    except Exception:
        return str(val)


# ═══════════════════════════════════════════════════════════════════════
# Context processor — alertas activas en todas las páginas
# ═══════════════════════════════════════════════════════════════════════

@app.context_processor
def inject_alertas():
    if "uid" in session:
        db = get_db()
        alertas = db.execute(
            "SELECT * FROM alertas WHERE activa=1 ORDER BY created_at DESC"
        ).fetchall()
        return {"alertas_activas": alertas}
    return {"alertas_activas": []}


# ═══════════════════════════════════════════════════════════════════════
# RUTAS — Autenticación
# ═══════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    if "uid" in session:
        return redirect(url_for(
            "bo_dashboard" if session.get("rol") == "backoffice" else "citizen_dashboard"
        ))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pwd = request.form.get("password", "")
        db = get_db()
        u = db.execute("SELECT * FROM usuarios WHERE email=?", (email,)).fetchone()
        if u and check_password_hash(u["password"], pwd):
            session["uid"] = u["id"]
            session["nombre"] = u["nombre"]
            session["rol"] = u["rol"]
            flash(f"¡Bienvenido/a, {u['nombre']}!", "success")
            return redirect(url_for(
                "bo_dashboard" if u["rol"] == "backoffice" else "citizen_dashboard"
            ))
        flash("Email o contraseña incorrectos.", "danger")
    return render_template("auth/login.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pwd = request.form.get("password", "")
        nombre = request.form.get("nombre", "").strip()
        rol = request.form.get("rol", "ciudadano")

        if not email or not pwd or not nombre:
            flash("Completa los campos obligatorios.", "danger")
            return render_template("auth/registro.html")

        db = get_db()
        if db.execute("SELECT 1 FROM usuarios WHERE email=?", (email,)).fetchone():
            flash("Ya existe una cuenta con ese email.", "danger")
            return render_template("auth/registro.html")

        if rol == "backoffice" and request.form.get("codigo_admin") != "UPM2026ADMIN":
            flash("Código de administrador incorrecto.", "danger")
            return render_template("auth/registro.html")

        necesidades = ",".join(request.form.getlist("necesidades"))

        db.execute(
            """INSERT INTO usuarios
               (email,password,nombre,rol,provincia,municipio,tipo_vivienda,
                piso_numero,necesidades,num_personas,tiene_vehiculo,telefono_emergencia)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                email,
                generate_password_hash(pwd),
                nombre,
                rol,
                request.form.get("provincia", "Valencia"),
                request.form.get("municipio", "").strip(),
                request.form.get("tipo_vivienda", ""),
                int(request.form.get("piso_numero") or 0),
                necesidades,
                int(request.form.get("num_personas") or 1),
                1 if request.form.get("tiene_vehiculo") == "si" else 0,
                request.form.get("telefono_emergencia", "").strip(),
            ),
        )
        db.commit()
        u = db.execute("SELECT * FROM usuarios WHERE email=?", (email,)).fetchone()
        session["uid"] = u["id"]
        session["nombre"] = u["nombre"]
        session["rol"] = u["rol"]
        flash("¡Cuenta creada! Bienvenido/a.", "success")
        return redirect(url_for(
            "bo_dashboard" if rol == "backoffice" else "citizen_dashboard"
        ))

    return render_template("auth/registro.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))


# ═══════════════════════════════════════════════════════════════════════
# RUTAS — Perfil
# ═══════════════════════════════════════════════════════════════════════

@app.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    db = get_db()
    u = current_user()
    if request.method == "POST":
        db.execute(
            """UPDATE usuarios SET nombre=?, municipio=?, tipo_vivienda=?,
               piso_numero=?, necesidades=?, num_personas=?,
               tiene_vehiculo=?, telefono_emergencia=?
               WHERE id=?""",
            (
                request.form.get("nombre", u["nombre"]).strip(),
                request.form.get("municipio", "").strip(),
                request.form.get("tipo_vivienda", ""),
                int(request.form.get("piso_numero") or 0),
                ",".join(request.form.getlist("necesidades")),
                int(request.form.get("num_personas") or 1),
                1 if request.form.get("tiene_vehiculo") == "si" else 0,
                request.form.get("telefono_emergencia", "").strip(),
            ),
        )
        db.commit()
        session["nombre"] = request.form.get("nombre", u["nombre"]).strip()
        flash("Perfil actualizado.", "success")
        return redirect(url_for("perfil"))
    return render_template("perfil.html", user=u, perfil_txt=perfil_texto(u))


# ═══════════════════════════════════════════════════════════════════════
# RUTAS — Ciudadano
# ═══════════════════════════════════════════════════════════════════════

@app.route("/ciudadano")
@login_required
def citizen_dashboard():
    return render_template("ciudadano/dashboard.html", user=current_user())


@app.route("/ciudadano/clima")
@login_required
def citizen_weather():
    disaster = request.args.get("disaster", "false") == "true"
    data = api_weather(disaster)
    db = get_db()
    db.execute(
        "INSERT INTO historial_meteo (datos,disaster,usuario_id) VALUES (?,?,?)",
        (json.dumps(data), int(disaster), session["uid"]),
    )
    db.commit()
    return render_template(
        "ciudadano/clima.html", user=current_user(), weather=data, disaster=disaster
    )


@app.route("/ciudadano/recomendacion", methods=["POST"])
@login_required
def citizen_recomendacion():
    u = current_user()
    disaster = request.form.get("disaster", "false") == "true"
    weather = api_weather(disaster)

    sys_p = sp_ciudadano(u)
    usr_p = (
        f"Datos meteorológicos actuales para Valencia:\n"
        f"{json.dumps(weather, indent=2, ensure_ascii=False)}\n\n"
        f"Dame instrucciones claras y específicas para mi situación personal."
    )
    resp = api_llm(sys_p, usr_p)

    db = get_db()
    db.execute(
        "INSERT INTO historial_llm (system_p,user_p,respuesta,usuario_id) VALUES (?,?,?,?)",
        (sys_p, usr_p, resp, session["uid"]),
    )
    db.commit()
    return jsonify({"respuesta": resp})


@app.route("/ciudadano/consulta", methods=["POST"])
@login_required
def citizen_consulta():
    pregunta = request.form.get("pregunta", "").strip()
    if not pregunta:
        return jsonify({"error": "Escribe una pregunta."}), 400

    u = current_user()
    sys_p = sp_ciudadano(u)
    resp = api_llm(sys_p, pregunta)

    db = get_db()
    db.execute(
        "INSERT INTO historial_llm (system_p,user_p,respuesta,usuario_id) VALUES (?,?,?,?)",
        (sys_p, pregunta, resp, session["uid"]),
    )
    db.commit()
    return jsonify({"respuesta": resp})


@app.route("/ciudadano/historial")
@login_required
def citizen_historial():
    db = get_db()
    llm = db.execute(
        "SELECT * FROM historial_llm WHERE usuario_id=? ORDER BY created_at DESC LIMIT 50",
        (session["uid"],),
    ).fetchall()
    meteo = db.execute(
        "SELECT * FROM historial_meteo WHERE usuario_id=? ORDER BY created_at DESC LIMIT 50",
        (session["uid"],),
    ).fetchall()
    return render_template("ciudadano/historial.html", user=current_user(), llm=llm, meteo=meteo)


# ═══════════════════════════════════════════════════════════════════════
# RUTAS — Backoffice
# ═══════════════════════════════════════════════════════════════════════

@app.route("/backoffice")
@admin_required
def bo_dashboard():
    db = get_db()
    alertas = db.execute("SELECT * FROM alertas ORDER BY created_at DESC LIMIT 30").fetchall()
    n_ciudadanos = db.execute("SELECT count(*) c FROM usuarios WHERE rol='ciudadano'").fetchone()["c"]
    n_activas = db.execute("SELECT count(*) c FROM alertas WHERE activa=1").fetchone()["c"]
    return render_template(
        "backoffice/dashboard.html",
        user=current_user(), alertas=alertas,
        n_ciudadanos=n_ciudadanos, n_activas=n_activas,
    )


@app.route("/backoffice/clima")
@admin_required
def bo_weather():
    disaster = request.args.get("disaster", "false") == "true"
    data = api_weather(disaster)
    db = get_db()
    db.execute(
        "INSERT INTO historial_meteo (datos,disaster,usuario_id) VALUES (?,?,?)",
        (json.dumps(data), int(disaster), session["uid"]),
    )
    db.commit()
    return render_template("backoffice/clima.html", user=current_user(), weather=data, disaster=disaster)


@app.route("/backoffice/analizar", methods=["POST"])
@admin_required
def bo_analizar():
    disaster = request.form.get("disaster", "false") == "true"
    weather = api_weather(disaster)
    sys_p = sp_backoffice()
    usr_p = (
        f"Analiza estos datos meteorológicos para Valencia y recomienda "
        f"si emitir alerta:\n\n{json.dumps(weather, indent=2, ensure_ascii=False)}\n\n"
        f"Indica: 1) ¿Emitir alerta? 2) Nivel (amarilla/naranja/roja) "
        f"3) Texto sugerido 4) Zonas afectadas 5) Duración estimada."
    )
    resp = api_llm(sys_p, usr_p)

    db = get_db()
    db.execute(
        "INSERT INTO historial_llm (system_p,user_p,respuesta,usuario_id) VALUES (?,?,?,?)",
        (sys_p, usr_p, resp, session["uid"]),
    )
    db.commit()
    return jsonify({"analisis": resp})


@app.route("/backoffice/alertas/crear", methods=["POST"])
@admin_required
def bo_crear_alerta():
    titulo = request.form.get("titulo", "").strip()
    desc = request.form.get("descripcion", "").strip()
    nivel = request.form.get("nivel", "amarilla")
    zona = request.form.get("zona", "Valencia")
    if not titulo or not desc:
        flash("Título y descripción son obligatorios.", "danger")
        return redirect(url_for("bo_dashboard"))
    db = get_db()
    db.execute(
        "INSERT INTO alertas (titulo,descripcion,nivel,zona,created_by) VALUES (?,?,?,?,?)",
        (titulo, desc, nivel, zona, session["uid"]),
    )
    db.commit()
    flash(f"Alerta {nivel.upper()} emitida a todos los ciudadanos.", "success")
    return redirect(url_for("bo_dashboard"))


@app.route("/backoffice/alertas/<int:aid>/desactivar", methods=["POST"])
@admin_required
def bo_desactivar_alerta(aid):
    db = get_db()
    db.execute("UPDATE alertas SET activa=0 WHERE id=?", (aid,))
    db.commit()
    flash("Alerta desactivada.", "info")
    return redirect(url_for("bo_dashboard"))


@app.route("/backoffice/historial")
@admin_required
def bo_historial():
    db = get_db()
    llm = db.execute(
        """SELECT h.*, u.nombre as user_nombre FROM historial_llm h
           LEFT JOIN usuarios u ON u.id=h.usuario_id
           ORDER BY h.created_at DESC LIMIT 100"""
    ).fetchall()
    meteo = db.execute(
        """SELECT h.*, u.nombre as user_nombre FROM historial_meteo h
           LEFT JOIN usuarios u ON u.id=h.usuario_id
           ORDER BY h.created_at DESC LIMIT 100"""
    ).fetchall()
    return render_template("backoffice/historial.html", user=current_user(), llm=llm, meteo=meteo)


# ═══════════════════════════════════════════════════════════════════════
# API JSON (para polling de alertas)
# ═══════════════════════════════════════════════════════════════════════

@app.route("/api/alertas")
@login_required
def api_alertas_json():
    db = get_db()
    rows = db.execute("SELECT * FROM alertas WHERE activa=1 ORDER BY created_at DESC").fetchall()
    return jsonify([dict(r) for r in rows])


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


# ═══════════════════════════════════════════════════════════════════════
# Run
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
