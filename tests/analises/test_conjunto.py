"""Composição e geração do conjunto de usinas (spec das Análises, FR-060; plano das Análises, D22).

Uma PCH num conjunto em que uma térmica sai no meio do período e uma CGH entra: a geração do conjunto por trecho de
composição, com os tipos e a potência das usinas de cada trecho; nenhum número dividido entre as usinas; o tipo que o
ONS publica comparado com a composição. A integração (linhas próprias sem valor, omissões e conclusão) está em
``tests/integracao/test_usinas_ficticias.py``.
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from src.analises.conjunto import (
    COLUNAS_COMPOSICAO,
    COLUNAS_TRECHOS,
    achados_conjunto,
    analisar_conjunto,
    trechos_de_composicao,
)

PCH, UTE, CGH = "PCH.PH.GO.000001-0.01", "UTE.BI.GO.000002-0.01", "CGH.PH.GO.000003-0.01"


def _trecho(n: int, inicio: str, fim: str, composicao: str, tipos: str, modalidade: str = "Conjunto de Usinas"):
    return {"trecho": n, "inicio": f"{inicio} 00:00:00", "fim": f"{fim} 23:00:00", "modalidade": modalidade,
            "id_conjunto": "CJU_GOTEST", "composicao": composicao, "tipos_composicao": tipos,
            "codigos_planejamento": "", "nivel_geracao": "conjunto", "mostrar": True}


# Coleta: a térmica sai em 15/02; em 21/02 só a modalidade muda (o mesmo trecho de composição)
TRECHOS = pd.DataFrame([
    _trecho(1, "2024-01-10", "2024-01-31", f"{PCH};{UTE}", "PCH;UTE"),
    _trecho(2, "2024-02-01", "2024-02-14", f"{CGH};{PCH};{UTE}", "CGH;PCH;UTE"),
    _trecho(3, "2024-02-15", "2024-02-20", f"{CGH};{PCH}", "CGH;PCH"),
    _trecho(4, "2024-02-21", "2024-02-29", f"{CGH};{PCH}", "CGH;PCH", modalidade="TIPO II-C"),
])
MEMBROS = pd.DataFrame([
    {"id_conjunto": "CJU_GOTEST", "nom_conjunto": "Conj. Teste", "ceg": PCH, "nom_usina": "PCH Alfa", "tipo": "PCH",
     "inicio": "2024-01-10", "fim": ""},
    {"id_conjunto": "CJU_GOTEST", "nom_conjunto": "Conj. Teste", "ceg": UTE, "nom_usina": "UTE Beta", "tipo": "UTE",
     "inicio": "2011-01-06", "fim": "2024-02-15"},
    {"id_conjunto": "CJU_GOTEST", "nom_conjunto": "Conj. Teste", "ceg": CGH, "nom_usina": "CGH Gama", "tipo": "CGH",
     "inicio": "2024-02-01", "fim": ""},
])


def _unidade(ceg: str, n: int, potencia: float, entrada: str, desativacao: str = "9999-12-31"):
    return {"ceg": ceg, "nom_usina": ceg[:3], "num_unidadegeradora": str(n), "val_potenciaefetiva": str(potencia),
            "dat_entradaoperacao": entrada, "dat_desativacao": desativacao}


# A CGH não tem unidade cadastrada; a terceira unidade da PCH entra em operação em 10/02 (dentro do trecho 2)
CAPACIDADE = pd.DataFrame([
    _unidade(PCH, 1, 8.0, "2016-03-01"), _unidade(PCH, 2, 8.0, "2016-03-01"), _unidade(PCH, 3, 4.0, "2024-02-10"),
    _unidade(UTE, 1, 15.0, "2011-01-06"), _unidade(UTE, 2, 15.0, "2011-01-06"),
    _unidade(UTE, 3, 50.0, "2005-01-01", "2010-01-01"),  # desativada antes do período: fora
])
TIPO_PUBLICADO = pd.DataFrame([
    {"trecho": n, "inicio": TRECHOS.iloc[n - 1]["inicio"], "fim": TRECHOS.iloc[n - 1]["fim"], "nom_tipousina": "TÉRMICA",
     "nom_tipocombustivel": "Biomassa", "horas": h} for n, h in ((1, 528), (2, 336), (3, 144), (4, 216))])


def _serie() -> pd.DataFrame:
    horas = pd.date_range("2024-01-10 00:00", "2024-02-29 23:00", freq="h")
    valores = [22.0 if t < pd.Timestamp("2024-02-15") else 15.0 for t in horas]
    return pd.DataFrame({"din_instante": horas, "geracao_mw": valores})


@pytest.fixture
def conjunto():
    return analisar_conjunto(_serie(), TRECHOS, MEMBROS, CAPACIDADE, TIPO_PUBLICADO, "CJU_GOTEST", "Conj. Teste")


def test_trechos_de_composicao_juntam_os_trechos_com_a_mesma_composicao() -> None:
    c = trechos_de_composicao(TRECHOS)
    assert list(c["trecho"]) == [1, 2, 3]
    assert list(c["tipos"]) == ["PCH;UTE", "CGH;PCH;UTE", "CGH;PCH"]
    assert c.iloc[2]["fim"] == pd.Timestamp("2024-02-29 23:00")  # o trecho 4 da Coleta (só a modalidade) junto


def test_geracao_do_conjunto_por_trecho_com_os_tipos(conjunto) -> None:
    t = conjunto["trechos"]
    assert list(t.columns) == COLUNAS_TRECHOS
    assert list(t["usinas"]) == [2, 3, 2]
    assert list(t["horas_com_valor"]) == [22 * 24, 14 * 24, 15 * 24]
    assert list(t["geracao_media_mw"]) == [22.0, 22.0, 15.0]
    assert t.iloc[0]["energia_mwh"] == pytest.approx(22.0 * 22 * 24)
    assert conjunto["resumo"]["composicoes"] == 3 and conjunto["nivel"] == "conjunto"
    assert set(conjunto["mensal"]["trecho"]) == {1, 2, 3}


def test_potencia_das_usinas_por_trecho_sem_dividir_a_geracao(conjunto) -> None:
    t = conjunto["trechos"]
    # trecho 1: PCH 16 + UTE 30; trecho 2: a terceira unidade da PCH entra em 10/02 (em operação no trecho)
    assert list(t["potencia_somada_mw"]) == [46.0, 50.0, 20.0]
    assert list(t["usinas_sem_potencia"]) == [0, 1, 1]  # a CGH sem unidade cadastrada
    comp = conjunto["composicao"]
    assert list(comp.columns) == COLUNAS_COMPOSICAO
    cgh = comp[comp["ceg"] == CGH]
    assert cgh["potencia_mw"].isna().all() and set(cgh["usina"]) == {"CGH Gama"}
    # nenhuma geração por usina: só a geração do conjunto, por trecho e por mês (princípio VIII)
    assert not any("geracao" in coluna for coluna in comp.columns)
    assert not any("fator" in coluna for coluna in t.columns)  # nem fator de capacidade do conjunto


def test_tipo_publicado_comparado_com_a_composicao(conjunto) -> None:
    tp = conjunto["tipo_publicado"]
    assert list(tp["trecho"]) == [1, 2, 3]
    assert list(tp["corresponde"]) == [True, True, False]  # térmico só com a térmica no conjunto
    assert int(tp.iloc[2]["horas"]) == 144 + 216  # os dois trechos da Coleta do mesmo trecho de composição
    assert conjunto["resumo"]["trechos_tipo_divergente"] == 1


def test_constatacao_identifica_o_conjunto_e_a_divergencia(conjunto) -> None:
    [(titulo, texto)] = achados_conjunto(conjunto)
    assert titulo == "Composição do conjunto"
    assert texto.startswith("O conjunto Conj. Teste (CJU_GOTEST) teve 3 composições no período: de 10/01/2024 a "
                            "31/01/2024, 2 usinas (PCH e UTE), geração média do conjunto de 22,0 MWmed;")
    assert "Os números são do conjunto, sem divisão entre as usinas." in texto
    # a divergência do tipo publicado vai para a qualidade dos dados, não para a seção do conjunto
    assert "O ONS publica" not in texto
    from src.analises.conjunto import frases_tipo_publicado

    assert frases_tipo_publicado(conjunto) == [
        "O ONS publica a série do conjunto como TÉRMICA (Biomassa) de 15/02/2024 a 29/02/2024, quando a composição tem "
        "só CGH e PCH; o tipo das usinas vem do CEG."]
    assert frases_tipo_publicado({}) == []


def test_sem_a_capacidade_das_usinas_a_composicao_sai_sem_a_potencia() -> None:
    """Coleta anterior (referência congelada): sem ``capacidade_membros.csv``."""
    c = analisar_conjunto(_serie(), TRECHOS, MEMBROS, None, None, "CJU_GOTEST", "")
    assert not c["com_capacidade"] and c["trechos"]["potencia_somada_mw"].isna().all()
    assert c["tipo_publicado"].empty and "O ONS publica" not in achados_conjunto(c)[0][1]
    assert achados_conjunto(c)[0][1].startswith("O conjunto (CJU_GOTEST) teve")


@pytest.mark.parametrize("serie, trechos, membros", [
    (None, TRECHOS, MEMBROS), (_serie().iloc[0:0], TRECHOS, MEMBROS), (_serie(), None, MEMBROS),
    (_serie(), TRECHOS, MEMBROS.iloc[0:0]),
])
def test_sem_base_o_resultado_fica_vazio(serie, trechos, membros) -> None:
    assert analisar_conjunto(serie, trechos, membros) == {}
    assert achados_conjunto({}) == []


def test_horas_fora_dos_trechos_nao_entram() -> None:
    serie = pd.concat([_serie(), pd.DataFrame({"din_instante": [pd.Timestamp("2024-03-01")], "geracao_mw": [99.0]})])
    c = analisar_conjunto(serie, TRECHOS, MEMBROS, CAPACIDADE)
    assert c["trechos"]["geracao_maxima_mw"].max() == 22.0 and not math.isnan(c["trechos"]["energia_mwh"].sum())


def test_peso_da_usina_na_potencia_sem_estimar_a_geracao() -> None:
    """Decisão do usuário de 22/10/2026: o peso da usina na potência do conjunto, por composição, como fato do
    cadastro; a geração do conjunto não é dividida."""
    from src.analises.conjunto import COLUNAS_PESO, achado_usina_no_conjunto

    c = analisar_conjunto(_serie(), TRECHOS, MEMBROS, CAPACIDADE, None, "CJU_GOTEST", "Conj. Teste", PCH)
    peso = c["peso_usina"]
    assert list(peso.columns) == COLUNAS_PESO
    # trecho 1: 16 de 46 MW; trecho 2: 20 de 50 (a terceira unidade entra em 10/02); trecho 3: 20 de 20 (a CGH sem
    # unidade cadastrada)
    assert [round(p, 1) for p in peso["peso_pct"]] == [34.8, 40.0, 100.0]
    assert not any("geracao" in coluna for coluna in peso.columns)
    titulo, texto = achado_usina_no_conjunto(c, "PCH Alfa", 20.0)
    assert titulo == "A usina no conjunto"
    assert ("Peso da usina (20,0 MW) na potência das usinas do conjunto: 34,8% de 10/01/2024 a 31/01/2024, 40,0% de "
            "01/02/2024 a 14/02/2024 e 100,0% de 15/02/2024 a 29/02/2024; esse peso não estima a geração dela.") in texto
    sem_usina = analisar_conjunto(_serie(), TRECHOS, MEMBROS, CAPACIDADE, None, "CJU_GOTEST", "", "")
    assert sem_usina["peso_usina"].empty


def test_relatorio_em_duas_partes_so_com_todos_os_numeros_do_conjunto(conjunto) -> None:
    from types import SimpleNamespace

    from src.analises.conjunto import em_duas_partes

    def res(niveis, c=conjunto):
        return SimpleNamespace(conjunto=c, comum={"cobertura": {"niveis": niveis}})

    assert em_duas_partes(res({"conjunto": 10}))
    # a série própria (a Seriemas 1): a estrutura da FR-046 da spec da Geração do relatório
    assert not em_duas_partes(res({"usina": 10}))
    assert not em_duas_partes(res({"usina": 5, "conjunto": 5}))
    assert not em_duas_partes(res({"conjunto": 10}, c={}))
