"""Relatórios de referência (spec 006, decisão R22; contrato cli-referencias.md).

``python -m src referencia --usina <slug> --data-geracao "DD/MM/AAAA HH:MM" --aprovado-em "DD/MM/AAAA"`` registra em
``relatorios_referencia/<slug>/`` o relatório da usina aprovado pelo usuário, com:

- os arquivos do relatório, os do ``etapa.json`` do relatório;
- ``coleta/``: a Coleta congelada, só os arquivos do ``etapa.json`` da Coleta e o próprio ``etapa.json``, sem ``.bak``;
- ``perfil.toml``: a cópia do perfil usado;
- ``referencia.json``: data de geração, data da aprovação, período e SHA-256 de cada arquivo.

Exige o relatório ``concluida``, gerado com a data pedida, e a Coleta ``concluida`` no formato atual. Grava numa pasta
temporária, confere os SHA-256 e só então troca a referência anterior (Requisito Técnico 3). Uma referência anterior
com mudanças fora do git não é substituída, para que ela fique no histórico (princípio IX).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src import pipeline
from src.comum import caminhos
from src.comum import perfil as modulo_perfil
from src.comum.logger import setup_logger

logger = setup_logger("pipeline")

NOME_REFERENCIA = "referencia.json"
NOME_PERFIL = "perfil.toml"
PASTA_COLETA = "coleta"
FORMATO_DATA_GERACAO = "%d/%m/%Y %H:%M"
FORMATO_DATA_APROVACAO = "%d/%m/%Y"


class ReferenciaInvalida(Exception):
    """Coleta ou perfil congelados ausentes ou com SHA-256 diferente do ``referencia.json``."""


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _item(pasta: Path, nome: str) -> Dict[str, Any]:
    caminho = pasta / nome
    return {"nome": nome, "bytes": caminho.stat().st_size, "sha256": sha256_arquivo(caminho)}


def referencia_commitada(pasta: Path) -> bool:
    """A referência não tem mudanças fora do git (``git status --porcelain`` vazio); sem git, não está commitada."""
    try:
        saida = subprocess.run(["git", "status", "--porcelain", "--", str(pasta)], cwd=str(Path(pasta).parent),
                               capture_output=True, text=True, check=False)
    except OSError:
        return False
    return saida.returncode == 0 and not saida.stdout.strip()


def ler_referencia(pasta: Path) -> Dict[str, Any]:
    """``referencia.json`` da pasta."""
    return json.loads((Path(pasta) / NOME_REFERENCIA).read_text(encoding="utf-8"))


def conferir_congelados(pasta: Path, referencia: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Confere o perfil e a Coleta congelados pelos SHA-256 do ``referencia.json``; devolve o ``referencia.json``."""
    pasta = Path(pasta)
    try:
        referencia = referencia or ler_referencia(pasta)
    except (OSError, ValueError) as exc:
        raise ReferenciaInvalida(f"{NOME_REFERENCIA} ausente ou ilegível em {pasta}: {exc}") from exc
    perfil = pasta / NOME_PERFIL
    if not perfil.is_file() or sha256_arquivo(perfil) != referencia.get("perfil"):
        raise ReferenciaInvalida(f"perfil congelado ausente ou com SHA-256 diferente: {perfil}")
    for item in referencia.get("coleta") or []:
        caminho = pasta / PASTA_COLETA / item["nome"]
        if not caminho.is_file() or sha256_arquivo(caminho) != item["sha256"]:
            raise ReferenciaInvalida(f"Coleta congelada ausente ou com SHA-256 diferente: {caminho}")
    if not referencia.get("coleta"):
        raise ReferenciaInvalida(f"{NOME_REFERENCIA} sem a lista da Coleta congelada: {pasta}")
    return referencia


def conferir_referencia(pasta: Path) -> Dict[str, Any]:
    """Confere todos os arquivos da referência (relatório, perfil e Coleta) pelos SHA-256 do ``referencia.json``."""
    referencia = conferir_congelados(pasta)
    for item in referencia.get("arquivos") or []:
        caminho = Path(pasta) / item["nome"]
        if not caminho.is_file() or sha256_arquivo(caminho) != item["sha256"]:
            raise ReferenciaInvalida(f"arquivo do relatório ausente ou com SHA-256 diferente: {caminho}")
    return referencia


def _manifesto_concluido(slug: str, etapa: str) -> Optional[Dict[str, Any]]:
    manifesto = pipeline.ler_manifesto(slug, etapa)
    if (not manifesto or manifesto.get("status") != "concluida"
            or manifesto.get("versao_formato") != pipeline.VERSAO_FORMATO[etapa]):
        return None
    return manifesto


def _copiar_conferido(origem: Path, destino: Path, item: Dict[str, Any]) -> None:
    """Copia o arquivo do manifesto da etapa, conferindo antes que ele não mudou depois da execução."""
    if not origem.is_file() or sha256_arquivo(origem) != item["sha256"]:
        raise RuntimeError(f"{origem} mudou depois da execução da etapa (SHA-256 diferente do etapa.json)")
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origem, destino)


def _montar(slug: str, temporaria: Path, relatorio: Dict[str, Any], coleta: Dict[str, Any], data_geracao: str,
            aprovado_em: str) -> None:
    pasta_relatorio = caminhos.pasta_relatorio(slug)
    pasta_coleta = caminhos.pasta_etapa(slug, "coleta")
    for item in relatorio["arquivos"]:
        _copiar_conferido(pasta_relatorio / item["nome"], temporaria / item["nome"], item)
    for item in coleta["arquivos"]:
        _copiar_conferido(pasta_coleta / item["nome"], temporaria / PASTA_COLETA / item["nome"], item)
    shutil.copy2(pasta_coleta / caminhos.MANIFESTO_ETAPA, temporaria / PASTA_COLETA / caminhos.MANIFESTO_ETAPA)
    shutil.copy2(modulo_perfil.arquivo_perfil(slug), temporaria / NOME_PERFIL)
    periodo = (coleta.get("resumo") or {}).get("periodo")
    if not periodo:  # sem o período no resumo da Coleta, o das Análises
        periodo = ((pipeline.ler_manifesto(slug, "analises") or {}).get("resumo") or {}).get("periodo") or {}
    nomes_coleta = [item["nome"] for item in coleta["arquivos"]] + [caminhos.MANIFESTO_ETAPA]
    referencia = {
        "usina": slug,
        "data_geracao": data_geracao,
        "aprovado_em": aprovado_em,
        "periodo": {"inicio": periodo.get("inicio", ""), "fim": periodo.get("fim", "")},
        "arquivos": [_item(temporaria, item["nome"]) for item in relatorio["arquivos"]],
        "perfil": sha256_arquivo(temporaria / NOME_PERFIL),
        "coleta": [_item(temporaria / PASTA_COLETA, nome) for nome in nomes_coleta],
    }
    (temporaria / NOME_REFERENCIA).write_text(json.dumps(referencia, ensure_ascii=False, indent=1), encoding="utf-8")
    conferir_referencia(temporaria)
    gravados = {p.relative_to(temporaria).as_posix() for p in temporaria.rglob("*") if p.is_file()}
    esperados = ({i["nome"] for i in referencia["arquivos"]} | {f"{PASTA_COLETA}/{n}" for n in nomes_coleta}
                 | {NOME_PERFIL, NOME_REFERENCIA})
    if gravados != esperados:
        raise RuntimeError(f"referência com arquivos inesperados: {sorted(gravados ^ esperados)}")


def _trocar(temporaria: Path, pasta: Path) -> None:
    """Troca a referência anterior pela nova; se a troca falhar, a anterior volta como estava."""
    anterior = pasta.with_name(f".anterior_{pasta.name}")
    shutil.rmtree(anterior, ignore_errors=True)
    if pasta.exists():
        os.replace(pasta, anterior)
    try:
        os.replace(temporaria, pasta)
    except OSError:
        if anterior.exists():
            os.replace(anterior, pasta)
        raise
    shutil.rmtree(anterior, ignore_errors=True)


def registrar_referencia(slug: str, data_geracao: datetime, aprovado_em: date,
                         referencia_commitada: Callable[[Path], bool] = referencia_commitada) -> int:
    """Registra o relatório aprovado de ``slug`` como referência. Códigos: 0, 1 e 5 (contrato cli-referencias.md)."""
    data = data_geracao.strftime(FORMATO_DATA_GERACAO)
    aprovado = aprovado_em.strftime(FORMATO_DATA_APROVACAO)
    relatorio = _manifesto_concluido(slug, "relatorio")
    coleta = _manifesto_concluido(slug, "coleta")
    if relatorio is None or coleta is None:
        etapa = "relatorio" if relatorio is None else "coleta"
        logger.error("A etapa '%s' da usina '%s' não está concluída no formato atual (ausente, desatualizada, com "
                     "falha ou em formato antigo). Execute: python -m src completo --usina %s", etapa, slug, slug)
        return pipeline.CODIGO_ETAPA_ANTERIOR
    gerado_em = (relatorio.get("resumo") or {}).get("data_geracao")
    if gerado_em != data:
        logger.error('O relatório de \'%s\' foi gerado em %s, não em %s. Gere com: python -m src relatorio --usina %s '
                     '--data-geracao "%s"', slug, gerado_em or "data não registrada", data, slug, data)
        return pipeline.CODIGO_ERRO
    pasta = caminhos.pasta_referencia(slug)
    if pasta.exists() and not referencia_commitada(pasta):
        logger.error("A referência atual de '%s' tem mudanças fora do git. Faça o commit antes de substituí-la.", slug)
        return pipeline.CODIGO_ERRO
    temporaria = pasta.with_name(f".gravando_{slug}")
    shutil.rmtree(temporaria, ignore_errors=True)
    try:
        temporaria.mkdir(parents=True)
        _montar(slug, temporaria, relatorio, coleta, data, aprovado)
        _trocar(temporaria, pasta)
    except Exception as exc:  # falha de gravação ou de conferência: a referência anterior fica intacta
        logger.error("Referência de '%s' não registrada: %s. A referência anterior não foi alterada.", slug, exc)
        return pipeline.CODIGO_ERRO
    finally:
        shutil.rmtree(temporaria, ignore_errors=True)
    mensagem = f'git add relatorios_referencia/{slug} && git commit -m "docs: relatório de referência de {slug} ' \
               f'(gerado em {data}, aprovado em {aprovado})"'
    logger.info("Referência de '%s' registrada em relatorios_referencia/%s/ (gerada em %s, aprovada em %s). "
                "Sugestão de commit: %s", slug, slug, data, aprovado, mensagem)
    return pipeline.CODIGO_SUCESSO


def referencias_existentes() -> List[Path]:
    """Pastas das usinas em ``relatorios_referencia/``, em ordem de slug, sem as temporárias (``.`` ou ``_``)."""
    raiz = caminhos.RELATORIOS_REFERENCIA_DIR
    if not raiz.is_dir():
        return []
    return [p for p in sorted(raiz.iterdir()) if p.is_dir() and not p.name.startswith((".", "_"))]
