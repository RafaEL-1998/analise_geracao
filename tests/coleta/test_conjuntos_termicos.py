"""Conjuntos das térmicas na Coleta (plano da Coleta de dados, D27).

Com brutos sintéticos: o despacho pelo CEG, com o código de planejamento conferido como número e só no período de cada
código; o CVU pelos códigos do perfil, conferido pelo subsistema; o CMO pelo subsistema, como agregado; e o
``planejamento.csv`` do catálogo, com o primeiro e o último mês de cada código.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from src.coleta import registro
from src.coleta.catalogo_usinas import COLUNAS_PLANEJAMENTO, montar_planejamento
from src.coleta.conjuntos import extrair_arquivo, extrair_conjunto
from src.comum.perfil import Planejamento

CEG = "UTE.GN.MS.999999-0.01"
OUTRO_CEG = "UTE.GN.MS.888888-0.01"
PLANEJAMENTO = (Planejamento(34, "2013-01", "2018-08"), Planejamento(334, "2021-07", ""),
                Planejamento(434, "2021-08", "2026-01"))


def _perfil(cobertura=None, subsistema="SE") -> SimpleNamespace:
    ident = SimpleNamespace(ceg=CEG, id_ons="MSUTXX", cod_usina=None, nome_ons=None, id_reservatorio=None,
                            cod_programacao="MSUTXX", codigos_programacao=("MSUTXX",), id_conjunto=None,
                            planejamento=PLANEJAMENTO, membros=())
    usina = SimpleNamespace(estado="MS", tipo="UTE", modalidade="TIPO I", subsistema=subsistema)
    return SimpleNamespace(identificacao=ident, usina=usina,
                           cobertura=cobertura or {"geracao": "proprio", "despacho": "proprio", "cvu": "proprio"})


def _gravar(caminho: Path, linhas) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tabela = pd.DataFrame(linhas)
    if caminho.suffix == ".parquet":
        tabela.to_parquet(caminho, index=False)
    else:
        tabela.to_csv(caminho, sep=";", index=False)
    return caminho


def _despacho(ceg: str, codigo, instante: str, verificado="10.5") -> dict:
    linha = {"din_instante": instante, "nom_tipopatamar": "LEVE", "id_subsistema": "SE", "nom_subsistema": "SUDESTE",
             "nom_usina": "W. ARJONA", "cod_usinaplanejamento": codigo, "ceg": ceg}
    linha.update({c: "0.0" for c in registro.COLUNAS_DESPACHO_PROGRAMADO + registro.COLUNAS_DESPACHO_VERIFICADO})
    linha.update(val_proggeracao="12.0", val_verifgeracao=verificado, tip_restricaoeletrica=0.0)
    return linha


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------


def test_registro_das_termicas_com_o_cmo_so_com_o_subsistema() -> None:
    chaves = [e.chave for e in registro.conjuntos_da_usina(_perfil())]
    assert {"despacho", "cvu", "cmo"} <= set(chaves)
    assert "cmo" not in [e.chave for e in registro.conjuntos_da_usina(_perfil(subsistema=None))]
    d = registro.descricoes(_perfil())
    assert (d["despacho"].nivel, d["despacho"].resolucao) == ("usina", "horaria")
    assert (d["cvu"].nivel, d["cvu"].resolucao, d["cvu"].coluna_instante) == ("usina", "semanal", "dat_iniciosemana")
    assert (d["cmo"].nivel, d["cmo"].resolucao, d["cmo"].conferencias) == ("agregado", "semanal", ())
    assert "despacho" in registro.chaves_da_cobertura("UTE") and "cmo" not in registro.chaves_da_cobertura("UTE")
    assert "despacho" not in registro.chaves_da_cobertura("UFV")


# ---------------------------------------------------------------------------
# Despacho
# ---------------------------------------------------------------------------


def test_despacho_pelo_ceg_com_o_codigo_no_periodo(tmp_path: Path) -> None:
    desc = registro.descricoes(_perfil())["despacho"]
    caminho = _gravar(tmp_path / "GERACAO_TERMICA_DESPACHO_2021.csv", [
        _despacho(CEG, "334", "2021-07-10 00:00:00"),        # da usina (código inteiro)
        _despacho(CEG, "434,0", "2021-09-01 05:00:00", "7,25"),  # da usina (código decimal, vírgula)
        _despacho(CEG, "434", "2021-07-15 00:00:00"),        # código antes do período dele: só identificador
        _despacho(CEG, "34", "2021-07-10 01:00:00"),         # código fora do período: só identificador
        _despacho(CEG, "999", "2021-07-10 02:00:00"),        # código fora da lista: só identificador
        _despacho(OUTRO_CEG, "334", "2021-07-10 00:00:00"),  # outro CEG com o código: só conferência
        _despacho(OUTRO_CEG, "777", "2021-07-10 00:00:00"),  # outra usina
    ])
    dados, auditoria = extrair_arquivo(desc, caminho)
    assert (auditoria["linhas_usina"], auditoria["linhas_so_identificador"], auditoria["linhas_so_conferencia"]) == \
        (2, 3, 1)
    assert list(dados["cod_usinaplanejamento"]) == [334.0, 434.0]
    assert list(dados["val_verifgeracao"]) == [10.5, 7.25]
    assert set(registro.COLUNAS_DESPACHO_PROGRAMADO + registro.COLUNAS_DESPACHO_VERIFICADO) <= set(dados.columns)
    assert list(dados["nom_tipopatamar"]) == ["LEVE", "LEVE"] and "tip_restricaoeletrica" in dados.columns


def test_despacho_em_parquet_anual_e_mensal_com_o_codigo_decimal(tmp_path: Path) -> None:
    desc = registro.descricoes(_perfil())["despacho"]
    pasta = tmp_path / "despacho"
    _gravar(pasta / "GERACAO_TERMICA_DESPACHO_2018.parquet",
            [_despacho(CEG, 34.0, "2018-08-10 23:00:00"), _despacho(CEG, 34.0, "2018-09-01 00:00:00"),
             _despacho(OUTRO_CEG, 35.0, "2018-08-10 23:00:00")])
    _gravar(pasta / "GERACAO_TERMICA_DESPACHO-2_2022_01.parquet",
            [_despacho(CEG, 334.0, "2022-01-01 00:00:00"), _despacho(CEG, 434.0, "2022-01-01 00:00:00")])
    extraido, auditoria = extrair_conjunto(desc, pasta, pd.Timestamp("2018-01-01"), pd.Timestamp("2022-12-31 23:00"))
    assert len(extraido) == 3 and set(extraido["arquivo_origem"]) == {"GERACAO_TERMICA_DESPACHO_2018.parquet",
                                                                     "GERACAO_TERMICA_DESPACHO-2_2022_01.parquet"}
    anual = auditoria.set_index("arquivo").loc["GERACAO_TERMICA_DESPACHO_2018.parquet"]
    assert (anual["linhas_usina"], anual["linhas_so_identificador"]) == (1, 1)  # 34 depois de 08/2018


# ---------------------------------------------------------------------------
# CVU e CMO
# ---------------------------------------------------------------------------


def test_cvu_pelos_codigos_do_perfil_conferido_pelo_subsistema(tmp_path: Path) -> None:
    desc = registro.descricoes(_perfil())["cvu"]
    semana = {"dat_iniciosemana": pd.Timestamp("2022-01-01"), "dat_fimsemana": pd.Timestamp("2022-01-07"),
              "ano_referencia": 2022, "mes_referencia": 1, "nom_semanaoperativa": "S1", "nom_usina": "W.ARJONA"}
    caminho = _gravar(tmp_path / "CVU_USINA_TERMICA_2022.parquet", [
        {**semana, "num_revisao": 0, "cod_usinaplanejamento": 334, "id_subsistema": "SE", "val_cvu": 900.0},
        {**semana, "num_revisao": 1, "cod_usinaplanejamento": 334, "id_subsistema": "SE", "val_cvu": 950.0},
        {**semana, "num_revisao": 0, "cod_usinaplanejamento": 434, "id_subsistema": "NE", "val_cvu": 2000.0},
        {**semana, "num_revisao": 0, "cod_usinaplanejamento": 999, "id_subsistema": "SE", "val_cvu": 100.0},
    ])
    dados, auditoria = extrair_arquivo(desc, caminho)
    assert (auditoria["linhas_usina"], auditoria["linhas_so_identificador"], auditoria["linhas_so_conferencia"]) == \
        (2, 1, 1)
    assert list(dados["din_instante"]) == [pd.Timestamp("2022-01-01")] * 2  # o início da semana operativa
    assert list(dados["num_revisao"]) == [0.0, 1.0] and list(dados["val_cvu"]) == [900.0, 950.0]
    assert set(dados["dat_fimsemana"].str[:10]) == {"2022-01-07"}


def test_cmo_pelo_subsistema_como_agregado(tmp_path: Path) -> None:
    desc = registro.descricoes(_perfil())["cmo"]
    caminho = _gravar(tmp_path / "CMO_SEMANAL_2022.csv", [
        {"id_subsistema": "SE", "nom_subsistema": "SUDESTE", "din_instante": "2022-01-07 00:00:00",
         "val_cmomediasemanal": "123,45", "val_cmoleve": "100", "val_cmomedia": "120", "val_cmopesada": "150"},
        {"id_subsistema": "NE", "nom_subsistema": "NORDESTE", "din_instante": "2022-01-07 00:00:00",
         "val_cmomediasemanal": "50", "val_cmoleve": "40", "val_cmomedia": "50", "val_cmopesada": "60"},
    ])
    dados, auditoria = extrair_arquivo(desc, caminho)
    assert auditoria["linhas_usina"] == 1 and auditoria["linhas_so_conferencia"] == 0
    assert dados.iloc[0]["val_cmomediasemanal"] == 123.45 and dados.iloc[0]["id_subsistema"] == "SE"


# ---------------------------------------------------------------------------
# Catálogo: planejamento.csv
# ---------------------------------------------------------------------------


def test_planejamento_com_o_primeiro_e_o_ultimo_mes_de_cada_codigo(tmp_path: Path) -> None:
    pasta = tmp_path / "geracao_termica_despacho_2"
    _gravar(pasta / "GERACAO_TERMICA_DESPACHO_2013.parquet",
            [_despacho(CEG, 34.0, "2013-01-01 00:00:00"), _despacho(CEG, 34.0, "2013-12-31 23:00:00")])
    _gravar(pasta / "GERACAO_TERMICA_DESPACHO_2018.parquet", [_despacho(CEG, 34.0, "2018-08-10 23:00:00")])
    _gravar(pasta / "GERACAO_TERMICA_DESPACHO-2_2026_01.parquet",
            [_despacho(CEG, 334.0, "2026-01-01 00:00:00"), _despacho(CEG, 434.5, "2026-01-01 00:00:00")])
    _gravar(pasta / "GERACAO_TERMICA_DESPACHO-2_2026_02.csv",
            [_despacho(CEG, "334", "2026-02-01 00:00:00"), _despacho(OUTRO_CEG, "35", "2026-02-01 00:00:00")])
    p = montar_planejamento(pasta)
    assert list(p.columns) == COLUNAS_PLANEJAMENTO
    linhas = {(r.ceg, r.codigo): (r.primeiro_mes, r.ultimo_mes, r.arquivos) for r in p.itertuples()}
    assert linhas == {(CEG, 34): ("2013-01", "2018-08", 2), (CEG, 334): ("2026-01", "2026-02", 2),
                      (CEG, 434.5): ("2026-01", "2026-01", 1), (OUTRO_CEG, 35): ("2026-02", "2026-02", 1)}
    assert set(p["nomes_publicados"]) == {"W. ARJONA"}
    assert montar_planejamento(tmp_path / "vazia").empty
