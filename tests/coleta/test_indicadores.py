"""Testes da extração dos indicadores por unidade geradora e das taxas TEIFa e TEIP na Coleta de dados (FR-042)."""

from __future__ import annotations

from pathlib import Path
from typing import List
from unittest.mock import patch

import pandas as pd

from src.coleta.indicadores import (
    ANUAL,
    COLUNAS_AUDITORIA_INDICADORES,
    MENSAL,
    PARAMETROS,
    TAXAS,
    ano_do_recurso,
    extrair_indicadores,
    filtrar_csv,
    selecionar_recursos,
    separar_conjuntos,
    sincronizar_indicadores,
)
from src.comum.modelos import RecursoONS

CEG = "UHE.PH.MS.028761-0.01"
ID_ONS = "MSUHSD"
OUTRO_CEG = "UHE.PH.RS.000012-4.01"
CAB_UG = "ceg;id_usina;dat_mesreferencia;num_unidadegeradora;val_dispf"
CAB_PARAM = "nom_usina;id_tipousina;nom_unidadegeradora;cod_ceg;dat_periodo;nom_tpinsumo;val_parametro;num_versao"
CAB_TAXA = "cod_ceg;din_mes;nom_taxa;val_taxa;num_versao"


def _recurso(nome_arquivo: str) -> RecursoONS:
    return RecursoONS("id", nome_arquivo, f"https://ons/dataset/x/{nome_arquivo}", "CSV")


def _gravar(pasta: Path, nome: str, linhas: List[str]) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / nome
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return caminho


def test_selecao_de_arquivos_por_ano() -> None:
    recursos = [_recurso(f"IND_MENSAL_{ano}.csv") for ano in (2017, 2018, 2026)] + [_recurso("TAXA_TEIF_TEIP.csv")]
    assert [ano_do_recurso(r) for r in recursos] == [2017, 2018, 2026, None]
    nomes = [r.nome_recurso for r in selecionar_recursos(recursos, 2018, 2026)]
    assert nomes == ["IND_MENSAL_2018.csv", "IND_MENSAL_2026.csv", "TAXA_TEIF_TEIP.csv"]


def test_filtro_por_ceg_remove_espacos(tmp_path: Path) -> None:
    arquivo = _gravar(tmp_path, "TAXA_TEIF_TEIP_PARAM_2026.csv", [
        CAB_PARAM,
        f"14 DE JULHO;Hidroelétrica   ;UG   50 MW 14 DE JULHO   1 RS;{OUTRO_CEG};01/2026;HDF;0.0;1.0",
        f"SAO DOMINGOS;Hidroelétrica   ;UG   24 MW SAO DOMINGOS   1 MS;{CEG};01/2026;HDF;4.7;1.0",
    ])
    linhas, auditoria = filtrar_csv(arquivo, PARAMETROS, CEG, ID_ONS)
    assert len(linhas) == 1
    assert linhas.iloc[0]["id_tipousina"] == "Hidroelétrica" and linhas.iloc[0]["arquivo_origem"] == arquivo.name
    assert (auditoria["linhas_lidas"], auditoria["linhas_usina"], auditoria["status"]) == (2, 1, "PROCESSADO")
    assert auditoria["periodo"] == "2026"
    # as taxas não publicam o id ONS: as contagens parciais não se aplicam
    assert pd.isna(auditoria["linhas_so_identificador"]) and pd.isna(auditoria["linhas_so_conferencia"])


def test_indicadores_por_unidade_conferidos_pelo_id_ons(tmp_path: Path) -> None:
    arquivo = _gravar(tmp_path, "IND_MENSAL_2025.csv", [
        CAB_UG,
        f"{CEG};{ID_ONS};2025-01-01;1;0.99",
        f"{CEG};GOUSD;2025-01-01;2;0.50",  # só o CEG confere
        f"{OUTRO_CEG};{ID_ONS};2025-01-01;1;0.10",  # só o id ONS confere
        f"{OUTRO_CEG};RSOUTR;2025-01-01;1;0.10",
    ])
    linhas, auditoria = filtrar_csv(arquivo, MENSAL, CEG, ID_ONS)
    assert linhas["val_dispf"].tolist() == ["0.99"]  # as colunas ficam como publicadas (texto)
    assert (auditoria["linhas_so_identificador"], auditoria["linhas_so_conferencia"]) == (1, 1)


def test_arquivo_sem_a_coluna_do_ceg_falha(tmp_path: Path) -> None:
    arquivo = _gravar(tmp_path, "TAXA_TEIF_TEIP.csv", ["din_mes;nom_taxa", "2025-01-01;TEIFa"])
    linhas, auditoria = filtrar_csv(arquivo, TAXAS, CEG, ID_ONS)
    assert linhas.empty and auditoria["status"] == "FALHA" and "cod_ceg" in auditoria["mensagem"]


def test_extracao_dos_quatro_conjuntos_e_separacao(tmp_path: Path) -> None:
    raiz = tmp_path / "indicadores_ons"
    _gravar(raiz / MENSAL, "IND_MENSAL_2024.csv", [CAB_UG, f"{CEG};{ID_ONS};2024-12-01;1;0.98"])
    _gravar(raiz / MENSAL, "IND_MENSAL_2025.csv", [CAB_UG, f"{CEG};{ID_ONS};2025-01-01;1;0.99"])
    _gravar(raiz / MENSAL, "IND_MENSAL_2017.csv", [CAB_UG, f"{CEG};{ID_ONS};2017-01-01;1;0.90"])  # fora do período
    _gravar(raiz / ANUAL, "IND_ANUAL.csv", [CAB_UG, f"{CEG};{ID_ONS};2024;1;0.97", f"{OUTRO_CEG};RSOUTR;2024;1;0.5"])
    _gravar(raiz / PARAMETROS, "TAXA_TEIF_TEIP_PARAM_2025.csv",
            [CAB_PARAM, f"SAO DOMINGOS;H;UG 24 MW SAO DOMINGOS 1 MS;{CEG};01/2025;HP;744.0;1.0"])
    _gravar(raiz / TAXAS, "TAXA_TEIF_TEIP.csv", [CAB_TAXA, f"{OUTRO_CEG};2025-01-01;TEIFa;0.01;1.0"])
    falhas = [{"conjunto": TAXAS, "arquivo": "TAXA_NOVA.csv", "formato": "CSV", "periodo": "", "status": "FALHA",
               "mensagem": "HTTP 500"}]
    extraido, auditoria = extrair_indicadores(raiz, pd.Timestamp("2024-06-01"), pd.Timestamp("2025-03-31 23:00"),
                                              CEG, ID_ONS, falhas)
    assert list(auditoria.columns) == COLUNAS_AUDITORIA_INDICADORES
    assert auditoria["arquivo"].tolist() == ["IND_MENSAL_2024.csv", "IND_MENSAL_2025.csv", "IND_ANUAL.csv",
                                             "TAXA_TEIF_TEIP_PARAM_2025.csv", "TAXA_TEIF_TEIP.csv", "TAXA_NOVA.csv"]
    assert auditoria["status"].tolist() == ["PROCESSADO"] * 4 + ["SEM_REGISTROS", "FALHA"]
    assert auditoria["obtido"].tolist() == [True] * 5 + [False]
    assert extraido["conjunto"].value_counts().to_dict() == {MENSAL: 2, ANUAL: 1, PARAMETROS: 1}

    caminho = tmp_path / "indicadores_extraido.parquet"
    extraido.to_parquet(caminho, index=False)
    tabelas = separar_conjuntos(pd.read_parquet(caminho))
    assert sorted(tabelas[MENSAL].columns) == sorted(CAB_UG.split(";") + ["arquivo_origem"])
    assert sorted(tabelas[PARAMETROS].columns) == sorted(CAB_PARAM.split(";") + ["arquivo_origem"])
    assert tabelas[MENSAL]["arquivo_origem"].tolist() == ["IND_MENSAL_2024.csv", "IND_MENSAL_2025.csv"]
    assert tabelas[TAXAS].empty


def test_sincronizacao_registra_falha_sem_interromper(tmp_path: Path) -> None:
    metadados = {"result": {"resources": [
        {"id": "1", "name": "A_2025.csv", "url": "https://ons/x/A_2025.csv", "format": "CSV", "size": 1},
        {"id": "2", "name": "B_2025.csv", "url": "https://ons/x/B_2025.csv", "format": "CSV", "size": 1},
    ]}}
    obtidos = []

    def baixar(recurso, destination_dir, force, manifest):
        if recurso.nome_recurso.startswith("A_"):
            raise OSError("HTTP 500")
        obtidos.append(recurso.nome_recurso)
        return "DOWNLOADED"

    with patch("src.coleta.indicadores.fetch_ckan_package_metadata", return_value=metadados), \
            patch("src.coleta.indicadores.download_resource", side_effect=baixar):
        falhas = sincronizar_indicadores(2025, 2025, tmp_path)
    assert len(falhas) == 4 and {f["arquivo"] for f in falhas} == {"A_2025.csv"}
    assert {f["periodo"] for f in falhas} == {"2025"} and len(obtidos) == 4
