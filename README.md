# geocodificador-co

Normaliza direcciones urbanas colombianas y las geocodifica en cascada: prueba varios proveedores en orden y se queda con el primero que alcanza la precisión que pides.

> **In English:** a small Python library and CLI that normalizes Colombian street addresses ("CL 10 N 43-20" → "Calle 10 # 43-20") and geocodes them through a cascade of providers (OpenStreetMap Nominatim, HERE, Google), keeping an audit trail of every attempt.

Es una versión genérica, con datos de ejemplo, del enfoque que usé para geocodificar informes de siniestros viales en Medellín: normalizar primero y luego pasar por varios servicios, del más barato al más preciso.

## Por qué

Las direcciones colombianas se escriben de muchas formas: `CL 10 N 43-20`, `Calle 10 # 43 - 20`, `cll 010 no. 43-20`. Un geocodificador falla o se equivoca con la mitad de ellas. Normalizar antes de consultar sube la tasa de acierto, y la cascada evita pagar por un servicio comercial cuando uno gratuito ya resolvió la dirección.

## Instalación

```bash
pip install git+https://github.com/Davidgraciano/geocodificador-co.git
```

Requiere Python 3.10 o superior.

## Uso

Normalizar una dirección:

```python
from geocodificador import normalizar

d = normalizar("Cra. 43A # 1 sur - 50")
d.canonica   # 'Carrera 43A # 1-50 Sur'
d.via, d.cruce, d.placa, d.cuadrante   # ('43A', '1', '50', 'Sur')
```

Geocodificar en cascada:

```python
from geocodificador import Cascada, Nominatim, Here

cascada = Cascada([Nominatim(), Here()], precision_minima=0.7, ciudad="Medellín")
g = cascada.geocodificar("CL 10 N 43-20")
g.resultado.lat, g.resultado.lon, g.resultado.proveedor
g.intentos   # qué proveedor se consultó, qué respondió y qué falló
```

Desde la terminal:

```bash
geocodificar "TV 39 74B 47" --solo-normalizar
geocodificar --csv ejemplos/direcciones.csv --salida geocodificadas.csv --ciudad Medellín
```

## Proveedores

| Proveedor | Llave | Notas |
| --- | --- | --- |
| Nominatim (OpenStreetMap) | No necesita | Gratis, máximo 1 solicitud por segundo; la librería respeta ese límite |
| HERE | `HERE_API_KEY` | Se activa solo si la variable existe |
| Google Maps | `GOOGLE_MAPS_API_KEY` | Se activa solo si la variable existe |

Cada proveedor devuelve una precisión de 0 a 1 para poder compararlos. Agregar uno nuevo (por ejemplo, el servicio de una alcaldía) es implementar un método `geocodificar(texto) -> Resultado | None`.

## Qué reconoce el normalizador

- Tipos de vía y sus abreviaturas: Calle (CL, CLL), Carrera (KR, CRA, CR, K), Diagonal (DG), Transversal (TV, TR), Avenida (AV), Circular (CQ), Autopista.
- Separadores `#`, `N`, `No.`, `Nº`, guion o solo espacios.
- Letras (`43A`), `Bis`, cuadrantes (`Sur`, `Este`) y complementos (`Int 301`, `Apto 502`).
- Ceros a la izquierda y tildes.

Lo que no sigue el patrón vía-cruce-placa (veredas, nombres de lugares) se marca como no válido, con una nota, en lugar de inventar una dirección.

## Pruebas

```bash
pip install -e ".[dev]"
pytest
```

## Licencia

MIT
