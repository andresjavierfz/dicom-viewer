# src/ui.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.reader import cargar_dicom, extraer_metadatos, extraer_pixel_array
from src.render import render_image


# Presets clínicos estándar (WC, WW)
PRESETS = {
    "Abdomen":   (40,   400),
    "Pulmón":    (-600, 1500),
    "Hueso":     (400,  1800),
    "Cerebro":   (40,   80),
    "Mediastino":(50,   350),
}


class DicomViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DICOM Viewer")
        self.resizable(True, True)
        self.configure(bg="#1a1a1a")

        # Estado interno
        self._ds = None          # dataset pydicom
        self._pixel_array = None # numpy array
        self._meta = {}          # dict de metadatos

        self._build_ui()

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        # Layout principal: panel izquierdo | canvas derecho
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self._panel = tk.Frame(self, bg="#1a1a1a", width=220)
        self._panel.grid(row=0, column=0, sticky="ns", padx=(10, 0), pady=10)
        self._panel.grid_propagate(False)

        self._canvas_frame = tk.Frame(self, bg="#1a1a1a")
        self._canvas_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self._canvas_frame.rowconfigure(0, weight=1)
        self._canvas_frame.columnconfigure(0, weight=1)

        self._build_panel()
        self._build_canvas()

    def _build_panel(self):
        p = self._panel

        # Botón abrir
        btn = tk.Button(
            p, text="Abrir .dcm",
            command=self._abrir_archivo,
            bg="#2a9d8f", fg="white",
            relief="flat", cursor="hand2",
            font=("Helvetica", 11, "bold"),
            pady=6,
        )
        btn.pack(fill="x", pady=(0, 12))

        # Metadatos
        meta_frame = tk.LabelFrame(
            p, text="Metadatos",
            bg="#1a1a1a", fg="#aaaaaa",
            font=("Helvetica", 9),
        )
        meta_frame.pack(fill="x", pady=(0, 12))

        self._lbl_paciente  = self._meta_label(meta_frame, "Paciente")
        self._lbl_modalidad = self._meta_label(meta_frame, "Modalidad")
        self._lbl_fecha     = self._meta_label(meta_frame, "Fecha")
        self._lbl_dim       = self._meta_label(meta_frame, "Dimensiones")

        # Sliders WC / WW
        self._wc_var = tk.DoubleVar(value=40)
        self._ww_var = tk.DoubleVar(value=400)

        self._slider_wc = self._build_slider(p, "Window Center", self._wc_var, -1000, 3000)
        self._slider_ww = self._build_slider(p, "Window Width",  self._ww_var, 1,    4000)

        # Presets
        preset_frame = tk.LabelFrame(
            p, text="Presets clínicos",
            bg="#1a1a1a", fg="#aaaaaa",
            font=("Helvetica", 9),
        )
        preset_frame.pack(fill="x", pady=(12, 0))

        for nombre, (wc, ww) in PRESETS.items():
            tk.Button(
                preset_frame, text=nombre,
                command=lambda c=wc, w=ww: self._aplicar_preset(c, w),
                bg="#2c2c2c", fg="#dddddd",
                relief="flat", cursor="hand2",
                font=("Helvetica", 9),
                pady=3,
            ).pack(fill="x", pady=1)

    def _meta_label(self, parent, campo: str) -> tk.Label:
        frame = tk.Frame(parent, bg="#1a1a1a")
        frame.pack(fill="x", padx=6, pady=1)
        tk.Label(
            frame, text=f"{campo}:",
            bg="#1a1a1a", fg="#888888",
            font=("Helvetica", 8), width=10, anchor="w",
        ).pack(side="left")
        lbl = tk.Label(
            frame, text="—",
            bg="#1a1a1a", fg="#dddddd",
            font=("Helvetica", 8), anchor="w",
        )
        lbl.pack(side="left", fill="x", expand=True)
        return lbl

    def _build_slider(
        self, parent, label: str, var: tk.DoubleVar, from_: float, to: float
    ) -> ttk.Scale:
        frame = tk.Frame(parent, bg="#1a1a1a")
        frame.pack(fill="x", pady=(6, 0))

        header = tk.Frame(frame, bg="#1a1a1a")
        header.pack(fill="x")
        tk.Label(
            header, text=label,
            bg="#1a1a1a", fg="#aaaaaa",
            font=("Helvetica", 9),
        ).pack(side="left")
        val_lbl = tk.Label(
            header, textvariable=var,
            bg="#1a1a1a", fg="#2a9d8f",
            font=("Helvetica", 9, "bold"),
        )
        val_lbl.pack(side="right")

        slider = ttk.Scale(
            frame, from_=from_, to=to, orient="horizontal",
            variable=var,
            command=lambda _: self._render(),
        )
        slider.pack(fill="x")
        return slider

    def _build_canvas(self):
        # Figura vacía inicial
        import matplotlib.pyplot as plt
        self._fig, self._ax = plt.subplots(figsize=(7, 7), facecolor="#1a1a1a")
        self._ax.set_facecolor("#1a1a1a")
        self._ax.axis("off")

        self._mpl_canvas = FigureCanvasTkAgg(self._fig, master=self._canvas_frame)
        self._mpl_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self._mpl_canvas.draw()

    # ---------------------------------------------------------------- Lógica

    def _abrir_archivo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo DICOM",
            filetypes=[("DICOM", "*.dcm"), ("Todos", "*.*")],
        )
        if not ruta:
            return

        try:
            self._ds = cargar_dicom(ruta)
            self._meta = extraer_metadatos(self._ds)
            self._pixel_array = extraer_pixel_array(self._ds)
        except Exception as e:
            messagebox.showerror("Error al cargar", str(e))
            return

        self._actualizar_metadatos()

        # Usar WC/WW del archivo si están disponibles
        wc = self._meta.get("WindowCenter", 40)
        ww = self._meta.get("WindowWidth", 400)
        self._wc_var.set(float(wc))
        self._ww_var.set(float(ww))

        self._render()

    def _actualizar_metadatos(self):
        m = self._meta
        self._lbl_paciente.config( text=str(m.get("Nombre paciente", "—")))
        self._lbl_modalidad.config(text=str(m.get("Modalidad",     "—")))
        self._lbl_fecha.config(    text=str(m.get("Fecha estudio",    "—")))
        h, w = self._pixel_array.shape[:2]
        self._lbl_dim.config(text=f"{w} × {h} px")

    def _aplicar_preset(self, wc: float, ww: float):
        self._wc_var.set(wc)
        self._ww_var.set(ww)
        self._render()

    def _render(self):
        if self._pixel_array is None:
            return

        wc = self._wc_var.get()
        ww = max(self._ww_var.get(), 1.0)  # WW nunca puede ser 0

        from src.render import apply_window_level
        import numpy as np

        windowed = apply_window_level(self._pixel_array, wc, ww)

        self._ax.clear()
        self._ax.imshow(windowed, cmap="gray", vmin=0.0, vmax=1.0)
        self._ax.axis("off")
        self._fig.tight_layout(pad=0)
        self._mpl_canvas.draw()