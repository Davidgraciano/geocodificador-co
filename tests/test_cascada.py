import pytest

from geocodificador import Cascada, Resultado


class Falso:
    def __init__(self, nombre, resultado=None, error=None):
        self.nombre = nombre
        self.resultado = resultado
        self.error = error
        self.consultas = []

    def geocodificar(self, texto):
        self.consultas.append(texto)
        if self.error:
            raise self.error
        return self.resultado


def r(precision, proveedor):
    return Resultado(6.25, -75.57, precision, proveedor)


def test_se_detiene_en_el_primero_suficiente():
    a, b = Falso("a", r(0.9, "a")), Falso("b", r(0.95, "b"))
    g = Cascada([a, b], precision_minima=0.7).geocodificar("CL 10 N 43-20")
    assert g.resultado.proveedor == "a"
    assert b.consultas == []


def test_sigue_si_la_precision_es_baja():
    a, b = Falso("a", r(0.3, "a")), Falso("b", r(0.9, "b"))
    g = Cascada([a, b], precision_minima=0.7).geocodificar("CL 10 N 43-20")
    assert g.resultado.proveedor == "b"
    assert [i.proveedor for i in g.intentos] == ["a", "b"]


def test_un_proveedor_caido_no_detiene_la_cascada():
    a, b = Falso("a", error=TimeoutError("sin respuesta")), Falso("b", r(0.8, "b"))
    g = Cascada([a, b]).geocodificar("CL 10 N 43-20")
    assert g.resultado.proveedor == "b"
    assert g.intentos[0].error == "sin respuesta"


def test_devuelve_el_mejor_si_ninguno_alcanza():
    a, b = Falso("a", r(0.4, "a")), Falso("b", r(0.5, "b"))
    g = Cascada([a, b], precision_minima=0.9).geocodificar("CL 10 N 43-20")
    assert g.resultado.proveedor == "b"


def test_envia_la_direccion_normalizada():
    a = Falso("a", r(0.9, "a"))
    Cascada([a], ciudad="Medellín").geocodificar("cll 10 n 43-20")
    assert a.consultas == ["Calle 10 # 43-20, Medellín, Colombia"]


def test_sin_proveedores():
    with pytest.raises(ValueError):
        Cascada([])
