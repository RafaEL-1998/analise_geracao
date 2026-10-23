"""Resumo executivo (spec da Geração do relatório, US11): até duas páginas, gerado com o relatório completo, com a
conclusão copiada igual, os indicadores da capa, as colunas principais da tabela anual e "Sobre os dados"."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pytest

from src.analises.conclusao import FRASE_CONCLUSAO_VAZIA, montar_conclusao
from src.analises.etapa import analisar
from src.analises.evt import preparar_dados
from src.comum.regras import (
    GLOSSARIO_RESUMO,
    RESUMO_MAXIMO_PAGINAS,
    RESUMO_MAXIMO_PALAVRAS,
    RESUMO_MAXIMO_PALAVRAS_DADOS,
)
from src.relatorio import resumo as modulo_resumo
from src.relatorio.conteudo import indicadores_capa, linhas_tabela_anual, listas_conclusao
from src.relatorio.estrutura import secoes_presentes
from src.relatorio.etapa import completar_resultados
from src.relatorio.fontes import CONFERENCIAS, fontes_resumo, origem_dos_dados, texto_conferencia_curto
from src.relatorio.markdown import _md_conteudo_secao, gerar_relatorio_md
from src.relatorio.resumo import AVISO_SECOES, COLUNAS_RESUMO_ANUAL, gerar_resumo, montar_resumo
from src.relatorio.resumo_pdf import gerar_resumo_pdf, paginas_do_pdf
from tests.analises.test_conclusao import _neutro, _tudo
from tests.analises.test_indicadores import _conferencias, _indicadores_sinteticos

DATA = datetime(2026, 10, 7, 8, 53)
PAGINAS_RELATORIO = 27  # número de páginas do relatório completo citado no cabeçalho (única exceção da FR-063)
TERMOS_PROIBIDOS = ("satisfatório", "insatisfatório", "cumpre", "descumpre")
NUMERO = re.compile(r"\d[\d.]*(?:,\d+)?")


def _sintetico(res: Any) -> Any:
    """Resultados de ``_tudo`` ou ``_neutro``: conclusão refeita com os números ajustados e a origem dos dados.

    Esses resultados trazem só os campos que as regras da conclusão usam; as conferências recebem um resultado mínimo.
    """
    res.conclusao = montar_conclusao(res)
    conferencia = {"horas_comuns": 10, "coincidentes": 10, "divergentes": 0, "pct_coincidentes": 100.0}
    for campo in ("disponibilidade", "geracao_oficial"):
        if getattr(res, campo):
            getattr(res, campo).setdefault("conferencia", conferencia)
    if res.hidrologia:
        res.hidrologia.setdefault("alinhamento", pd.DataFrame([{"horas_comuns": 10, "coincidentes_ambas": 10,
                                                                "pct_coincidencia": 100.0, "confirmado": True}]))
    res.fontes = origem_dos_dados(res)
    return res


def _gerar(res: Any, pasta: Path, nome: str = "resumo") -> Dict[str, Any]:
    pdf, md, info = gerar_resumo(res, pasta / f"{nome}.pdf", pasta / f"{nome}.md", DATA, True, PAGINAS_RELATORIO)
    return {"pdf": pdf, "md": md.read_text(encoding="utf-8"), "info": info}


@pytest.fixture
def df_base(df_sintetico: pd.DataFrame) -> pd.DataFrame:
    return preparar_dados(df_sintetico)


@pytest.fixture
def res_completo(df_base: pd.DataFrame, tmp_path: Path):
    """Resultados com os indicadores oficiais, como os de ``tests/analises/test_indicadores.py``, completados."""
    indicadores = _indicadores_sinteticos()
    return completar_resultados(analisar(df_base, _conferencias(indicadores), tmp_path / "sem_auditoria.csv",
                                         indicadores=indicadores))


@pytest.fixture
def gerado(res_completo, tmp_path: Path) -> Dict[str, Any]:
    saida = _gerar(res_completo, tmp_path)
    saida["res"] = res_completo
    saida["relatorio"] = gerar_relatorio_md(res_completo, None, tmp_path / "relatorio.md",
                                            data_geracao=DATA).read_text(encoding="utf-8")
    return saida


def _titulos(md: str) -> List[str]:
    return [linha[3:] for linha in md.splitlines() if linha.startswith("## ")]


def _bloco(md: str, titulo: str) -> str:
    """Texto de um bloco "## <titulo>" do resumo, até o bloco seguinte."""
    m = re.search(rf"^## {re.escape(titulo)}\n(.*?)(?=^## |\Z)", md, flags=re.S | re.M)
    assert m, titulo
    return m.group(1).strip()


def _conclusao_do_resumo(md: str) -> str:
    bloco = _bloco(md, "Conclusão")
    assert bloco.startswith(AVISO_SECOES + "\n\n")
    return bloco[len(AVISO_SECOES):].strip()


def _fora_das_tabelas(md: str) -> List[str]:
    return [linha for linha in md.splitlines() if not linha.startswith("|")]


def _palavras(linhas: List[str]) -> int:
    """Palavras separadas por espaço, sem as marcas de Markdown (a mesma regra do resumo do etapa.json)."""
    return sum(len(re.sub(r"^\s*(#+|-)\s+", "", linha).replace("**", "").replace("\\", "").split()) for linha in linhas)


def _tabelas(md: str) -> int:
    return len(re.findall(r"(?:^\|.*\n)+", md + "\n", flags=re.M))


# ---------------------------------------------------------------------------
# US11, cenários 1 a 4: o documento
# ---------------------------------------------------------------------------


def test_resumo_gerado_com_a_data_do_relatorio(gerado) -> None:
    assert gerado["pdf"].read_bytes()[:5] == b"%PDF-"
    assert "Gerado em 07/10/2026 08:53" in gerado["md"]
    assert "**Gerado em**: 07/10/2026 08:53" in gerado["relatorio"]
    assert f"de {PAGINAS_RELATORIO} páginas" in gerado["md"]


def test_blocos_na_ordem_fixa(gerado) -> None:
    assert gerado["md"].startswith("# ") and " — resumo executivo" in gerado["md"].splitlines()[0]
    # FR-056: a conclusão fecha o resumo
    assert _titulos(gerado["md"]) == ["Indicadores-chave", "Evolução anual", "Sobre os dados", "Conclusão"]


def test_indicadores_iguais_aos_da_capa(gerado) -> None:
    bloco = _bloco(gerado["md"], "Indicadores-chave")
    for rotulo, valor, detalhe in indicadores_capa(gerado["res"])[0]:
        assert f"| {rotulo} | {valor} | {detalhe} |" in bloco
    assert "Seção de origem: capa do relatório completo." in bloco


def test_evolucao_anual_com_as_colunas_e_os_valores_da_tabela_do_relatorio(gerado) -> None:
    bloco = _bloco(gerado["md"], "Evolução anual")
    colunas = COLUNAS_RESUMO_ANUAL["evt"]
    assert f"| {' | '.join(colunas)} |" in bloco
    cabecalho, linhas = linhas_tabela_anual(gerado["res"])
    indices = [cabecalho.index(c) for c in colunas]
    for linha in linhas:
        assert f"| {' | '.join(linha[i] for i in indices)} |" in bloco
    secao = next(n for n, s in secoes_presentes(gerado["res"]) if s.chave == "indicadores_anuais")
    assert "Ano parcial." in bloco and f"seção {secao} do relatório completo" in bloco


def test_todo_numero_do_resumo_esta_no_relatorio(gerado) -> None:
    for linha in gerado["md"].splitlines():
        if linha.startswith("Resume o relatório completo"):
            continue  # número de páginas do relatório completo
        for numero in NUMERO.findall(linha):
            assert numero in gerado["relatorio"], (numero, linha)


def test_limites_de_paginas_figuras_tabelas_e_palavras(gerado) -> None:
    assert paginas_do_pdf(gerado["pdf"]) <= RESUMO_MAXIMO_PAGINAS
    assert b"/Subtype /Image" not in gerado["pdf"].read_bytes()
    assert _tabelas(gerado["md"]) == 2
    assert _palavras(_fora_das_tabelas(gerado["md"])) <= RESUMO_MAXIMO_PALAVRAS
    assert _palavras(_bloco(gerado["md"], "Sobre os dados").splitlines()) <= RESUMO_MAXIMO_PALAVRAS_DADOS
    assert gerado["info"] == {"paginas": paginas_do_pdf(gerado["pdf"]), "evolucao_anual": True,
                              "palavras": _palavras(_fora_das_tabelas(gerado["md"]))}


def test_sobre_os_dados_com_conferencias_e_fontes(gerado) -> None:
    res, bloco = gerado["res"], _bloco(gerado["md"], "Sobre os dados")
    feitas = [cid for cid, c in CONFERENCIAS.items() if c.base in res.fontes["carregados"]]
    assert feitas
    for cid in feitas:
        assert texto_conferencia_curto(res, cid) in bloco, cid
    for texto in fontes_resumo(res):
        assert texto in bloco
    assert "não informam a causa das paradas" in bloco


def test_linha_de_termos_so_com_as_siglas_do_resumo_na_ordem(res_completo) -> None:
    resumo = montar_resumo(res_completo, PAGINAS_RELATORIO, DATA)
    siglas = [s for s, _ in resumo.termos]
    assert siglas and set(siglas) <= set(GLOSSARIO_RESUMO)
    assert all(texto == GLOSSARIO_RESUMO[s] for s, texto in resumo.termos)
    corpo = modulo_resumo.texto_corrido(resumo)
    posicoes = [modulo_resumo.primeira_ocorrencia(corpo, s) for s in siglas]
    assert all(p >= 0 for p in posicoes) and posicoes == sorted(posicoes)
    ausentes = [s for s in GLOSSARIO_RESUMO if s not in siglas]
    assert all(modulo_resumo.primeira_ocorrencia(corpo, s) < 0 for s in ausentes)


def test_pdf_reproduzivel_com_a_data_fixa(res_completo, tmp_path: Path) -> None:
    primeiro, segundo = _gerar(res_completo, tmp_path, "a"), _gerar(res_completo, tmp_path, "b")
    assert primeiro["pdf"].read_bytes() == segundo["pdf"].read_bytes()


def test_pdf_e_markdown_com_os_mesmos_blocos(gerado, tmp_path: Path) -> None:
    resumo = montar_resumo(gerado["res"], PAGINAS_RELATORIO, DATA)
    assert gerar_resumo_pdf(resumo, tmp_path / "blocos.pdf", True) == _titulos(gerado["md"])


# ---------------------------------------------------------------------------
# US11, cenários 1 a 4: a regra das duas páginas (FR-055)
# ---------------------------------------------------------------------------


def test_evolucao_anual_sai_quando_o_resumo_passa_de_duas_paginas(res_completo, tmp_path: Path, monkeypatch) -> None:
    paginas = iter([RESUMO_MAXIMO_PAGINAS + 1, RESUMO_MAXIMO_PAGINAS])
    monkeypatch.setattr(modulo_resumo, "paginas_do_pdf", lambda caminho: next(paginas))
    saida = _gerar(res_completo, tmp_path)
    assert saida["info"]["evolucao_anual"] is False and saida["info"]["paginas"] == RESUMO_MAXIMO_PAGINAS
    bloco = _bloco(saida["md"], "Evolução anual")
    secao = next(n for n, s in secoes_presentes(res_completo) if s.chave == "indicadores_anuais")
    assert bloco == f"A evolução anual está na seção {secao} do relatório completo."
    assert _tabelas(saida["md"]) == 1


def test_resumo_acima_de_duas_paginas_sem_a_evolucao_anual_e_erro(res_completo, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(modulo_resumo, "paginas_do_pdf", lambda caminho: RESUMO_MAXIMO_PAGINAS + 1)
    with pytest.raises(RuntimeError, match="acima do máximo"):
        _gerar(res_completo, tmp_path)
    assert not (tmp_path / "resumo.md").exists()


def test_conclusao_longa_de_verdade_e_erro(res_completo, tmp_path: Path, monkeypatch) -> None:
    longo = " ".join(["indício a confirmar com o agente"] * 60)
    listas = [(titulo, [f"{longo} {i}" for i in range(5)]) for titulo in ("A", "B", "C", "D")]
    monkeypatch.setattr(modulo_resumo, "listas_conclusao", lambda res: listas)
    with pytest.raises(RuntimeError, match="acima do máximo"):
        _gerar(res_completo, tmp_path)


# ---------------------------------------------------------------------------
# US11, cenários 5 a 8: conclusão igual à do relatório completo
# ---------------------------------------------------------------------------


def test_conclusao_igual_a_do_relatorio_completo(gerado) -> None:
    m = re.search(r"^## \d+\. Conclusão\n(.*?)(?=^## \d+\. )", gerado["relatorio"], flags=re.S | re.M)
    assert m
    assert _conclusao_do_resumo(gerado["md"]) == m.group(1).strip()


def test_conclusao_igual_com_todas_as_regras(df_base: pd.DataFrame, tmp_path: Path) -> None:
    res = _sintetico(_tudo(df_base))
    listas = listas_conclusao(res)
    assert len(listas) == 4
    secao = "\n".join(_md_conteudo_secao(res, "conclusao", "Conclusão", None, {})).strip()
    md = _gerar(res, tmp_path)["md"]
    assert _conclusao_do_resumo(md) == secao
    assert [linha[4:] for linha in _conclusao_do_resumo(md).splitlines() if linha.startswith("### ")] == [
        titulo for titulo, _ in listas]


def test_conclusao_vazia(df_base: pd.DataFrame, tmp_path: Path) -> None:
    res = _sintetico(_neutro(df_base))
    assert listas_conclusao(res) == []
    assert _conclusao_do_resumo(_gerar(res, tmp_path)["md"]) == FRASE_CONCLUSAO_VAZIA


def test_sem_termos_de_parecer_fora_da_conclusao(gerado) -> None:
    md = gerado["md"].replace(_conclusao_do_resumo(gerado["md"]), "").lower()
    for termo in TERMOS_PROIBIDOS:
        assert not re.search(rf"\b{termo}\b", md), termo
