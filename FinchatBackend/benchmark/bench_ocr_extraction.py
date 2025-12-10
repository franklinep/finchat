

import sys
import time
from pathlib import Path

# Add project root to Python path to allow imports from 'app'
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.libs.ocr.imagen_ocr import extraer_texto_img
except ImportError as e:
    print(f"Error: No se pudo importar el módulo de OCR. Asegúrate de que las dependencias estén instaladas y las rutas sean correctas.")
    print(f"Detalle del error: {e}")
    sys.exit(1)

def run_ocr_benchmark():
    """
    Ejecuta un benchmark de extracción de texto con OCR sobre un conjunto de imágenes.
    """
    image_dir = Path(__file__).resolve().parent / "data" / "boletasFisicas"
    
    if not image_dir.exists():
        print(f"Error: El directorio de imágenes no existe en '{image_dir}'")
        return

    image_files = [
        "img1.jpg",
        "img2.jpg",
        "img3.jpg",
        "img4.jpg",
        "img5.jpg"
    ]

    image_paths = [image_dir / f for f in image_files if (image_dir / f).exists()]
    
    if not image_paths:
        print(f"No se encontraron las imágenes especificadas en '{image_dir}'")
        return

    print("--- Iniciando Benchmark de Extracción OCR ---")
    
    total_time = 0

    for image_path in image_paths:
        try:
            print(f"\n--- Procesando: {image_path.name} ---")
            
            t0 = time.perf_counter()
            # Pass the image path directly as a string
            result = extraer_texto_img(str(image_path))
            dt = time.perf_counter() - t0
            
            total_time += dt
            texto_extraido = result.get("texto", "")

            print(f"Tiempo de extracción: {dt:.4f} segundos")
            print(f"Confianza promedio: {result.get('confianza_promedio', 0.0):.4f}")
            print("--- Texto Extraído ---")
            print(texto_extraido if texto_extraido.strip() else "[No se extrajo texto]")
            print("----------------------" + "-" * len(image_path.name))

        except Exception as e:
            print(f"Ocurrió un error procesando {image_path.name}: {e}")

    avg_time = total_time / len(image_paths) if image_paths else 0
    print(f"\n--- Benchmark Finalizado ---")
    print(f"Total de imágenes procesadas: {len(image_paths)}")
    print(f"Tiempo promedio por imagen: {avg_time:.4f} segundos")
    print("----------------------------")

if __name__ == "__main__":
    run_ocr_benchmark()

