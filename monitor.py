import re
import threading

import keyboard

import ia_classifier

# ── Normalización de texto evasivo ────────────────────────────────────────────
# Tabla leet speak: 1→i, 0→o, 4→a, 3→e, @→a, $→s, 5→s, 7→t
_LEET = str.maketrans("104 35@$7", "ioa e3as t".replace(" ", ""))
_LEET = {ord('1'): 'i', ord('0'): 'o', ord('4'): 'a', ord('3'): 'e',
         ord('@'): 'a', ord('$'): 's', ord('5'): 's', ord('7'): 't'}


def _normalizar(texto: str) -> str:
    texto = texto.lower()
    # Colapsar letras separadas por espacios: "v i v o" → "vivo", "c 4 s 4" → "c4s4"
    texto = re.sub(
        r'(?<!\w)([a-z0-9])( [a-z0-9]){2,}(?!\w)',
        lambda m: m.group(0).replace(" ", ""),
        texto,
    )
    # Reemplazar leet speak
    texto = texto.translate(_LEET)
    return texto


# ── Palabras clave ─────────────────────────────────────────────────────────────
PALABRAS_CLAVE = [
    # Ubicación — palabra sola y frases comunes
    "vivo", "vivo en", "vive en", "vivimos", "vivir en",
    "mi casa", "en casa", "voy a casa",
    "mi dirección", "mi domicilio", "mi colonia", "mi calle", "mi barrio",
    "estoy en", "estamos en", "quedo en", "quedamos en",
    "voy a", "vamos a", "cerca de", "a dos cuadras", "a unas cuadras",
    # Datos personales
    "me llamo", "mi nombre es", "soy ",
    "mi número", "mi teléfono", "mi celular", "llámame", "llama al", "llamame",
    "mi correo", "mi email", "mi mail",
    "mi contraseña", "mi clave", "mi pass", "mi password",
    "whatsapp", "mi whats", "mi wa",
    # Escuela
    "mi escuela", "mi colegio", "mi cole", "estudio en",
    "voy al colegio", "voy a la escuela", "mi profe", "mi maestro",
    # Contacto peligroso
    "te mando foto", "te mando una foto", "mándame foto", "manda foto",
    "nos vemos", "te veo", "podemos vernos", "dónde vives", "donde vives",
    "cuántos años tienes", "cuantos años tienes", "mi edad", "tengo años",
    "ven a", "pásate", "pasate", "ven aquí", "ven acá",
    # Datos bancarios
    "mi tarjeta", "número de cuenta", "num de cuenta",
    "mi cuenta", "mi cvv", "cvv", "transferencia",
    "pin del banco", "clave del banco", "mi clabe",
]


def _tiene_palabras_clave(texto: str) -> tuple[bool, str]:
    """Retorna (encontrado, palabra_hallada). Normaliza el texto antes de buscar."""
    texto_norm = _normalizar(texto)
    for kw in PALABRAS_CLAVE:
        if kw in texto_norm:
            return True, kw
    return False, ""


# ── Monitor ───────────────────────────────────────────────────────────────────
class Monitor:
    def __init__(self, on_alert):
        self._on_alert = on_alert
        self._buffer = ""
        self._running = False
        self._stop_event = threading.Event()

    def iniciar(self):
        self._running = True
        self._stop_event.clear()
        keyboard.on_press(self._on_key)
        print("[Monitor] Keylogger iniciado.")
        self._stop_event.wait()
        keyboard.unhook_all()
        print("[Monitor] Detenido.")

    def detener(self):
        self._running = False
        self._stop_event.set()

    def _on_key(self, event):
        if not self._running:
            return

        name = event.name

        if name in ("enter", "return"):
            texto = self._buffer.strip()
            self._buffer = ""
            if texto:
                self._analizar(texto)
        elif name == "backspace":
            self._buffer = self._buffer[:-1]
        elif name == "space":
            self._buffer += " "
        elif name and len(name) == 1:
            self._buffer += name

    def _analizar(self, texto: str):
        encontrado, palabra = _tiene_palabras_clave(texto)
        if not encontrado:
            print(f"[Monitor] Sin coincidencia: '{texto[:50]}'")
            return

        print(f"[Monitor] Coincidencia '{palabra}' → consultando IA...")
        result = ia_classifier.clasificar(texto)
        if result.get("riesgo"):
            self._on_alert(
                result.get("tipo", "desconocido"),
                result.get("razon", ""),
                result.get("fragmento", ""),
                "teclado",
                None,
            )
