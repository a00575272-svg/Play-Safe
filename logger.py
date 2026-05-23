import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path

if getattr(sys, "frozen", False):
    _BASE = Path(sys.executable).parent
else:
    _BASE = Path(__file__).parent

ALERTS_FILE = str(_BASE / "alertas.json")
MAX_ENTRIES = 500


class Logger:
    def __init__(self):
        self._lock = threading.Lock()

    def guardar_alerta(self, tipo: str, razon: str, fragmento: str, fuente: str) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "tipo": tipo,
            "razon": razon,
            "fragmento": fragmento,
            "fuente": fuente,
        }
        with self._lock:
            entries = self._load()
            entries.append(entry)
            if len(entries) > MAX_ENTRIES:
                entries = entries[-MAX_ENTRIES:]
            self._save(entries)

    def obtener_historial(self, n: int = 10) -> list:
        with self._lock:
            entries = self._load()
        return entries[-n:]

    def _load(self) -> list:
        if not os.path.exists(ALERTS_FILE):
            return []
        try:
            with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("Expected JSON array")
            return data
        except (json.JSONDecodeError, ValueError):
            bak = ALERTS_FILE + ".bak"
            try:
                os.rename(ALERTS_FILE, bak)
                print(f"[Logger] Archivo corrupto, renombrado a {bak}")
            except OSError:
                pass
            return []

    def _save(self, entries: list) -> None:
        with open(ALERTS_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
