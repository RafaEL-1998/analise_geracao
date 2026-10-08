"""Coleta de dados: obtém os conjuntos do ONS e extrai as linhas da usina do perfil (spec da Coleta de dados).

Ordem (FR-016, FR-017 e FR-020): Energia Vertida Turbinável (EVT), que define o período; indicadores e taxas;
Programação diária; disponibilidade, hidrologia e geração; cadastro; dicionários de dados. A coleta para no primeiro
conjunto com falha (código 2), depois de gravar o que dele foi lido e a auditoria. Com ``sem_portal``, nada é consultado
no portal nem gravado em ``data/raw/`` (FR-021). Só esta etapa acessa o portal do ONS.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

import pandas as pd

from src.coleta import cadastro, conjuntos, indicadores, programacao
from src.coleta.catalogo import load_manifest
from src.coleta.dicionarios import NOME_REGISTRO, exportar_registro, sincronizar_dicionarios
from src.coleta.evt import (
    consolidate_records,
    filter_all_raw_files,
    save_audit_report,
    save_consolidated_records,
    sincronizar_evt,
)
from src.comum import caminhos
from src.comum.logger import setup_logger
from src.comum.modelos import AuditoriaArquivo
from src.comum.persistencia import gravar_csv, gravar_parquet
from src.comum.regras import (
    CONJUNTOS_INDICADORES_ONS,
    CONJUNTOS_PIPELINE,
    PASTA_CADASTRO_RAW,
    PASTA_INDICADORES_RAW,
    PASTA_PROGRAMACAO_RAW,
)
from src.pipeline import CODIGO_DADO_NAO_OBTIDO, CODIGO_SUCESSO, ResultadoEtapa

logger = setup_logger("coleta")

FORMATO_DATA = "%Y-%m-%d %H:%M:%S"
ARQ = caminhos.ARQUIVOS_COLETA


# ---------------------------------------------------------------------------
# Resumo do etapa.json (FR-048)
# ---------------------------------------------------------------------------


def _agora_utc() -> str:
    return datetime.now(timezone.utc).strftime(FORMATO_DATA)


def _entradas_manifesto(pastas: Iterable[Path]) -> Dict[str, Dict[str, Any]]:
    entradas: Dict[str, Dict[str, Any]] = {}
    for pasta in pastas:
        for nome, entrada in load_manifest(Path(pasta) / caminhos.RAW_MANIFEST_FILE.name).items():
            if isinstance(entrada, dict) and not nome.startswith("_"):
                entradas[nome] = entrada
    return entradas


def resumo_conjunto(auditoria: pd.DataFrame, pastas_raw: Iterable[Path], inicio_execucao: str,
                    sem_portal: bool) -> Dict[str, Any]:
    """Resumo de um conjunto a partir da auditoria (colunas normalizadas) e dos manifestos das pastas brutas.

    ``auditoria`` traz ``arquivo``, ``obtido``, ``status`` e as contagens que se aplicam ao conjunto
    (``linhas_usina``, ``linhas_so_identificador``, ``linhas_so_conferencia``, ``linhas_formato_irregular`` e
    ``valores_invalidos``); as ausentes contam zero. Baixados são os arquivos do escopo registrados no manifesto por
    download durante esta execução; reaproveitados, os demais obtidos.
    """
    def soma(coluna: str) -> int:
        if coluna not in auditoria.columns:
            return 0
        return int(pd.to_numeric(auditoria[coluna], errors="coerce").fillna(0).sum())

    entradas = _entradas_manifesto(pastas_raw)
    obtidos = set(auditoria.loc[auditoria["obtido"].astype(bool), "arquivo"]) if len(auditoria) else set()
    nao_obtidos = set(auditoria.loc[~auditoria["obtido"].astype(bool), "arquivo"]) if len(auditoria) else set()
    baixados = 0
    if not sem_portal:
        baixados = sum(1 for nome in obtidos - nao_obtidos
                       if (entradas.get(nome) or {}).get("origem_registro") == "DOWNLOAD"
                       and str((entradas.get(nome) or {}).get("registrado_em_utc", "")) >= inicio_execucao)
    status = auditoria["status"] if len(auditoria) else pd.Series(dtype=str)
    lidos = auditoria["obtido"].astype(bool) & (status != "FALHA") if len(auditoria) else pd.Series(dtype=bool)
    publicacoes = [str(e.get("ultima_modificacao")) for e in entradas.values() if e.get("ultima_modificacao")]
    registros = [str(e.get("registrado_em_utc")) for e in entradas.values() if e.get("registrado_em_utc")]
    return {
        "arquivos_no_escopo": len(obtidos | nao_obtidos),
        "baixados": baixados,
        "reaproveitados": 0 if sem_portal else len(obtidos - nao_obtidos) - baixados,
        "nao_obtidos": len(nao_obtidos),
        "lidos": int(lidos.sum()),
        "sem_linhas_da_usina": int((status == "SEM_REGISTROS").sum()),
        "com_falha": int((status == "FALHA").sum()),
        "linhas_extraidas": soma("linhas_usina"),
        "linhas_so_identificador": soma("linhas_so_identificador"),
        "linhas_so_conferencia": soma("linhas_so_conferencia"),
        "linhas_formato_irregular": soma("linhas_formato_irregular"),
        "valores_invalidos": soma("valores_invalidos"),
        "registrados_no_manifesto": len(entradas),
        "publicacao_mais_recente": max(publicacoes) if publicacoes else "",
        "data_obtencao": max(registros) if registros else "",
    }


def auditoria_evt_normalizada(audits: List[AuditoriaArquivo]) -> pd.DataFrame:
    """Auditoria da EVT nas colunas comuns do resumo."""
    return pd.DataFrame({
        "arquivo": [a.nome_arquivo for a in audits],
        "obtido": [a.obtido for a in audits],
        "status": [a.status_processamento for a in audits],
        "linhas_usina": [a.registros_extraidos for a in audits],
        "linhas_so_identificador": [a.registros_codigo_sem_nome for a in audits],
        "linhas_so_conferencia": [a.registros_nome_sem_codigo for a in audits],
        "linhas_formato_irregular": [a.registros_formato_irregular for a in audits],
        "valores_invalidos": [a.valores_invalidos for a in audits],
    }, columns=["arquivo", "obtido", "status", "linhas_usina", "linhas_so_identificador", "linhas_so_conferencia",
                "linhas_formato_irregular", "valores_invalidos"])


def _com_falha(auditoria: pd.DataFrame) -> List[str]:
    if not len(auditoria):
        return []
    return sorted(set(auditoria.loc[auditoria["status"] == "FALHA", "arquivo"]))


# ---------------------------------------------------------------------------
# Etapa
# ---------------------------------------------------------------------------


class _Coleta:
    """Estado de uma execução: pasta da usina, arquivos gravados, resumo e opções."""

    def __init__(self, perfil: Any, sem_portal: bool, forcar_download: bool) -> None:
        self.perfil = perfil
        self.sem_portal = sem_portal
        self.forcar = forcar_download and not sem_portal
        self.pasta = caminhos.pasta_etapa(perfil.usina.slug, "coleta")
        self.raw = caminhos.RAW_DATA_DIR
        self.inicio_execucao = _agora_utc()
        self.arquivos: List[Path] = []
        self.resumo: Dict[str, Any] = {"sem_portal": sem_portal, "forcar_download": self.forcar, "conjuntos": {}}

    def gravar_csv(self, tabela: pd.DataFrame, chave: str, **opcoes: Any) -> None:
        destino = self.pasta / ARQ[chave]
        gravar_csv(tabela, destino, **opcoes)
        self.arquivos.append(destino)

    def gravar_parquet(self, tabela: pd.DataFrame, chave: str) -> None:
        destino = self.pasta / ARQ[chave]
        gravar_parquet(tabela, destino)
        self.arquivos.append(destino)

    def sincronizar(self, rotulo: str, funcao: Callable[[], Any]) -> Any:
        """Executa a sincronização com o portal (nada com ``sem_portal``); catálogo inacessível propaga (código 1)."""
        if self.sem_portal:
            return None
        logger.info("Sincronização com o portal: %s.", rotulo)
        return funcao()

    def resultado(self, codigo: int) -> ResultadoEtapa:
        return ResultadoEtapa(codigo=codigo, arquivos=list(self.arquivos), resumo=self.resumo)

    def registrar(self, nome: str, auditoria: pd.DataFrame, pastas_raw: Iterable[Path]) -> List[str]:
        """Resumo do conjunto e lista dos arquivos com falha (não obtidos ou não lidos)."""
        self.resumo["conjuntos"][nome] = resumo_conjunto(auditoria, pastas_raw, self.inicio_execucao, self.sem_portal)
        falhas = _com_falha(auditoria)
        if falhas:
            logger.error("Coleta interrompida no conjunto '%s': arquivos não obtidos ou não lidos: %s", nome, falhas)
        return falhas


def _coletar_evt(c: _Coleta) -> Optional[ResultadoEtapa]:
    ident = c.perfil.identificacao
    falhas = c.sincronizar("Energia Vertida Turbinável", lambda: sincronizar_evt(c.raw, c.forcar)) or []
    registros, audits = filter_all_raw_files(c.raw, ident.cod_usina, ident.nome_ons)
    manifesto = load_manifest(c.raw / caminhos.RAW_MANIFEST_FILE.name)
    for a in audits:
        a.data_publicacao = str((manifesto.get(a.nome_arquivo) or {}).get("ultima_modificacao") or "")
    for f in falhas:
        audits.append(AuditoriaArquivo(nome_arquivo=f["arquivo"], periodo_referencia=Path(f["arquivo"]).stem,
                                       status_processamento="FALHA", obtido=False, mensagem=f["mensagem"]))
    consolidados = consolidate_records(registros)
    destino_evt, destino_auditoria = c.pasta / ARQ["evt"], c.pasta / ARQ["auditoria_evt"]
    save_consolidated_records(consolidados, destino_evt)
    save_audit_report(audits, destino_auditoria)
    c.arquivos += [destino_evt, destino_auditoria]
    if c.registrar("energia-vertida-turbinavel", auditoria_evt_normalizada(audits), [c.raw]):
        return c.resultado(CODIGO_DADO_NAO_OBTIDO)
    if not consolidados:
        logger.error("A usina (cod_usina %s, %s) não foi encontrada na Energia Vertida Turbinável; os demais conjuntos "
                     "não são coletados.", ident.cod_usina, ident.nome_ons)
        return c.resultado(CODIGO_DADO_NAO_OBTIDO)
    instantes = pd.to_datetime([r.din_instante for r in consolidados])
    c.inicio, c.fim = instantes.min(), instantes.max()
    c.resumo["periodo"] = {"inicio": c.inicio.strftime(FORMATO_DATA), "fim": c.fim.strftime(FORMATO_DATA)}
    logger.info("Período da base de EVT: %s a %s (%d registros).", c.inicio, c.fim, len(consolidados))
    return None


def _coletar_indicadores(c: _Coleta) -> Optional[ResultadoEtapa]:
    ident = c.perfil.identificacao
    raiz = c.raw / PASTA_INDICADORES_RAW
    falhas = c.sincronizar("indicadores e taxas", lambda: indicadores.sincronizar_indicadores(
        c.inicio.year, c.fim.year, raiz, c.forcar)) or []
    extraido, auditoria = indicadores.extrair_indicadores(raiz, c.inicio, c.fim, ident.ceg, ident.id_ons, falhas)
    c.gravar_parquet(extraido, "indicadores")
    c.gravar_csv(auditoria, "auditoria_indicadores")
    if c.registrar("indicadores", auditoria, [raiz / conjunto for conjunto in CONJUNTOS_INDICADORES_ONS]):
        return c.resultado(CODIGO_DADO_NAO_OBTIDO)
    return None


def _coletar_programacao(c: _Coleta) -> Optional[ResultadoEtapa]:
    ident, estado = c.perfil.identificacao, c.perfil.usina.estado
    pasta = c.raw / PASTA_PROGRAMACAO_RAW
    falhas = c.sincronizar("Programação diária", lambda: programacao.sincronizar_programacao(
        c.inicio, c.fim, pasta, c.forcar)) or []
    extraido, auditoria = programacao.extrair_programacao(pasta, c.inicio, c.fim, ident.cod_programacao,
                                                          ident.nome_ons, estado, falhas)
    c.gravar_parquet(extraido, "programacao")
    c.gravar_csv(auditoria, "auditoria_programacao", date_format=FORMATO_DATA)
    if c.registrar("programacao_diaria", auditoria.rename(columns={
            "linhas_codigo_sem_conferencia": "linhas_so_identificador"}), [pasta]):
        return c.resultado(CODIGO_DADO_NAO_OBTIDO)
    return None


def _coletar_horario(c: _Coleta, nome: str) -> Optional[ResultadoEtapa]:
    desc = conjuntos.descricoes(c.perfil)[nome]
    pasta = c.raw / desc.pasta
    falhas = c.sincronizar(desc.pacote, lambda: conjuntos.sincronizar_conjunto(desc, c.inicio, c.fim, pasta,
                                                                                c.forcar)) or []
    extraido, auditoria = conjuntos.extrair_conjunto(desc, pasta, c.inicio, c.fim, falhas)
    c.gravar_parquet(extraido, nome)
    c.gravar_csv(auditoria, f"auditoria_{nome}")
    if c.registrar(desc.pacote, auditoria, [pasta]):
        return c.resultado(CODIGO_DADO_NAO_OBTIDO)
    return None


def _coletar_cadastro(c: _Coleta) -> Optional[ResultadoEtapa]:
    ident, estado = c.perfil.identificacao, c.perfil.usina.estado
    pasta = c.raw / PASTA_CADASTRO_RAW
    nome, falhas = c.sincronizar("Modalidade das usinas", lambda: cadastro.sincronizar_cadastro(pasta, c.forcar)) \
        or (None, [])
    ficha, auditoria = cadastro.extrair_cadastro(pasta, ident.ceg, ident.id_ons, estado, ident.nome_ons, nome, falhas)
    c.gravar_csv(ficha, "cadastro_ficha")
    c.gravar_csv(auditoria, "auditoria_cadastro")
    if c.registrar("modalidade-usina", auditoria, [pasta]) or ficha.empty:
        if ficha.empty:
            logger.error("Coleta interrompida: a usina (CEG %s) não tem ficha no cadastro do ONS.", ident.ceg)
        return c.resultado(CODIGO_DADO_NAO_OBTIDO)
    return None


def _coletar_dicionarios(c: _Coleta) -> None:
    """Dicionários dos dez conjuntos (só com o portal) e o registro, montado a partir dos manifestos locais."""
    if not c.sem_portal:
        try:
            sincronizar_dicionarios(list(CONJUNTOS_PIPELINE), c.raw)
        except Exception as exc:  # FR-033: falha nos dicionários não interrompe a coleta nem muda o código
            logger.warning("Dicionários de dados não obtidos (%s); a coleta continua.", exc)
    registro = exportar_registro(c.raw, c.pasta, NOME_REGISTRO)
    c.arquivos.append(c.pasta / NOME_REGISTRO)
    c.resumo["dicionarios"] = {str(k): int(v) for k, v in
                               registro["resultado_ultima_obtencao"].value_counts().sort_index().items()}


def executar_coleta(perfil: Any, sem_portal: bool = False, forcar_download: bool = False) -> ResultadoEtapa:
    """Coleta os dez conjuntos para a usina do perfil e grava ``data/usinas/<slug>/coleta/``.

    Códigos: 0 (sucesso), 2 (arquivo não obtido ou não lido, ou usina sem registro na EVT ou no cadastro); o erro
    (código 1, inclusive o catálogo inacessível) é tratado por ``src.pipeline``.
    """
    c = _Coleta(perfil, sem_portal, forcar_download)
    c.pasta.mkdir(parents=True, exist_ok=True)
    if sem_portal:
        logger.info("Coleta sem consulta ao portal (--sem-portal): só os arquivos locais de %s.", c.raw)
    etapas: List[Callable[[_Coleta], Optional[ResultadoEtapa]]] = [
        _coletar_evt,
        _coletar_indicadores,
        _coletar_programacao,
        lambda x: _coletar_horario(x, "disponibilidade"),
        lambda x: _coletar_horario(x, "hidrologia"),
        lambda x: _coletar_horario(x, "geracao"),
        _coletar_cadastro,
    ]
    for etapa in etapas:
        interrompida = etapa(c)
        if interrompida is not None:
            _coletar_dicionarios(c)  # a consulta ao portal obtém os dicionários mesmo com a coleta interrompida
            return c.resultado(interrompida.codigo)
    _coletar_dicionarios(c)
    return c.resultado(CODIGO_SUCESSO)
