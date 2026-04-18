# src/renderer.py

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.figure


def apply_window_level(
    pixel_array: np.ndarray,
    window_center: float,
    window_width: float,
) -> np.ndarray:
    """
    Aplica transformación window/level al pixel array DICOM.

    El contraste clínico se define por dos parámetros:
      - window_center (WC): valor de HU en el centro de la ventana
      - window_width  (WW): rango total de HU que cabe en la escala de grises

    Valores fuera del rango se recortan (clip) a 0.0 o 1.0.
    Retorna un array float32 normalizado en [0.0, 1.0].
    """
    ww = float(window_width)
    wc = float(window_center)

    lower = wc - ww / 2.0
    upper = wc + ww / 2.0

    # Convertir a float para evitar overflow con int16
    arr = pixel_array.astype(np.float32)

    # Clip y normalización lineal al rango [0, 1]
    arr = np.clip(arr, lower, upper)
    arr = (arr - lower) / ww

    return arr


def render_image(
    pixel_array: np.ndarray,
    window_center: float,
    window_width: float,
    title: str = "DICOM Image",
    colormap: str = "gray",
    save_path: str | None = None,
) -> matplotlib.figure.Figure:
    """
    Renderiza el pixel array con window/level y devuelve la Figure de matplotlib.

    Parámetros
    ----------
    pixel_array   : numpy array crudo extraído con extraer_pixel_array()
    window_center : WC extraído de los metadatos (o ajuste manual)
    window_width  : WW extraído de los metadatos (o ajuste manual)
    title         : título que aparece en la figura
    colormap      : 'gray' por defecto; 'bone' o 'hot' para uso clínico alternativo
    save_path     : si se entrega una ruta, guarda la imagen en disco (PNG)

    Retorna
    -------
    matplotlib.figure.Figure — permite mostrar o guardar externamente
    """
    windowed = apply_window_level(pixel_array, window_center, window_width)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(windowed, cmap=colormap, vmin=0.0, vmax=1.0)
    ax.set_title(title, fontsize=11)
    ax.axis("off")
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def render_comparacion(
    pixel_array: np.ndarray,
    presets: list[dict],
) -> matplotlib.figure.Figure:
    """
    Renderiza varias ventanas lado a lado para comparación rápida.

    Útil para verificar que los presets clínicos funcionan correctamente.

    Ejemplo de presets:
        [
            {"wc": 40,   "ww": 400,  "label": "Abdomen"},
            {"wc": 600,  "ww": 2000, "label": "Pulmón"},
            {"wc": 1000, "ww": 4000, "label": "Hueso"},
        ]
    """
    n = len(presets)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 5))

    if n == 1:
        axes = [axes]

    for ax, preset in zip(axes, presets):
        windowed = apply_window_level(
            pixel_array,
            preset["wc"],
            preset["ww"],
        )
        ax.imshow(windowed, cmap="gray", vmin=0.0, vmax=1.0)
        ax.set_title(f'{preset["label"]}\nWC={preset["wc"]} WW={preset["ww"]}', fontsize=9)
        ax.axis("off")

    fig.tight_layout()
    return fig