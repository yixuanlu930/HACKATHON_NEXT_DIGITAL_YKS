import requests
import os
from dotenv import load_dotenv
import json


URL = "http://ec2-54-171-51-31.eu-west-1.compute.amazonaws.com/prompt"



def build_system_prompt() -> str:
    """
    Construye el system_prompt personalizado según el perfil del ciudadano.
    Aquí está la magia del Prompt Engineering del reto.
    """

    return """Eres un experto en gestión de emergencias climáticas y protección civil en España.
    Tu misión es analizar los datos proporcionados sobre el clima actual y dar instrucciones claras, concretas y personalizadas para proteger la vida del ciudadano, según las características concretas que tenga.

    Reglas de comportamiento:
    1. Da siempre instrucciones específicas para su tipo de vivienda. 
    2. Si tiene necesidades especiales (silla de ruedas, persona dependiente, mascotas), adapta las instrucciones.
    3. Sé directo y claro. Usa frases cortas. En emergencias no hay tiempo para textos largos.
    4. Indica el nivel de urgencia: URGENTE, PRECAUCIÓN o INFORMATIVO.
    5. Responde siempre en español."""

def build_system_prompt_analyze() -> str:
    """
    Analiza los datos de la API de clima
    """
    return """
    Eres un experto en análisis de datos meteorológicos. Tu misión es analizar los datos proporcionados por una API de clima y devolver información relevante extraída de esos datos.
    El usuario proporcionará un JSON de los datos meteorológicos extraídos directamente de la API. Tu tarea es analizarlos y devolver en formato JSON la información con la siguiente estructura:
    {
    "temperatura":float,
    "probabilidad_precipitacion":float,
    "volumen_precipitacion":float,
    "velocidad_viento":float,
    "direccion_viento":float,
    "indice_uv":float,
    "presion_atmosferica":float,
    "humedad_relativa":float,
    "nivel_alerta":str
    }

    Donde:
    - temperatura: Temperatura actual en grados Celsius.
    - probabilidad_precipitacion: Probabilidad de que llueva en porcentaje.
    - volumen_precipitacion: Volumen de lluvia esperado en mm.
    - velocidad_viento: Velocidad del viento en km/h.
    - direccion_viento: Dirección del viento en grados (0-360).
    - indice_uv: Índice de radiación UV.
    - presion_atmosferica: Presión atmosférica en hPa.
    - humedad_relativa: Humedad relativa en porcentaje.
    - nivel_alerta: Nivel de alerta meteorológica (VERDE, AMARILLO, NARANJA, ROJO) basado en los datos anteriores. 

    Dame solo el JSON con la información solicitada, sin explicaciones ni texto adicional. Si algún dato no está disponible, pon null en su valor. 
    NO empieces la respuesta con json. Solo devuelve el JSON puro. Empieza directamente con { y termina con }.
"""
def build_user_prompt_analyze(weather_data: dict) -> str:
    """Construye el user_prompt con los datos meteorológicos actuales."""
    return f"""Situación meteorológica actual en {weather_data.get('provincia')} obtenido de la API en formato JSON es:
    {json.dumps(weather_data)}

    Dame un análisis de estos datos en formato JSON
    """


def build_user_prompt(user_data: dict, weather_data: dict) -> str:
    """Construye el user_prompt con los datos del usuario."""
    return f"""Los datos del usuario son:
    - Nombre: {user_data.get('nombre')}
    - Provincia: {user_data.get('provincia')}
    - Municipio: {user_data.get('municipio') or 'No especificado'}
    - Código postal: {user_data.get('codigo_postal') or 'No especificado'}
    - Cerca de barranco/rambla: {'Sí' if user_data.get('cerca_cauce') else 'No'}
    - Tipo de vivienda: {user_data.get('tipo_vivienda')}
    - Número de planta: {user_data.get('numero_planta') or 'N/A'}
    - Personas en el hogar: {user_data.get('num_personas', 1)}
    - Tiene vehículo: {'Sí' if user_data.get('tiene_vehiculo') else 'No'}
    - Garaje subterráneo: {'Sí (planta ' + str(user_data.get('planta_garaje', '?')) + ')' if user_data.get('garaje_subterraneo') else 'No'}
    - Necesidades especiales: {user_data.get('necesidades_especiales') or 'Ninguna'}
    - Detalle mascotas: {user_data.get('detalle_mascotas') or 'N/A'}
    - Teléfono emergencia: {user_data.get('telefono_emergencia') or 'No proporcionado'}

    El clima actual en su provincia es:
    - Temperatura: {weather_data.get('temperatura', 'N/A')} °C
    - Probabilidad de precipitación: {weather_data.get('probabilidad_precipitacion', 'N/A')} %
    - Volumen de precipitación: {weather_data.get('volumen_precipitacion', 'N/A')} mm
    - Velocidad del viento: {weather_data.get('velocidad_viento', 'N/A')} km/h
    - Dirección del viento: {weather_data.get('direccion_viento', 'N/A')} °
    - Índice UV: {weather_data.get('indice_uv', 'N/A')}
    - Presión atmosférica: {weather_data.get('presion_atmosferica', 'N/A')} hPa
    - Humedad relativa: {weather_data.get('humedad_relativa', 'N/A')} %
    - Nivel de alerta: {weather_data.get('nivel_alerta', 'N/A')}

    ¿Qué debe hacer este ciudadano para protegerse? Da instrucciones concretas, numeradas y personalizadas según su perfil."""



def ask_llm(function:str = "analyze", user_data: dict = {},weather_data: dict = {}) -> str:
    if function == "analyze":
        system_prompt = build_system_prompt_analyze()
        user_prompt = build_user_prompt_analyze(weather_data)
        response = requests.post(URL,headers ={"Authorization": f'Bearer {os.getenv("BEARER_TOKEN")}'}, json={"system_prompt": system_prompt, "user_prompt": user_prompt})

        if response.status_code == 200:
            return response.json().get("response", {})
        else:
            return {"error": f"Error al comunicarse con el LLM: {response.status_code} - {response.text}"}
    else:
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(user_data, weather_data)
        response = requests.post(URL,headers ={"Authorization": f'Bearer {os.getenv("BEARER_TOKEN")}'}, json={"system_prompt": system_prompt, "user_prompt": user_prompt})
        if response.status_code == 200:
            return response.json().get("response", {})
        else:
            return {"error": f"Error al comunicarse con el LLM: {response.status_code} - {response.text}"}