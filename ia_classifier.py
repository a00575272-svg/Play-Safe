import json
import re

import anthropic

SYSTEM_PROMPT = (
    "Eres un sistema de control parental. Analiza si el texto contiene "
    "información privada de un menor: nombre completo, dirección, escuela, "
    "teléfono, contraseñas, datos bancarios, ubicación o contacto con adultos "
    "desconocidos. Responde SOLO en JSON sin texto extra: "
    '{"riesgo": true/false, "tipo": "categoria", "razon": "explicacion breve", '
    '"fragmento": "texto sospechoso"}'
)

_FALLBACK = {"riesgo": False, "tipo": "sin_analisis", "razon": "", "fragmento": ""}


def clasificar(texto: str) -> dict:
    if not texto or len(texto.strip()) < 5:
        return {**_FALLBACK}

    texto_enviado = texto[:2000]

    try:
        client = anthropic.Anthropic()
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": texto_enviado}],
        )
        raw = message.content[0].text.strip()
        raw = _limpiar_markdown(raw)
        resultado = json.loads(raw)
        return _normalizar(resultado)

    except json.JSONDecodeError as e:
        print(f"[Classifier] Error al parsear JSON: {e}")
        return {**_FALLBACK, "tipo": "error_parseo"}

    except anthropic.AuthenticationError:
        print("[Classifier] Error de autenticación con Anthropic")
        return {**_FALLBACK, "tipo": "error_auth"}

    except anthropic.RateLimitError:
        print("[Classifier] Rate limit alcanzado")
        return {**_FALLBACK, "tipo": "error_ratelimit"}

    except anthropic.APIConnectionError:
        print("[Classifier] Error de conexión con Anthropic")
        return {**_FALLBACK, "tipo": "error_conexion"}

    except Exception as e:
        print(f"[Classifier] Error inesperado: {type(e).__name__}: {e}")
        return {**_FALLBACK, "tipo": "error_inesperado"}


def _limpiar_markdown(texto: str) -> str:
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    if match:
        return match.group(1).strip()
    return texto.strip()


def _normalizar(data: dict) -> dict:
    return {
        "riesgo": bool(data.get("riesgo", False)),
        "tipo": str(data.get("tipo", "desconocido")),
        "razon": str(data.get("razon", "")),
        "fragmento": str(data.get("fragmento", "")),
    }
