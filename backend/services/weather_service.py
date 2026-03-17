import requests
from dotenv import load_dotenv
import os
from services.llm_service import ask_llm
import json

load_dotenv()


def get_weather(disaster: bool = False) -> dict:

    """
    Obtiene la previsión meteorológica
    """
    URL ="http://ec2-54-171-51-31.eu-west-1.compute.amazonaws.com/weather?disaster=true" if disaster else "http://ec2-54-171-51-31.eu-west-1.compute.amazonaws.com/weather?disaster=false"
    try:
        response = requests.get(URL, headers={"Authorization": f'Bearer {os.getenv("BEARER_TOKEN")}'})

        response.raise_for_status()
        raw = response.json()

        normalized = _normalize_weather(raw).replace("json\n","").replace("```","").replace("```","").strip()

        # Normalizar respuesta para uso interno
        return json.loads(normalized)

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def _normalize_weather(raw: dict) -> dict:

    normalized = ask_llm(function="analyze", weather_data=raw)
    return normalized