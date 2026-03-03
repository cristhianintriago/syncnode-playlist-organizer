"""
SyncNode 2.0 — Premium UI
Estética: Luxury dark, oro/champagne sobre negro profundo.
Animaciones: Partículas en splash, barras animadas, fade de nav.
"""

import customtkinter as ctk
from tkinter import messagebox, Canvas
import threading
import random

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# ─────────────────────────────────────────────────────────────
# PALETA PREMIUM
# ─────────────────────────────────────────────────────────────
C = {
    "bg":         "#080810",
    "bg2":        "#0D0D1A",
    "sidebar":    "#06060E",
    "card":       "#0F0F1E",
    "card_h":     "#14142A",
    "oro":        "#C9A84C",
    "oro_claro":  "#E2C97E",
    "oro_oscuro": "#7A5C10",
    "blanco":     "#EDE8E0",
    "gris":       "#64648A",
    "gris2":      "#2A2A42",
    "acento":     "#6B4FA0",
    "error":      "#A93226",
    "verde":      "#1DB954",
}

GEMS = {
    "Hip Hop / Rap":       "#C9940A",
    "Reggaeton / Latin":   "#B03A2E",
    "Pop":                 "#7D3C98",
    "Rock":                "#1F618D",
    "Electrónica / Dance": "#117864",
    "R&B / Soul":          "#CA6F1E",
    "Indie / Alternativo": "#1E8449",
    "Folk / Country":      "#7D6608",
    "Jazz / Clásica":      "#154360",
    "Otros":               "#424268",
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
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        self.configure(fg_color=C["bg"])
        self.attributes("-topmost", True)

        W, H = 500, 360
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

        self.W, self.H = W, H
        self.cv = Canvas(self, width=W, height=H, bg=C["bg"], highlightthickness=0)
        self.cv.pack(fill="both", expand=True)

        # Partículas
        self._parts = [
            {
                "x": random.uniform(0, W),
                "y": random.uniform(0, H),
                "vx": random.uniform(-0.3, 0.3),
                "vy": random.uniform(-0.5, -0.1),
                "r": random.uniform(1, 2.5),
            }
            for _ in range(45)
        ]

        # Elementos fijos
        self.cv.create_text(W//2, 110, text="◈", font=("Georgia", 64),
                            fill=C["oro"], tags="fijo")
        self.cv.create_text(W//2, 185, text="SYNCNODE",
                            font=("Georgia", 30, "bold"),
                            fill=C["blanco"], tags="fijo")
        self.cv.create_text(W//2, 215, text="Tu música. Organizada con elegancia.",
                            font=("Helvetica", 11), fill=C["gris"], tags="fijo")

        # Líneas decorativas
        self.cv.create_line(60, 155, 190, 155, fill=C["oro_oscuro"], width=1, tags="fijo")
        self.cv.create_line(310, 155, 440, 155, fill=C["oro_oscuro"], width=1, tags="fijo")

        # Barra progreso
        self.cv.create_rectangle(80, 270, 420, 278,
                                  fill=C["gris2"], outline="", tags="fijo")
        self._barra = self.cv.create_rectangle(80, 270, 80, 278,
                                                fill=C["oro"], outline="")
        self._txt   = self.cv.create_text(W//2, 295, text="Iniciando...",
                                           font=("Helvetica", 10), fill=C["gris"])

        self._animar()

    def _animar(self):
        if not self.winfo_exists():
            return
        W, H = self.W, self.H
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
            self.cv.create_oval(p["x"]-r, p["y"]-r, p["x"]+r, p["y"]+r,
                                 fill=C["oro_oscuro"], outline="", tags="part")

        self.cv.tag_raise("fijo")
        self.cv.tag_raise(self._barra)
        self.cv.tag_raise(self._txt)
        self.after(30, self._animar)

    def actualizar(self, prog: float, msg: str):
        if not self.winfo_exists():
            return
        x = 80 + (340 * min(prog, 1.0))
        self.cv.coords(self._barra, 80, 270, x, 278)
        self.cv.itemconfig(self._txt, text=msg)

    def cerrar(self):
        try:
            self.destroy()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────
# COMPONENTES
# ─────────────────────────────────────────────────────────────

class GoldBtn(ctk.CTkButton):
    def __init__(self, parent, **kw):
        kw.setdefault("fg_color", C["oro"])
        kw.setdefault("hover_color", C["oro_claro"])
        kw.setdefault("text_color", C["bg"])
        kw.setdefault("font", ctk.CTkFont("Helvetica", 12, weight="bold"))
        kw.setdefault("corner_radius", 6)
        kw.setdefault("height", 40)
        super().__init__(parent, **kw)


class GhostBtn(ctk.CTkButton):
    def __init__(self, parent, **kw):
        kw.setdefault("fg_color", "transparent")
        kw.setdefault("hover_color", C["card_h"])
        kw.setdefault("text_color", C["oro"])
        kw.setdefault("border_color", C["oro_oscuro"])
        kw.setdefault("border_width", 1)
        kw.setdefault("font", ctk.CTkFont("Helvetica", 11))
        kw.setdefault("corner_radius", 6)
        kw.setdefault("height", 34)
        super().__init__(parent, **kw)


class StatCard(ctk.CTkFrame):
    def __init__(self, parent, label: str, valor: str, color: str, **kw):
        super().__init__(parent, fg_color=C["card"], corner_radius=10,
                         border_width=1, border_color=C["gris2"], **kw)
        ctk.CTkFrame(self, height=2, fg_color=color, corner_radius=0).pack(fill="x")
        ctk.CTkLabel(self, text=label, font=ctk.CTkFont("Helvetica", 9),
                     text_color=C["gris"]).pack(anchor="w", padx=16, pady=(12, 2))
        self._v = ctk.CTkLabel(self, text=valor,
                                font=ctk.CTkFont("Georgia", 28, weight="bold"),
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

        ctk.CTkLabel(self, text=label, font=ctk.CTkFont("Helvetica", 11),
                     text_color=C["blanco"], width=165, anchor="w"
                     ).grid(row=0, column=0, padx=(0, 10))

        rail = ctk.CTkFrame(self, fg_color=C["gris2"], corner_radius=2, height=5)
        rail.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        rail.grid_propagate(False)

        self._fill = ctk.CTkFrame(rail, fg_color=color, corner_radius=2, height=5)
        self._fill.place(relwidth=0, rely=0, relheight=1)
        self._tgt = pct
        self.after(60, self._tick)

        ctk.CTkLabel(self, text=f"{cantidad:,}",
                     font=ctk.CTkFont("Helvetica", 11, weight="bold"),
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
        self.title("SyncNode 2.0")
        self.geometry("1240x800")
        self.minsize(1040, 700)
        self.configure(fg_color=C["bg"])

        self.controlador = None
        self.cbs_gen     = []
        self.cbs_art     = []

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._mk_sidebar()
        self._mk_vistas()
        self._ir("conexion")

    def vincular_controlador(self, ctrl):
        self.controlador = ctrl

    # ── SIDEBAR ──────────────────────────────

    def _mk_sidebar(self):
        sb = ctk.CTkFrame(self, width=232, fg_color=C["sidebar"], corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(7, weight=1)

        # Logo
        lg = ctk.CTkFrame(sb, fg_color="transparent")
        lg.grid(row=0, column=0, sticky="ew", padx=22, pady=(34, 2))
        ctk.CTkLabel(lg, text="◈ ", font=ctk.CTkFont("Georgia", 24),
                     text_color=C["oro"]).pack(side="left")
        ctk.CTkLabel(lg, text="SYNCNODE", font=ctk.CTkFont("Georgia", 17, weight="bold"),
                     text_color=C["blanco"]).pack(side="left")

        ctk.CTkLabel(sb, text="M U S I C   O R G A N I Z E R",
                     font=ctk.CTkFont("Helvetica", 7),
                     text_color=C["oro_oscuro"]
                     ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 22))

        ctk.CTkFrame(sb, height=1, fg_color=C["gris2"]
                     ).grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))

        nav = [
            ("⬡", "Conectar",       "conexion"),
            ("▦", "Biblioteca",     "biblioteca"),
            ("◎", "Buscar Artista", "busqueda"),
            ("◈", "Estadísticas",   "stats"),
        ]
        self._nframes = {}
        for i, (ico, txt, vista) in enumerate(nav):
            f = self._nav_item(sb, ico, txt, vista)
            f.grid(row=3+i, column=0, sticky="ew", padx=10, pady=2)
            self._nframes[vista] = f

        ctk.CTkFrame(sb, height=1, fg_color=C["gris2"]
                     ).grid(row=8, column=0, sticky="ew", padx=18, pady=10)

        self.lbl_user = ctk.CTkLabel(sb, text="Sin conectar",
                                      font=ctk.CTkFont("Helvetica", 10),
                                      text_color=C["gris"])
        self.lbl_user.grid(row=9, column=0, sticky="w", padx=22, pady=(4, 28))

    def _nav_item(self, parent, ico, txt, vista):
        f = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=8, cursor="hand2")
        f.grid_columnconfigure(1, weight=1)

        def _in(e):  f.configure(fg_color=C["card"])
        def _out(e): f.configure(fg_color="transparent")
        def _clk(e=None): self._ir(vista)

        f.bind("<Enter>", _in); f.bind("<Leave>", _out); f.bind("<Button-1>", _clk)

        ctk.CTkLabel(f, text=ico, font=ctk.CTkFont("Georgia", 14),
                     text_color=C["oro"], width=26
                     ).grid(row=0, column=0, padx=(12, 0), pady=10)
        lbl = ctk.CTkLabel(f, text=txt, font=ctk.CTkFont("Helvetica", 12),
                            text_color=C["blanco"], anchor="w")
        lbl.grid(row=0, column=1, padx=(8, 12), sticky="w")
        lbl.bind("<Button-1>", _clk)
        return f

    def _ir(self, nombre: str):
        for v in self._vistas.values():
            v.grid_forget()
        self._vistas[nombre].grid(row=0, column=1, sticky="nsew")
        for k, f in self._nframes.items():
            activo = k == nombre
            f.configure(
                fg_color=C["card"] if activo else "transparent",
                border_width=1 if activo else 0,
                border_color=C["oro_oscuro"] if activo else C["card"]
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
        box.place(relx=0.5, rely=0.46, anchor="center")

        self.ico_conn = ctk.CTkLabel(box, text="◈",
                                      font=ctk.CTkFont("Georgia", 90),
                                      text_color=C["oro"])
        self.ico_conn.pack()

        ctk.CTkLabel(box, text="SYNCNODE",
                     font=ctk.CTkFont("Georgia", 38, weight="bold"),
                     text_color=C["blanco"]).pack(pady=(2, 0))

        ctk.CTkLabel(box, text="Tu música. Organizada con elegancia.",
                     font=ctk.CTkFont("Helvetica", 13),
                     text_color=C["gris"]).pack(pady=(6, 36))

        # Líneas decorativas
        deco = ctk.CTkFrame(box, fg_color="transparent")
        deco.pack(pady=(0, 30))
        ctk.CTkFrame(deco, width=70, height=1, fg_color=C["oro_oscuro"]).pack(side="left")
        ctk.CTkLabel(deco, text="  ◆  ", font=ctk.CTkFont("Georgia", 9),
                     text_color=C["oro_oscuro"]).pack(side="left")
        ctk.CTkFrame(deco, width=70, height=1, fg_color=C["oro_oscuro"]).pack(side="left")

        self.btn_conn = GoldBtn(
            box, text="  Conectar con Spotify  ",
            width=270, height=50,
            font=ctk.CTkFont("Helvetica", 14, weight="bold"),
            command=self._conectar
        )
        self.btn_conn.pack()

        self.lbl_conn = ctk.CTkLabel(box, text="",
                                      font=ctk.CTkFont("Helvetica", 11),
                                      text_color=C["gris"])
        self.lbl_conn.pack(pady=12)

        self._pulsar()
        return v

    def _pulsar(self):
        seq = [C["oro"], C["oro_claro"], C["oro"], C["oro_oscuro"]]
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
        self.lbl_conn.configure(text="Abriendo navegador...", text_color=C["gris"])
        threading.Thread(target=self._t_conn, daemon=True).start()

    def _t_conn(self):
        try:
            u = self.controlador.spotify.autenticar()
            n = u.get("display_name") or u.get("id", "Usuario")
            self.after(0, lambda: self._conn_ok(n))
        except Exception as e:
            self.after(0, lambda err=e: self._conn_err(str(err)))

    def _conn_ok(self, nombre):
        self.lbl_user.configure(text=f"◆  {nombre}", text_color=C["oro"])
        self.btn_conn.configure(
            state="normal", text="✓  Conectado",
            fg_color="transparent", hover_color=C["card_h"],
            text_color=C["oro"], border_width=1, border_color=C["oro_oscuro"]
        )
        self.lbl_conn.configure(
            text=f"Bienvenido, {nombre}. Sincroniza tu biblioteca.",
            text_color=C["oro"]
        )

    def _conn_err(self, msg):
        self.btn_conn.configure(state="normal", text="  Conectar con Spotify  ")
        self.lbl_conn.configure(text=f"Error: {msg[:72]}", text_color=C["error"])

    # ── BIBLIOTECA ───────────────────────────

    def _mk_biblioteca(self):
        v = ctk.CTkFrame(self, fg_color=C["bg"])
        v.grid_rowconfigure(3, weight=1)
        v.grid_columnconfigure((0, 1), weight=1)

        # Header
        hdr = ctk.CTkFrame(v, fg_color="transparent")
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew", padx=32, pady=(28, 0))
        ctk.CTkLabel(hdr, text="Biblioteca",
                     font=ctk.CTkFont("Georgia", 26, weight="bold"),
                     text_color=C["blanco"]).pack(side="left")

        self.btn_sync = GoldBtn(hdr, text="⟳  Sincronizar",
                                 width=140, command=self._sync)
        self.btn_sync.pack(side="right")
        GhostBtn(hdr, text="Desel.", width=82,
                 command=lambda: self._toggle(False)).pack(side="right", padx=(0, 6))
        GhostBtn(hdr, text="Sel. Todo", width=94,
                 command=lambda: self._toggle(True)).pack(side="right", padx=(0, 6))

        # Progreso
        self.bar_sync = ctk.CTkProgressBar(v, fg_color=C["gris2"],
                                            progress_color=C["oro"],
                                            corner_radius=2, height=3)
        self.lbl_sync = ctk.CTkLabel(v, text="",
                                      font=ctk.CTkFont("Helvetica", 10),
                                      text_color=C["gris"])

        ctk.CTkFrame(v, height=1, fg_color=C["gris2"]
                     ).grid(row=2, column=0, columnspan=2,
                            sticky="ew", padx=32, pady=(12, 4))

        for col, txt in enumerate(["GÉNEROS", "ARTISTAS"]):
            ctk.CTkLabel(v, text=txt, font=ctk.CTkFont("Helvetica", 8),
                         text_color=C["gris"]
                         ).grid(row=2, column=col, sticky="w",
                                padx=(32 if col == 0 else 14, 0), pady=(16, 2))

        self.scr_gen = ctk.CTkScrollableFrame(
            v, fg_color=C["card"], corner_radius=10,
            scrollbar_button_color=C["gris2"],
            scrollbar_button_hover_color=C["oro_oscuro"])
        self.scr_gen.grid(row=3, column=0, sticky="nsew", padx=(32, 8), pady=4)

        self.scr_art = ctk.CTkScrollableFrame(
            v, fg_color=C["card"], corner_radius=10,
            scrollbar_button_color=C["gris2"],
            scrollbar_button_hover_color=C["oro_oscuro"])
        self.scr_art.grid(row=3, column=1, sticky="nsew", padx=(8, 32), pady=4)

        # Footer
        foot = ctk.CTkFrame(v, fg_color="transparent")
        foot.grid(row=4, column=0, columnspan=2, sticky="ew", padx=32, pady=16)

        self.btn_crear = GoldBtn(foot, text="Crear Playlists Seleccionadas",
                                  width=270, height=44, command=self._crear)
        self.btn_crear.pack(side="right")

        self.bar_crear = ctk.CTkProgressBar(foot, fg_color=C["gris2"],
                                             progress_color=C["oro"],
                                             corner_radius=2, height=3, width=260)
        self.lbl_crear = ctk.CTkLabel(foot, text="",
                                       font=ctk.CTkFont("Helvetica", 10),
                                       text_color=C["gris"])
        return v

    def _sync(self):
        if not self.controlador:
            messagebox.showwarning("Aviso", "Primero conecta con Spotify.")
            return
        self.btn_sync.configure(state="disabled", text="⟳  Sincronizando...")
        self.bar_sync.grid(row=1, column=0, columnspan=2,
                           sticky="ew", padx=32, pady=(8, 0))
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
                self.btn_sync.configure(state="normal", text="⟳  Sincronizar")
            ))

    def _sync_ok(self):
        g  = self.controlador.grupos
        gn = sorted(g.keys(), key=lambda x: -len(g[x]))
        at = sorted({a for items in g.values() for _, _, a in items if a})
        self._poblar(gn, at)
        self._actualizar_stats(self.controlador.calcular_estadisticas())
        self.bar_sync.grid_forget()
        self.lbl_sync.grid_forget()
        self.btn_sync.configure(state="normal", text="⟳  Sincronizar")
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
                                  text="Crear Playlists Seleccionadas")
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
                                  font=ctk.CTkFont("Helvetica", 11),
                                  text_color=C["blanco"],
                                  fg_color=color, hover_color=color,
                                  checkmark_color=C["bg"],
                                  border_color=C["gris2"], corner_radius=3)
            cb.pack(side="left")
            cnt = len(self.controlador.grupos.get(g, []))
            ctk.CTkLabel(row, text=f"{cnt:,}",
                         font=ctk.CTkFont("Helvetica", 10),
                         text_color=color).pack(side="right", padx=10)
            self.cbs_gen.append(cb)

        self.cbs_art = []
        for a in artistas[:300]:
            cb = ctk.CTkCheckBox(self.scr_art, text=a,
                                  font=ctk.CTkFont("Helvetica", 11),
                                  text_color=C["blanco"],
                                  fg_color=C["oro_oscuro"],
                                  hover_color=C["oro"],
                                  checkmark_color=C["bg"],
                                  border_color=C["gris2"], corner_radius=3)
            cb.pack(anchor="w", padx=10, pady=3)
            self.cbs_art.append(cb)

    # ── BÚSQUEDA ─────────────────────────────

    def _mk_busqueda(self):
        v = ctk.CTkFrame(self, fg_color=C["bg"])
        v.grid_columnconfigure(0, weight=1)
        v.grid_rowconfigure(3, weight=1)

        hdr = ctk.CTkFrame(v, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=32, pady=(28, 4))
        ctk.CTkLabel(hdr, text="Buscar Artista",
                     font=ctk.CTkFont("Georgia", 26, weight="bold"),
                     text_color=C["blanco"]).pack(side="left")

        ctk.CTkLabel(v,
                     text="Crea una playlist con la discografía completa de cualquier artista",
                     font=ctk.CTkFont("Helvetica", 12),
                     text_color=C["gris"]
                     ).grid(row=1, column=0, sticky="w", padx=32, pady=(0, 16))

        # Panel
        pnl = ctk.CTkFrame(v, fg_color=C["card"], corner_radius=12)
        pnl.grid(row=2, column=0, sticky="ew", padx=32, pady=(0, 16))
        pnl.grid_columnconfigure(1, weight=1)

        # Modo
        self.modo = ctk.StringVar(value="spotify")
        mr = ctk.CTkFrame(pnl, fg_color="transparent")
        mr.grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(18, 8))
        ctk.CTkLabel(mr, text="BUSCAR EN", font=ctk.CTkFont("Helvetica", 8),
                     text_color=C["gris"]).pack(side="left", padx=(0, 14))
        for txt, val, col in [("Todo Spotify","spotify",C["oro"]),
                                ("Mi Biblioteca","biblioteca",C["acento"])]:
            rb = ctk.CTkRadioButton(mr, text=txt, variable=self.modo, value=val,
                                     font=ctk.CTkFont("Helvetica", 12),
                                     text_color=C["blanco"],
                                     fg_color=col, hover_color=col)
            rb.pack(side="left", padx=10)
            rb.configure(command=self._modo_chg)

        self.entry = ctk.CTkEntry(pnl, placeholder_text="Nombre del artista...",
                                   font=ctk.CTkFont("Helvetica", 13),
                                   fg_color=C["bg2"], border_color=C["gris2"],
                                   text_color=C["blanco"],
                                   placeholder_text_color=C["gris"],
                                   corner_radius=6, height=42)
        self.entry.grid(row=1, column=0, columnspan=2,
                        sticky="ew", padx=20, pady=(0, 8))
        self.entry.bind("<Return>", lambda e: self._buscar())

        self.btn_bus = GoldBtn(pnl, text="Buscar", width=110, height=42,
                                command=self._buscar)
        self.btn_bus.grid(row=1, column=2, padx=(0, 20), pady=(0, 8))

        self.row_cant = ctk.CTkFrame(pnl, fg_color="transparent")
        self.row_cant.grid(row=2, column=0, columnspan=3,
                           sticky="ew", padx=20, pady=(0, 18))
        ctk.CTkLabel(self.row_cant, text="CANTIDAD DE CANCIONES",
                     font=ctk.CTkFont("Helvetica", 8),
                     text_color=C["gris"]).pack(side="left")
        self.lbl_cant = ctk.CTkLabel(self.row_cant, text="50",
                                      font=ctk.CTkFont("Georgia", 13, weight="bold"),
                                      text_color=C["oro"])
        self.lbl_cant.pack(side="right", padx=(0, 4))
        self.slider = ctk.CTkSlider(self.row_cant,
                                     from_=10, to=200, number_of_steps=19,
                                     fg_color=C["gris2"],
                                     progress_color=C["oro_oscuro"],
                                     button_color=C["oro"],
                                     button_hover_color=C["oro_claro"],
                                     width=170,
                                     command=lambda v: self.lbl_cant.configure(
                                         text=str(int(v))))
        self.slider.set(50)
        self.slider.pack(side="right", padx=10)

        self.scr_res = ctk.CTkScrollableFrame(
            v, fg_color=C["card"], corner_radius=12,
            scrollbar_button_color=C["gris2"],
            scrollbar_button_hover_color=C["oro_oscuro"])
        self.scr_res.grid(row=3, column=0, sticky="nsew", padx=32, pady=(0, 16))

        self.bar_bus = ctk.CTkProgressBar(v, fg_color=C["gris2"],
                                           progress_color=C["oro"],
                                           corner_radius=2, height=3)
        self.lbl_bus_txt = ctk.CTkLabel(v, text="",
                                         font=ctk.CTkFont("Helvetica", 10),
                                         text_color=C["gris"])
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
                             font=ctk.CTkFont("Helvetica", 13),
                             text_color=C["gris"]).pack(pady=40)
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
                         font=ctk.CTkFont("Helvetica", 13),
                         text_color=C["gris"]).pack(pady=40)
            return

        for art in artistas:
            nombre  = art.get("name", "")
            sigs    = art.get("followers", {}).get("total", 0)
            generos = art.get("genres", [])
            g_str   = generos[0] if generos else "Género desconocido"

            card = ctk.CTkFrame(self.scr_res, fg_color=C["card_h"],
                                corner_radius=10,
                                border_width=1, border_color=C["gris2"])
            card.pack(fill="x", padx=10, pady=5)
            card.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(card, text="◎",
                         font=ctk.CTkFont("Georgia", 26), text_color=C["oro"]
                         ).grid(row=0, column=0, rowspan=2, padx=20, pady=14)
            ctk.CTkLabel(card, text=nombre,
                         font=ctk.CTkFont("Georgia", 14, weight="bold"),
                         text_color=C["blanco"], anchor="w"
                         ).grid(row=0, column=1, sticky="w", pady=(14, 2))
            ctk.CTkLabel(card,
                         text=f"{g_str}  ·  {sigs:,} seguidores",
                         font=ctk.CTkFont("Helvetica", 10),
                         text_color=C["gris"], anchor="w"
                         ).grid(row=1, column=1, sticky="w", pady=(0, 14))

            GoldBtn(card, text="Crear Playlist", width=138, height=36,
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

        self.bar_bus.grid(row=4, column=0, sticky="ew", padx=32, pady=(0, 2))
        self.bar_bus.set(0)
        self.lbl_bus_txt.grid(row=5, column=0, padx=32, pady=(0, 8))
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
                            corner_radius=10,
                            border_width=1, border_color=C["oro_oscuro"])
        card.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(card, text=f"◎  {nombre}",
                     font=ctk.CTkFont("Georgia", 15, weight="bold"),
                     text_color=C["blanco"]).pack(anchor="w", padx=20, pady=(18, 4))
        ctk.CTkLabel(card,
                     text=f"{len(uris)} canciones encontradas en tu biblioteca",
                     font=ctk.CTkFont("Helvetica", 11),
                     text_color=C["gris"]).pack(anchor="w", padx=20)
        GoldBtn(card, text="Crear Playlist", width=156, height=38,
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
                     font=ctk.CTkFont("Georgia", 26, weight="bold"),
                     text_color=C["blanco"]
                     ).grid(row=0, column=0, columnspan=3,
                            sticky="w", padx=32, pady=(28, 16))

        self.sc_tot = StatCard(v, "CANCIONES",  "—", C["oro"])
        self.sc_gen = StatCard(v, "GÉNEROS",    "—", C["acento"])
        self.sc_art = StatCard(v, "ARTISTAS",   "—", C["oro_claro"])
        self.sc_tot.grid(row=1, column=0, padx=(32, 8),  pady=(0, 16), sticky="ew")
        self.sc_gen.grid(row=1, column=1, padx=8,         pady=(0, 16), sticky="ew")
        self.sc_art.grid(row=1, column=2, padx=(8, 32),   pady=(0, 16), sticky="ew")

        self.pnl_gen = ctk.CTkScrollableFrame(
            v, fg_color=C["card"], corner_radius=12,
            label_text="DISTRIBUCIÓN DE GÉNEROS",
            label_font=ctk.CTkFont("Helvetica", 8),
            label_text_color=C["gris"],
            scrollbar_button_color=C["gris2"],
            scrollbar_button_hover_color=C["oro_oscuro"])
        self.pnl_gen.grid(row=2, column=0, columnspan=2,
                          padx=(32, 8), pady=(0, 24), sticky="nsew")

        self.pnl_top = ctk.CTkScrollableFrame(
            v, fg_color=C["card"], corner_radius=12,
            label_text="TOP ARTISTAS",
            label_font=ctk.CTkFont("Helvetica", 8),
            label_text_color=C["gris"],
            scrollbar_button_color=C["gris2"],
            scrollbar_button_hover_color=C["oro_oscuro"])
        self.pnl_top.grid(row=2, column=2,
                          padx=(8, 32), pady=(0, 24), sticky="nsew")
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
            color = C["oro"] if i == 0 else (C["oro_oscuro"] if i < 3 else C["gris"])

            ctk.CTkLabel(row, text=med,
                         font=ctk.CTkFont("Georgia", 13, weight="bold"),
                         text_color=color, width=30
                         ).grid(row=0, column=0, padx=(12, 0), pady=10)
            ctk.CTkLabel(row,
                         text=(artista[:23]+"…") if len(artista)>23 else artista,
                         font=ctk.CTkFont("Helvetica", 12),
                         text_color=C["blanco"], anchor="w"
                         ).grid(row=0, column=1, sticky="w", padx=8)
            ctk.CTkLabel(row, text=str(cnt),
                         font=ctk.CTkFont("Georgia", 13, weight="bold"),
                         text_color=C["gris"]
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
        (0.45, "Preparando servicios..."),
        (0.70, "Construyendo interfaz..."),
        (0.92, "Casi listo..."),
        (1.00, "¡Bienvenido a SyncNode 2.0!"),
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
