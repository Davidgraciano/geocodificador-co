"""Geocodificación en cascada: prueba proveedores en orden hasta lograr la precisión pedida."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from .normalizador import Direccion, normalizar
from .proveedores import Proveedor, Resultado

log = logging.getLogger(__name__)


@dataclass
class Intento:
    proveedor: str
    resultado: Resultado | None = None
    error: str | None = None


@dataclass
class Geocodificacion:
    direccion: Direccion
    resultado: Resultado | None
    intentos: list[Intento] = field(default_factory=list)

    @property
    def encontrada(self) -> bool:
        return self.resultado is not None


class Cascada:
    """Recorre los proveedores en orden y se queda con el primero que alcance `precision_minima`.

    Si ninguno la alcanza, devuelve el mejor resultado obtenido. Cada intento queda
    registrado para auditar de dónde salió cada coordenada.
    """

    def __init__(self, proveedores: list[Proveedor], precision_minima: float = 0.7, ciudad: str | None = None):
        if not proveedores:
            raise ValueError("Se necesita al menos un proveedor")
        self.proveedores = proveedores
        self.precision_minima = precision_minima
        self.ciudad = ciudad

    def geocodificar(self, texto: str) -> Geocodificacion:
        direccion = normalizar(texto)
        consulta = direccion.para_geocodificar(self.ciudad)
        intentos: list[Intento] = []
        mejor: Resultado | None = None
        for proveedor in self.proveedores:
            try:
                resultado = proveedor.geocodificar(consulta)
            except Exception as exc:  # un proveedor caído no detiene la cascada
                log.warning("%s falló con %r: %s", proveedor.nombre, consulta, exc)
                intentos.append(Intento(proveedor.nombre, error=str(exc)))
                continue
            intentos.append(Intento(proveedor.nombre, resultado))
            if resultado and (mejor is None or resultado.precision > mejor.precision):
                mejor = resultado
            if resultado and resultado.precision >= self.precision_minima:
                break
        return Geocodificacion(direccion, mejor, intentos)
