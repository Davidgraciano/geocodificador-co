"""Línea de comandos: normaliza y geocodifica una dirección o un CSV."""
from __future__ import annotations

import argparse
import csv
import json
import sys

from .cascada import Cascada
from .normalizador import normalizar
from .proveedores import proveedores_disponibles


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="geocodificar", description="Normaliza y geocodifica direcciones colombianas.")
    p.add_argument("direccion", nargs="?", help="Una dirección, por ejemplo \"CL 10 N 43-20\"")
    p.add_argument("--csv", help="CSV de entrada con una columna 'direccion'")
    p.add_argument("--salida", help="CSV de salida (por defecto, la salida estándar)")
    p.add_argument("--ciudad", default="Medellín", help="Ciudad que se agrega a la consulta (por defecto Medellín)")
    p.add_argument("--precision", type=float, default=0.7, help="Precisión mínima para detener la cascada (0 a 1)")
    p.add_argument("--solo-normalizar", action="store_true", help="No consulta proveedores, solo normaliza")
    args = p.parse_args(argv)

    if not args.direccion and not args.csv:
        p.error("indica una dirección o --csv")

    if args.direccion:
        d = normalizar(args.direccion)
        salida = {"original": d.original, "canonica": d.canonica, "valida": d.valida, "complemento": d.complemento, "notas": d.notas}
        if not args.solo_normalizar:
            g = Cascada(proveedores_disponibles(), args.precision, args.ciudad).geocodificar(args.direccion)
            if g.resultado:
                salida.update(lat=g.resultado.lat, lon=g.resultado.lon, proveedor=g.resultado.proveedor, precision=g.resultado.precision)
            salida["intentos"] = [{"proveedor": i.proveedor, "ok": i.resultado is not None, "error": i.error} for i in g.intentos]
        print(json.dumps(salida, ensure_ascii=False, indent=2))
        return 0

    cascada = None if args.solo_normalizar else Cascada(proveedores_disponibles(), args.precision, args.ciudad)
    with open(args.csv, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    destino = open(args.salida, "w", newline="", encoding="utf-8") if args.salida else sys.stdout
    campos = ["direccion", "canonica", "valida", "lat", "lon", "proveedor", "precision"]
    w = csv.DictWriter(destino, fieldnames=campos)
    w.writeheader()
    for fila in filas:
        d = normalizar(fila["direccion"])
        registro = {"direccion": fila["direccion"], "canonica": d.canonica, "valida": d.valida}
        if cascada:
            g = cascada.geocodificar(fila["direccion"])
            if g.resultado:
                registro.update(lat=g.resultado.lat, lon=g.resultado.lon, proveedor=g.resultado.proveedor, precision=g.resultado.precision)
        w.writerow(registro)
    if args.salida:
        destino.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
