"""Testes da programação diária do ONS (spec 004, US1) e da sua integração ao relatório."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd
import pytest

from src.analyzer import analisar, gerar_relatorio_md, linhas_tabela_programacao_mensal, preparar_dados
from src.models import RecursoONS
from src.pdf_generator import PDFReportGenerator
from src.programacao_ons import (
    GERANDO_COM_PROGRAMACAO,
    GERANDO_PROGRAMACAO_ZERO,
    PARADA_EVT_PROGRAMACAO_POSITIVA,
    PARADA_EVT_PROGRAMACAO_ZERO,
    PARADA_SEM_EVT,
    ProgramacaoONS,
    carregar_programacao_processada,
    classificar_horas,
    data_interna_confere,
    dia_do_arquivo,
    eventos_desvio,
    executar_programacao_ons,
    ler_arquivo,
    perfil_hora_do_dia,
    programacao_horaria,
    resumo_mensal,
    selecionar_recursos_periodo,
)


def _gravar_dia(pasta: Path, dia: str, valores: Optional[List[float]] = None, data_interna: Optional[str] = None,
                patamares: int = 48) -> Path:
    """Arquivo diário sintético no formato do ONS, com a usina, um homônimo e outra usina."""
    d = pd.Timestamp(dia)
    valores = valores if valores is not None else [22.0] * patamares
    data_interna = data_interna or d.strftime("%Y-%m-%d")
    linhas = []
    for p in range(1, patamares + 1):
        linhas.append({"din_programacaodia": data_interna, "num_patamar": p, "cod_exibicaousina": "PRUHSD",
                       "nom_usina": "SAO DOMINGOS", "id_estado": "MS", "val_geracaoprogramada": f"{valores[p - 1]:.2f}"})
        linhas.append({"din_programacaodia": data_interna, "num_patamar": p, "cod_exibicaousina": "GOUSD",
                       "nom_usina": "UHE SAO DOMINGOS", "id_estado": "GO", "val_geracaoprogramada": "5.00"})
        linhas.append({"din_programacaodia": data_interna, "num_patamar": p, "cod_exibicaousina": "OUTRA",
                       "nom_usina": "OUTRA USINA", "id_estado": "SP", "val_geracaoprogramada": "100.00"})
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"PROGRAMACAO_DIARIA_{d.strftime('%Y_%m_%d')}.parquet"
    pd.DataFrame(linhas).to_parquet(caminho, index=False)
    return caminho


def test_datas_do_nome_e_data_interna() -> None:
    dia = dia_do_arquivo("PROGRAMACAO_DIARIA_2026_07_01.parquet")
    assert dia == pd.Timestamp("2026-07-01")
    assert data_interna_confere(pd.Series(["2026-07-01"]), dia)
    assert data_interna_confere(pd.Series(["01/07/2026"]), dia)
    assert data_interna_confere(pd.Series(["2026-07-01 00:00:00"]), dia)
    assert not data_interna_confere(pd.Series(["07/01/2026"]), dia)
    assert dia_do_arquivo("TAXA_TEIF_TEIP.parquet") is None


def test_selecao_de_recursos_pelo_periodo() -> None:
    recursos = [RecursoONS("id", n, f"https://ons/x/{n}", "PARQUET")
                for n in ("PROGRAMACAO_DIARIA_2024_09_30.parquet", "PROGRAMACAO_DIARIA_2024_10_01.parquet",
                          "PROGRAMACAO_DIARIA_2026_09_28.parquet", "PROGRAMACAO_DIARIA_2026_09_29.parquet")]
    selecionados = selecionar_recursos_periodo(recursos, pd.Timestamp("2024-10-01 05:00"), pd.Timestamp("2026-09-28 23:00"))
    assert [r.nome_recurso for r in selecionados] == ["PROGRAMACAO_DIARIA_2024_10_01.parquet",
                                                       "PROGRAMACAO_DIARIA_2026_09_28.parquet"]


def test_extracao_ignora_homonimos_e_aceita_data_brasileira(tmp_path: Path) -> None:
    caminho = _gravar_dia(tmp_path, "2026-07-01", data_interna="01/07/2026")
    linhas, auditoria = ler_arquivo(caminho)
    assert len(linhas) == 48
    assert set(linhas["geracao_programada_mw"]) == {22.0}
    assert auditoria["status"] == "PROCESSADO"
    assert auditoria["linhas_lidas"] == 144 and auditoria["linhas_usina"] == 48
    assert auditoria["data_interna_confere"] is True


def test_dia_incompleto_e_data_divergente(tmp_path: Path) -> None:
    caminho = _gravar_dia(tmp_path, "2026-07-02", data_interna="2026-07-03", patamares=46)
    _, auditoria = ler_arquivo(caminho)
    assert auditoria["status"] == "INCOMPLETO"
    assert auditoria["patamares"] == 46
    assert auditoria["data_interna_confere"] is False


def test_programacao_horaria_usa_a_media_dos_patamares() -> None:
    patamares = pd.DataFrame({
        "dia": pd.Timestamp("2026-07-01"),
        "num_patamar": [1, 2, 3],
        "geracao_programada_mw": [10.0, 20.0, 22.0],
        "arquivo_origem": "x",
    })
    h = programacao_horaria(patamares).set_index("din_instante")
    assert h.loc["2026-07-01 00:00", "geracao_programada_mw"] == pytest.approx(15.0)
    assert h.loc["2026-07-01 00:00", "patamares"] == 2
    assert h.loc["2026-07-01 01:00", "patamares"] == 1


def _operacao_e_programacao() -> tuple:
    """Dez horas com todas as classes: 3 h paradas com EVT e programação zero (9h a 11h), 2 h de desvio."""
    t = pd.date_range("2026-07-01 08:00", periods=10, freq="h")
    ger = [20, 0, 0, 0, 0, 0, 0.5, 15, 15, 20]
    evt = [0, 2, 2, 2, 1, 0, 0, 0, 0, 0]
    prog = [22, 0, 0, 0, 22, 22, 0, 0, 22, 22]
    operacao = pd.DataFrame({"din_instante": t, "val_geracao": ger, "val_energiavertidaturbinavel": evt,
                             "val_disponibilidade": 46.0})
    horaria = pd.DataFrame({"din_instante": t, "geracao_programada_mw": prog, "patamares": 2})
    return operacao, horaria


def test_classificacao_resumo_eventos_e_perfil() -> None:
    operacao, horaria = _operacao_e_programacao()
    c = classificar_horas(operacao, horaria)
    assert c["classe"].tolist() == [
        GERANDO_COM_PROGRAMACAO, PARADA_EVT_PROGRAMACAO_ZERO, PARADA_EVT_PROGRAMACAO_ZERO, PARADA_EVT_PROGRAMACAO_ZERO,
        PARADA_EVT_PROGRAMACAO_POSITIVA, PARADA_SEM_EVT, PARADA_SEM_EVT, GERANDO_PROGRAMACAO_ZERO,
        GERANDO_COM_PROGRAMACAO, GERANDO_COM_PROGRAMACAO,
    ]
    m = resumo_mensal(c).iloc[0]
    assert m["horas_parada_com_evt"] == 4
    assert m["horas_parada_evt_programacao_zero"] == 3
    assert m["evt_parada_programacao_zero_mwh"] == pytest.approx(6.0)
    assert m["participacao_evt_programacao_zero_pct"] == pytest.approx(6 / 7 * 100)
    assert m["horas_desvio_programacao"] == 2

    eventos = eventos_desvio(c)
    assert eventos["duracao_h"].tolist() == [2]
    assert eventos["inicio"].iloc[0] == pd.Timestamp("2026-07-01 12:00")

    perfil = perfil_hora_do_dia(c).set_index("hora")
    assert perfil.loc[[9, 10, 11], "horas"].tolist() == [1, 1, 1]
    assert perfil["horas"].sum() == 3


def test_execucao_completa_em_pastas_temporarias(tmp_path: Path) -> None:
    """Sem rede: lê só os dias do período, lista o dia ausente e grava só na pasta de saída informada."""
    raw, saida = tmp_path / "raw", tmp_path / "processed"
    saida.mkdir()
    _gravar_dia(raw, "2026-07-01")
    _gravar_dia(raw, "2026-07-03", data_interna="03/07/2026")
    _gravar_dia(raw, "2026-07-05")  # fora do período
    codigo = executar_programacao_ons(
        baixar=False, periodo=(pd.Timestamp("2026-07-01"), pd.Timestamp("2026-07-03 23:00")),
        pasta_raw=raw, pasta_saida=saida,
    )
    assert codigo == 0
    prog = carregar_programacao_processada(saida)
    assert len(prog.horaria) == 48
    assert list(prog.dias_ausentes["dia"]) == [pd.Timestamp("2026-07-02")]
    assert prog.auditoria["status"].tolist() == ["PROCESSADO", "PROCESSADO"]
    assert carregar_programacao_processada(tmp_path / "vazia") is None


# ---------------------------------------------------------------------------
# Integração com a análise, o Markdown e o PDF
# ---------------------------------------------------------------------------


@pytest.fixture
def resultados_com_programacao(df_sintetico: pd.DataFrame, tmp_path: Path):
    """Programação de 22 MW em todo o período, zero durante a parada de 10/02/2024 (9h a 13h)."""
    df = preparar_dados(df_sintetico)
    horaria = pd.DataFrame({"din_instante": df["din_instante"], "geracao_programada_mw": 22.0, "patamares": 2})
    parada = (horaria["din_instante"] >= "2024-02-10 09:00") & (horaria["din_instante"] <= "2024-02-10 13:00")
    horaria.loc[parada, "geracao_programada_mw"] = 0.0
    horaria = horaria[horaria["din_instante"] != pd.Timestamp("2024-01-15 10:00")]  # hora sem programação
    prog = ProgramacaoONS(horaria=horaria, dias_ausentes=pd.DataFrame({"dia": [pd.Timestamp("2024-01-20")]}),
                          auditoria=pd.DataFrame({"arquivo": ["x"], "status": ["PROCESSADO"]}))
    return analisar(df, tmp_path / "a.csv", tmp_path / "m.json", programacao=prog)


def test_analise_inclui_a_constatacao_da_programacao(resultados_com_programacao) -> None:
    res = resultados_com_programacao
    titulos = [t for t, _ in res.achados]
    assert len(titulos) == 13
    assert titulos[7] == "Programação diária do ONS"
    p = res.programacao["periodo"]
    assert p["horas_parada_evt_programacao_zero"] == 5
    assert p["pct_horas_programacao_zero"] == pytest.approx(100.0)
    assert p["horas_base_sem_programacao"] == 1
    # 30 h de indisponibilidade total com programação de 22 MW = um evento de desvio
    assert p["eventos_desvio"] == 1 and p["horas_desvio"] == 30
    texto = dict(res.achados)["Programação diária do ONS"]
    assert "ficou parada com EVT em 5 h; em 5 delas (100,0%)" in texto
    assert "reprogramações em tempo real" in texto


def test_relatorios_com_programacao(resultados_com_programacao, tmp_path: Path) -> None:
    res = resultados_com_programacao
    md = gerar_relatorio_md(res, None, tmp_path / "relatorio.md").read_text(encoding="utf-8")
    assert "Operação verificada e programação diária do ONS" in md
    _, linhas = linhas_tabela_programacao_mensal(res)
    for linha in linhas:
        assert f"| {' | '.join(linha)} |" in md
    assert "20/01/2024" in md  # dia sem arquivo listado
    saida = PDFReportGenerator(res, {}, tmp_path / "relatorio.pdf").build_pdf()
    assert saida.read_bytes()[:5] == b"%PDF-"
