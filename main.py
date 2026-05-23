import hashlib
import json
import os
import sys
import threading
from pathlib import Path

# Funciona tanto ejecutando main.py como desde el .exe generado por PyInstaller
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

CONFIG_PATH = BASE_DIR / "config.json"

REQUIRED_FIELDS = [
    "telegram_token",
    "telegram_chat_id",
    "anthropic_api_key",
    "password_padres",
    "modo_prueba",
]


def load_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] No se encontró '{CONFIG_PATH}'.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[ERROR] config.json inválido: {e}")
        sys.exit(1)

    missing = [k for k in REQUIRED_FIELDS if k not in cfg]
    if missing:
        print(f"[ERROR] Campos faltantes en config.json: {missing}")
        sys.exit(1)

    return cfg


def main():
    print("=" * 52)
    print("  🛡️  SISTEMA DE CONTROL PARENTAL CON IA")
    print("=" * 52)

    cfg = load_config()

    os.environ["ANTHROPIC_API_KEY"] = cfg["anthropic_api_key"]

    modo_prueba = cfg["modo_prueba"]
    if modo_prueba:
        print("[Main] ⚙️  Modo prueba activo — sin bloqueos de pantalla")

    from logger import Logger
    from monitor import Monitor
    from overlay import Overlay
    from telegram_bot import TelegramBot

    logger = Logger()
    password_hash = hashlib.sha256(cfg["password_padres"].encode()).hexdigest()
    overlay = Overlay(password_hash)
    bot = TelegramBot(cfg["telegram_token"], cfg["telegram_chat_id"], logger)

    bot.set_overlay_callback(overlay.unlock)

    def on_alert(
        tipo: str,
        razon: str,
        fragmento: str,
        fuente: str,
        screenshot_bytes: bytes | None = None,
    ):
        print(f"\n[ALERTA] ⚠️  Tipo: {tipo} | Fuente: {fuente}")
        print(f"         Razón: {razon}")

        logger.guardar_alerta(tipo, razon, fragmento, fuente)
        bot.enviar_alerta(tipo, razon, fragmento, fuente, screenshot_bytes)

        if not modo_prueba:
            overlay.mostrar_alerta(tipo, razon)

    monitor = Monitor(on_alert)

    print("[Main] 🤖 Iniciando bot de Telegram...")
    bot_thread = threading.Thread(target=bot.run_in_thread, name="TelegramBot", daemon=True)
    bot_thread.start()

    if bot.esperar_listo(20):
        print("[Main] ✅ Bot de Telegram conectado.")
    else:
        print("[Main] ⚠️  Bot tardó más de 20s. Verifica el token y la conexión.")

    print("[Main] 👁️  Iniciando monitor...")
    monitor_thread = threading.Thread(target=monitor.iniciar, name="Monitor", daemon=True)
    monitor_thread.start()

    print("[Main] 🖥️  Iniciando overlay (hilo principal)...\n")
    overlay.iniciar()

    print("\n[Main] Overlay cerrado. Deteniendo monitor...")
    monitor.detener()
    print("[Main] Sistema finalizado. 👋")


if __name__ == "__main__":
    main()
