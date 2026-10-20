"""Seções de térmica das Análises (spec 006, fase B; decisão R18; tarefa T081).

- geração por motivo, com as parcelas, e a inflexibilidade programada e verificada;
- atendimento: horas e energia abaixo e acima, e os maiores desvios;
- horas disponíveis sem despacho;
- CVU × CMO por semana e por unidade, sem julgamento;
- térmica sem geração no período: nenhuma divisão por zero, e a constatação de usina disponível e não despachada (US2-5).
"""

from __future__ import annotations

import math

import pandas as pd

from src.analises.termica import achados_termica, analisar_termica
from src.coleta.registro import COLUNAS_DESPACHO_PROGRAMADO, COLUNAS_DESPACHO_VERIFICADO
from src.comum.regras import LIMIAR_DESVIO_DESPACHO_MW
from src.tratamento.termica import DespachoTratado, SemanalTratado, somar_unidades

# Duas semanas operativas inteiras: 06/01/2024 (sábado) a 19/01/2024 (sexta)
HORAS = pd.date_range("2024-01-06 00:00", "2024-01-19 23:00", freq="h")
PROIBIDOS = ("satisfatório", "insatisfatório", "descumpr", "deficiente", "falha do agente", "culpa", "deveria")


def _unidades(programado_902, verificado_902, inflex_prog, inflex_verif) -> pd.DataFrame:
    linhas = pd.DataFrame({c: 0.0 for c in COLUNAS_DESPACHO_PROGRAMADO + COLUNAS_DESPACHO_VERIFICADO}, index=HORAS)
    u902 = linhas.copy()
    u902["val_proggeracao"] = programado_902
    u902["val_progordemmerito"] = programado_902 - inflex_prog
    u902["val_proginflexibilidade"] = inflex_prog
    u902["val_verifgeracao"] = verificado_902
    u902["val_verifordemmerito"] = verificado_902 - inflex_verif
    u902["val_verifinflexibilidade"] = inflex_verif
    u903 = linhas.copy()  # a unidade a óleo, nunca despachada
    partes = [u902.assign(codigo=902), u903.assign(codigo=903)]
    return pd.concat(partes).rename_axis("din_instante").reset_index()


def _despacho(**valores) -> DespachoTratado:
    unidades = _unidades(**valores)
    return DespachoTratado(unidades=unidades, horario=somar_unidades(unidades))


def _base(disponibilidade) -> pd.DataFrame:
    return pd.DataFrame({"din_instante": HORAS, "nivel": "usina", "geracao_mw": 0.0,
                         "disponibilidade_operacional_mw": disponibilidade})


def _semanais(cvu_902_semana2: float = 400.0):
    semanas = pd.to_datetime(["2024-01-06", "2024-01-13"])
    cvu = pd.DataFrame({"codigo": [902, 903, 902, 903], "semana_inicio": [semanas[0], semanas[0], semanas[1], semanas[1]],
                        "semana_fim": [semanas[0] + pd.Timedelta(days=6)] * 2 + [semanas[1] + pd.Timedelta(days=6)] * 2,
                        "val_cvu": [300.0, 900.0, cvu_902_semana2, None], "sinal_cvu": ["", "", "", "ausente"]})
    cmo = pd.DataFrame({"semana_inicio": semanas, "semana_fim": semanas + pd.Timedelta(days=6),
                        "val_cmomediasemanal": [500.0, 350.0]})
    return SemanalTratado(semanal=cvu), SemanalTratado(semanal=cmo)


def _cenario():
    hora = HORAS.hour.to_numpy()
    dia = HORAS.day.to_numpy()
    programado = ((hora >= 8) & (hora <= 21)) * 100.0
    verificado = programado.copy()
    verificado[(dia == 8) & (programado > 0)] = 40.0  # 14 h a 60 MW abaixo da programada
    verificado[(dia == 9) & (hora == 22)] = 50.0  # 1 h sem programação, 50 MW acima
    inflex_prog = ((hora >= 8) & (hora <= 21)) * 30.0
    inflex_verif = inflex_prog.copy()
    inflex_verif[(dia == 8) & (inflex_prog > 0)] = 10.0
    despacho = _despacho(programado_902=programado, verificado_902=verificado, inflex_prog=inflex_prog,
                         inflex_verif=inflex_verif)
    disponibilidade = pd.Series(120.0, index=range(len(HORAS)))
    disponibilidade[(HORAS.day == 19).nonzero()[0]] = 0.0  # indisponível na última sexta
    cvu, cmo = _semanais()
    return analisar_termica(despacho, _base(disponibilidade.to_numpy()), cvu, cmo)


def test_geracao_por_motivo_com_as_parcelas_e_a_inflexibilidade() -> None:
    t = _cenario()
    anual = t["motivos_anual"].set_index("motivo")
    total = anual.loc["Geração total"]
    assert total["programado_mwh"] == 14 * 14 * 100.0
    assert total["verificado_mwh"] == 13 * 14 * 100.0 + 14 * 40.0 + 50.0
    assert anual.loc["Inflexibilidade", "verificado_mwh"] == 13 * 14 * 30.0 + 14 * 10.0
    assert math.isclose(anual.loc["Inflexibilidade", "parcela_programado_pct"], 30.0)
    assert "Exportação" not in anual.index  # só os motivos com energia
    mensal = t["inflexibilidade"].iloc[0]
    assert (mensal["programada_mwh"], mensal["verificada_mwh"], mensal["nao_verificada_mwh"]) == (
        14 * 14 * 30.0, 13 * 14 * 30.0 + 14 * 10.0, 14 * 20.0)
    assert math.isclose(t["inflexibilidade_resumo"]["nao_verificada_pct"], 14 * 20.0 / (14 * 14 * 30.0) * 100)
    assert t["codigos"] == [902, 903] and t["horas_com_despacho"] == 14 * 14


def test_atendimento_abaixo_acima_e_maiores_desvios() -> None:
    a = _cenario()["atendimento"]
    r = a["resumo"]
    assert (r["horas_programadas"], r["horas_abaixo"], r["energia_abaixo_mwh"]) == (196, 14, 14 * 60.0)
    assert (r["horas_acima"], r["horas_sem_programacao"], r["energia_sem_programacao_mwh"]) == (0, 1, 50.0)
    assert r["limiar_mw"] == LIMIAR_DESVIO_DESPACHO_MW
    assert len(a["maiores_desvios"]) == 14 and set(a["maiores_desvios"]["desvio_mw"]) == {-60.0}
    assert a["anual"].iloc[0]["horas_abaixo"] == 14


def test_horas_disponiveis_sem_despacho() -> None:
    d = _cenario()["disponivel_sem_despacho"]["resumo"]
    # fora das 8h-21h, disponível e sem geração, menos a hora 22h do dia 9 (com geração) e a sexta indisponível
    esperado = 13 * 10 - 1
    assert d["horas"] == esperado and d["horas_comuns"] == len(HORAS)
    assert d["potencia_disponivel_media_mw"] == 120.0


def test_cvu_e_cmo_por_semana_e_por_unidade_sem_julgamento() -> None:
    t = _cenario()
    c = t["cvu_cmo"]
    s = c["semanal"].set_index(["codigo", "semana_inicio"])
    assert s.loc[(902, pd.Timestamp("2024-01-06")), "relacao"] == "abaixo"  # 300 < 500
    assert s.loc[(903, pd.Timestamp("2024-01-06")), "relacao"] == "acima"  # 900 > 500
    assert s.loc[(902, pd.Timestamp("2024-01-13")), "relacao"] == "acima"  # 400 > 350
    assert s.loc[(903, pd.Timestamp("2024-01-13")), "relacao"] == "sem comparação"  # CVU ausente
    assert s.loc[(902, pd.Timestamp("2024-01-06")), "geracao_mwh"] == 7 * 14 * 100.0 - 14 * 60.0 + 50.0
    resumo = c["resumo"].set_index("codigo")
    assert (resumo.loc[902, "semanas_abaixo"], resumo.loc[902, "semanas_acima"]) == (1, 1)
    assert resumo.loc[903, "semanas_cvu_sinalizado"] == 1 and resumo.loc[903, "semanas_sem_comparacao"] == 1
    assert (resumo[["semanas_abaixo", "semanas_acima", "semanas_igual", "semanas_sem_comparacao"]].sum(axis=1)
            == resumo["semanas"]).all()  # as colunas da tabela fecham o total de semanas
    # C13: horas disponíveis sem despacho só na semana com algum CVU abaixo do CMO (a primeira)
    assert c["horas_disponivel_cvu_abaixo"] == 7 * 10 - 1 and c["semanas_disponivel_cvu_abaixo"] == 1
    textos = " ".join(texto for _, texto in achados_termica(t))
    assert "CVU abaixo do CMO" in textos and not any(p in textos.lower() for p in PROIBIDOS)


def test_termica_sem_geracao_no_periodo() -> None:
    zeros = pd.Series(0.0, index=range(len(HORAS))).to_numpy()
    despacho = _despacho(programado_902=zeros, verificado_902=zeros, inflex_prog=zeros, inflex_verif=zeros)
    cvu, cmo = _semanais()
    t = analisar_termica(despacho, _base(120.0), cvu, cmo)
    assert t["sem_geracao"] and t["geracao_verificada_mwh"] == 0.0
    total = t["motivos_anual"].set_index("motivo").loc["Geração total"]
    assert math.isnan(total["parcela_verificado_pct"])  # nenhuma divisão por zero
    assert list(t["motivos_anual"]["motivo"]) == ["Geração total"]
    assert math.isnan(t["inflexibilidade_resumo"]["nao_verificada_pct"])
    assert t["atendimento"]["resumo"]["horas_programadas"] == 0
    assert math.isnan(t["atendimento"]["resumo"]["desvio_medio_mw"])
    titulo, texto = achados_termica(t)[0]
    assert titulo == "Despacho por motivo" and texto.startswith("A usina não gerou de 06/01/2024 a 19/01/2024")
    assert f"Ficou disponível e não foi despachada em {len(HORAS)} horas" in texto.replace(".", "")
    assert analisar_termica(None, _base(120.0)) == {}
