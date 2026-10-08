"""Testes da ficha cadastral da usina na Coleta de dados (FR-045 e FR-046)."""

from __future__ import annotations

import io
import json
import logging
import urllib.error
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest

from src.coleta.cadastro import (
    COLUNAS_AUDITORIA_CADASTRO,
    COLUNAS_FICHA,
    extrair_cadastro,
    extrair_ficha,
    ler_cadastro,
    sincronizar_cadastro,
)

IDENT = dict(ceg="UHE.PH.MS.028761-0.01", id_ons="MSUHSD", estado="MS", nome_ons="SAO DOMINGOS")
CABECALHO = "nom_usina;ceg;nom_modalidadeoperacao;val_potenciaautorizada;sgl_centrooperacao;nom_pontoconexao;id_estado;nom_estado;sts_aneel;id_ons"
USINA = "UHE SÃO DOMINGOS;UHE.PH.MS.028761-0.01;TIPO II-A;48.000;COSR-S         ;SE ÁGUA CLARA 138 KV;MS;MATO GROSSO DO SUL    ;A;MSUHSD"
HOMONIMOS = [
    "PCH SÃO DOMINGOS I;UHE.PH.GO.027665-0.01;TIPO III;12.000;COSR-NCO;;GO;GOIAS;A;GOUSD",
    "CGH SÂO DOMINGOS;CGH.PH.SC.037229-3.01;TIPO III;1.000;COSR-S;Sist. De Distribuição 23 kV;SC;SANTA CATARINA;A;SCSAOD",
    "EOL SÃO DOMINGOS;EOL.CV.RN.032215-6.01;TIPO II-C;25.200;COSR-NE;SE João Câmara III 138 kV;RN;RIO GRANDE DO NORTE;A;RNEDOM",
]
OUTRA = "UHE OUTRA;UHE.PH.SP.000001-0.01;TIPO I;100.000;COSR-SE;SE X;SP;SAO PAULO;A;SPOUTR"


def _csv(linhas: List[str]) -> bytes:
    return ("\n".join([CABECALHO, *linhas]) + "\n").encode("utf-8")


def _gravar(pasta: Path, linhas: List[str]) -> Path:
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / "MODALIDADE_USINA.csv"
    caminho.write_bytes(_csv(linhas))
    return caminho


def test_ficha_pelo_ceg_com_homonimos_contados(tmp_path: Path) -> None:
    cadastro, irregulares = ler_cadastro(_gravar(tmp_path, [OUTRA, *HOMONIMOS, USINA]))
    assert irregulares == []
    ficha = extrair_ficha(cadastro, "2026-10-05 13:00:00", "MODALIDADE_USINA.csv", **IDENT)
    assert list(ficha.columns) == COLUNAS_FICHA and len(ficha) == 1
    f = ficha.iloc[0]
    assert (f["ceg"], f["id_ons"], f["id_estado"]) == ("UHE.PH.MS.028761-0.01", "MSUHSD", "MS")
    assert (f["nom_modalidadeoperacao"], f["sgl_centrooperacao"], f["nom_pontoconexao"]) == (
        "TIPO II-A", "COSR-S", "SE ÁGUA CLARA 138 KV")
    assert f["val_potenciaautorizada"] == pytest.approx(48.0)
    assert f["homonimos"] == 3 and f["linhas_ceg"] == 1
    assert f["data_consulta_utc"] == "2026-10-05 13:00:00"
    assert "divergencias" not in ficha.columns  # as divergências com o perfil são da Conferência


def test_id_ons_ou_estado_diferente_nao_exclui_a_ficha(tmp_path: Path) -> None:
    linha = USINA.replace(";MS;MATO GROSSO DO SUL", ";GO;GOIAS")
    ficha = extrair_ficha(ler_cadastro(_gravar(tmp_path, [linha, USINA]))[0], "", "MODALIDADE_USINA.csv", **IDENT)
    f = ficha.iloc[0]
    assert f["id_estado"] == "GO" and f["linhas_ceg"] == 2 and f["linhas_so_identificador"] == 1


def test_usina_ausente_no_cadastro(tmp_path: Path) -> None:
    assert extrair_ficha(ler_cadastro(_gravar(tmp_path, [OUTRA]))[0], "", "MODALIDADE_USINA.csv", **IDENT).empty


def test_linhas_irregulares_de_outras_usinas_nao_interrompem_a_leitura(tmp_path: Path, caplog) -> None:
    curta = ";".join(OUTRA.split(";")[:-2])
    longa = HOMONIMOS[0] + ";excedente"
    with caplog.at_level(logging.WARNING):
        cadastro, irregulares = ler_cadastro(_gravar(tmp_path, [curta, USINA, longa, *HOMONIMOS[1:]]))
    assert irregulares == [2, 4]
    ficha = extrair_ficha(cadastro, "", "MODALIDADE_USINA.csv", **IDENT)
    assert len(ficha) == 1 and ficha.iloc[0]["homonimos"] == 2
    avisos = " ".join(r.getMessage() for r in caplog.records if r.levelno == logging.WARNING)
    assert "MODALIDADE_USINA.csv" in avisos and "2, 4" in avisos


def test_auditoria_da_leitura_do_cadastro(tmp_path: Path) -> None:
    curta = ";".join(OUTRA.split(";")[:-2])
    so_conferencia = "UHE X;UHE.PH.SP.000001-0.01;TIPO I;100.000;COSR-SE;SE X;MS;MATO GROSSO DO SUL;A;MSUHSD"
    raw = tmp_path / "modalidade_usina"
    _gravar(raw, [OUTRA, curta, so_conferencia, *HOMONIMOS, USINA])
    (raw / "_manifesto_ons.json").write_text(json.dumps({"MODALIDADE_USINA.csv": {
        "ultima_modificacao": "2026-10-04T22:04:50", "registrado_em_utc": "2026-10-05 15:07:29"}}), encoding="utf-8")
    ficha, auditoria = extrair_cadastro(raw, **IDENT)
    assert list(auditoria.columns) == COLUNAS_AUDITORIA_CADASTRO
    a = auditoria.iloc[0]
    assert (a["arquivo"], a["formato"], a["status"], a["obtido"]) == ("MODALIDADE_USINA.csv", "CSV", "PROCESSADO", True)
    assert (a["linhas_lidas"], a["linhas_formato_irregular"], a["linhas_usina"]) == (7, 1, 1)
    assert (a["linhas_so_identificador"], a["linhas_so_conferencia"]) == (0, 1)
    assert a["data_publicacao"] == "2026-10-04T22:04:50"
    assert ficha.iloc[0]["data_consulta_utc"] == "2026-10-05 15:07:29"


def test_auditoria_sem_a_usina_com_falha_de_leitura_e_sem_arquivo(tmp_path: Path) -> None:
    raw = tmp_path / "modalidade_usina"
    _gravar(raw, [OUTRA, *HOMONIMOS])
    ficha, auditoria = extrair_cadastro(raw, **IDENT)
    assert ficha.empty and auditoria.iloc[0]["status"] == "SEM_REGISTROS"
    (raw / "MODALIDADE_USINA.csv").write_text("usina;estado\nX;MS\n", encoding="utf-8")
    ficha, auditoria = extrair_cadastro(raw, **IDENT)
    assert ficha.empty and auditoria.iloc[0]["status"] == "FALHA" and "colunas ausentes" in auditoria.iloc[0]["mensagem"]
    ficha, auditoria = extrair_cadastro(tmp_path / "vazia", **IDENT)
    assert ficha.empty and auditoria.empty


class _Resposta(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_sincronizacao_com_republicacao_preserva_a_versao_anterior(tmp_path: Path) -> None:
    raw = tmp_path / "modalidade_usina"
    publicado = {"conteudo": _csv([USINA, *HOMONIMOS]), "data": "2026-10-04T22:04:50"}

    def urlopen(requisicao, timeout=None):
        url = getattr(requisicao, "full_url", requisicao)
        if "package_show" in url:
            recursos = [{"id": "1", "name": "ModalidadeUsina", "format": "CSV", "size": len(publicado["conteudo"]),
                         "last_modified": publicado["data"], "url": "https://ons.example/MODALIDADE_USINA.csv"},
                        {"id": "2", "name": "Dicionário de Dados", "format": "PDF", "size": None,
                         "url": "https://ons.example/DicionarioDados_Modalidade.pdf"}]
            return _Resposta(json.dumps({"success": True, "result": {"resources": recursos}}).encode("utf-8"))
        if url.endswith(".csv"):
            return _Resposta(publicado["conteudo"])
        raise urllib.error.URLError("não usado")

    with patch("src.coleta.catalogo.urllib.request.urlopen", side_effect=urlopen), patch("src.coleta.catalogo.time.sleep"):
        assert sincronizar_cadastro(raw) == ("MODALIDADE_USINA.csv", [])
        ficha, _ = extrair_cadastro(raw, **IDENT)
        assert ficha.iloc[0]["homonimos"] == 3 and ficha.iloc[0]["data_consulta_utc"]
        publicado.update(conteudo=_csv([USINA.replace("TIPO II-A", "TIPO I")]), data="2026-10-05T22:04:50")
        assert sincronizar_cadastro(raw) == ("MODALIDADE_USINA.csv", [])
    assert extrair_cadastro(raw, **IDENT)[0].iloc[0]["nom_modalidadeoperacao"] == "TIPO I"
    preservados = list((raw / "_versoes_anteriores").iterdir())
    assert len(preservados) == 1 and b"TIPO II-A" in preservados[0].read_bytes()


def test_falha_de_download_entra_na_auditoria_e_le_a_copia_local(tmp_path: Path) -> None:
    raw = tmp_path / "modalidade_usina"
    _gravar(raw, [USINA])
    metadados = {"result": {"resources": [{"id": "1", "name": "ModalidadeUsina", "format": "CSV", "size": 10,
                                           "url": "https://ons.example/MODALIDADE_USINA.csv"}]}}
    with patch("src.coleta.cadastro.fetch_ckan_package_metadata", return_value=metadados), \
            patch("src.coleta.cadastro.download_resource", side_effect=OSError("HTTP 500")):
        nome, falhas = sincronizar_cadastro(raw)
    ficha, auditoria = extrair_cadastro(raw, **IDENT, nome=nome, falhas=falhas)
    assert len(ficha) == 1
    assert auditoria["status"].tolist() == ["PROCESSADO", "FALHA"]
    assert auditoria["obtido"].tolist() == [True, False]
