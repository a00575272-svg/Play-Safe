import hashlib
import tkinter as tk
from tkinter import simpledialog


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class Overlay:
    def __init__(self, password_hash: str):
        self._password_hash = password_hash
        self._root: tk.Tk | None = None
        self._indicator: tk.Label | None = None
        self._blocker: tk.Toplevel | None = None
        self._locked = False
        self._drag_x = 0
        self._drag_y = 0

    # ── Inicio (hilo principal) ───────────────────────────────────────────────
    def iniciar(self):
        self._root = tk.Tk()
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 0.88)
        self._root.configure(bg="#1a1a2e")

        sw = self._root.winfo_screenwidth()
        self._root.geometry(f"180x44+{sw - 192}+12")

        self._indicator = tk.Label(
            self._root,
            text="🟢 Activo",
            bg="#1a1a2e",
            fg="#00e676",
            font=("Segoe UI", 11, "bold"),
            cursor="fleur",
            padx=8,
            pady=8,
        )
        self._indicator.pack(fill=tk.BOTH, expand=True)

        for widget in (self._root, self._indicator):
            widget.bind("<ButtonPress-1>", self._on_press)
            widget.bind("<B1-Motion>", self._on_drag)
            widget.bind("<Button-3>", self._show_menu)

        self._root.mainloop()

    # ── API pública (thread-safe) ─────────────────────────────────────────────
    def mostrar_alerta(self, tipo: str, razon: str):
        if self._root:
            self._root.after(0, lambda: self._bloquear_pantalla(tipo, razon))

    def unlock(self):
        if self._root:
            self._root.after(0, self._desbloquear)

    # ── Bloqueo de pantalla completa ──────────────────────────────────────────
    def _bloquear_pantalla(self, tipo: str, razon: str):
        if self._locked:
            return
        self._locked = True
        self._indicator.config(text="🔴 Bloqueado", fg="#ff5252")

        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()

        # Ventana que cubre toda la pantalla
        self._blocker = tk.Toplevel(self._root)
        self._blocker.overrideredirect(True)
        self._blocker.attributes("-topmost", True)
        self._blocker.attributes("-alpha", 0.96)
        self._blocker.configure(bg="#0d0d1a")
        self._blocker.geometry(f"{sw}x{sh}+0+0")

        # Bloquear Alt+F4 y cualquier cierre
        self._blocker.protocol("WM_DELETE_WINDOW", lambda: None)
        self._blocker.bind("<Alt-F4>", lambda e: "break")

        # ── Contenido centrado ────────────────────────────────────────────────
        frame = tk.Frame(self._blocker, bg="#0d0d1a")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            frame, text="🛡️", font=("Segoe UI", 72),
            bg="#0d0d1a", fg="white",
        ).pack(pady=(0, 10))

        tk.Label(
            frame,
            text="Pantalla bloqueada",
            font=("Segoe UI", 28, "bold"),
            bg="#0d0d1a", fg="#ff5252",
        ).pack()

        tk.Label(
            frame,
            text="Tus papás han sido notificados. 💙",
            font=("Segoe UI", 14),
            bg="#0d0d1a", fg="#aaaaff",
        ).pack(pady=(8, 4))

        tk.Label(
            frame,
            text=(
                "Recuerda: nunca compartas tu nombre, dirección,\n"
                "escuela, teléfono ni contraseñas con nadie en línea.\n"
                "¡Tu seguridad es lo más importante!"
            ),
            font=("Segoe UI", 11),
            bg="#0d0d1a", fg="#888888",
            justify="center",
        ).pack(pady=(0, 30))

        # Separador
        tk.Frame(frame, bg="#333355", height=1, width=400).pack(pady=(0, 20))

        # ── Zona de desbloqueo para el padre ─────────────────────────────────
        tk.Label(
            frame,
            text="Contraseña de padres para desbloquear:",
            font=("Segoe UI", 10),
            bg="#0d0d1a", fg="#666688",
        ).pack()

        pwd_var = tk.StringVar()
        pwd_entry = tk.Entry(
            frame,
            textvariable=pwd_var,
            show="●",
            font=("Segoe UI", 13),
            bg="#1e1e3a", fg="white",
            insertbackground="white",
            relief="flat",
            width=22,
            justify="center",
        )
        pwd_entry.pack(pady=(6, 8))
        pwd_entry.focus_set()

        error_lbl = tk.Label(
            frame, text="", font=("Segoe UI", 10),
            bg="#0d0d1a", fg="#ff5252",
        )
        error_lbl.pack()

        def _intentar_desbloqueo(event=None):
            if _sha256(pwd_var.get()) == self._password_hash:
                self._desbloquear()
            else:
                error_lbl.config(text="Contraseña incorrecta")
                pwd_var.set("")
                pwd_entry.focus_set()

        pwd_entry.bind("<Return>", _intentar_desbloqueo)

        tk.Button(
            frame,
            text="  Desbloquear  ",
            font=("Segoe UI", 11, "bold"),
            bg="#3a3a6e", fg="white",
            activebackground="#5a5a9e",
            relief="flat", cursor="hand2",
            padx=20, pady=8,
            command=_intentar_desbloqueo,
        ).pack(pady=(4, 0))

    # ── Desbloqueo ────────────────────────────────────────────────────────────
    def _desbloquear(self):
        self._locked = False
        self._indicator.config(text="🟢 Activo", fg="#00e676")
        if self._blocker and self._blocker.winfo_exists():
            self._blocker.destroy()
            self._blocker = None

    # ── Indicador pequeño — menú clic derecho ─────────────────────────────────
    def _show_menu(self, event: tk.Event):
        menu = tk.Menu(
            self._root, tearoff=0,
            bg="#1a1a2e", fg="white",
            activebackground="#3a3a5e", activeforeground="white",
            font=("Segoe UI", 9),
        )
        menu.add_command(label="🔓 Desbloquear", command=self._menu_unlock)
        menu.add_separator()
        menu.add_command(label="❌ Cerrar sistema", command=self._menu_close)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _menu_unlock(self):
        pwd = simpledialog.askstring(
            "🔓 Desbloquear", "Contraseña de padres:", show="*", parent=self._root
        )
        if pwd and _sha256(pwd) == self._password_hash:
            self._desbloquear()

    def _menu_close(self):
        pwd = simpledialog.askstring(
            "❌ Cerrar", "Contraseña para cerrar:", show="*", parent=self._root
        )
        if pwd and _sha256(pwd) == self._password_hash:
            self._root.destroy()

    # ── Arrastre del indicador ────────────────────────────────────────────────
    def _on_press(self, event: tk.Event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _on_drag(self, event: tk.Event):
        x = self._root.winfo_x() + event.x - self._drag_x
        y = self._root.winfo_y() + event.y - self._drag_y
        self._root.geometry(f"+{x}+{y}")
