import re
from datetime import datetime
from typing import Optional
from datetime import date

def limpiar_ruc(texto: str) -> Optional[str]:
    if not texto:
        return None
    match = re.search(r"\b(\d{11})\b", texto)
    return match.group(1) if match else None


def limpiar_monto(fila: str) -> Optional[float]:
  if fila is None:
      return None
  txt = fila.replace(",", "")
  num = re.search(r"\d+(?:\.\d+)?", txt)
  return float(num.group()) if num else None


def parsear_fecha(texto: str) -> Optional[date]:
    if not texto:
        return None
    texto = texto.strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    return None

def normalizar_moneda(texto: str) -> Optional[str]:
    texto = texto.strip().upper()
    monedas_soles = ["S/.", "S/", "SOLES", "PEN"]
    monedas_dolares = ["US$", "DOLARES", "USD"]
    if texto in monedas_soles:
        return "PEN"
    elif texto in monedas_dolares:
        return "USD"
    else:
        return "PEN"
