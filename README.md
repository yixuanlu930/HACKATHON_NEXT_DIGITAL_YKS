# ClimAlert Valencia (YKS)

Aplicación web para la **gestión de emergencias climáticas** en la **Comunidad Valenciana**, desarrollada para el **Hackathon UPM 2026 (Next Digital)** — Reto de Gestión de Emergencias Climáticas.

La plataforma:
- Consulta previsiones meteorológicas desde una **API externa**.
- Emite **alertas** segmentadas por provincia (o globales).
- Genera **recomendaciones personalizadas con IA (LLM)** combinando el estado meteorológico con el perfil del ciudadano (vivienda, ubicación, necesidades especiales, etc.).

---

## Tabla de contenidos
- [Descripción](#descripción)
- [Roles](#roles)
- [Arquitectura](#arquitectura)
- [Tecnologías](#tecnologías)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Instalación y ejecución](#instalación-y-ejecución)
  - [Opción A — Local](#opción-a--local)
  - [Opción B — Docker Compose](#opción-b--docker-compose)
- [Variables de entorno](#variables-de-entorno)
- [Credenciales de administrador (desarrollo)](#credenciales-de-administrador-desarrollo)
- [Funcionalidades](#funcionalidades)
- [API del backend](#api-del-backend)
- [Modelo de datos (resumen)](#modelo-de-datos-resumen)
- [Enfoque sostenible](#enfoque-sostenible)
- [Equipo](#equipo)
- [Licencia](#licencia)

---

## Descripción

**ClimAlert Valencia** es una herramienta de soporte a la ciudadanía ante emergencias climáticas (p. ej. DANAs, lluvias intensas, viento fuerte, inundaciones, etc.).

A partir de:
1. **Datos meteorológicos** obtenidos de la API del hackathon, y
2. **Perfil del ciudadano** (ubicación, tipo de vivienda, movilidad reducida, mascotas, cercanía a cauces/barrancos, etc.),

el sistema genera **recomendaciones de autoprotección** con un **LLM**, además de permitir a administradores emitir **alertas** y consultar el **historial del sistema**.

---

## Roles

- **Ciudadano**
  - Consulta previsión meteorológica.
  - Recibe **recomendaciones IA** personalizadas.
  - Recibe **alertas** emitidas por administradores.
  - Consulta su historial (meteo y recomendaciones).

- **Administrador (Backoffice)**
  - Visualiza datos meteorológicos por provincia.
  - Crea/activa/desactiva alertas (verde/amarillo/rojo).
  - Consulta el historial global del sistema.
  - Administra usuarios y puede crear otros administradores.

---

## Arquitectura

Arquitectura cliente-servidor desacoplada:

```
Frontend (Flask + Jinja2, :3000)
        │  HTTP
        ▼
Backend (Flask REST API, :5000)  ───► API Hackathon (/weather, /prompt, EC2 AWS)
        │
        ▼
Base de datos (SQLite dev / MySQL prod)
```

- **Frontend**: Flask que renderiza HTML (Jinja2) y consume el backend vía HTTP.
- **Backend**: API REST en Flask con autenticación JWT, modelos de datos y orquestación de llamadas a la API externa (clima + LLM).
- **Base de datos**: SQLite en desarrollo; compatible con MySQL en producción (Docker).

---

## Tecnologías

- **Backend**: Python 3.12, Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-CORS  
- **Frontend**: Python 3.12, Flask, Jinja2, HTML5, CSS3, JavaScript (vanilla)  
- **Base de datos**: SQLite (desarrollo) / MySQL 8.0 (producción)  
- **Infra/DevOps**: Docker + Docker Compose  
- **Servicios externos**: API meteorológica y LLM proporcionados por la organización del hackathon  

---

## Estructura del proyecto

```
YKS/
  backend/
    app.py                  Punto de entrada del backend (crea la app Flask)
    config.py               Configuración (DB, JWT, claves)
    extensions.py           Instancias de SQLAlchemy y JWTManager
    requirements.txt        Dependencias del backend
    models/
      user.py               Modelo de usuario (ciudadano/admin)
      alert.py              Modelos: Alert, WeatherLog, LLMLog
    routes/
      auth.py               Registro, login, perfil (JWT)
      citizen.py            Rutas del ciudadano (clima, recomendaciones, alertas)
      backoffice.py         Rutas del admin (alertas, usuarios, logs)
    services/
      weather_service.py    Conexión con la API de clima
      llm_service.py        Prompt engineering + conexión con el LLM

  frontend/
    app.py                  Servidor web, rutas de vistas, proxy al backend
    requirements.txt        Dependencias del frontend
    static/
      css/style.css         Estilos (dark, responsive)
      js/app.js             Polling de alertas, notificaciones, toasts
    templates/
      base.html             Layout base con nav, alertas, campana
      perfil.html           Edición de perfil
      404.html              Página de error
      auth/
        login.html
        registro.html
      ciudadano/
        dashboard.html
        clima.html
        recomendaciones.html
        historial.html
      backoffice/
        dashboard.html
        clima.html
        historial.html

  docker/
    Dockerfile.backend
    Dockerfile.frontend
    docker-compose.yaml

  .env                      Variables de entorno (tokens, claves)
  .gitignore
```

---

## Instalación y ejecución

### Requisitos
- **Python 3.10+** (recomendado 3.12)
- `pip`
- (Opcional) **Docker + Docker Compose**

---

### Opción A — Local

1) Clonar el repo:
```bash
git clone https://github.com/ZyroEolu-sk/YKS.git
cd YKS
```

2) Crear `.env` en la raíz del proyecto (ver ejemplo abajo).

3) Backend:
```bash
cd backend
pip install -r requirements.txt
python app.py
```
Backend: `http://localhost:5000`

4) Frontend (otra terminal):
```bash
cd frontend
pip install -r requirements.txt
python app.py
```
Frontend: `http://localhost:3000`

---

### Opción B — Docker Compose

```bash
cd docker
docker-compose up --build
```

Aplicación: `http://localhost:3000`

---

## Variables de entorno

Crear un fichero `.env` en la raíz del proyecto (ejemplo):

```env
SECRET_KEY=tu-clave-secreta
JWT_SECRET_KEY=tu-clave-jwt
DATABASE_URL=sqlite:///hackathon.db
BEARER_TOKEN=tu-token-del-hackathon
```

> Nota: si usas MySQL en Docker/producción, `DATABASE_URL` deberá apuntar a tu instancia MySQL (según el `docker-compose.yaml`).

---

## Credenciales de administrador (desarrollo)

Al arrancar por primera vez, se crea automáticamente un usuario administrador:

- Email: `admin@climalert.es`
- Contraseña: `Admin123!`

> Recomendación: cambiar estas credenciales en cualquier despliegue no local.

---

## Funcionalidades

### 1) Registro y perfil del ciudadano
El registro recoge información para personalizar recomendaciones:
- **Ubicación**: provincia, municipio, código postal, cercanía a cauces/barrancos.
- **Vivienda**: tipo (sótano/semisótano/planta baja/piso alto/casa de campo/urbanización), planta, nº de personas.
- **Vehículo**: disponibilidad, garaje subterráneo y planta.
- **Necesidades especiales**: movilidad reducida, persona dependiente/mayor, mascotas (detalle), niños pequeños.
- **Contacto de emergencia**: teléfono.

### 2) Vista Ciudadano
- **Datos meteorológicos** desde API externa.
- **Recomendaciones IA** adaptadas al perfil y al clima.
- **Alertas activas**:
  - Banner visible en páginas.
  - Campana de notificaciones con indicador.
  - Toast con sonido al recibir nuevas alertas.
- **Historial** (meteo + recomendaciones).

### 3) Vista Backoffice (Administrador)
- Estadísticas de ciudadanos y alertas.
- Clima por provincia.
- Gestión de alertas (crear / desactivar) con niveles **verde / amarillo / rojo**.
- Creación de nuevos administradores.
- Historial global (consultas meteo y LLM).

### 4) Integración con LLM (Prompt Engineering)
Las recomendaciones se generan mediante prompts que incluyen:
- Perfil completo del ciudadano (system prompt).
- Datos meteorológicos actuales (user prompt).
- Reglas contextualizadas para la Comunidad Valenciana (ramblas, barrancos, DANAs, etc.).

### 5) Sistema de alertas casi en tiempo real
Cuando un administrador emite una alerta:
1. Se guarda en base de datos.
2. Se distribuye a ciudadanos por provincia (o a todos).
3. El frontend hace **polling cada 15s** para mostrar nuevas alertas sin refrescar.

---

## API del backend

### Autenticación
- `POST /api/auth/register` — Registro de ciudadano  
- `POST /api/auth/login` — Login (devuelve JWT)  
- `GET  /api/auth/me` — Perfil del usuario autenticado  
- `PUT  /api/auth/me` — Actualizar perfil  

### Ciudadano (requiere JWT)
- `GET /api/citizen/weather` — Datos meteorológicos  
- `GET /api/citizen/recommendations` — Recomendaciones IA  
- `GET /api/citizen/alerts` — Alertas activas (por provincia)  
- `GET /api/citizen/history/weather` — Historial meteo  
- `GET /api/citizen/history/llm` — Historial LLM  

### Backoffice (requiere JWT + rol admin)
- `GET    /api/backoffice/weather/<prov>` — Clima por provincia  
- `GET    /api/backoffice/alerts` — Listar alertas  
- `POST   /api/backoffice/alerts` — Crear/emitir alerta  
- `DELETE /api/backoffice/alerts/<id>` — Desactivar alerta  
- `POST   /api/backoffice/create-admin` — Crear administrador  
- `GET    /api/backoffice/users` — Listar ciudadanos  
- `GET    /api/backoffice/logs/weather` — Historial global meteo  
- `GET    /api/backoffice/logs/llm` — Historial global LLM  

---

## Modelo de datos (resumen)

**User**
- `email` (único), `nombre`, `rol` (ciudadano/admin)
- `provincia`, `municipio`, `codigo_postal`, `cerca_cauce`
- `tipo_vivienda`, `numero_planta`, `num_personas`
- `tiene_vehiculo`, `garaje_subterraneo`, `planta_garaje`
- `necesidades_especiales`, `detalle_mascotas`, `telefono_emergencia`

**Alert**
- `titulo`, `mensaje`, `nivel` (verde/amarillo/rojo)
- `provincia` (vacío = todas), `activa`
- `creado_por`, `creado_en`

**WeatherLog / LLMLog**
- Logs de consultas meteorológicas e interacciones con el LLM por usuario.

---

## Enfoque sostenible

ClimAlert contribuye a la resiliencia climática mediante:
- **Prevención de daños**: recomendaciones personalizadas para fenómenos extremos.
- **Concienciación**: el ciudadano entiende riesgos según su situación real.
- **Accesibilidad**: atención a colectivos vulnerables (movilidad reducida, dependientes, etc.).
- **Reducción de desplazamientos innecesarios**: instrucciones claras evitan exposición a riesgo.

---

## Equipo

**Equipo 💵💵💵** — Universidad Politécnica de Madrid, Hackathon 2026.
- 

---

## Licencia

Proyecto desarrollado para el **Hackathon UPM 2026** organizado por **Next Digital**.
