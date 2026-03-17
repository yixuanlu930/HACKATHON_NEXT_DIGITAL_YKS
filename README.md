ClimAlert Valencia

Aplicación web para la gestión de emergencias climáticas en la Comunidad Valenciana.
Desarrollada para el Hackathon UPM 2026 — Reto de Gestión de Emergencias Climáticas.


DESCRIPCIÓN

ClimAlert Valencia es una herramienta de soporte a la ciudadanía ante emergencias climáticas. La aplicación recupera previsiones meteorológicas de una API externa y, combinándolas con los datos del perfil del ciudadano (tipo de vivienda, ubicación, necesidades especiales), genera instrucciones personalizadas para proteger su vida mediante un LLM (modelo de lenguaje).

El sistema diferencia entre dos roles:

  Ciudadano: consulta el clima, recibe recomendaciones IA personalizadas según su perfil y recibe alertas emitidas por los administradores.

  Administrador (Backoffice): visualiza datos meteorológicos, gestiona alertas, consulta el historial global del sistema y administra usuarios.


ARQUITECTURA

El proyecto sigue una arquitectura cliente-servidor desacoplada:

  Frontend (Flask + Jinja2, puerto 3000) --> Backend (Flask REST, puerto 5000) --> API Hackathon (/weather, /prompt, EC2 AWS)
                                                        |
                                                        v
                                               Base de datos (SQLite / MySQL)

  Frontend: aplicación Flask que renderiza HTML con Jinja2 y llama al backend vía HTTP.
  Backend: API REST Flask que gestiona autenticación (JWT), modelos de datos, y orquesta las llamadas a la API externa de clima y al LLM.
  Base de datos: SQLite en desarrollo, compatible con MySQL en producción.


TECNOLOGÍAS

  Backend: Python 3.12, Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-CORS
  Frontend: Python 3.12, Flask, Jinja2, HTML5, CSS3, JavaScript vanilla
  Base de datos: SQLite (desarrollo) / MySQL 8.0 (producción con Docker)
  API externa: Servicio meteorológico y LLM proporcionados por la organización del hackathon
  Contenerización: Docker + Docker Compose


ESTRUCTURA DEL PROYECTO

  YKS/
    backend/
      app.py                  Punto de entrada del backend, crea la app Flask
      config.py               Configuración (DB, JWT, claves)
      extensions.py           Instancias de SQLAlchemy y JWTManager
      requirements.txt        Dependencias del backend
      models/
        user.py               Modelo de usuario (ciudadano/admin)
        alert.py              Modelos: Alert, WeatherLog, LLMLog
      routes/
        auth.py               Registro, login, perfil (JWT)
        citizen.py            Rutas del ciudadano (clima, recomendaciones, alertas)
        backoffice.py         Rutas del admin (gestión alertas, usuarios, logs)
      services/
        weather_service.py    Conexión con la API de clima
        llm_service.py        Prompt engineering + conexión con el LLM
    frontend/
      app.py                  Servidor web, rutas de vistas, proxy al backend
      requirements.txt        Dependencias del frontend
      static/
        css/style.css         Estilos (tema dark, responsive)
        js/app.js             Polling de alertas, notificaciones, toasts
      templates/
        base.html             Layout base con nav, alertas, campana
        perfil.html           Edición de perfil del usuario
        404.html              Página de error
        auth/
          login.html          Inicio de sesión
          registro.html       Registro con perfil completo
        ciudadano/
          dashboard.html      Panel del ciudadano
          clima.html          Datos meteorológicos
          recomendaciones.html  Recomendaciones IA personalizadas
          historial.html      Historial de consultas
        backoffice/
          dashboard.html      Panel de control admin
          clima.html          Clima por provincia
          historial.html      Historial global del sistema
    docker/
      Dockerfile.backend      Imagen Docker del backend
      Dockerfile.frontend     Imagen Docker del frontend
      docker-compose.yaml     Orquestación de servicios
    .env                      Variables de entorno (tokens, claves)
    .gitignore


INSTALACIÓN Y EJECUCIÓN

Requisitos previos: Python 3.10 o superior, pip.

Opción 1: Ejecución local

  1. Clonar el repositorio:

     git clone https://github.com/K06-Z/YKS.git
     cd YKS

  2. Configurar variables de entorno. Crear un fichero .env en la raíz del proyecto:

     SECRET_KEY=tu-clave-secreta
     JWT_SECRET_KEY=tu-clave-jwt
     DATABASE_URL=sqlite:///hackathon.db
     BEARER_TOKEN=tu-token-del-hackathon

  3. Instalar dependencias e iniciar el backend:

     cd backend
     pip install -r requirements.txt
     python app.py

     El backend arranca en http://localhost:5000. Al iniciar por primera vez, se crea automáticamente un usuario administrador:

     Email: admin@climalert.es
     Contraseña: Admin123!

  4. Instalar dependencias e iniciar el frontend (en otra terminal):

     cd frontend
     pip install -r requirements.txt
     python app.py

     El frontend arranca en http://localhost:3000.

Opción 2: Docker Compose

     cd docker
     docker-compose up --build

     La aplicación estará disponible en http://localhost:3000.


FUNCIONALIDADES

1. Registro y gestión de perfil

El registro recoge información detallada del ciudadano para personalizar las recomendaciones:

  Ubicación: provincia, municipio, código postal, cercanía a cauces/barrancos.
  Vivienda: tipo (sótano, semisótano, planta baja, piso alto, casa de campo, urbanización cerrada), número de planta, personas en el hogar.
  Vehículo: disponibilidad, garaje subterráneo y planta del garaje.
  Necesidades especiales: silla de ruedas, movilidad reducida, persona dependiente, persona mayor, mascotas (con detalle), niños pequeños.
  Contacto de emergencia: teléfono.

Dos roles de usuario:

  Ciudadano: acceso a clima, recomendaciones, alertas e historial personal.
  Administrador: acceso al panel de control, gestión de alertas, historial global.

2. Vista de Ciudadano

  Datos meteorológicos: visualización de la previsión obtenida de la API externa.
  Recomendaciones IA personalizadas: el LLM analiza el clima actual junto con el perfil completo del ciudadano y genera instrucciones específicas (adaptadas a tipo de vivienda, necesidades especiales, cercanía a cauces, etc.).
  Alertas activas: banners visibles, campana de notificaciones con polling automático cada 15 segundos, y toasts con sonido cuando llegan alertas nuevas.
  Historial: registro de todas las consultas meteorológicas y recomendaciones del LLM.

3. Vista de Backoffice (Administrador)

  Panel de control: estadísticas de ciudadanos registrados, alertas activas y totales, con listados desplegables.
  Datos meteorológicos: consulta de clima por provincia.
  Gestión de alertas: creación de alertas con nivel (verde, amarillo, rojo), título, mensaje y provincia destino. Posibilidad de desactivar alertas.
  Crear administradores: formulario para crear nuevas cuentas de administrador.
  Historial global: registro de todas las consultas meteorológicas y al LLM de todos los usuarios.

4. Integración LLM — Prompt Engineering

La personalización de las recomendaciones se logra mediante Prompt Engineering. El system_prompt incluye el perfil completo del ciudadano y reglas específicas para la Comunidad Valenciana (DANAs, ramblas, barrancos). El user_prompt incluye los datos meteorológicos actuales.

Ejemplo de personalización:

  Un ciudadano en sótano cerca de un barranco con silla de ruedas recibe instrucciones de evacuación vertical asistida con máxima urgencia.
  Un ciudadano en piso alto sin necesidades especiales recibe instrucciones de precaución ante viento y recomendación de no salir.

5. Sistema de alertas en tiempo casi real

Cuando un administrador emite una alerta:

  1. Se almacena en base de datos con nivel, título, mensaje y provincia.
  2. Los ciudadanos de esa provincia (o todos, si no se especifica) la reciben mediante:
     Banner visible en todas las páginas.
     Campana de notificaciones con indicador de alerta nueva.
     Toast emergente con sonido de alerta.
  3. El sistema hace polling cada 15 segundos para detectar alertas nuevas sin necesidad de refrescar la página.


API DEL BACKEND

Autenticación:

  POST  /api/auth/register             Registro de ciudadano
  POST  /api/auth/login                Inicio de sesión (devuelve JWT)
  GET   /api/auth/me                   Obtener perfil del usuario autenticado
  PUT   /api/auth/me                   Actualizar perfil

Ciudadano (requiere JWT):

  GET   /api/citizen/weather            Obtener datos meteorológicos
  GET   /api/citizen/recommendations    Obtener recomendaciones IA personalizadas
  GET   /api/citizen/alerts             Obtener alertas activas para su provincia
  GET   /api/citizen/history/weather    Historial de consultas meteorológicas
  GET   /api/citizen/history/llm        Historial de recomendaciones del LLM

Backoffice (requiere JWT + rol admin):

  GET   /api/backoffice/weather/<prov>  Clima por provincia
  GET   /api/backoffice/alerts          Listar todas las alertas
  POST  /api/backoffice/alerts          Crear y emitir alerta
  DELETE /api/backoffice/alerts/<id>    Desactivar alerta
  POST  /api/backoffice/create-admin    Crear nuevo administrador
  GET   /api/backoffice/users           Listar ciudadanos registrados
  GET   /api/backoffice/logs/weather    Historial global de consultas meteo
  GET   /api/backoffice/logs/llm        Historial global de consultas al LLM


MODELO DE DATOS

User:

  email                  String     Email único del usuario
  nombre                 String     Nombre completo
  rol                    String     ciudadano o admin
  provincia              String     Provincia de residencia
  municipio              String     Municipio
  codigo_postal          String     Código postal
  cerca_cauce            Boolean    Vive cerca de barranco/rambla/cauce
  tipo_vivienda          String     Sótano, Semisótano, Planta baja, Piso alto, etc.
  numero_planta          Integer    Planta del edificio
  num_personas           Integer    Personas en el hogar
  tiene_vehiculo         Boolean    Dispone de vehículo
  garaje_subterraneo     Boolean    Garaje bajo tierra
  planta_garaje          String     Planta del garaje
  necesidades_especiales String     Lista de necesidades especiales
  detalle_mascotas       String     Tipo y número de mascotas
  telefono_emergencia    String     Contacto de emergencia

Alert:

  titulo                 String     Título de la alerta
  mensaje                Text       Contenido de la alerta
  nivel                  String     verde, amarillo o rojo
  provincia              String     Provincia destino (vacío = todas)
  activa                 Boolean    Estado de la alerta
  creado_por             Integer    ID del admin que la creó
  creado_en              DateTime   Fecha de creación

WeatherLog / LLMLog:

  Tablas de historial que registran cada consulta meteorológica y cada interacción con el LLM, asociadas al usuario que las realizó.


ENFOQUE SOSTENIBLE

ClimAlert contribuye a la gestión ecológica y sostenible del campus y la comunidad:

  Prevención de daños: las recomendaciones personalizadas reducen el impacto humano y material de fenómenos extremos como las DANAs.
  Concienciación climática: el ciudadano interactúa directamente con datos meteorológicos reales y comprende los riesgos asociados a su situación concreta.
  Accesibilidad: el perfil detallado permite atender a personas con movilidad reducida, dependientes y otros colectivos vulnerables que suelen quedar desatendidos en alertas genéricas.
  Reducción de desplazamientos innecesarios: instrucciones claras evitan que los ciudadanos se expongan a riesgos o realicen evacuaciones no necesarias.


EQUIPO

Equipo $$$ YKS — Universidad Politécnica de Madrid, Hackathon 2026


LICENCIA

Proyecto desarrollado para el Hackathon UPM 2026 organizado por Next Digital.
