# DICOM Viewer

Visor de imágenes DICOM con ajuste de window/level.

## Requisitos

- Python 3.10+
- macOS / Linux

## Instalación

```bash
git clone https://github.com/andresjavierfz/dicom-viewer.git
cd dicom-viewer
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

Abre un archivo `.dcm` con el botón "Abrir .dcm" y ajusta el contraste con los sliders o presets clínicos.

## Estructura

    src/
    ├── reader.py    — carga y validación del archivo DICOM
    ├── renderer.py  — transformación window/level
    └── ui.py        — interfaz gráfica tkinter

## Stack

- `pydicom` — lectura de archivos DICOM
- `numpy` — procesamiento del pixel array
- `matplotlib` — renderizado de imagen
- `tkinter` — interfaz gráfica