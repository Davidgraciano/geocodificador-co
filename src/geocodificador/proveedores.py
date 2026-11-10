"""Proveedores de geocodificación con una interfaz común.

Cada proveedor recibe un texto y devuelve un `Resultado` o `None`. La precisión
va de 0 a 1 para que la cascada pueda comparar proveedores distintos.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Protocol

import requests


@dataclass
class Resultado:
    lat: float
    lon: float
    precision: float
    proveedor: str
    direccion_encontrada: str = ""


class Proveedor(Protocol):
    nombre: str

    def geocodificar(self, texto: str) -> Resultado | None: ...


class Nominatim:
    """OpenStreetMap Nominatim. Gratis, sin llave, máximo 1 solicitud por segundo."""

    nombre = "nominatim"
    url = "https://nominatim.openstreetmap.org/search"

    def __init__(self, user_agent: str = "geocodificador-co (github.com/Davidgraciano)", sesion: requests.Session | None = None):
        self.sesion = sesion or requests.Session()
        self.sesion.headers["User-Agent"] = user_agent
        self._ultima = 0.0

    def geocodificar(self, texto: str) -> Resultado | None:
        espera = 1.0 - (time.monotonic() - self._ultima)
        if espera > 0:
            time.sleep(espera)
        self._ultima = time.monotonic()
        r = self.sesion.get(self.url, params={"q": texto, "format": "jsonv2", "limit": 1, "countrycodes": "co"}, timeout=10)
        r.raise_for_status()
        datos = r.json()
        if not datos:
            return None
        d = datos[0]
        # Una coincidencia de edificio o casa es más precisa que una de calle o barrio.
        precision = 0.9 if d.get("addresstype") in {"building", "house"} else 0.6 if d.get("addresstype") == "road" else 0.3
        return Resultado(float(d["lat"]), float(d["lon"]), precision, self.nombre, d.get("display_name", ""))


class Here:
    """HERE Geocoding & Search v7. Necesita HERE_API_KEY."""

    nombre = "here"
    url = "https://geocode.search.hereapi.com/v1/geocode"

    def __init__(self, api_key: str | None = None, sesion: requests.Session | None = None):
        self.api_key = api_key or os.environ["HERE_API_KEY"]
        self.sesion = sesion or requests.Session()

    def geocodificar(self, texto: str) -> Resultado | None:
        r = self.sesion.get(self.url, params={"q": texto, "in": "countryCode:COL", "limit": 1, "apiKey": self.api_key}, timeout=10)
        r.raise_for_status()
        items = r.json().get("items", [])
        if not items:
            return None
        it = items[0]
        precision = float(it.get("scoring", {}).get("queryScore", 0.5))
        return Resultado(it["position"]["lat"], it["position"]["lng"], precision, self.nombre, it.get("title", ""))


class Google:
    """Google Maps Geocoding API. Necesita GOOGLE_MAPS_API_KEY."""

    nombre = "google"
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    _PRECISION = {"ROOFTOP": 0.95, "RANGE_INTERPOLATED": 0.8, "GEOMETRIC_CENTER": 0.5, "APPROXIMATE": 0.3}

    def __init__(self, api_key: str | None = None, sesion: requests.Session | None = None):
        self.api_key = api_key or os.environ["GOOGLE_MAPS_API_KEY"]
        self.sesion = sesion or requests.Session()

    def geocodificar(self, texto: str) -> Resultado | None:
        r = self.sesion.get(self.url, params={"address": texto, "region": "co", "key": self.api_key}, timeout=10)
        r.raise_for_status()
        datos = r.json()
        if datos.get("status") != "OK" or not datos.get("results"):
            return None
        res = datos["results"][0]
        loc = res["geometry"]["location"]
        precision = self._PRECISION.get(res["geometry"].get("location_type", ""), 0.3)
        return Resultado(loc["lat"], loc["lng"], precision, self.nombre, res.get("formatted_address", ""))


def proveedores_disponibles() -> list[Proveedor]:
    """Los proveedores que se pueden usar con las llaves del entorno, del más barato al más caro."""
    lista: list[Proveedor] = [Nominatim()]
    if os.environ.get("HERE_API_KEY"):
        lista.append(Here())
    if os.environ.get("GOOGLE_MAPS_API_KEY"):
        lista.append(Google())
    return lista
