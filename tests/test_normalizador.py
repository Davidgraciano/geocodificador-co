import pytest

from geocodificador import normalizar


@pytest.mark.parametrize(
    "entrada, esperada",
    [
        ("CL 10 N 43-20", "Calle 10 # 43-20"),
        ("Calle 10 # 43 - 20", "Calle 10 # 43-20"),
        ("CALLE 50 N 45 37", "Calle 50 # 45-37"),
        ("Cra. 43A # 1 sur - 50", "Carrera 43A # 1-50 Sur"),
        ("KR 52 # 44B - 17", "Carrera 52 # 44B-17"),
        ("K52 N44B-17", "Carrera 52 # 44B-17"),
        ("TV 39 74B 47", "Transversal 39 # 74B-47"),
        ("Diagonal 75B # 2A-120", "Diagonal 75B # 2A-120"),
        ("Av. 80 # 65-223", "Avenida 80 # 65-223"),
        ("Avenida Carrera 70 # 44-10", "Carrera 70 # 44-10"),
        ("Calle 45 bis # 12-30", "Calle 45 Bis # 12-30"),
        ("Calle 45A bis B # 12-30", "Calle 45A Bis B # 12-30"),
        ("Calle 10 Sur No. 43-20", "Calle 10 # 43-20 Sur"),
        ("Circular 1 Nº 70-01", "Circular 1 # 70-1"),
        ("cll 033 # 065 - 018", "Calle 33 # 65-18"),
    ],
)
def test_forma_canonica(entrada, esperada):
    d = normalizar(entrada)
    assert d.valida, d.notas
    assert d.canonica == esperada


def test_complemento():
    d = normalizar("KR 52 # 44B - 17 Int 301")
    assert d.canonica == "Carrera 52 # 44B-17"
    assert d.complemento == "Int 301"


def test_partes():
    d = normalizar("Cra. 43A # 1 sur - 50")
    assert (d.tipo_via, d.via, d.cruce, d.placa, d.cuadrante) == ("Carrera", "43A", "1", "50", "Sur")


@pytest.mark.parametrize("entrada", ["Parque Berrío", "Vereda El Placer, finca La Esperanza", "Calle sin número"])
def test_no_interpretable(entrada):
    d = normalizar(entrada)
    assert not d.valida
    assert d.notas


def test_texto_para_geocodificar():
    assert normalizar("CL 10 N 43-20").para_geocodificar("Medellín") == "Calle 10 # 43-20, Medellín, Colombia"
