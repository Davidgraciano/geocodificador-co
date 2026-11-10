"""Normalización de direcciones urbanas colombianas.

Convierte variantes como "CL 10 N 43-20", "Cra. 43A # 1 sur - 50" o
"TV 39 74B 47" en una forma canónica ("Calle 10 # 43-20") y en sus partes,
que es lo que necesita un geocodificador para acertar.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

TIPOS_VIA = {
    "CALLE": "Calle", "CL": "Calle", "CLL": "Calle", "CALL": "Calle", "CLLE": "Calle",
    "CARRERA": "Carrera", "KR": "Carrera", "KRA": "Carrera", "CR": "Carrera", "CRA": "Carrera", "CARR": "Carrera", "K": "Carrera",
    "DIAGONAL": "Diagonal", "DG": "Diagonal", "DIAG": "Diagonal",
    "TRANSVERSAL": "Transversal", "TV": "Transversal", "TR": "Transversal", "TRANSV": "Transversal", "TRV": "Transversal",
    "AVENIDA": "Avenida", "AV": "Avenida", "AVE": "Avenida",
    "CIRCULAR": "Circular", "CQ": "Circular", "CIR": "Circular", "CIRC": "Circular",
    "AUTOPISTA": "Autopista", "AU": "Autopista", "AUT": "Autopista",
}
CUADRANTES = {"SUR": "Sur", "ESTE": "Este", "NORTE": "Norte", "OESTE": "Oeste"}

_SEPARADOR_NUMERO = re.compile(r"\b(?:NO|NRO|NUM|N)\s*\.?\s*(?=\d)|N[°º]|#")
_PATRON = re.compile(
    r"""^
    (?P<tipo>[A-Z]+)\s+
    (?P<via>\d{1,3})\s*(?P<via_letra>[A-Z](?![A-Z]))?\s*(?P<via_bis>BIS)?\s*(?P<via_bis_letra>[A-Z](?![A-Z]))?\s*(?P<via_cuad>SUR|ESTE|NORTE|OESTE)?
    \s*\#?\s*
    (?P<cruce>\d{1,3})\s*(?P<cruce_letra>[A-Z](?![A-Z]))?\s*(?P<cruce_bis>BIS)?\s*(?P<cruce_cuad>SUR|ESTE|NORTE|OESTE)?
    \s*-?\s*
    (?P<placa>\d{1,4})\s*(?P<placa_cuad>SUR|ESTE|NORTE|OESTE)?
    \s*(?P<complemento>.*)
    $""",
    re.VERBOSE,
)


@dataclass
class Direccion:
    """Una dirección urbana colombiana separada en sus partes."""

    original: str
    tipo_via: str | None = None
    via: str | None = None
    cruce: str | None = None
    placa: str | None = None
    cuadrante: str | None = None
    complemento: str | None = None
    valida: bool = False
    notas: list[str] = field(default_factory=list)

    @property
    def canonica(self) -> str:
        """La dirección en forma canónica, o el texto limpio si no se pudo interpretar."""
        if not self.valida:
            return _limpiar(self.original).title()
        texto = f"{self.tipo_via} {self.via} # {self.cruce}-{self.placa}"
        if self.cuadrante:
            texto += f" {self.cuadrante}"
        return texto

    def para_geocodificar(self, ciudad: str | None = None, pais: str = "Colombia") -> str:
        """Texto listo para enviar a un geocodificador."""
        partes = [self.canonica]
        if ciudad:
            partes.append(ciudad)
        partes.append(pais)
        return ", ".join(partes)


def _limpiar(texto: str) -> str:
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", sin_tildes).strip()


def _parte(numero: str, letra: str | None, bis: str | None, bis_letra: str | None = None) -> str:
    texto = numero.lstrip("0") or "0"
    if letra:
        texto += letra
    if bis:
        texto += " Bis"
        if bis_letra:
            texto += f" {bis_letra}"
    return texto


def normalizar(texto: str) -> Direccion:
    """Interpreta una dirección colombiana y devuelve sus partes y su forma canónica.

    >>> normalizar("CL 10 N 43-20").canonica
    'Calle 10 # 43-20'
    >>> normalizar("Cra. 43A # 1 sur - 50").canonica
    'Carrera 43A # 1-50 Sur'
    """
    resultado = Direccion(original=texto)
    limpio = _limpiar(texto).upper()
    limpio = re.sub(r"[.,;:]", " ", limpio)
    limpio = _SEPARADOR_NUMERO.sub(" # ", limpio)
    # "43A-20" y "43 A - 20" son lo mismo: separa letras pegadas a números.
    limpio = re.sub(r"(\d)([A-Z])", r"\1 \2", limpio)
    limpio = re.sub(r"([A-Z])(\d)", r"\1 \2", limpio)
    limpio = re.sub(r"\s+", " ", limpio).strip()
    # Tipos de vía de dos palabras.
    limpio = re.sub(r"^AV(?:ENIDA)? (CALLE|CARRERA|CL|KR|CR|CRA)\b", lambda m: m.group(1), limpio)

    coincidencia = _PATRON.match(limpio)
    if not coincidencia:
        resultado.notas.append("No sigue el patrón vía # cruce-placa")
        return resultado
    g = coincidencia.groupdict()
    tipo = TIPOS_VIA.get(g["tipo"])
    if not tipo:
        resultado.notas.append(f"Tipo de vía desconocido: {g['tipo']}")
        return resultado

    resultado.tipo_via = tipo
    resultado.via = _parte(g["via"], g["via_letra"], g["via_bis"], g["via_bis_letra"])
    resultado.cruce = _parte(g["cruce"], g["cruce_letra"], g["cruce_bis"])
    resultado.placa = g["placa"].lstrip("0") or "0"
    cuadrantes = {c for c in (g["via_cuad"], g["cruce_cuad"], g["placa_cuad"]) if c}
    if len(cuadrantes) > 1:
        resultado.notas.append(f"Varios cuadrantes: {', '.join(sorted(cuadrantes))}")
    if cuadrantes:
        resultado.cuadrante = CUADRANTES[sorted(cuadrantes)[0]]
    complemento = (g["complemento"] or "").strip(" -")
    resultado.complemento = complemento.title() or None
    resultado.valida = True
    return resultado
