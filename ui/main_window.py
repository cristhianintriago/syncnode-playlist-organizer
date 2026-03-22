"""
SyncNode — UI inspirada en Apple Music: negro profundo, acentos azules, tipografía clara.
"""

import customtkinter as ctk
from tkinter import messagebox, Canvas
import threading
import random
import json
import os

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

CONFIG_FILE = "config.json"

# Paleta tipo Apple Music (dark + azules)
C = {
    "bg":           "#000000",
    "bg_elevated":  "#0d0d0d",
    "bg2":          "#1c1c1e",
    "sidebar":      "#161616",
    "card":         "#1c1c1e",
    "card_h":       "#2c2c2e",
    "nav_sel":      "#2c2c2e",
    "nav_hover":    "#252528",
    "accent":       "#0A84FF",
    "accent_hover": "#64B5FF",
    "accent_muted": "#1a3a5c",
    "accent2":      "#5E5CE6",
    "text":         "#F5F5F7",
    "text_sec":     "#8E8E93",
    "separator":    "#38383a",
    "error":        "#FF453A",
    "success":      "#32D74B",
}

GEMS = {
    "Hip Hop / Rap":       "#5AC8FA",
    "Reggaeton / Latin":   "#0A84FF",
    "Pop":                 "#BF5AF2",
    "Rock":                "#64D2FF",
    "Electrónica / Dance": "#30D158",
    "R&B / Soul":          "#FF9F0A",
    "Indie / Alternativo": "#5E5CE6",
    "Folk / Country":      "#AC8E68",
    "Jazz / Clásica":      "#98989D",
    "Otros":               "#48484A",
}

def gem(nombre: str) -> str:
    for k, v in GEMS.items():
        if k in nombre:
            return v
    return GEMS["Otros"]


# ─────────────────────────────────────────────────────────────
# SPLASH SCREEN
# ─────────────────────────────────────────────────────────────

class SplashScreen(ctk.CTkToplevel):
    """
    Splash: partículas en canvas a pantalla completa; textos y barra con CTk
    centrados con place(anchor='center'). Evita el bug de Tk donde un canvas
    expandido alinea el dibujo (coord. fijas) a la izquierda del widget.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(fg_color=C["bg"])
        self.attributes("-topmost", True)

        W, H = 520, 380
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.resizable(False, False)

        self.W, self.H = W, H
        self._parts = [
            {
                "x": random.uniform(0, W),
                "y": random.uniform(0, H),
                "vx": random.uniform(-0.25, 0.25),
                "vy": random.uniform(-0.45, -0.08),
                "r": random.uniform(1, 2.2),
            }
            for _ in range(40)
        ]

        # Fondo: canvas solo para partículas (rellena el área del cliente)
        self.cv = Canvas(self, highlightthickness=0, bg=C["bg"])
        self.cv.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Contenido centrado en la ventana (no depende del sistema de coords. del canvas)
        box = ctk.CTkFrame(self, fg_color="transparent")
        box.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            box, text="♪", font=ctk.CTkFont("Segoe UI", 48),
            text_color=C["accent"], fg_color="transparent",
        ).pack()
        ctk.CTkLabel(
            box, text="SyncNode",
            font=ctk.CTkFont("Segoe UI", 22, weight="bold"),
            text_color=C["text"], fg_color="transparent",
        ).pack(pady=(4, 0))
        ctk.CTkLabel(
            box, text="Organiza tu música con Spotify",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=C["text_sec"], fg_color="transparent",
        ).pack(pady=(6, 0))

        self._prog = ctk.CTkProgressBar(
            box, width=280, height=5,
            fg_color=C["separator"],
            progress_color=C["accent"],
            corner_radius=3,
        )
        self._prog.pack(pady=(20, 8))
        self._prog.set(0)

        self._lbl_estado = ctk.CTkLabel(
            box, text="Iniciando…",
            font=ctk.CTkFont("Segoe UI", 10),
            text_color=C["text_sec"], fg_color="transparent",
        )
        self._lbl_estado.pack()

        self._animar()

    def _animar(self):
        if not self.winfo_exists():
            return
        try:
            W = max(2, self.cv.winfo_width())
            H = max(2, self.cv.winfo_height())
        except Exception:
            W, H = self.W, self.H
        self.W, self.H = W, H

        self.cv.delete("part")
        for p in self._parts:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            if p["y"] < -4:
                p["y"] = H + 4
                p["x"] = random.uniform(0, W)
            if not (0 <= p["x"] <= W):
                p["vx"] *= -1
            r = p["r"]
            self.cv.create_oval(
                p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r,
                fill=C["accent_muted"], outline="", tags="part",
            )

        self.after(32, self._animar)

    def actualizar(self, prog: float, msg: str):
        if not self.winfo_exists():
            return
        self._prog.set(min(prog, 1.0))
        self._lbl_estado.configure(text=msg)

    def cerrar(self):
        try:
            self.destroy()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────
# COMPONENTES
# ─────────────────────────────────────────────────────────────

class PrimaryBtn(ctk.CTkButton):
    def __init__(self, parent, **kw):
        kw.setdefault("fg_color", C["accent"])
        kw.setdefault("hover_color", C["accent_hover"])
        kw.setdefault("text_color", "#FFFFFF")
        kw.setdefault("font", ctk.CTkFont("Segoe UI", 12, weight="bold"))
        kw.setdefault("corner_radius", 22)
        kw.setdefault("height", 44)
        super().__init__(parent, **kw)


class SecondaryBtn(ctk.CTkButton):
    def __init__(self, parent, **kw):
        kw.setdefault("fg_color", "transparent")
        kw.setdefault("hover_color", C["nav_hover"])
        kw.setdefault("text_color", C["accent"])
        kw.setdefault("border_color", C["separator"])
        kw.setdefault("border_width", 1)
        kw.setdefault("font", ctk.CTkFont("Segoe UI", 11))
        kw.setdefault("corner_radius", 22)
        kw.setdefault("height", 36)
        super().__init__(parent, **kw)


class StatCard(ctk.CTkFrame):
    def __init__(self, parent, label: str, valor: str, color: str, **kw):
        super().__init__(parent, fg_color=C["bg2"], corner_radius=14,
                         border_width=0, **kw)
        ctk.CTkFrame(self, height=2, fg_color=color, corner_radius=0).pack(fill="x")
        ctk.CTkLabel(self, text=label, font=ctk.CTkFont("Segoe UI", 9),
                     text_color=C["text_sec"]).pack(anchor="w", padx=16, pady=(12, 2))
        self._v = ctk.CTkLabel(self, text=valor,
                                font=ctk.CTkFont("Segoe UI", 28, weight="bold"),
                                text_color=color)
        self._v.pack(anchor="w", padx=16, pady=(0, 14))

    def set(self, v: str):
        self._v.configure(text=v)


class GenreBar(ctk.CTkFrame):
    def __init__(self, parent, nombre: str, cantidad: int, total: int):
        super().__init__(parent, fg_color="transparent")
        self.columnconfigure(1, weight=1)
        color = gem(nombre)
        pct   = cantidad / total if total > 0 else 0
        label = (nombre[:25] + "…") if len(nombre) > 25 else nombre

        ctk.CTkLabel(self, text=label, font=ctk.CTkFont("Segoe UI", 11),
                     text_color=C["text"], width=165, anchor="w"
                     ).grid(row=0, column=0, padx=(0, 10))

        rail = ctk.CTkFrame(self, fg_color=C["separator"], corner_radius=2, height=5)
        rail.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        rail.grid_propagate(False)

        self._fill = ctk.CTkFrame(rail, fg_color=color, corner_radius=2, height=5)
        self._fill.place(relwidth=0, rely=0, relheight=1)
        self._tgt = pct
        self.after(60, self._tick)

        ctk.CTkLabel(self, text=f"{cantidad:,}",
                     font=ctk.CTkFont("Segoe UI", 11, weight="bold"),
                     text_color=color, width=55, anchor="e"
                     ).grid(row=0, column=2)

    def _tick(self, cur=0.0):
        if cur < self._tgt:
            cur = min(cur + 0.022, self._tgt)
            try:
                self._fill.place(relwidth=cur)
                self.after(14, self._tick, cur)
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────
# VENTANA PRINCIPAL
# ─────────────────────────────────────────────────────────────

class VentanaPrincipal(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SyncNode")
        self.geometry("1240x800")
        self.minsize(880, 620)
        self.configure(fg_color=C["bg"])

        self.controlador = None
        self.cbs_gen     = []
        self.cbs_art     = []
        self.sidebar     = None
        self._resize_after = None
        self._vista_actual = "conexion"
        self._nav_refs     = {}

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._mk_sidebar()
        self._mk_vistas()
        self._mk_footer()
        self._ir("conexion")

        self.bind("<Configure>", self._on_root_configure)

    def vincular_controlador(self, ctrl):
        self.controlador = ctrl
        if self.sidebar and hasattr(self, "sw_prueba"):
            if ctrl.spotify.modo_prueba:
                self.sw_prueba.select()
            else:
                self.sw_prueba.deselect()
            self._refresh_slider_prueba()

    def _on_root_configure(self, event):
        if event.widget is not self:
            return
        if self._resize_after is not None:
            self.after_cancel(self._resize_after)
        self._resize_after = self.after(120, self._apply_window_size)

    def _apply_window_size(self):
        self._resize_after = None
        w = self.winfo_width()
        if not self.sidebar:
            return
        if w < 1000:
            self.sidebar.configure(width=212)
        else:
            self.sidebar.configure(width=244)

    def _mk_footer(self):
        bar = ctk.CTkFrame(self, fg_color=C["sidebar"], corner_radius=0, height=40)
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)
        ctk.CTkLabel(
            bar,
            text="By Klyro — Derechos reservados",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=C["text_sec"],
        ).pack(side="right", padx=20, pady=10)
        ctk.CTkLabel(
            bar,
            text="Spotify",
            font=ctk.CTkFont("Segoe UI", 11),
            text_color=C["text_sec"],
        ).pack(side="left", padx=20, pady=10)

    def _persist_modo_prueba(self, activo: bool):
        if self.controlador:
            self.controlador.spotify.modo_prueba = activo
        try:
            path = CONFIG_FILE
            with open(path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            cfg["modo_prueba"] = activo
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        self._refresh_slider_prueba()

    def _refresh_slider_prueba(self):
        if not hasattr(self, "slider"):
            return
        prueba = (
            self.controlador.spotify.modo_prueba
            if self.controlador
            else False
        )
        if prueba:
            self.slider.configure(from_=10, to=40, number_of_steps=30)
            self.slider.set(min(int(self.slider.get()), 40))
            self.lbl_cant.configure(text=str(int(self.slider.get())))
        else:
            self.slider.configure(from_=10, to=200, number_of_steps=19)

    # ── SIDEBAR ──────────────────────────────

    def _mk_sidebar(self):
        sb = ctk.CTkFrame(self, width=244, fg_color=C["sidebar"], corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(7, weight=1)
        self.sidebar = sb

        lg = ctk.CTkFrame(sb, fg_color="transparent")
        lg.grid(row=0, column=0, sticky="ew", padx=20, pady=(28, 4))
        ctk.CTkLabel(lg, text="♪ ", font=ctk.CTkFont("Segoe UI", 20),
                     text_color=C["accent"]).pack(side="left")
        ctk.CTkLabel(lg, text="SyncNode", font=ctk.CTkFont("Segoe UI", 17, weight="bold"),
                     text_color=C["text"]).pack(side="left")

        ctk.CTkLabel(sb, text="BIBLIOTECA",
                     font=ctk.CTkFont("Segoe UI", 9),
                     text_color=C["text_sec"]
                     ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 12))

        nav = [
            ("🔗", "Conectar",       "conexion"),
            ("📚", "Biblioteca",     "biblioteca"),
            ("🔎", "Playlist por artista", "busqueda"),
            ("📊", "Estadísticas",   "stats"),
        ]
        self._nframes = {}
        for i, (ico, txt, vista) in enumerate(nav):
            f = self._nav_item(sb, ico, txt, vista)
            f.grid(row=3+i, column=0, sticky="ew", padx=12, pady=1)
            self._nframes[vista] = f

        ctk.CTkFrame(sb, height=1, fg_color=C["separator"]
                     ).grid(row=8, column=0, sticky="ew", padx=16, pady=12)

        pr = ctk.CTkFrame(sb, fg_color="transparent")
        pr.grid(row=9, column=0, sticky="ew", padx=18, pady=(0, 6))
        ctk.CTkLabel(pr, text="Modo prueba",
                     font=ctk.CTkFont("Segoe UI", 10),
                     text_color=C["text"], anchor="w").pack(anchor="w")
        ctk.CTkLabel(pr, text="Menos llamadas a la API de Spotify.",
                     font=ctk.CTkFont("Segoe UI", 9),
                     text_color=C["text_sec"], anchor="w").pack(anchor="w", pady=(2, 6))
        self.sw_prueba = ctk.CTkSwitch(
            pr, text="", width=42,
            fg_color=C["separator"], progress_color=C["accent"],
            button_color=C["text"], button_hover_color=C["text"],
            command=self._on_toggle_prueba,
        )
        self.sw_prueba.pack(anchor="w")

        self.lbl_user = ctk.CTkLabel(sb, text="Sin conectar",
                                      font=ctk.CTkFont("Segoe UI", 10),
                                      text_color=C["text_sec"])
        self.lbl_user.grid(row=10, column=0, sticky="w", padx=20, pady=(4, 22))

    def _on_toggle_prueba(self):
        activo = self.sw_prueba.get() == 1
        self._persist_modo_prueba(activo)

    def _nav_item(self, parent, ico, txt, vista):
        f = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=6, cursor="hand2")
        f.grid_columnconfigure(1, weight=1)

        def _in(_):
            if self._vista_actual != vista:
                f.configure(fg_color=C["nav_hover"])

        def _out(_):
            if self._vista_actual == vista:
                f.configure(fg_color=C["nav_sel"])
            else:
                f.configure(fg_color="transparent")

        def _clk(_=None):
            self._ir(vista)

        for w in (f,):
            w.bind("<Enter>", _in)
            w.bind("<Leave>", _out)
            w.bind("<Button-1>", _clk)

        ico_l = ctk.CTkLabel(
            f, text=ico, font=ctk.CTkFont("Segoe UI", 14),
            text_color=C["text_sec"], width=28,
        )
        ico_l.grid(row=0, column=0, padx=(8, 0), pady=6)
        lbl = ctk.CTkLabel(
            f, text=txt, font=ctk.CTkFont("Segoe UI", 11),
            text_color=C["text"], anchor="w",
        )
        lbl.grid(row=0, column=1, padx=(6, 10), sticky="w")
        for w in (ico_l, lbl):
            w.bind("<Enter>", _in)
            w.bind("<Leave>", _out)
            w.bind("<Button-1>", _clk)

        self._nav_refs[vista] = {"frame": f, "ico": ico_l, "txt": lbl}
        return f

    def _ir(self, nombre: str):
        self._vista_actual = nombre
        for v in self._vistas.values():
            v.grid_forget()
        self._vistas[nombre].grid(row=0, column=1, sticky="nsew")
        for k, ref in self._nav_refs.items():
            sel = k == nombre
            fr, ic, tx = ref["frame"], ref["ico"], ref["txt"]
            if sel:
                fr.configure(fg_color=C["nav_sel"])
                ic.configure(text_color=C["accent"])
                tx.configure(
                    text_color=C["accent"],
                    font=ctk.CTkFont("Segoe UI", 11, weight="bold"),
                )
            else:
                fr.configure(fg_color="transparent")
                ic.configure(text_color=C["text_sec"])
                tx.configure(
                    text_color=C["text"],
                    font=ctk.CTkFont("Segoe UI", 11),
                )

    # ── VISTAS ───────────────────────────────

    def _mk_vistas(self):
        self._vistas = {
            "conexion":   self._mk_conexion(),
            "biblioteca": self._mk_biblioteca(),
            "busqueda":   self._mk_busqueda(),
            "stats":      self._mk_stats(),
        }

    # ── CONEXIÓN ─────────────────────────────

    def _mk_conexion(self):
        v = ctk.CTkFrame(self, fg_color=C["bg"])
        v.grid_rowconfigure(0, weight=1)
        v.grid_columnconfigure(0, weight=1)

        box = ctk.CTkFrame(v, fg_color="transparent")
        box.place(relx=0.5, rely=0.5, anchor="center")

        self.ico_conn = ctk.CTkLabel(box, text="♪",
                                      font=ctk.CTkFont("Segoe UI", 72),
                                      text_color=C["accent"])
        self.ico_conn.pack()

        ctk.CTkLabel(box, text="SyncNode",
                     font=ctk.CTkFont("Segoe UI", 32, weight="bold"),
                     text_color=C["text"]).pack(pady=(4, 0))

        ctk.CTkLabel(box, text="Inicia sesión con Spotify para organizar tu biblioteca.",
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=C["text_sec"]).pack(pady=(6, 32))

        self.btn_conn = PrimaryBtn(
            box, text="  Conectar con Spotify  ",
            width=280, height=50,
            font=ctk.CTkFont("Segoe UI", 14, weight="bold"),
            command=self._conectar
        )
        self.btn_conn.pack()

        self.lbl_conn = ctk.CTkLabel(box, text="",
                                      font=ctk.CTkFont("Segoe UI", 11),
                                      text_color=C["text_sec"])
        self.lbl_conn.pack(pady=14)

        self._pulsar()
        return v

    def _pulsar(self):
        seq = [C["accent"], C["accent_hover"], C["accent"], C["accent_muted"]]
        i   = [0]
        def tick():
            try:
                self.ico_conn.configure(text_color=seq[i[0] % len(seq)])
                i[0] += 1
                self.after(900, tick)
            except Exception:
                pass
        tick()

    def _conectar(self):
        if not self.controlador: return
        self.btn_conn.configure(state="disabled", text="Conectando...")
        self.lbl_conn.configure(text="Abriendo navegador...", text_color=C["text_sec"])
        threading.Thread(target=self._t_conn, daemon=True).start()

    def _t_conn(self):
        try:
            u = self.controlador.spotify.autenticar()
            n = u.get("display_name") or u.get("id", "Usuario")
            self.after(0, lambda: self._conn_ok(n))
        except Exception as e:
            self.after(0, lambda err=e: self._conn_err(str(err)))

    def _conn_ok(self, nombre):
        self.lbl_user.configure(text=f"👤  {nombre}", text_color=C["accent"])
        self.btn_conn.configure(
            state="normal", text="✓  Conectado",
            fg_color="transparent", hover_color=C["nav_hover"],
            text_color=C["accent"], border_width=1, border_color=C["separator"]
        )
        self.lbl_conn.configure(
            text=f"Bienvenido, {nombre}. Sincroniza tu biblioteca.",
            text_color=C["accent"]
        )

    def _conn_err(self, msg):
        self.btn_conn.configure(state="normal", text="  Conectar con Spotify  ")
        self.lbl_conn.configure(text=f"Error: {msg[:72]}", text_color=C["error"])

    # ── BIBLIOTECA ───────────────────────────

    def _mk_biblioteca(self):
        v = ctk.CTkFrame(self, fg_color=C["bg"])
        v.grid_rowconfigure(3, weight=1)
        v.grid_columnconfigure((0, 1), weight=1)

        hdr = ctk.CTkFrame(v, fg_color="transparent")
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew", padx=40, pady=(36, 0))
        ctk.CTkLabel(hdr, text="Biblioteca",
                     font=ctk.CTkFont("Segoe UI", 32, weight="bold"),
                     text_color=C["text"]).pack(side="left")

        self.btn_sync = PrimaryBtn(hdr, text="Sincronizar",
                                 width=148, command=self._sync)
        self.btn_sync.pack(side="right")
        SecondaryBtn(hdr, text="Ninguno", width=88,
                 command=lambda: self._toggle(False)).pack(side="right", padx=(0, 8))
        SecondaryBtn(hdr, text="Todo", width=88,
                 command=lambda: self._toggle(True)).pack(side="right", padx=(0, 8))

        # Progreso
        self.bar_sync = ctk.CTkProgressBar(v, fg_color=C["separator"],
                                            progress_color=C["accent"],
                                            corner_radius=2, height=3)
        self.lbl_sync = ctk.CTkLabel(v, text="",
                                      font=ctk.CTkFont("Segoe UI", 10),
                                      text_color=C["text_sec"])

        ctk.CTkFrame(v, height=1, fg_color=C["separator"]
                     ).grid(row=2, column=0, columnspan=2,
                            sticky="ew", padx=40, pady=(20, 4))

        for col, txt in enumerate(["GÉNEROS", "ARTISTAS"]):
            ctk.CTkLabel(v, text=txt, font=ctk.CTkFont("Segoe UI", 11),
                         text_color=C["text_sec"]
                         ).grid(row=2, column=col, sticky="w",
                                padx=(40 if col == 0 else 16, 0), pady=(18, 6))

        self.scr_gen = ctk.CTkScrollableFrame(
            v, fg_color=C["bg2"], corner_radius=14, border_width=0,
            scrollbar_button_color=C["separator"],
            scrollbar_button_hover_color=C["accent_muted"])
        self.scr_gen.grid(row=3, column=0, sticky="nsew", padx=(40, 10), pady=4)

        self.scr_art = ctk.CTkScrollableFrame(
            v, fg_color=C["bg2"], corner_radius=14, border_width=0,
            scrollbar_button_color=C["separator"],
            scrollbar_button_hover_color=C["accent_muted"])
        self.scr_art.grid(row=3, column=1, sticky="nsew", padx=(10, 40), pady=4)

        foot = ctk.CTkFrame(v, fg_color="transparent")
        foot.grid(row=4, column=0, columnspan=2, sticky="ew", padx=40, pady=20)

        self.btn_crear = PrimaryBtn(foot, text="Crear playlists seleccionadas",
                                  width=280, height=48, command=self._crear)
        self.btn_crear.pack(side="right")

        self.bar_crear = ctk.CTkProgressBar(foot, fg_color=C["separator"],
                                             progress_color=C["accent"],
                                             corner_radius=2, height=3, width=260)
        self.lbl_crear = ctk.CTkLabel(foot, text="",
                                       font=ctk.CTkFont("Segoe UI", 10),
                                       text_color=C["text_sec"])
        return v

    def _sync(self):
        if not self.controlador:
            messagebox.showwarning("Aviso", "Primero conecta con Spotify.")
            return
        self.btn_sync.configure(state="disabled", text="Sincronizando…")
        self.bar_sync.grid(row=1, column=0, columnspan=2,
                           sticky="ew", padx=40, pady=(8, 0))
        self.bar_sync.set(0)
        self.lbl_sync.grid(row=1, column=0, columnspan=2)
        threading.Thread(target=self._t_sync, daemon=True).start()

    def _t_sync(self):
        try:
            def cb(p, m):
                self.after(0, lambda pp=p, mm=m: (
                    self.bar_sync.set(pp),
                    self.lbl_sync.configure(text=mm)
                ))
            self.controlador.cargar_biblioteca(cb)
            self.controlador.clasificar(cb)
            self.after(0, self._sync_ok)
        except Exception as e:
            self.after(0, lambda err=e: (
                messagebox.showerror("Error", str(err)),
                self.btn_sync.configure(state="normal", text="Sincronizar")
            ))

    def _sync_ok(self):
        g  = self.controlador.grupos
        gn = sorted(g.keys(), key=lambda x: -len(g[x]))
        at = sorted({a for items in g.values() for _, _, a in items if a})
        self._poblar(gn, at)
        self._actualizar_stats(self.controlador.calcular_estadisticas())
        self.bar_sync.grid_forget()
        self.lbl_sync.grid_forget()
        self.btn_sync.configure(state="normal", text="Sincronizar")
        total = sum(len(v) for v in g.values())
        messagebox.showinfo("Sincronización completa",
                            f"{total:,} canciones en {len(g)} géneros.")

    def _crear(self):
        gen = [cb.cget("text") for cb in self.cbs_gen if cb.get() == 1]
        art = [cb.cget("text") for cb in self.cbs_art if cb.get() == 1]
        if not gen and not art:
            messagebox.showwarning("Sin selección",
                                   "Selecciona al menos un género o artista.")
            return
        self.btn_crear.configure(state="disabled", text="Creando...")
        self.bar_crear.pack(side="right", padx=(0, 10))
        self.bar_crear.set(0)
        self.lbl_crear.pack(side="right", padx=(0, 8))
        threading.Thread(target=self._t_crear, args=(gen, art), daemon=True).start()

    def _t_crear(self, gen, art):
        try:
            def cb(p, m):
                self.after(0, lambda pp=p, mm=m: (
                    self.bar_crear.set(pp),
                    self.lbl_crear.configure(text=mm)
                ))
            if gen: self.controlador.crear_playlists_generos(gen, cb)
            if art: self.controlador.crear_playlists_artistas(art, cb)
            self.after(0, self._crear_ok)
        except Exception as e:
            self.after(0, lambda err=e: (
                messagebox.showerror("Error", str(err)),
                self._reset_crear()
            ))

    def _crear_ok(self):
        self._reset_crear()
        messagebox.showinfo("Listo", "Playlists creadas exitosamente en Spotify.")

    def _reset_crear(self):
        self.btn_crear.configure(state="normal",
                                  text="Crear playlists seleccionadas")
        self.bar_crear.pack_forget()
        self.lbl_crear.pack_forget()

    def _toggle(self, sel):
        for cb in self.cbs_gen + self.cbs_art:
            cb.select() if sel else cb.deselect()

    def _poblar(self, generos, artistas):
        for w in self.scr_gen.winfo_children(): w.destroy()
        for w in self.scr_art.winfo_children(): w.destroy()

        self.cbs_gen = []
        for g in generos:
            color = gem(g)
            row   = ctk.CTkFrame(self.scr_gen, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=3)
            cb = ctk.CTkCheckBox(row, text=g,
                                  font=ctk.CTkFont("Segoe UI", 11),
                                  text_color=C["text"],
                                  fg_color=color, hover_color=color,
                                  checkmark_color=C["bg"],
                                  border_color=C["separator"], corner_radius=3)
            cb.pack(side="left")
            cnt = len(self.controlador.grupos.get(g, []))
            ctk.CTkLabel(row, text=f"{cnt:,}",
                         font=ctk.CTkFont("Segoe UI", 10),
                         text_color=color).pack(side="right", padx=10)
            self.cbs_gen.append(cb)

        self.cbs_art = []
        for a in artistas[:300]:
            cb = ctk.CTkCheckBox(self.scr_art, text=a,
                                  font=ctk.CTkFont("Segoe UI", 11),
                                  text_color=C["text"],
                                  fg_color=C["accent_muted"],
                                  hover_color=C["accent"],
                                  checkmark_color=C["bg"],
                                  border_color=C["separator"], corner_radius=3)
            cb.pack(anchor="w", padx=10, pady=3)
            self.cbs_art.append(cb)

    # ── BÚSQUEDA ─────────────────────────────

    def _mk_busqueda(self):
        v = ctk.CTkFrame(self, fg_color=C["bg"])
        v.grid_columnconfigure(0, weight=1)
        v.grid_rowconfigure(3, weight=1)

        hdr = ctk.CTkFrame(v, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=40, pady=(36, 4))
        ctk.CTkLabel(hdr, text="Playlist por artista",
                     font=ctk.CTkFont("Segoe UI", 32, weight="bold"),
                     text_color=C["text"]).pack(side="left")

        ctk.CTkLabel(v,
                     text="Busca en Spotify o en tu biblioteca y crea una playlist al instante.",
                     font=ctk.CTkFont("Segoe UI", 13),
                     text_color=C["text_sec"]
                     ).grid(row=1, column=0, sticky="w", padx=40, pady=(0, 20))

        pnl = ctk.CTkFrame(v, fg_color=C["bg2"], corner_radius=16, border_width=0)
        pnl.grid(row=2, column=0, sticky="ew", padx=40, pady=(0, 16))
        pnl.grid_columnconfigure(1, weight=1)

        # Modo
        self.modo = ctk.StringVar(value="spotify")
        mr = ctk.CTkFrame(pnl, fg_color="transparent")
        mr.grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(18, 8))
        ctk.CTkLabel(mr, text="BUSCAR EN", font=ctk.CTkFont("Segoe UI", 8),
                     text_color=C["text_sec"]).pack(side="left", padx=(0, 14))
        for txt, val, col in [("Todo Spotify","spotify",C["accent"]),
                                ("Mi Biblioteca","biblioteca",C["accent2"])]:
            rb = ctk.CTkRadioButton(mr, text=txt, variable=self.modo, value=val,
                                     font=ctk.CTkFont("Segoe UI", 12),
                                     text_color=C["text"],
                                     fg_color=col, hover_color=col)
            rb.pack(side="left", padx=10)
            rb.configure(command=self._modo_chg)

        self.entry = ctk.CTkEntry(pnl, placeholder_text="Buscar por artista",
                                   font=ctk.CTkFont("Segoe UI", 14),
                                   fg_color=C["bg"], border_color=C["separator"],
                                   text_color=C["text"],
                                   placeholder_text_color=C["text_sec"],
                                   corner_radius=22, height=46)
        self.entry.grid(row=1, column=0, columnspan=2,
                        sticky="ew", padx=20, pady=(0, 8))
        self.entry.bind("<Return>", lambda e: self._buscar())

        self.btn_bus = PrimaryBtn(pnl, text="Buscar", width=120, height=46,
                                command=self._buscar)
        self.btn_bus.grid(row=1, column=2, padx=(0, 20), pady=(0, 8))

        self.row_cant = ctk.CTkFrame(pnl, fg_color="transparent")
        self.row_cant.grid(row=2, column=0, columnspan=3,
                           sticky="ew", padx=20, pady=(0, 18))
        ctk.CTkLabel(self.row_cant, text="CANTIDAD DE CANCIONES",
                     font=ctk.CTkFont("Segoe UI", 8),
                     text_color=C["text_sec"]).pack(side="left")
        self.lbl_cant = ctk.CTkLabel(self.row_cant, text="50",
                                      font=ctk.CTkFont("Segoe UI", 13, weight="bold"),
                                      text_color=C["accent"])
        self.lbl_cant.pack(side="right", padx=(0, 4))
        self.slider = ctk.CTkSlider(self.row_cant,
                                     from_=10, to=200, number_of_steps=19,
                                     fg_color=C["separator"],
                                     progress_color=C["accent_muted"],
                                     button_color=C["accent"],
                                     button_hover_color=C["accent_hover"],
                                     width=170,
                                     command=lambda v: self.lbl_cant.configure(
                                         text=str(int(v))))
        self.slider.set(50)
        self.slider.pack(side="right", padx=10)

        self.scr_res = ctk.CTkScrollableFrame(
            v, fg_color=C["bg2"], corner_radius=14, border_width=0,
            scrollbar_button_color=C["separator"],
            scrollbar_button_hover_color=C["accent_muted"])
        self.scr_res.grid(row=3, column=0, sticky="nsew", padx=40, pady=(0, 16))

        self.bar_bus = ctk.CTkProgressBar(v, fg_color=C["separator"],
                                           progress_color=C["accent"],
                                           corner_radius=2, height=3)
        self.lbl_bus_txt = ctk.CTkLabel(v, text="",
                                         font=ctk.CTkFont("Segoe UI", 10),
                                         text_color=C["text_sec"])
        return v

    def _modo_chg(self):
        if self.modo.get() == "biblioteca":
            self.row_cant.grid_remove()
        else:
            self.row_cant.grid()

    def _buscar(self):
        nombre = self.entry.get().strip()
        if not nombre or not self.controlador: return
        for w in self.scr_res.winfo_children(): w.destroy()

        if self.modo.get() == "biblioteca":
            uris = self.controlador.buscar_en_biblioteca(nombre)
            if uris:
                self._res_bib(nombre, uris)
            else:
                ctk.CTkLabel(self.scr_res,
                             text=f"No se encontró «{nombre}» en tu biblioteca.",
                             font=ctk.CTkFont("Segoe UI", 13),
                             text_color=C["text_sec"]).pack(pady=40)
        else:
            self.btn_bus.configure(state="disabled", text="...")
            threading.Thread(target=self._t_buscar,
                             args=(nombre,), daemon=True).start()

    def _t_buscar(self, nombre):
        try:
            arts = self.controlador.spotify.buscar_artista(nombre)
            self.after(0, lambda: self._mostrar_arts(arts))
        except Exception as e:
            self.after(0, lambda err=e: (
                messagebox.showerror("Error", str(err)),
                self.btn_bus.configure(state="normal", text="Buscar")
            ))

    def _mostrar_arts(self, artistas):
        self.btn_bus.configure(state="normal", text="Buscar")
        if not artistas:
            ctk.CTkLabel(self.scr_res, text="No se encontraron artistas.",
                         font=ctk.CTkFont("Segoe UI", 13),
                         text_color=C["text_sec"]).pack(pady=40)
            return

        for art in artistas:
            nombre  = art.get("name", "")
            sigs    = art.get("followers", {}).get("total", 0)
            generos = art.get("genres", [])
            g_str   = generos[0] if generos else "Género desconocido"

            card = ctk.CTkFrame(self.scr_res, fg_color=C["card_h"],
                                corner_radius=12,
                                border_width=0)
            card.pack(fill="x", padx=10, pady=5)
            card.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(card, text="🎵",
                         font=ctk.CTkFont("Segoe UI", 22), text_color=C["accent"]
                         ).grid(row=0, column=0, rowspan=2, padx=20, pady=14)
            ctk.CTkLabel(card, text=nombre,
                         font=ctk.CTkFont("Segoe UI", 14, weight="bold"),
                         text_color=C["text"], anchor="w"
                         ).grid(row=0, column=1, sticky="w", pady=(14, 2))
            ctk.CTkLabel(card,
                         text=f"{g_str}  ·  {sigs:,} seguidores",
                         font=ctk.CTkFont("Segoe UI", 10),
                         text_color=C["text_sec"], anchor="w"
                         ).grid(row=1, column=1, sticky="w", pady=(0, 14))

            PrimaryBtn(card, text="Crear playlist", width=148, height=40,
                    command=lambda a=art: self._crear_sp(a)
                    ).grid(row=0, column=2, rowspan=2, padx=18)

    def _crear_sp(self, art):
        nombre    = art["name"]
        artist_id = art["id"]
        cantidad  = int(self.slider.get())

        for w in self.scr_res.winfo_children():
            for btn in w.winfo_children():
                if isinstance(btn, ctk.CTkButton):
                    btn.configure(state="disabled")

        self.bar_bus.grid(row=4, column=0, sticky="ew", padx=40, pady=(0, 2))
        self.bar_bus.set(0)
        self.lbl_bus_txt.grid(row=5, column=0, padx=40, pady=(0, 8))
        self.lbl_bus_txt.configure(text=f"Explorando discografía de {nombre}...")

        threading.Thread(target=self._t_crear_sp,
                         args=(nombre, artist_id, cantidad), daemon=True).start()

    def _t_crear_sp(self, nombre, artist_id, cantidad):
        try:
            def cb(p, m):
                self.after(0, lambda pp=p, mm=m: (
                    self.bar_bus.set(pp),
                    self.lbl_bus_txt.configure(text=mm)
                ))
            uris = self.controlador.spotify.obtener_canciones_artista_spotify(
                artist_id, cantidad, cb)
            if not uris:
                self.after(0, lambda: messagebox.showwarning(
                    "Sin canciones", f"No se encontraron canciones de {nombre}."))
                return
            pls = self.controlador.spotify.obtener_playlists_usuario()
            self.controlador.spotify.crear_o_actualizar_playlist(
                nombre, uris, pls, callback=cb)
            self.after(0, lambda: self._bus_ok(nombre, len(uris)))
        except Exception as e:
            self.after(0, lambda err=e: (
                messagebox.showerror("Error", str(err)),
                self._reset_bus()
            ))

    def _res_bib(self, nombre, uris):
        card = ctk.CTkFrame(self.scr_res, fg_color=C["card_h"],
                            corner_radius=12,
                            border_width=0)
        card.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(card, text=f"🎵  {nombre}",
                     font=ctk.CTkFont("Segoe UI", 15, weight="bold"),
                     text_color=C["text"]).pack(anchor="w", padx=20, pady=(18, 4))
        ctk.CTkLabel(card,
                     text=f"{len(uris)} canciones encontradas en tu biblioteca",
                     font=ctk.CTkFont("Segoe UI", 11),
                     text_color=C["text_sec"]).pack(anchor="w", padx=20)
        PrimaryBtn(card, text="Crear playlist", width=168, height=40,
                command=lambda: threading.Thread(
                    target=self._t_bib, args=(nombre, uris), daemon=True
                ).start()).pack(anchor="w", padx=20, pady=16)

    def _t_bib(self, nombre, uris):
        try:
            pls = self.controlador.spotify.obtener_playlists_usuario()
            self.controlador.spotify.crear_o_actualizar_playlist(nombre, uris, pls)
            self.after(0, lambda: messagebox.showinfo(
                "Listo", f"Playlist de {nombre}: {len(uris)} canciones."))
        except Exception as e:
            self.after(0, lambda err=e: messagebox.showerror("Error", str(err)))

    def _bus_ok(self, nombre, cant):
        self._reset_bus()
        messagebox.showinfo("Playlist creada",
                            f"◈  {nombre}\n{cant} canciones añadidas a Spotify.")

    def _reset_bus(self):
        self.bar_bus.grid_forget()
        self.lbl_bus_txt.grid_forget()
        for w in self.scr_res.winfo_children():
            for btn in w.winfo_children():
                if isinstance(btn, ctk.CTkButton):
                    btn.configure(state="normal")

    # ── ESTADÍSTICAS ─────────────────────────

    def _mk_stats(self):
        v = ctk.CTkFrame(self, fg_color=C["bg"])
        v.grid_columnconfigure((0, 1, 2), weight=1)
        v.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(v, text="Estadísticas",
                     font=ctk.CTkFont("Segoe UI", 32, weight="bold"),
                     text_color=C["text"]
                     ).grid(row=0, column=0, columnspan=3,
                            sticky="w", padx=40, pady=(36, 20))

        self.sc_tot = StatCard(v, "CANCIONES",  "—", C["accent"])
        self.sc_gen = StatCard(v, "GÉNEROS",    "—", C["accent2"])
        self.sc_art = StatCard(v, "ARTISTAS",   "—", C["accent_hover"])
        self.sc_tot.grid(row=1, column=0, padx=(40, 8),  pady=(0, 16), sticky="ew")
        self.sc_gen.grid(row=1, column=1, padx=8,         pady=(0, 16), sticky="ew")
        self.sc_art.grid(row=1, column=2, padx=(8, 40),   pady=(0, 16), sticky="ew")

        self.pnl_gen = ctk.CTkScrollableFrame(
            v, fg_color=C["bg2"], corner_radius=14, border_width=0,
            label_text="Distribución por género",
            label_font=ctk.CTkFont("Segoe UI", 11),
            label_text_color=C["text_sec"],
            scrollbar_button_color=C["separator"],
            scrollbar_button_hover_color=C["accent_muted"])
        self.pnl_gen.grid(row=2, column=0, columnspan=2,
                          padx=(40, 8), pady=(0, 28), sticky="nsew")

        self.pnl_top = ctk.CTkScrollableFrame(
            v, fg_color=C["bg2"], corner_radius=14, border_width=0,
            label_text="Artistas más frecuentes",
            label_font=ctk.CTkFont("Segoe UI", 11),
            label_text_color=C["text_sec"],
            scrollbar_button_color=C["separator"],
            scrollbar_button_hover_color=C["accent_muted"])
        self.pnl_top.grid(row=2, column=2,
                          padx=(8, 40), pady=(0, 28), sticky="nsew")
        return v

    def _actualizar_stats(self, stats):
        if not stats: return
        total = stats.get("total", 0)
        tops  = stats.get("top_artistas", [])

        self.sc_tot.set(f"{total:,}")
        self.sc_gen.set(str(stats.get("total_generos", 0)))
        self.sc_art.set(str(len(tops)))

        for w in self.pnl_gen.winfo_children(): w.destroy()
        for genero, cnt in stats.get("generos", []):
            GenreBar(self.pnl_gen, genero, cnt, total).pack(
                fill="x", padx=16, pady=6)

        for w in self.pnl_top.winfo_children(): w.destroy()
        medallas = ["◆", "◇", "◈"]
        for i, (artista, cnt) in enumerate(tops):
            row = ctk.CTkFrame(self.pnl_top, fg_color=C["card_h"], corner_radius=8)
            row.pack(fill="x", padx=8, pady=3)
            row.grid_columnconfigure(1, weight=1)

            med   = medallas[i] if i < 3 else str(i+1)
            color = C["accent"] if i == 0 else (C["accent_muted"] if i < 3 else C["text_sec"])

            ctk.CTkLabel(row, text=med,
                         font=ctk.CTkFont("Segoe UI", 13, weight="bold"),
                         text_color=color, width=30
                         ).grid(row=0, column=0, padx=(12, 0), pady=10)
            ctk.CTkLabel(row,
                         text=(artista[:23]+"…") if len(artista)>23 else artista,
                         font=ctk.CTkFont("Segoe UI", 12),
                         text_color=C["text"], anchor="w"
                         ).grid(row=0, column=1, sticky="w", padx=8)
            ctk.CTkLabel(row, text=str(cnt),
                         font=ctk.CTkFont("Segoe UI", 13, weight="bold"),
                         text_color=C["text_sec"]
                         ).grid(row=0, column=2, padx=12)


# ─────────────────────────────────────────────────────────────
# SPLASH HELPER
# ─────────────────────────────────────────────────────────────

def lanzar_con_splash(app: VentanaPrincipal):
    # Ocultar ventana principal hasta que termine el splash
    app.withdraw()

    splash = SplashScreen(app)
    pasos  = [
        (0.20, "Cargando configuración..."),
        (0.45, "Preparando Spotify..."),
        (0.70, "Montando la interfaz..."),
        (0.92, "Casi listo..."),
        (1.00, "¡Listo!"),
    ]

    def paso(i=0):
        if i < len(pasos):
            splash.actualizar(*pasos[i])
            splash.after(460, paso, i+1)
        else:
            splash.after(500, _mostrar_app)

    def _mostrar_app():
        splash.cerrar()
        app.deiconify()
        app.lift()

    splash.after(150, paso)
