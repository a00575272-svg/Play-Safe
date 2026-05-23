import asyncio
import logging
import threading
from datetime import datetime
from io import BytesIO

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)


class TelegramBot:
    def __init__(self, token: str, chat_id: str, logger):
        self._token = token
        self._chat_id = str(chat_id)
        self._logger = logger
        self._app: Application | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._ready = threading.Event()
        self._overlay_callback = None

    def set_overlay_callback(self, callback):
        self._overlay_callback = callback

    def run_in_thread(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._start())
        except Exception as e:
            print(f"[TelegramBot] Error fatal en loop: {e}")

    async def _start(self):
        self._app = Application.builder().token(self._token).build()
        self._app.add_handler(CommandHandler("estado", self._cmd_estado))
        self._app.add_handler(CommandHandler("historial", self._cmd_historial))
        self._app.add_handler(CommandHandler("desbloquear", self._cmd_desbloquear))
        self._app.add_handler(CallbackQueryHandler(self._handle_callback))

        async with self._app:
            await self._app.start()
            await self._app.updater.start_polling(drop_pending_updates=True)
            # Notify parent that system is online
            try:
                ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                await self._app.bot.send_message(
                    chat_id=self._chat_id,
                    text=f"🛡️ *Sistema de control parental INICIADO*\n✅ Monitor activo\n🕐 {ts}",
                    parse_mode="Markdown",
                )
            except Exception as e:
                print(f"[TelegramBot] No se pudo enviar notificación de inicio: {e}")
            print("[TelegramBot] Bot iniciado y listo.")
            self._ready.set()
            await asyncio.get_running_loop().create_future()

    def esperar_listo(self, timeout: int = 20) -> bool:
        return self._ready.wait(timeout=timeout)

    def enviar_alerta(
        self,
        tipo: str,
        razon: str,
        fragmento: str,
        fuente: str,
        screenshot_bytes: bytes | None = None,
    ):
        if self._loop is None or not self._loop.is_running():
            print("[TelegramBot] Loop no disponible; alerta descartada.")
            return
        asyncio.run_coroutine_threadsafe(
            self._send_alerta(tipo, razon, fragmento, fuente, screenshot_bytes),
            self._loop,
        )

    async def _send_alerta(
        self,
        tipo: str,
        razon: str,
        fragmento: str,
        fuente: str,
        screenshot_bytes: bytes | None,
    ):
        if not self._app:
            return

        frag = (fragmento[:80] + "…") if len(fragmento) > 80 else fragmento
        ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        emoji = {"ubicacion": "📍", "contacto": "👤", "contraseña": "🔑", "bancario": "💳"}.get(
            tipo.lower(), "⚠️"
        )

        texto = (
            f"{emoji} *ALERTA DE CONTROL PARENTAL*\n\n"
            f"🔴 *Tipo:* `{tipo}`\n"
            f"📋 *Razón:* {razon}\n"
            f"📝 *Fragmento:* `{frag}`\n\n"
            f"📡 *Fuente:* {fuente}\n"
            f"🕐 *Hora:* {ts}"
        )

        teclado = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("✅ Revisado", callback_data="revisado"),
                InlineKeyboardButton("🔓 Desbloquear", callback_data="desbloquear"),
            ]]
        )

        try:
            if screenshot_bytes:
                photo = InputFile(BytesIO(screenshot_bytes), filename="captura.png")
                await self._app.bot.send_photo(
                    chat_id=self._chat_id,
                    photo=photo,
                    caption=texto,
                    parse_mode="Markdown",
                    reply_markup=teclado,
                )
            else:
                await self._app.bot.send_message(
                    chat_id=self._chat_id,
                    text=texto,
                    parse_mode="Markdown",
                    reply_markup=teclado,
                )
        except Exception as e:
            print(f"[TelegramBot] Error enviando alerta: {e}")

    async def _cmd_estado(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        await update.message.reply_text(
            f"✅ *Sistema de control parental ACTIVO*\n🕐 {ts}",
            parse_mode="Markdown",
        )

    async def _cmd_historial(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        alertas = self._logger.obtener_historial(10)
        if not alertas:
            await update.message.reply_text("📭 No hay alertas registradas.")
            return
        lineas = ["📋 *Últimas alertas:*\n"]
        for a in reversed(alertas):
            ts = a.get("timestamp", "")[:19].replace("T", " ")
            tipo = a.get("tipo", "—")
            razon = a.get("razon", "")[:60]
            fuente = a.get("fuente", "")
            lineas.append(f"• `{ts}` [{fuente}] *{tipo}*: {razon}")
        await update.message.reply_text("\n".join(lineas), parse_mode="Markdown")

    async def _cmd_desbloquear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self._overlay_callback:
            self._overlay_callback()
            await update.message.reply_text("🔓 Sistema desbloqueado remotamente.")
        else:
            await update.message.reply_text("⚠️ No hay overlay activo para desbloquear.")

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        if query.data == "revisado":
            nuevo = InlineKeyboardMarkup(
                [[InlineKeyboardButton("✅ Marcado como revisado", callback_data="noop")]]
            )
            await query.edit_message_reply_markup(reply_markup=nuevo)

        elif query.data == "desbloquear":
            if self._overlay_callback:
                self._overlay_callback()
            nuevo = InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔓 Desbloqueado", callback_data="noop")]]
            )
            await query.edit_message_reply_markup(reply_markup=nuevo)
            await query.message.reply_text("🔓 Sistema desbloqueado remotamente.")
