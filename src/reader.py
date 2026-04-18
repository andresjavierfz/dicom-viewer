import pydicom
import numpy as np
from pathlib import Path


def cargar_dicom(ruta: str) -> pydicom.Dataset:
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")
    if ruta.suffix.lower() != ".dcm":
        raise ValueError(f"El archivo no es .dcm: {ruta}")
    try:
        return pydicom.dcmread(str(ruta))
    except pydicom.errors.InvalidDicomError:
        return pydicom.dcmread(str(ruta), force=True)


def extraer_metadatos(ds: pydicom.Dataset) -> dict:
    campos = {
        "Nombre paciente":   getattr(ds, "PatientName", "N/D"),
        "ID paciente":       getattr(ds, "PatientID", "N/D"),
        "Fecha estudio":     getattr(ds, "StudyDate", "N/D"),
        "Modalidad":         getattr(ds, "Modality", "N/D"),
        "Descripción":       getattr(ds, "StudyDescription", "N/D"),
        "Institución":       getattr(ds, "InstitutionName", "N/D"),
        "Window Center":     getattr(ds, "WindowCenter", "N/D"),
        "Window Width":      getattr(ds, "WindowWidth", "N/D"),
        "Rows":              getattr(ds, "Rows", "N/D"),
        "Columns":           getattr(ds, "Columns", "N/D"),
    }
    return {k: str(v) for k, v in campos.items()}


def extraer_pixel_array(ds: pydicom.Dataset) -> np.ndarray:
    if not hasattr(ds, "PixelData"):
        raise ValueError("El archivo DICOM no contiene datos de imagen.")
    
    arr = ds.pixel_array.astype(np.float32)
    
    # Aplicar conversión a HU si están presentes los tags
    slope     = float(getattr(ds, "RescaleSlope",     1))
    intercept = float(getattr(ds, "RescaleIntercept", 0))
    
    arr = arr * slope + intercept
    
    return arr