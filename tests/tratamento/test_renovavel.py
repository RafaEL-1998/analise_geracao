"""Tratamento das eólicas e solares: restrição semi-horária, energia cortada, razão, fator de capacidade e membros
(spec 006, fase C; decisões R11 e R12; tarefa T100).

- energia cortada só nas semi-horas restritas; a diferença fora delas é erro da estimativa;
- semi-hora sem a marca de restrição contada e fora do total;
- hora cheia pela média das duas meias-horas; a hora com uma só meia-hora fica ausente e é contada;
- fator de capacidade com o nível e as sinalizações, sem descarte.
"""

from __future__ import annotations

import pandas as pd

from src.coleta.conjuntos import COLUNAS_AUDITORIA_COLETA
from src.coleta.registro import COLUNAS_FATOR_CAPACIDADE, DescricaoConjunto, Regra
from src.comum.caminhos import ARQUIVOS_TRATAMENTO
from src.tratamento.renovavel import (
    carregar_renovavel,
    em_hora_cheia,
    exportar_renovavel,
    montar_membros,
    montar_razao,
    montar_restricao,
    serie_da_referencia,
    tratar_fator_capacidade,
)

INICIO, FIM = pd.Timestamp("2024-02-01 00:00"), pd.Timestamp("2024-02-01 02:30")
A, B = "RESTRICAO_COFF_EOLICA_DETAIL_2024_02.parquet", "RESTRICAO_COFF_EOLICA_DETAIL-2_2024_02.parquet"


def _auditoria(*arquivos: str) -> pd.DataFrame:
    linhas = [{c: "" for c in COLUNAS_AUDITORIA_COLETA} | {"arquivo": a, "obtido": True, "status": "PROCESSADO",
                                                          "linhas_lidas": 1} for a in arquivos]
    return pd.DataFrame(linhas, columns=COLUNAS_AUDITORIA_COLETA)


def _semi(instante: str, verificada: float, estimada: float, vento: float, invalido: float, restrita: float,
          arquivo: str = A) -> dict:
    return {"din_instante": pd.Timestamp(instante), "val_geracaoestimada": estimada,
            "val_geracaoverificada": verificada, "val_ventoverificado": vento, "flg_dadoventoinvalido": invalido,
            "flg_geracaorestrita": restrita, "val_geracaoreferenciafinal": float("nan"),
            "id_ons_conjuntousina": "", "nom_modalidadeoperacao": "TIPO II-C", "_nao_numerico": False,
            "arquivo_origem": arquivo}


def _restricao_eol() -> pd.DataFrame:
    nan = float("nan")
    return pd.DataFrame([
        _semi("2024-02-01 00:00", 10.0, 20.0, 8.0, 0, 1),  # restrita: (20 − 10) × 0,5 = 5 MWh
        _semi("2024-02-01 00:30", 12.0, 10.0, 8.0, 0, 1),  # restrita, verificada acima da estimada: 0
        _semi("2024-02-01 01:00", 10.0, 30.0, 9.0, 1, 0),  # fora da restrição: erro da estimativa, não entra
        _semi("2024-02-01 01:30", 10.0, 14.0, 9.0, 0, nan),  # sem a marca: contada e fora do total
        _semi("2024-02-01 02:00", 25.0, 30.0, 9.5, 0, 1),
        _semi("2024-02-01 02:00", 20.0, 30.0, 9.5, 0, 1, B),  # publicado por último: vale este (5 MWh)
    ])


def _razao() -> pd.DataFrame:
    linhas = [{"din_instante": pd.Timestamp(i), "val_geracao": 30.0, "val_geracaolimitada": 20.0,
               "val_disponibilidade": 40.0, "val_geracaoreferencia": 35.0, "num_minutos_rel": rel,
               "num_minutos_cnf": cnf, "num_minutos_ene": ene, "cod_razaorestricao": cod, "_nao_numerico": False,
               "arquivo_origem": "RESTRICAO_COFF_EOLICA_2024_02.parquet"}
              for i, cod, rel, cnf, ene in [("2024-02-01 00:00", "rel", 30, 0, 0), ("2024-02-01 00:30", " CNF", 0, 30, 0),
                                            ("2024-02-01 02:00", "ENE", 0, 0, 30), ("2024-02-02 00:00", "REL", 30, 0, 0)]]
    return pd.DataFrame(linhas)


def _tratada():
    razao = montar_razao(_razao(), _auditoria("RESTRICAO_COFF_EOLICA_2024_02.parquet"), "conjunto", INICIO, FIM)
    return montar_restricao(_restricao_eol(), _auditoria(A, B), "EOL", INICIO, FIM, razao), razao


def test_razao_da_restricao_por_semi_hora_com_o_nivel() -> None:
    _, razao = _tratada()
    assert list(razao["cod_razaorestricao"]) == ["REL", "CNF", "ENE"]  # normalizada; fora do período fica de fora
    assert set(razao["nivel"]) == {"conjunto"}
    assert razao.loc[2, "num_minutos_ene"] == 30


def test_energia_cortada_so_nas_semi_horas_restritas() -> None:
    r, _ = _tratada()
    s = r.semi_horaria.set_index("din_instante")
    assert len(s) == 5 and s.loc["2024-02-01 02:00", "val_geracaoverificada"] == 20.0
    assert s["energia_cortada_mwh"].tolist()[:3] == [5.0, 0.0, 0.0]
    assert pd.isna(s.loc["2024-02-01 01:30", "energia_cortada_mwh"])  # sem a marca
    assert s.loc["2024-02-01 01:30", "sem_marca_restricao"] and not s.loc["2024-02-01 01:00", "restrita"]
    assert s.loc["2024-02-01 01:00", "sinal_recurso_invalido"]  # sinalizada, mantida na base
    assert s.loc["2024-02-01 00:00", "val_recurso"] == 8.0
    # a razão da semi-hora, com o nível dela
    assert s.loc["2024-02-01 00:00", "cod_razaorestricao"] == "REL" and s.loc["2024-02-01 00:00", "nivel_razao"] == "conjunto"
    assert s.loc["2024-02-01 01:00", "cod_razaorestricao"] == ""
    assert r.resumo == {"semi_horas": 5, "horas": 2, "horas_ausentes": 1, "semi_horas_restritas": 3,
                        "semi_horas_sem_marca": 1, "semi_horas_recurso_invalido": 1, "energia_cortada_mwh": 10.0,
                        "duplicatas_conflitantes": 1}
    assert r.auditoria.set_index("arquivo")[["horas_usina", "duplicatas_conflitantes"]].to_dict("index") == {
        A: {"horas_usina": 5, "duplicatas_conflitantes": 1}, B: {"horas_usina": 1, "duplicatas_conflitantes": 0}}


def test_hora_cheia_pela_media_das_duas_meias_horas() -> None:
    r, _ = _tratada()
    h = r.horaria.set_index("din_instante")
    assert list(h.index) == [pd.Timestamp("2024-02-01 00:00"), pd.Timestamp("2024-02-01 01:00")]
    assert h.loc["2024-02-01 00:00", ["val_geracaoverificada", "val_geracaoestimada"]].tolist() == [11.0, 15.0]
    assert h.loc["2024-02-01 00:00", "semi_horas_restritas"] == 2 and h.loc["2024-02-01 00:00", "energia_cortada_mwh"] == 5.0
    assert h.loc["2024-02-01 01:00", "semi_horas_recurso_invalido"] == 1
    # a hora 02h tem só uma meia-hora: fica ausente, nunca preenchida
    assert r.ausencias[["tipo", "horas"]].to_dict("records") == [{"tipo": "HORAS", "horas": 1}]
    assert r.ausencias.loc[0, "inicio"] == pd.Timestamp("2024-02-01 02:00")
    assert em_hora_cheia(pd.DataFrame(), ["val_geracaoverificada"]).empty


def test_fotovoltaica_sem_as_colunas_da_marca() -> None:
    """Arquivo de 2024 da fotovoltaica sem as cinco colunas novas: a Coleta as deixa vazias; nenhuma semi-hora entra
    na energia cortada, todas contadas como sem a marca."""
    linhas = [{"din_instante": pd.Timestamp("2024-02-01 00:00") + pd.Timedelta(minutes=30 * i),
               "val_geracaoestimada": 40.0, "val_geracaoverificada": 10.0, "val_irradianciaverificado": 800.0,
               "flg_dadoirradianciainvalido": 0.0, "flg_geracaorestrita": float("nan"),
               "val_geracaoreferenciafinal": float("nan"), "_nao_numerico": False,
               "arquivo_origem": "RESTRICAO_COFF_FOTOVOLTAICA_DETAIL_2024_02.parquet"} for i in range(6)]
    r = montar_restricao(pd.DataFrame(linhas), _auditoria("RESTRICAO_COFF_FOTOVOLTAICA_DETAIL_2024_02.parquet"),
                         "UFV", INICIO, FIM)
    assert r.semi_horaria["val_recurso"].eq(800.0).all() and r.semi_horaria["sem_marca_restricao"].all()
    assert r.resumo["energia_cortada_mwh"] == 0.0 and r.resumo["semi_horas_sem_marca"] == 6
    assert len(r.horaria) == 3 and r.ausencias.empty


def test_restricao_como_serie_de_referencia() -> None:
    r, _ = _tratada()
    serie = serie_da_referencia(r)
    assert serie.horaria["val_geracao"].tolist() == [11.0, 10.0]
    assert serie.ausencias.equals(r.ausencias)


def test_fator_capacidade_com_nivel_e_sinalizacoes(tmp_path) -> None:
    desc = DescricaoConjunto(pacote="fator-capacidade-2", pasta="fator_capacidade_2",
                             identificador=Regra("id_ons", "GOCJUF"), conferencias=(),
                             colunas_valor=COLUNAS_FATOR_CAPACIDADE, nivel="conjunto")
    arquivo = "FATOR_CAPACIDADE-2_2024_02.parquet"
    linhas = [{"din_instante": pd.Timestamp(f"2024-02-01 0{h}:00"), "val_geracaoprogramada": 12.0,
               "val_geracaoverificada": v, "val_capacidadeinstalada": 30.0, "val_fatorcapacidade": fc,
               "_nao_numerico": False, "arquivo_origem": arquivo}
              for h, v, fc in [(0, 10.0, 0.33), (1, 31.5, 1.05), (2, 30.8, 1.0)]]
    serie = tratar_fator_capacidade(desc, pd.DataFrame(linhas), _auditoria(arquivo), INICIO, pd.Timestamp("2024-02-01 02:00"),
                                    tmp_path)
    h = serie.horaria
    assert h["nivel"].eq("conjunto").all()
    assert h["sinal_fc_fora_0_1"].tolist() == [False, True, False]
    assert h["sinal_acima_capacidade"].tolist() == [False, True, False]  # 30,8 MW fica na folga de 1 MW
    gravado = pd.read_csv(tmp_path / ARQUIVOS_TRATAMENTO["fator_capacidade_horario"], sep=";")
    assert len(gravado) == 3 and "_ordem" not in gravado.columns
    assert (tmp_path / ARQUIVOS_TRATAMENTO["fator_capacidade_ausencias"]).exists()


def test_membros_em_hora_cheia_por_id() -> None:
    meia = pd.Timedelta(minutes=30)
    extraido = pd.concat([
        pd.DataFrame({"din_instante": [INICIO + i * meia for i in range(3)], "val_geracaoverificada": [4.0, 6.0, 8.0],
                      "id_ons": "MSSRI2"}),
        pd.DataFrame({"din_instante": [INICIO + i * meia for i in range(4)], "val_geracaoverificada": 2.0,
                      "id_ons": "MSSRI3"}),
    ])
    m = montar_membros(extraido, INICIO, FIM)
    assert m.groupby("id_ons").size().to_dict() == {"MSSRI2": 1, "MSSRI3": 2}  # só as horas completas
    assert m[m["id_ons"] == "MSSRI2"]["val_geracaoverificada"].iloc[0] == 5.0
    assert montar_membros(None, INICIO, FIM).empty


def test_gravacao_e_leitura(tmp_path) -> None:
    r, razao = _tratada()
    exportar_renovavel(tmp_path, r, razao, pd.DataFrame())
    lido = carregar_renovavel(tmp_path)
    s = lido["restricao_semi_horaria"]
    assert s["restrita"].tolist() == r.semi_horaria["restrita"].tolist()
    assert s["sem_marca_restricao"].sum() == 1 and s["cod_razaorestricao"].tolist()[2] == ""
    assert len(lido["restricao_horaria"]) == 2 and len(lido["restricao_razao_semi_horaria"]) == 3
    assert lido["restricao_ausencias"].loc[0, "inicio"] == pd.Timestamp("2024-02-01 02:00")
    assert lido["fator_capacidade_horario"] is None and lido["restricao_membros_horaria"] is None
