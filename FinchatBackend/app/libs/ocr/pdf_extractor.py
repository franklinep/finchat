import fitz  # PyMuPDF


def extraer_texto_pdf(ruta_pdf: str) -> list[dict]:
    paginas = []
    with fitz.open(ruta_pdf) as doc:
        for i, page in enumerate(doc, start=1):
            paginas.append({"numero_pagina": i, "texto": page.get_text("text")})
    return paginas
