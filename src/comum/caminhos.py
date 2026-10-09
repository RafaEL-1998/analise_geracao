"""Pastas e nomes de arquivo do fluxo (constituição, Requisito Técnico 6; spec da Coleta de dados, FR-010).

- ``data/raw/``: dados brutos do ONS, compartilhados por todas as usinas e gravados só pela Coleta de dados.
- ``data/catalogo/``: catálogo de usinas, montado pela Coleta (spec 006).
- ``data/usinas/<slug>/<etapa>/``: resultados de cada etapa, separados por usina.
- ``reports/<slug>/``: relatório da usina; ``reports/carteiras/<nome>/``: relatórios de carteira.
- ``usinas/<slug>/``: perfil da usina e, fora do controle de versões, os documentos de referência dela.
- ``relatorios_referencia/<slug>/``: relatórios aprovados, com a Coleta e o perfil congelados (spec 006, decisão R22).
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from src.comum.regras import (
    DIRETORIO_DICIONARIOS,
    PASTA_CADASTRO_RAW,
    PASTA_DISPONIBILIDADE_RAW,
    PASTA_GERACAO_RAW,
    PASTA_HIDROLOGIA_RAW,
    PASTA_INDICADORES_RAW,
    PASTA_PROGRAMACAO_RAW,
)

RAIZ_PROJETO: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = RAIZ_PROJETO / "data"
USINAS_DIR: Path = RAIZ_PROJETO / "usinas"
REPORTS_DIR: Path = RAIZ_PROJETO / "reports"
RELATORIOS_REFERENCIA_DIR: Path = RAIZ_PROJETO / "relatorios_referencia"
PASTA_CATALOGO: str = "catalogo"  # dentro de data/
PASTA_CARTEIRAS: str = "carteiras"  # dentro de reports/; nome reservado, não pode ser slug de usina

# Dados brutos compartilhados
RAW_DATA_DIR: Path = DATA_DIR / "raw"
RAW_MANIFEST_FILE: Path = RAW_DATA_DIR / "_manifesto_ons.json"
INDICADORES_RAW_DIR: Path = RAW_DATA_DIR / PASTA_INDICADORES_RAW
PROGRAMACAO_RAW_DIR: Path = RAW_DATA_DIR / PASTA_PROGRAMACAO_RAW
DISPONIBILIDADE_RAW_DIR: Path = RAW_DATA_DIR / PASTA_DISPONIBILIDADE_RAW
HIDROLOGIA_RAW_DIR: Path = RAW_DATA_DIR / PASTA_HIDROLOGIA_RAW
GERACAO_RAW_DIR: Path = RAW_DATA_DIR / PASTA_GERACAO_RAW
CADASTRO_RAW_DIR: Path = RAW_DATA_DIR / PASTA_CADASTRO_RAW
NOME_DICIONARIO_EVT: str = "DicionarioDados_EnergiaVertidaTurbinavel.json"

ETAPAS: tuple = ("coleta", "tratamento", "conferencia", "analises", "relatorio")
MANIFESTO_ETAPA: str = "etapa.json"

# Nomes dos arquivos de cada etapa (as pastas já identificam a usina)
ARQUIVOS_COLETA = {
    "evt": "evt_extraido.csv",
    "indicadores": "indicadores_extraido.parquet",
    "programacao": "programacao_extraido.parquet",
    "disponibilidade": "disponibilidade_extraido.parquet",
    "hidrologia": "hidrologia_extraido.parquet",
    "geracao": "geracao_extraido.parquet",
    "cadastro_ficha": "cadastro_ficha.csv",
    "auditoria_evt": "auditoria_evt.csv",
    "auditoria_indicadores": "auditoria_indicadores.csv",
    "auditoria_programacao": "auditoria_programacao.csv",
    "auditoria_disponibilidade": "auditoria_disponibilidade.csv",
    "auditoria_hidrologia": "auditoria_hidrologia.csv",
    "auditoria_geracao": "auditoria_geracao.csv",
    "auditoria_cadastro": "auditoria_cadastro.csv",
    "dicionarios": "dicionarios.csv",
    # Formato 2 (spec 006, decisão R22): as etapas seguintes leem estes arquivos, nunca data/raw/
    "datas_obtencao": "datas_obtencao.csv",
    "dicionario_evt": "dicionario_evt.json",
}
ARQUIVOS_TRATAMENTO = {
    "evt_parquet": "evt_tratado.parquet",
    "evt_csv": "evt_tratado.csv",
    "evt_xlsx": "evt_tratado.xlsx",
    "validacao_csv": "validacao_fisica.csv",
    "validacao_md": "validacao_fisica.md",
    "indicadores_ug_mensal": "indicadores_ug_mensal.csv",
    "indicadores_ug_anual": "indicadores_ug_anual.csv",
    "horas_estado_mensal": "horas_estado_mensal.csv",
    "teifa_teip_mensal": "teifa_teip_mensal.csv",
    "indicadores_xlsx": "indicadores.xlsx",
    "programacao_horaria": "programacao_horaria.csv",
    "programacao_dias_ausentes": "programacao_dias_ausentes.csv",
    "disponibilidade_horaria": "disponibilidade_horaria.csv",
    "disponibilidade_ausencias": "disponibilidade_ausencias.csv",
    "auditoria_disponibilidade": "auditoria_disponibilidade.csv",
    "hidrologia_horaria": "hidrologia_horaria.csv",
    "hidrologia_ausencias": "hidrologia_ausencias.csv",
    "auditoria_hidrologia": "auditoria_hidrologia.csv",
    "geracao_horaria": "geracao_horaria.csv",
    "geracao_ausencias": "geracao_ausencias.csv",
    "auditoria_geracao": "auditoria_geracao.csv",
}
ARQUIVOS_CONFERENCIA = {
    "resultados": "conferencias.pkl",
    "geracao": "geracao.csv",
    "geracao_divergencias": "geracao_divergencias.csv",
    "disponibilidade": "disponibilidade.csv",
    "disponibilidade_divergencias": "disponibilidade_divergencias.csv",
    "vazoes": "vazoes.csv",
    "dispf_horas": "dispf_horas.csv",
    "teifa_teip": "teifa_teip.csv",
    "cadastro": "cadastro.csv",
}
ARQUIVOS_ANALISES = {"resultados": "resultados.pkl"}
ARQUIVOS_RELATORIO = {
    "pdf": "relatorio_analise_estatistica.pdf",
    "md": "relatorio_analise_estatistica.md",
    "xlsx": "perfil_estatistico_anual.xlsx",
    "csv": "perfil_estatistico_anual.csv",
    "figuras": "figures",
}


def pasta_usina(slug: str) -> Path:
    """``usinas/<slug>/``: perfil e documentos de referência da usina."""
    return USINAS_DIR / slug


def pasta_relatorio(slug: str) -> Path:
    """``reports/<slug>/``: relatório da usina."""
    return REPORTS_DIR / slug


def pasta_etapa(slug: str, etapa: str) -> Path:
    """Pasta de resultados de uma etapa para a usina: ``data/usinas/<slug>/<etapa>/`` (o relatório, em ``reports/``)."""
    if etapa not in ETAPAS:
        raise ValueError(f"etapa desconhecida: {etapa!r} (esperado: {', '.join(ETAPAS)})")
    if etapa == "relatorio":
        return pasta_relatorio(slug)
    return DATA_DIR / "usinas" / slug / etapa


def dicionario_evt() -> Path:
    """Dicionário de dados JSON da EVT, obtido pela Coleta: ``data/raw/_dicionarios/``."""
    return RAW_DATA_DIR / DIRETORIO_DICIONARIOS / NOME_DICIONARIO_EVT


def pasta_catalogo() -> Path:
    """``data/catalogo/``: catálogo de usinas, gravado pela Coleta (spec 006)."""
    return DATA_DIR / PASTA_CATALOGO


def pasta_referencia(slug: str) -> Path:
    """``relatorios_referencia/<slug>/``: relatório aprovado da usina, com a Coleta e o perfil congelados."""
    return RELATORIOS_REFERENCIA_DIR / slug


@contextmanager
def espaco_isolado(raiz: Path, raw: Optional[Path] = None) -> Iterator[Path]:
    """Durante o bloco, as pastas do fluxo e o perfil passam a ficar em ``raiz``.

    ``data/``, ``reports/`` e ``usinas/`` ficam em ``raiz``; os brutos, em ``raw`` (por padrão, ``raiz/data/raw``).
    Usado pelo ``comparar --todas`` para refazer as etapas sem tocar nas pastas do projeto (spec 006, decisão R22).
    """
    global DATA_DIR, RAW_DATA_DIR, REPORTS_DIR, USINAS_DIR
    from src.comum import perfil as modulo_perfil

    raiz = Path(raiz)
    anteriores = (DATA_DIR, RAW_DATA_DIR, REPORTS_DIR, USINAS_DIR, modulo_perfil.RAIZ_PROJETO)
    DATA_DIR, REPORTS_DIR, USINAS_DIR = raiz / "data", raiz / "reports", raiz / "usinas"
    RAW_DATA_DIR = Path(raw) if raw is not None else raiz / "data" / "raw"
    modulo_perfil.RAIZ_PROJETO = raiz
    try:
        yield raiz
    finally:
        DATA_DIR, RAW_DATA_DIR, REPORTS_DIR, USINAS_DIR, modulo_perfil.RAIZ_PROJETO = anteriores
