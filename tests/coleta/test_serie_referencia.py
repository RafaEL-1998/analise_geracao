"""Série de referência, período e trechos da Coleta (spec 006, decisões R6 e R7; data-model, seções 5.1 e 5.2).

A série de referência define o período: a EVT nas hidrelétricas com EVT (caminho de hoje, sem trechos); a Geração por
usina pelo id ONS na usina com geração própria; a Geração por usina do conjunto, pelo id do conjunto, na usina em
conjunto sem série própria. A série é varrida em todos os arquivos publicados.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pandas as pd
import pytest

from src.coleta import serie_referencia as sr
from src.comum.perfil import carregar_perfil


def _perfil(tipo: str, cobertura: Dict[str, Any], id_ons: str = "GOUSIN", id_conjunto: str = "CJU_GOCONJ",
            planejamento=()) -> SimpleNamespace:
    ceg = f"{tipo}.XX.GO.000001-0.01"
    ident = SimpleNamespace(ceg=ceg, id_ons=id_ons, id_conjunto=id_conjunto, cod_usina=None, nome_ons=None,
                            id_reservatorio=None, planejamento=tuple(planejamento))
    usina = SimpleNamespace(slug="teste", estado="GO", tipo=tipo, modalidade="TIPO II-C")
    return SimpleNamespace(usina=usina, identificacao=ident, cobertura=cobertura)


# ---------------------------------------------------------------------------
# Escolha da série (decisão R6, linhas da fase A)
# ---------------------------------------------------------------------------


def test_hidreletrica_com_evt_segue_o_caminho_de_hoje() -> None:
    escolha = sr.escolher(carregar_perfil("sao_domingos"))
    assert (escolha.conjunto, escolha.niveis) == ("evt", ("usina",))
    assert "Energia Vertida Turbinável" in escolha.motivo
    pch = sr.escolher(_perfil("PCH", {"evt": "proprio", "geracao": "conjunto"}))
    assert pch.conjunto == "evt"


@pytest.mark.parametrize("tipo, cobertura, niveis", [
    ("UTE", {"geracao": "proprio"}, ("usina",)),
    ("UHE", {"geracao": "proprio", "evt": "ausente"}, ("usina",)),
    ("PCH", {"geracao": "conjunto", "evt": "ausente"}, ("conjunto",)),
    ("UFV", {"geracao": "conjunto"}, ("conjunto",)),
    ("EOL", {"geracao": ["proprio", "conjunto"]}, ("usina", "conjunto")),
])
def test_geracao_por_usina_pelo_id_ons_ou_pelo_conjunto(tipo: str, cobertura: Dict[str, Any], niveis) -> None:
    escolha = sr.escolher(_perfil(tipo, cobertura))
    assert (escolha.conjunto, escolha.niveis) == ("geracao", niveis)
    descricoes = sr.descricoes_referencia(_perfil(tipo, cobertura), escolha)
    assert list(descricoes) == list(niveis)
    if "conjunto" in descricoes:
        assert descricoes["conjunto"].identificador.valor == "CJU_GOCONJ"
    if "usina" in descricoes:
        assert descricoes["usina"].identificador.valor == "GOUSIN"
    assert all(d.colunas_texto == ("cod_modalidadeoperacao",) for d in descricoes.values())


def test_sem_serie_de_referencia_e_erro() -> None:
    with pytest.raises(ValueError, match="série de referência"):
        sr.escolher(_perfil("UTE", {"geracao": "ausente"}))


# ---------------------------------------------------------------------------
# Varredura e período
# ---------------------------------------------------------------------------


def _geracao(raw: Path, mes: str, linhas: List[Dict[str, Any]]) -> None:
    tabela = pd.DataFrame(linhas)
    (raw / "geracao_usina_2").mkdir(parents=True, exist_ok=True)
    tabela.to_parquet(raw / "geracao_usina_2" / f"GERACAO_USINA-2_{mes}.parquet", index=False)


def _linha(t: str, id_ons: str, valor, modalidade: str = "TIPO I", ceg: str = "UTE.XX.GO.000001-0.01") -> Dict:
    return {"din_instante": pd.Timestamp(t), "id_estado": "GO", "cod_modalidadeoperacao": modalidade,
            "id_ons": id_ons, "ceg": ceg, "val_geracao": valor}


def test_varredura_de_todos_os_arquivos_e_periodo_so_com_valor(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    _geracao(raw, "2019_06", [_linha("2019-06-01 00:00", "GOUSIN", None), _linha("2019-06-01 01:00", "GOUSIN", 5.0)])
    _geracao(raw, "2021_03", [_linha("2021-03-10 05:00", "GOUSIN", 7.0)])
    _geracao(raw, "2024_12", [_linha("2024-12-31 22:00", "GOUSIN", 8.0), _linha("2024-12-31 23:00", "GOUSIN", None),
                              _linha("2024-12-31 23:00", "OUTRA", 9.0)])
    perfil = _perfil("UTE", {"geracao": "proprio"})
    escolha = sr.escolher(perfil)
    series, auditoria = sr.extrair_referencia(perfil, escolha, raw)
    assert len(auditoria) == 3  # todos os arquivos publicados, sem recorte de período
    inicio, fim = sr.periodo(series)
    assert (inicio, fim) == (pd.Timestamp("2019-06-01 01:00"), pd.Timestamp("2024-12-31 22:00"))
    resumo = sr.resumo(escolha, perfil, inicio, fim, auditoria)
    assert resumo == {"conjunto": "geracao", "identificador": "id_ons=GOUSIN", "inicio": "2019-06-01 01:00:00",
                      "fim": "2024-12-31 22:00:00", "arquivos_varridos": 3, "motivo": escolha.motivo}


def test_periodo_com_as_duas_series_e_a_uniao(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    ceg = "EOL.XX.GO.000001-0.01"
    _geracao(raw, "2022_01", [_linha("2022-01-01 00:00", "CJU_GOCONJ", 3.0, "Conjunto de Usinas", "-"),
                              _linha("2022-01-02 00:00", "CJU_GOCONJ", 3.0, "Conjunto de Usinas", "-")])
    _geracao(raw, "2023_05", [_linha("2023-05-05 10:00", "GOUSIN", 4.0, "TIPO I", ceg)])
    perfil = _perfil("EOL", {"geracao": ["proprio", "conjunto"]})
    series, _ = sr.extrair_referencia(perfil, sr.escolher(perfil), raw)
    assert sr.periodo(series) == (pd.Timestamp("2022-01-01 00:00"), pd.Timestamp("2023-05-05 10:00"))
    complemento = sr.complemento(series)
    assert list(complemento.columns) == ["din_instante", "cod_modalidadeoperacao", "nivel"]
    assert list(complemento["nivel"]) == ["conjunto", "conjunto", "usina"]


def test_periodo_vazio_sem_nenhuma_hora_com_valor() -> None:
    assert sr.periodo({"usina": pd.DataFrame({"din_instante": [pd.Timestamp("2024-01-01")],
                                              "val_geracao": [float("nan")]})}) == (None, None)


# ---------------------------------------------------------------------------
# Trechos (decisão R7; data-model 5.2)
# ---------------------------------------------------------------------------


def _complemento(*partes) -> pd.DataFrame:
    linhas = []
    for inicio, fim, modalidade, nivel in partes:
        for t in pd.date_range(inicio, fim, freq="h"):
            linhas.append({"din_instante": t, "cod_modalidadeoperacao": modalidade, "nivel": nivel})
    return pd.DataFrame(linhas)


COMPOSICAO = pd.DataFrame([
    {"id_conjunto": "CJU_GOCONJ", "ceg": "PCH.XX.GO.000001-0.01", "tipo": "PCH", "inicio": "2019-08-22", "fim": ""},
    {"id_conjunto": "CJU_GOCONJ", "ceg": "UTE.XX.GO.000009-0.01", "tipo": "UTE", "inicio": "2019-08-22",
     "fim": "2025-07-01"},
])


def test_trechos_pela_composicao_com_mostrar() -> None:
    comp = _complemento(("2025-06-30 00:00", "2025-07-01 23:00", "Conjunto de Usinas", "conjunto"))
    trechos = sr.trechos(comp, COMPOSICAO, (), "CJU_GOCONJ")
    assert list(trechos.columns) == ["trecho", "inicio", "fim", "modalidade", "id_conjunto", "composicao",
                                     "tipos_composicao", "codigos_planejamento", "nivel_geracao", "mostrar"]
    assert list(trechos["inicio"]) == ["2025-06-30 00:00:00", "2025-07-01 00:00:00"]
    assert list(trechos["fim"]) == ["2025-06-30 23:00:00", "2025-07-01 23:00:00"]
    assert list(trechos["tipos_composicao"]) == ["PCH;UTE", "PCH"]
    assert list(trechos["composicao"]) == ["PCH.XX.GO.000001-0.01;UTE.XX.GO.000009-0.01", "PCH.XX.GO.000001-0.01"]
    assert list(trechos["mostrar"]) == [True, True]
    assert list(trechos["trecho"]) == [1, 2]


def test_mudanca_de_modalidade_sem_mudanca_de_nivel_nao_e_mostrada() -> None:
    comp = _complemento(("2024-01-01 00:00", "2024-01-01 02:00", "TIPO II-B", "usina"),
                        ("2024-01-01 03:00", "2024-01-01 05:00", "TIPO I", "usina"))
    trechos = sr.trechos(comp, pd.DataFrame(columns=COMPOSICAO.columns), (), "")
    assert list(trechos["modalidade"]) == ["TIPO II-B", "TIPO I"]
    assert list(trechos["mostrar"]) == [False, False]


def test_mudanca_de_nivel_e_mostrada() -> None:
    comp = _complemento(("2024-01-01 00:00", "2024-01-01 02:00", "Conjunto de Usinas", "conjunto"),
                        ("2024-01-01 03:00", "2024-01-01 05:00", "TIPO II-C", "usina"))
    trechos = sr.trechos(comp, pd.DataFrame(columns=COMPOSICAO.columns), (), "CJU_GOCONJ")
    assert list(trechos["nivel_geracao"]) == ["conjunto", "usina"] and list(trechos["mostrar"]) == [True, True]


def test_codigos_de_planejamento_por_trecho() -> None:
    planejamento = [SimpleNamespace(codigo=34, inicio="2018-01", fim="2018-08"),
                    SimpleNamespace(codigo=334, inicio="2018-09", fim="")]
    comp = _complemento(("2018-08-31 22:00", "2018-09-01 01:00", "TIPO I", "usina"))
    trechos = sr.trechos(comp, pd.DataFrame(columns=COMPOSICAO.columns), planejamento, "")
    assert list(trechos["codigos_planejamento"]) == ["34", "334"]
    assert list(trechos["mostrar"]) == [False, False]  # código muda sem mudar nível nem composição


def test_um_so_trecho_nao_e_mostrado() -> None:
    comp = _complemento(("2024-01-01 00:00", "2024-01-02 00:00", "TIPO I", "usina"))
    trechos = sr.trechos(comp, pd.DataFrame(columns=COMPOSICAO.columns), (), "")
    assert len(trechos) == 1 and not trechos["mostrar"].iloc[0]
