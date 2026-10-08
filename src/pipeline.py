"""Ordem das etapas, manifesto da etapa (``etapa.json``), pré-requisitos e códigos de saída.

Regras comuns às cinco etapas (spec da Coleta de dados, FR-001 a FR-013):

- cada etapa usa só os resultados gravados pelas anteriores e grava os seus na pasta dela;
- antes de gravar, a etapa confere o ``etapa.json`` da anterior: só aceita a anterior ``concluida`` (com qualquer código
  registrado) e no formato atual; senão sai com o código 5, sem gravar nada;
- ao terminar, grava o ``etapa.json``: códigos 0 e 3 gravam ``concluida`` e marcam as seguintes como ``desatualizada``;
  códigos 1 e 2 gravam ``falha``;
- o comando ``completo`` executa as cinco etapas na ordem e para na primeira que não terminar com 0.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.comum import caminhos
from src.comum.logger import setup_logger
from src.comum.perfil import definir_perfil_ativo

logger = setup_logger("pipeline")

ETAPAS: Tuple[str, ...] = ("coleta", "tratamento", "conferencia", "analises", "relatorio")
ANTERIOR: Dict[str, str] = {b: a for a, b in zip(ETAPAS, ETAPAS[1:])}
# Muda quando os arquivos da etapa mudam de formato; a etapa seguinte recusa um formato antigo (código 5)
VERSAO_FORMATO: Dict[str, int] = {etapa: 1 for etapa in ETAPAS}

CODIGO_SUCESSO = 0
CODIGO_ERRO = 1
CODIGO_DADO_NAO_OBTIDO = 2
CODIGO_META_HIDROLOGIA = 3
CODIGO_PERFIL_INVALIDO = 4
CODIGO_ETAPA_ANTERIOR = 5
CODIGO_DIFERENCAS = 6
CODIGOS_CONCLUIDA = (CODIGO_SUCESSO, CODIGO_META_HIDROLOGIA)

# Função de cada etapa ("módulo:função"), importada só na execução
FUNCOES_ETAPA: Dict[str, str] = {
    "coleta": "src.coleta.etapa:executar_coleta",
    "tratamento": "src.tratamento.etapa:executar_tratamento",
    "conferencia": "src.conferencia.etapa:executar_conferencia",
    "analises": "src.analises.etapa:executar_analises",
    "relatorio": "src.relatorio.etapa:executar_relatorio",
}


@dataclass
class ResultadoEtapa:
    """O que a função de uma etapa devolve: código de saída, arquivos gravados e resumo do ``etapa.json``."""

    codigo: int = CODIGO_SUCESSO
    arquivos: List[Path] = field(default_factory=list)
    resumo: Dict[str, Any] = field(default_factory=dict)


def _agora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def arquivo_manifesto(slug: str, etapa: str) -> Path:
    return caminhos.pasta_etapa(slug, etapa) / caminhos.MANIFESTO_ETAPA


def ler_manifesto(slug: str, etapa: str) -> Optional[Dict[str, Any]]:
    caminho = arquivo_manifesto(slug, etapa)
    if not caminho.is_file():
        return None
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _gravar_manifesto(slug: str, etapa: str, dados: Dict[str, Any]) -> None:
    caminho = arquivo_manifesto(slug, etapa)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".json.tmp")
    temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    os.replace(temporario, caminho)


def mensagem_etapa_anterior(etapa: str, slug: str) -> str:
    anterior = ANTERIOR[etapa]
    return (f"A etapa '{etapa}' precisa da etapa '{anterior}' concluída para a usina '{slug}'. "
            f"Execute antes: python -m src {anterior} --usina {slug}")


def etapa_anterior_concluida(slug: str, etapa: str) -> Optional[Dict[str, Any]]:
    """Manifesto da etapa anterior, se ela está ``concluida`` e no formato atual; senão None."""
    anterior = ANTERIOR[etapa]
    manifesto = ler_manifesto(slug, anterior)
    if (not manifesto or manifesto.get("status") != "concluida"
            or manifesto.get("versao_formato") != VERSAO_FORMATO[anterior]):
        return None
    return manifesto


def marcar_seguintes_desatualizadas(slug: str, etapa: str) -> List[str]:
    """Marca como ``desatualizada`` o manifesto das etapas seguintes que já existirem."""
    marcadas = []
    for seguinte in ETAPAS[ETAPAS.index(etapa) + 1:]:
        manifesto = ler_manifesto(slug, seguinte)
        if manifesto is not None and manifesto.get("status") != "desatualizada":
            manifesto["status"] = "desatualizada"
            _gravar_manifesto(slug, seguinte, manifesto)
            marcadas.append(seguinte)
    return marcadas


def _funcao(etapa: str) -> Callable[..., ResultadoEtapa]:
    modulo, nome = FUNCOES_ETAPA[etapa].split(":")
    return getattr(importlib.import_module(modulo), nome)


def executar_etapa(etapa: str, perfil: Any, funcao: Optional[Callable[..., ResultadoEtapa]] = None,
                   **opcoes: Any) -> int:
    """Executa uma etapa para a usina do perfil, com pré-requisito, manifesto e invalidação das seguintes."""
    slug = perfil.usina.slug
    anterior = None
    if etapa != ETAPAS[0]:
        anterior = etapa_anterior_concluida(slug, etapa)
        if anterior is None:
            logger.error(mensagem_etapa_anterior(etapa, slug))
            return CODIGO_ETAPA_ANTERIOR
    pasta = caminhos.pasta_etapa(slug, etapa)
    iniciada_em = _agora()
    logger.info("Etapa '%s' da usina '%s' iniciada.", etapa, slug)
    definir_perfil_ativo(perfil)
    try:
        resultado = (funcao or _funcao(etapa))(perfil, **opcoes)
    except Exception as exc:  # qualquer erro vira código 1, registrado no manifesto
        logger.exception("Etapa '%s' da usina '%s' terminou com erro: %s", etapa, slug, exc)
        resultado = ResultadoEtapa(codigo=CODIGO_ERRO, resumo={"erro": str(exc)})
    except KeyboardInterrupt:  # interrupção pelo usuário (Ctrl+C): também código 1, com o manifesto em falha
        logger.error("Etapa '%s' da usina '%s' interrompida pelo usuário.", etapa, slug)
        resultado = ResultadoEtapa(codigo=CODIGO_ERRO, resumo={"erro": "interrompida pelo usuário"})
    finally:
        definir_perfil_ativo(None)
    status = "concluida" if resultado.codigo in CODIGOS_CONCLUIDA else "falha"
    arquivos = []
    for caminho in resultado.arquivos:
        caminho = Path(caminho)
        if caminho.is_file():
            nome = caminho.relative_to(pasta).as_posix() if caminho.is_relative_to(pasta) else caminho.as_posix()
            arquivos.append({"nome": nome, "bytes": caminho.stat().st_size, "sha256": _sha256(caminho)})
    _gravar_manifesto(slug, etapa, {
        "etapa": etapa,
        "usina": slug,
        "versao_formato": VERSAO_FORMATO[etapa],
        "iniciada_em": iniciada_em,
        "concluida_em": _agora(),
        "status": status,
        "codigo_saida": resultado.codigo,
        "etapa_anterior": ({"etapa": ANTERIOR[etapa], "concluida_em": anterior.get("concluida_em")}
                           if anterior else None),
        "arquivos": arquivos,
        "resumo": resultado.resumo,
    })
    if status == "concluida":
        marcadas = marcar_seguintes_desatualizadas(slug, etapa)
        if marcadas:
            logger.info("Etapas seguintes marcadas como desatualizadas: %s.", ", ".join(marcadas))
    logger.info("Etapa '%s' da usina '%s': %s (código %d). Resumo: %s. Pasta: %s", etapa, slug, status,
                resultado.codigo, json.dumps(resultado.resumo, ensure_ascii=False, default=str), pasta)
    return resultado.codigo


def executar_completo(perfil: Any, sem_portal: bool = False, forcar_download: bool = False,
                      data_geracao: Optional[datetime] = None) -> int:
    """As cinco etapas na ordem; para na primeira que não terminar com 0 e devolve o código dela."""
    opcoes: Dict[str, Dict[str, Any]] = {
        "coleta": {"sem_portal": sem_portal, "forcar_download": forcar_download},
        "relatorio": {"data_geracao": data_geracao},
    }
    for etapa in ETAPAS:
        codigo = executar_etapa(etapa, perfil, **opcoes.get(etapa, {}))
        if codigo != CODIGO_SUCESSO:
            logger.warning("Fluxo completo interrompido na etapa '%s' (código %d).", etapa, codigo)
            return codigo
    return CODIGO_SUCESSO
