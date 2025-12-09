import re
from typing import Optional

def compactar(texto: str) -> str:
    if not texto:
        return ""
    return re.sub(r"\s+", " ", texto).strip()

def extraer_serie_numero(texto: str) -> Optional[str]:
    if not texto:
        return None

    compact = compactar(texto)

    patrones = [
        r"\b((?:[FBTVE][A-Z0-9]{3})-\d{1,8})\b",  # FXXX-123, BXXX-123, EB01-123, etc.
        r"\b([A-Z]{1,4}\d{0,3}-\d{1,8})\b",       # B001-000123, T001-123, etc.
        r"\b([A-Z]{1,4}\d{0,3})\s*(?:N[Oº\.]|\bN\b)?\s*\.?\s*0*([0-9]{3,12})\b",  # B001 No.172923
    ]

    for patron in patrones:
        match = re.search(patron, compact)
        if match:
            if match.lastindex and match.lastindex >= 2:
                return f"{match.group(1)}-{match.group(2)}"
            return match.group(1)

    return None

def extraer_fecha(texto: str) -> Optional[str]:
    if not texto:
        return None

    compact = compactar(texto)

    patrones = [
        # "Fecha de Emisión : 02/08/2025"
        r"Fecha\s+de\s+Emisi[oó]n[^0-9]{0,20}(\d{2}/\d{2}/\d{4})",
        # "Fecha emision: 06/09/2025 ..."
        r"Fecha[^0-9]{0,20}(\d{2}/\d{2}/\d{4})",
        # Fallback: primer dd/mm/yyyy que aparezca
        r"(\d{2}/\d{2}/\d{4})",
    ]

    for patron in patrones:
        match = re.search(patron, compact, flags=re.IGNORECASE)
        if match:
            return match.group(1)

    return None

def extraer_moneda(texto: str) -> Optional[str]:
    if not texto:
        return None

    compact = compactar(texto)

    # 1) 'Tipo de Moneda : SOLES'
    match = re.search(
        r"Tipo\s+de?\s*Moneda\s*[:\-]?\s*([A-Z/.$]+)",
        compact,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1).upper()

    # 2) Si no hay campo explícito, usar la línea 'SON: ... SOLES'
    match = re.search(
        r"SON[:\s]+.*?\b(SOLES?|DOLARES?|USD|US\$|PEN|S/\.?)\b",
        compact,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1).upper()

    return None

def extraer_nombre_cliente(texto: str) -> Optional[str]:
    if not texto:
        return None

    lineas = [ln.strip() for ln in texto.splitlines()]
    for idx, linea in enumerate(lineas):
        if not linea:
            continue

        lower = linea.lower()
        if not any(kw in lower for kw in ["señor", "cliente", "nombre", "sr."]):
            continue

        # Unir con la siguiente línea para manejar el caso:
        # 'Señor(es)' / ': NOMBRE'
        joined = linea
        if idx + 1 < len(lineas):
            joined = linea + " " + lineas[idx + 1].strip()

        match = re.search(
            r"(?:Señor\(es\)|Cliente|Nombre(?:\s+Cliente)?|Sr\.?)\s*[:\-]?\s*(.+)",
            joined,
            flags=re.IGNORECASE,
        )
        if match:
            valor = match.group(1)
            # Cortar si aparecen otros labels ('DNI', 'RUC', etc.)
            valor = re.split(r"\b(DNI|RUC|DOC\.?|DOCUMENTO)\b", valor)[0]
            valor = valor.strip(" :,-")
            if len(valor) >= 3:
                return valor

    return None

def extraer_dni_cliente(texto: str) -> Optional[str]:
    if not texto:
        return None

    compact = compactar(texto)

    # 1) Preferir DNI (8 dígitos)
    match = re.search(
        r"(?:DNI|DOC(?:\.|UMENTO)?(?:\s+DE\s+IDENTIDAD)?)\s*[:\-]?\s*(\d{8})",
        compact,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1)

    # 2) RUC asociado al cliente
    match = re.search(
        r"Cliente.*?RUC\s*[:\-]?\s*(\d{11})",
        compact,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1)

    return None

def extraer_linea_importe_total(texto: str) -> Optional[str]:
    if not texto:
        return None

    compact = compactar(texto)

    labels = [
        "Importe Total",
        "Monto Total",
        "Total de Venta",
        "Total Venta",
        "Importe a Pagar",
        "Total a Pagar",
        "Neto a Pagar",
        "Total",
    ]

    for label in labels:
        patron = rf"{label}\s*[:\-]?\s*(S/\.?\s*)?([\d.,]+)"
        match = re.search(patron, compact, flags=re.IGNORECASE)
        if match:
            return match.group(0)

    return None
