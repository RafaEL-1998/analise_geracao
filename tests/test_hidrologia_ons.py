"""Testes dos dados hidrológicos horários do ONS (spec 006, US4: FR-021 a FR-026)."""

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
import pytest

from src.conjuntos_ons import ler_arquivo
from src.hidrologia_ons import (
    ACIMA_ENGOLIMENTO_USINA,
    ATE_UMA_UNIDADE,
    COM_PARADA_EVT,
    DEMAIS_DIAS,
    DESCRICAO,
    ENTRE_UMA_E_DUAS_UNIDADES,
    SEM_DADO_HIDROLOGICO,
    alinhar_com_evt,
    carregar_hidrologia_processada,
    classificar_faixas,
    executar_hidrologia_ons,
    perfil_hora_do_dia,
    qualidade,
    resumir_faixas,
    resumo_mensal,
)


def _linha(instante: str, afluente: object = "100.0", turbinada: object = "80.0", vertida: object = "20.0",
           cod: object = 153.0, nome: str = "SAO DOMINGOS", id_res: str = "PNUHSD", volume: object = "50.0") -> dict:
    return {"id_subsistema": "SE", "tip_reservatorio": "Fio dagua", "nom_bacia": "PARANA", "id_reservatorio": id_res,
            "nom_reservatorio": nome, "cod_usina": cod, "din_instante": instante, "val_nivelmontante": "344.5",
            "val_niveljusante": "309.1", "val_volumeutil": volume, "val_vazaoafluente": afluente,
            "val_vazaodefluente": "100.0", "val_vazaoturbinada": turbinada, "val_vazaovertida": vertida,
            "val_vazaooutrasestruturas": None, "val_vazaotransferida": None, "val_vazaovertidanaoturbinavel": "0.0"}


def _gravar(pasta: Path, nome: str, linhas: List[dict]) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / nome
    pd.DataFrame(linhas).to_parquet(caminho, index=False)
    return caminho


def _dia_publicado(dia: str) -> List[str]:
    """Instantes publicados de um dia na convenção de fim de hora: 01:00 ... 23:00 e 23:59."""
    d = pd.Timestamp(dia)
    return [(d + pd.Timedelta(hours=h)).strftime("%Y-%m-%d %H:%M:%S") for h in range(1, 24)] + [f"{dia} 23:59:00"]


def test_conversao_de_fim_para_inicio_de_hora_e_identificacao(tmp_path: Path) -> None:
    linhas = [_linha(t) for t in _dia_publicado("2025-01-01")]
    linhas.append(_linha("2025-01-01 12:00:00", cod=999.0))                     # só a conferência (nome e código do reservatório)
    linhas.append(_linha("2025-01-01 12:00:00", nome="SAO DOMINGOS II", id_res="GOXXXX"))  # só o identificador
    dados, auditoria = ler_arquivo(DESCRICAO, _gravar(tmp_path, "DADOS_HIDROLOGICOS_HO_2025_01.parquet", linhas))
    assert len(dados) == 24
    assert dados["din_instante"].min() == pd.Timestamp("2025-01-01 00:00")
    assert dados["din_instante"].max() == pd.Timestamp("2025-01-01 23:00")
    ultima = dados.set_index("din_instante").loc[pd.Timestamp("2025-01-01 23:00"), "din_instante_publicado"]
    assert ultima == pd.Timestamp("2025-01-01 23:59")
    assert (auditoria["linhas_so_conferencia"], auditoria["linhas_so_identificador"]) == (1, 1)


def test_regras_de_qualidade() -> None:
    h = pd.DataFrame({
        "val_vazaoafluente": [100.0, -1.0, 100.0, 100.0, 100.0],
        "val_vazaodefluente": [100.0] * 5, "val_vazaoturbinada": [80.0] * 5, "val_vazaovertida": [20.0] * 5,
        "val_vazaovertidanaoturbinavel": [0.0, 0.0, 0.0, None, 0.0], "val_vazaooutrasestruturas": [None] * 5,
        "val_nivelmontante": [344.5] * 5, "val_niveljusante": [None] * 5,
        "val_volumeutil": [50.0, 50.0, 101.0, 50.0, 50.0],
        "_nao_numerico": [False, False, False, False, True],
    })
    assert qualidade(h).tolist() == ["OK", "H1", "H2", "OK", "H3"]  # vazio não é erro nem zero


def test_nivel_implausivel_sai_so_do_campo_afetado() -> None:
    """H4: nível a mais de 10 m da mediana (leitura trocada) é sinalizado e excluído só no próprio campo."""
    from src.hidrologia_ons import _limpos

    h = pd.DataFrame({
        "din_instante": pd.date_range("2025-01-01", periods=6, freq="h"),
        "val_vazaoafluente": [100.0] * 6, "val_vazaoturbinada": [80.0] * 6, "val_vazaovertida": [20.0] * 6,
        "val_nivelmontante": [344.3, 344.2, 308.67, 342.1, 344.4, 344.3],   # 342,1 m: rebaixamento real (fica)
        "val_niveljusante": [309.9, 309.8, 309.9, 730.9, 309.7, 3.09],
        "val_volumeutil": [50.0] * 6, "_nao_numerico": [False] * 6,
    })
    assert qualidade(h).tolist() == ["OK", "OK", "H4", "H4", "OK", "H4"]
    limpos = _limpos(h)
    assert limpos["val_nivelmontante"].isna().tolist() == [False, False, True, False, False, False]
    assert limpos["val_niveljusante"].isna().tolist() == [False, False, False, True, False, True]
    assert limpos["val_vazaoturbinada"].notna().all()  # a hora continua nas demais análises


def _hid(valores: List[tuple], inicio: str = "2025-01-01 00:00") -> pd.DataFrame:
    """Série tratada (hora de início): (afluente, turbinada, vertida, nível) por hora."""
    instantes = pd.date_range(inicio, periods=len(valores), freq="h")
    return pd.DataFrame({"din_instante": instantes, "val_vazaoafluente": [v[0] for v in valores],
                         "val_vazaoturbinada": [v[1] for v in valores], "val_vazaovertida": [v[2] for v in valores],
                         "val_nivelmontante": [v[3] for v in valores], "val_niveljusante": 309.0, "val_volumeutil": 50.0,
                         "val_vazaodefluente": [v[1] + v[2] for v in valores], "val_vazaovertidanaoturbinavel": 0.0,
                         "qualidade": "OK"})


def _evt(valores: List[tuple], inicio: str = "2025-01-01 00:00") -> pd.DataFrame:
    """Base de EVT: (geração, EVT, turbinada, vertida) por hora."""
    instantes = pd.date_range(inicio, periods=len(valores), freq="h")
    return pd.DataFrame({"din_instante": instantes, "val_geracao": [v[0] for v in valores],
                         "val_energiavertidaturbinavel": [v[1] for v in valores],
                         "val_vazaoturbinada": [v[2] for v in valores], "val_vazaovertida": [v[3] for v in valores]})


def test_alinhamento_confirmado_e_reprovado() -> None:
    hid = _hid([(100, 80, 20, 344.5)] * 200)
    evt = _evt([(24, 0, 80, 20)] * 200)
    ok = alinhar_com_evt(hid, evt).iloc[0]
    assert (ok["horas_comuns"], ok["coincidentes_ambas"], ok["confirmado"]) == (200, 200, True)
    assert (ok["meta_pct"], ok["tolerancia_m3s"], ok["deslocamento_aplicado_h"]) == (99.0, 0.5, -1)
    evt_ruim = _evt([(24, 0, 80, 20)] * 197 + [(24, 0, 70, 20)] * 3)  # 98,5% coincidentes
    ruim = alinhar_com_evt(hid, evt_ruim).iloc[0]
    assert ruim["pct_coincidencia"] == pytest.approx(98.5) and not ruim["confirmado"]


def test_faixas_de_afluencia_nos_limites() -> None:
    hid = _hid([(163.01, 0, 100, 344.5), (163.0, 0, 100, 344.5), (81.51, 0, 50, 344.5), (81.5, 0, 50, 344.5),
                (None, 0, 50, 344.5), (60, 60, 0, 344.5)])
    evt = _evt([(0, 5.0, 0, 0), (0, 4.0, 0, 0), (0, 3.0, 0, 0), (0, 2.0, 0, 0), (0, 1.0, 0, 0), (20, 0.0, 0, 0)])
    faixas = classificar_faixas(hid, evt)
    assert faixas["faixa_afluencia"].tolist() == [ACIMA_ENGOLIMENTO_USINA, ENTRE_UMA_E_DUAS_UNIDADES,
                                                  ENTRE_UMA_E_DUAS_UNIDADES, ATE_UMA_UNIDADE, SEM_DADO_HIDROLOGICO]
    resumo = resumir_faixas(faixas, "Y")
    assert resumo["horas"].sum() == 5 and resumo["evt_mwh"].sum() == pytest.approx(15.0)
    assert set(resumo["faixa_afluencia"]) == {ACIMA_ENGOLIMENTO_USINA, ENTRE_UMA_E_DUAS_UNIDADES, ATE_UMA_UNIDADE,
                                              SEM_DADO_HIDROLOGICO}


def test_perfil_por_hora_do_dia_e_resumo_mensal() -> None:
    # 01/01: parada com EVT às 10h (nível sobe); 02/01: sem parada
    dia1 = [(100, 80, 20, 344.2 + 0.02 * h) for h in range(24)]
    dia2 = [(100, 100, 0, 344.2) for _ in range(24)]
    hid = _hid(dia1 + dia2)
    evt = _evt([(0 if h == 10 else 24, 3.0 if h == 10 else 0.0, 80, 20) for h in range(24)] + [(30, 0, 100, 0)] * 24)
    perfil = perfil_hora_do_dia(hid, evt)
    assert set(perfil["grupo_dias"]) == {COM_PARADA_EVT, DEMAIS_DIAS} and len(perfil) == 48
    linha = perfil[(perfil["grupo_dias"] == COM_PARADA_EVT) & (perfil["hora"] == 23)].iloc[0]
    assert linha["dias"] == 1 and linha["nivel_montante_medio_m"] == pytest.approx(344.2 + 0.46)
    mensal = resumo_mensal(hid).iloc[0]
    assert mensal["horas"] == 48 and mensal["afluencia_maxima_m3s"] == 100
    assert mensal["horas_afluencia_acima_engolimento"] == 0
    assert mensal["nivel_montante_min_m"] == pytest.approx(344.2)


def test_execucao_sem_rede_com_alinhamento(tmp_path: Path, df_sintetico: pd.DataFrame) -> None:
    raw, saida = tmp_path / "raw", tmp_path / "processed"
    saida.mkdir()
    janeiro = df_sintetico[(df_sintetico["din_instante"] >= "2024-01-01") & (df_sintetico["din_instante"] < "2024-01-03")]
    janeiro.to_parquet(saida / "uhe_sao_domingos_energia_vertida_tratado.parquet", index=False)
    linhas = []
    for r in janeiro.itertuples():
        fim = r.din_instante + pd.Timedelta(hours=1)
        publicado = (fim - pd.Timedelta(minutes=1)) if fim.hour == 0 else fim
        linhas.append(_linha(publicado.strftime("%Y-%m-%d %H:%M:%S"), turbinada=f"{r.val_vazaoturbinada:.4f}",
                             vertida=f"{r.val_vazaovertida:.4f}"))
    _gravar(raw, "DADOS_HIDROLOGICOS_HO_2024_01.parquet", linhas)
    periodo = (janeiro["din_instante"].min(), janeiro["din_instante"].max())
    assert executar_hidrologia_ons(baixar=False, periodo=periodo, pasta_raw=raw, pasta_saida=saida) == 0
    serie, alinhamento = carregar_hidrologia_processada(saida)
    assert len(serie.horaria) == 48 and bool(alinhamento.iloc[0]["confirmado"])
    assert "din_instante_publicado" in serie.horaria.columns and "qualidade" in serie.horaria.columns

    # vazões desalinhadas (sem a conversão de hora) reprovam o alinhamento: código 3
    _gravar(raw, "DADOS_HIDROLOGICOS_HO_2024_01.parquet",
            [dict(l, val_vazaoturbinada=str(float(l["val_vazaoturbinada"]) + 10)) for l in linhas])
    assert executar_hidrologia_ons(baixar=False, periodo=periodo, pasta_raw=raw, pasta_saida=saida) == 3
