# ClimAlert Valencia ⚡

**Aplicación Web para la Gestión de Emergencias Climáticas — Valencia**

Hackatón Campus Sostenible · Universidad Politécnica de Madrid 2026

## Descripción

ClimAlert Valencia proporciona **instrucciones de seguridad personalizadas** ante emergencias climáticas. El sistema considera el perfil del usuario (tipo de vivienda, planta, necesidades especiales, personas en el hogar) para dar recomendaciones que salvan vidas, en lugar de avisos genéricos.

## Instalación

```bash
pip install -r requirements.txt
python app.py
```

Abrir `http://localhost:5000`

## Credenciales

| Cuenta | Email | Contraseña |
|--------|-------|------------|
| Admin | admin@emergencias.es | admin2026 |
| Ciudadano | (crear desde registro) | — |
| Código admin extra | — | UPM2026ADMIN |

## Funcionalidades

### Ciudadano
- Registro con perfil completo (provincia, municipio, tipo vivienda, planta, necesidades especiales, vehículo, personas en hogar)
- Dashboard con asistente IA de consulta libre
- Recomendaciones personalizadas (modo normal / desastre)
- Visualización de datos meteorológicos + JSON
- Alertas activas con notificaciones toast en tiempo real
- Historial de consultas al LLM y datos meteorológicos

### Backoffice (Administrador)
- Panel con estadísticas (ciudadanos, alertas activas)
- Análisis IA: recomienda si emitir alerta y de qué nivel
- Crear y emitir alertas (amarilla/naranja/roja) a todos los ciudadanos
- Desactivar alertas
- Historial global de todas las consultas

### Integración LLM
- Prompt engineering personalizado por perfil del usuario
- System prompt experto en protección civil valenciana
- Adaptación para sótanos, movilidad reducida, mascotas, embarazadas, etc.
- Endpoints `/weather` y `/prompt` de la API del hackatón

### Sistema de Notificaciones
- Polling cada 30 segundos para nuevas alertas
- Toast notifications con sonido y nivel de alerta
- Banners persistentes para alertas activas
- Badge en título del navegador con número de alertas

## Stack

- **Backend:** Python 3.10+, Flask, SQLite (sin ORM, zero deps extra)
- **Frontend:** HTML5, CSS3 (variables, grid, responsive), Vanilla JS
- **API:** API del Hackatón (weather + LLM vía AWS Bedrock)
- **Diseño:** Dark theme, responsive, accesible

## Estructura

```
frontend/
├── app.py                  # Flask app completa
├── requirements.txt
├── .gitignore
├── static/
│   ├── css/style.css       # Estilos completos
│   └── js/app.js           # Polling alertas + toasts
└── templates/
    ├── base.html            # Layout con nav + alertas + footer
    ├── perfil.html
    ├── auth/
    │   ├── login.html
    │   └── registro.html
    ├── ciudadano/
    │   ├── dashboard.html
    │   ├── clima.html
    │   └── historial.html
    └── backoffice/
        ├── dashboard.html
        ├── clima.html
        └── historial.html
```

## Licencia

Proyecto académico — Hackatón UPM 2026
