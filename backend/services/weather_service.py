import requests
import os
from dotenv import load_dotenv

load_dotenv()


def _parse_decimal(val):
    """Convierte '1,9' → 1.9 o None si no es válido."""
    if val is None:
        return None
    try:
        return float(str(val).replace(",", "."))
    except (ValueError, TypeError):
        return None


def get_weather(disaster: bool = False) -> dict:
    URL = (
        "http://ec2-54-171-51-31.eu-west-1.compute.amazonaws.com/weather?disaster=true"
        if disaster
        else "http://ec2-54-171-51-31.eu-west-1.compute.amazonaws.com/weather?disaster=false"
    )
    try:
        response = requests.get(
            URL,
            headers={"Authorization": f'Bearer {os.getenv("BEARER_TOKEN")}'},
        )
        response.raise_for_status()
        raw = response.json()
        return _normalize_weather(raw)
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def _normalize_weather(raw: dict) -> dict:
    return {
        "estacion": raw.get("nombre"),
        "provincia": raw.get("provincia"),
        "fecha": raw.get("fecha"),
        "altitud": _parse_decimal(raw.get("altitud")),
        # Temperaturas
        "temperatura_media": _parse_decimal(raw.get("tmed")),
        "temperatura_maxima": _parse_decimal(raw.get("tmax")),
        "temperatura_minima": _parse_decimal(raw.get("tmin")),
        "hora_tmax": raw.get("horatmax"),
        "hora_tmin": raw.get("horatmin"),
        # Precipitación
        "precipitacion_mm": _parse_decimal(raw.get("prec")),
        # Humedad
        "humedad_media": _parse_decimal(raw.get("hrMedia")),
        "humedad_maxima": _parse_decimal(raw.get("hrMax")),
        "humedad_minima": _parse_decimal(raw.get("hrMin")),
        # Viento
        "velocidad_viento": _parse_decimal(raw.get("velmedia")),
        "direccion_viento": raw.get("dir"),
        "racha_maxima": _parse_decimal(raw.get("racha")),
        # Presión
        "presion_maxima": _parse_decimal(raw.get("presMax")),
        "presion_minima": _parse_decimal(raw.get("presMin")),
        # Otros
        "horas_sol": _parse_decimal(raw.get("sol")),
    }