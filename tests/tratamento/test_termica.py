"""Tratamento das térmicas: despacho, CVU e CMO (spec 006, fase B; decisão R11; tarefa T079).

- ``despacho_horario.csv``: a soma das unidades por hora, por motivo, programado e verificado;
- ``despacho_unidades_horario.csv``: o mesmo, por unidade;
- ``cvu_semanal.csv``: só a revisão mais recente, com ``sinal_cvu`` em CVU ausente ou negativo;
- ``cmo_semanal.csv``: sem duplicatas, contadas;
- semanais levadas à hora pelo intervalo da semana operativa.
"""

from __future__ import annotations

import pandas as pd

from src.coleta.conjuntos import COLUNAS_AUDITORIA_COLETA
from src.coleta.registro import COLUNAS_CMO, COLUNAS_DESPACHO_PROGRAMADO, COLUNAS_DESPACHO_VERIFICADO
from src.comum.perfil import Planejamento
from src.tratamento.termica import (
    SINAL_CVU_AUSENTE,
    SINAL_CVU_NEGATIVO,
    SINAL_CVU_ZERO,
    carregar_despacho_tratado,
    carregar_semanal_tratado,
    exportar_termica,
    inicio_da_semana_operativa,
    montar_cmo,
    montar_cvu,
    montar_despacho,
    semanal_em_horas,
)

PLANEJAMENTO = (Planejamento(901, "2023-01", "2023-12"), Planejamento(902, "2024-01", ""),
                Planejamento(903, "2024-01", ""))
INICIO, FIM = pd.Timestamp("2023-12-31 22:00"), pd.Timestamp("2024-01-01 03:00")


def _auditoria(*arquivos: str) -> pd.DataFrame:
    linhas = [{c: "" for c in COLUNAS_AUDITORIA_COLETA} | {"arquivo": a, "obtido": True, "status": "PROCESSADO",
                                                          "linhas_lidas": 1} for a in arquivos]
    return pd.DataFrame(linhas, columns=COLUNAS_AUDITORIA_COLETA)


def _linha(instante: str, codigo: float, merito: float, inflex: float, verificado: float, arquivo: str) -> dict:
    linha = {c: 0.0 for c in COLUNAS_DESPACHO_PROGRAMADO + COLUNAS_DESPACHO_VERIFICADO}
    linha.update(din_instante=pd.Timestamp(instante), cod_usinaplanejamento=codigo, nom_tipopatamar="LEVE",
                 tip_restricaoeletrica=0.0, val_proggeracao=merito + inflex, val_progordemmerito=merito,
                 val_proginflexibilidade=inflex, val_verifgeracao=verificado, val_verifinflexibilidade=inflex,
                 val_verifordemmerito=verificado - inflex, _nao_numerico=False, arquivo_origem=arquivo)
    return linha


def _despacho():
    linhas = [
        _linha("2023-12-31 22:00", 901, 0.0, 0.0, 0.0, "D_2023.parquet"),
        _linha("2023-12-31 23:00", 901, 0.0, 0.0, 0.0, "D_2023.parquet"),
        # 2024: duas unidades; a 903 sem a hora 02h; o arquivo anual repete o mensal, com um valor republicado
        *[_linha(f"2024-01-01 0{h}:00", 902, 60.0, 30.0, 85.0, "D_2024.parquet") for h in range(4)],
        *[_linha(f"2024-01-01 0{h}:00", 903, 10.0, 0.0, 10.0, "D_2024.parquet") for h in (0, 1, 3)],
        _linha("2024-01-01 00:00", 902, 60.0, 30.0, 80.0, "D-2_2024_01.parquet"),  # publicado por último: vale este
        _linha("2024-01-01 01:00", 902, 60.0, 30.0, 85.0, "D-2_2024_01.parquet"),  # repetido, mesmo valor
        _linha("2024-01-01 00:00", 901, 5.0, 0.0, 5.0, "D-2_2024_01.parquet"),  # 901 fora do período dele
    ]
    return pd.DataFrame(linhas), _auditoria("D_2023.parquet", "D_2024.parquet", "D-2_2024_01.parquet")


def test_despacho_por_unidade_e_a_soma_por_hora(tmp_path) -> None:
    extraido, auditoria = _despacho()
    d = montar_despacho(extraido, auditoria, PLANEJAMENTO, INICIO, FIM)
    u = d.unidades
    assert len(u) == 2 + 4 + 3 and set(u["codigo"]) == {901, 902, 903}
    assert u[(u["codigo"] == 902) & (u["din_instante"] == pd.Timestamp("2024-01-01 00:00"))]["val_verifgeracao"].iloc[0] \
        == 80.0  # o arquivo publicado por último
    h = d.horario.set_index("din_instante")
    assert list(h.columns[:2]) == ["unidades", "codigos"]
    assert h.loc["2024-01-01 00:00", "val_verifgeracao"] == 90.0 and h.loc["2024-01-01 00:00", "codigos"] == "902;903"
    assert h.loc["2024-01-01 02:00", "val_proggeracao"] == 90.0 and h.loc["2024-01-01 02:00", "unidades"] == 1
    assert h.loc["2024-01-01 01:00", "val_proginflexibilidade"] == 30.0  # por motivo
    assert h.loc["2023-12-31 23:00", "val_verifgeracao"] == 0.0
    # a hora 02h da 903 está ausente, nunca preenchida; a auditoria conta a repetição conflitante
    assert d.ausencias[["codigo", "horas"]].to_dict("records") == [{"codigo": 903, "horas": 1}]
    assert d.auditoria.set_index("arquivo")["duplicatas_conflitantes"].to_dict() == {
        "D_2023.parquet": 0, "D_2024.parquet": 1, "D-2_2024_01.parquet": 0}
    exportar_termica(tmp_path, despacho=d)
    lido = carregar_despacho_tratado(tmp_path)
    assert len(lido.horario) == len(d.horario) and len(lido.unidades) == len(u)
    assert carregar_despacho_tratado(tmp_path / "nada") is None


def _cvu():
    def linha(semana: str, codigo: int, revisao: int, valor, arquivo: str) -> dict:
        inicio = pd.Timestamp(semana)
        return {"din_instante": inicio, "cod_usinaplanejamento": float(codigo), "num_revisao": float(revisao),
                "val_cvu": valor, "dat_iniciosemana": str(inicio.date()),
                "dat_fimsemana": str((inicio + pd.Timedelta(days=6)).date()), "_nao_numerico": False,
                "arquivo_origem": arquivo}
    linhas = [linha("2023-12-30", 901, 0, 300.0, "C_2024.parquet"), linha("2023-12-30", 901, 1, 320.0, "C_2024.parquet"),
              linha("2024-01-06", 902, 0, -5.0, "C_2024.parquet"), linha("2024-01-06", 903, 0, None, "C_2024.parquet"),
              linha("2023-12-30", 902, 0, 400.0, "C_2024.parquet"), linha("2023-12-30", 903, 0, 0.0, "C_2024.parquet")]
    return pd.DataFrame(linhas), _auditoria("C_2024.parquet")


def test_cvu_pela_revisao_mais_recente_com_o_sinal(tmp_path) -> None:
    extraido, auditoria = _cvu()
    c = montar_cvu(extraido, auditoria, PLANEJAMENTO, pd.Timestamp("2023-12-31"), pd.Timestamp("2024-01-12 23:00"))
    s = c.semanal.set_index(["codigo", "semana_inicio"])
    assert s.loc[(901, pd.Timestamp("2023-12-30")), "val_cvu"] == 320.0  # revisão 1, a mais recente
    assert s.loc[(901, pd.Timestamp("2023-12-30")), "revisoes"] == 2
    assert s.loc[(902, pd.Timestamp("2024-01-06")), "sinal_cvu"] == SINAL_CVU_NEGATIVO
    assert s.loc[(903, pd.Timestamp("2024-01-06")), "sinal_cvu"] == SINAL_CVU_AUSENTE  # sem descarte
    assert s.loc[(902, pd.Timestamp("2023-12-30")), "sinal_cvu"] == ""
    # o zero publicado nas semanas sem CVU também é sinalizado (decisão do usuário de 20/10/2026)
    assert s.loc[(903, pd.Timestamp("2023-12-30")), "sinal_cvu"] == SINAL_CVU_ZERO
    assert c.resumo["revisoes_descartadas"] == 1
    assert c.resumo["sinalizados"] == {"negativo": 1, "ausente": 1, "zero": 1}
    exportar_termica(tmp_path, cvu=c)
    assert set(carregar_semanal_tratado(tmp_path, "cvu").semanal["sinal_cvu"]) == {"", "negativo", "ausente", "zero"}


def test_cmo_sem_duplicatas_contadas() -> None:
    def linha(publicado: str, valor: float, arquivo: str) -> dict:
        return {"din_instante": pd.Timestamp(publicado), "id_subsistema": "SE", **{c: valor for c in COLUNAS_CMO},
                "_nao_numerico": False, "arquivo_origem": arquivo}
    extraido = pd.DataFrame([linha("2024-01-05", 100.0, "CMO_2024.parquet"), linha("2024-01-12", 200.0, "CMO_2024.parquet"),
                             linha("2024-01-12", 210.0, "CMO_2024_b.parquet")])
    c = montar_cmo(extraido, _auditoria("CMO_2024.parquet", "CMO_2024_b.parquet"), "SE", pd.Timestamp("2024-01-01"),
                   pd.Timestamp("2024-01-12 23:00"))
    assert list(c.semanal["semana_inicio"]) == [pd.Timestamp("2023-12-30"), pd.Timestamp("2024-01-06")]
    assert list(c.semanal["val_cmomediasemanal"]) == [100.0, 210.0]  # a publicação mais recente
    assert (c.resumo["duplicatas"], c.resumo["duplicatas_conflitantes"]) == (1, 1)
    assert list(c.semanal["din_instante_publicado"]) == [pd.Timestamp("2024-01-05"), pd.Timestamp("2024-01-12")]


def test_semana_operativa_e_semanais_em_hora() -> None:
    datas = pd.Series(pd.to_datetime(["2024-01-05", "2024-01-06", "2024-01-11"]))  # sexta, sábado, quinta
    assert list(inicio_da_semana_operativa(datas)) == [pd.Timestamp("2023-12-30"), pd.Timestamp("2024-01-06"),
                                                       pd.Timestamp("2024-01-06")]
    semanal = pd.DataFrame({"codigo": [902], "semana_inicio": [pd.Timestamp("2024-01-06")],
                            "semana_fim": [pd.Timestamp("2024-01-12")], "val_cvu": [400.0]})
    horas = semanal_em_horas(semanal, ["val_cvu"], ["codigo"])
    assert len(horas) == 168 and horas["din_instante"].min() == pd.Timestamp("2024-01-06 00:00")
    assert horas["din_instante"].max() == pd.Timestamp("2024-01-12 23:00") and set(horas["val_cvu"]) == {400.0}
    assert semanal_em_horas(pd.DataFrame(), ["val_cvu"]).empty
