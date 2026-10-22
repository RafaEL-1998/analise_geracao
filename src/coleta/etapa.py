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

from src.coleta import cadastro, conjuntos, indicadores, programacao, registro, serie_referencia
from src.coleta.catalogo_usinas import CADASTRAIS, CadastralNaoObtido, ler_cadastral, montar_conjuntos, sincronizar_cadastral
from src.coleta.conjuntos import COLUNAS_AUDITORIA_COLETA
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
from src.comum.persistencia import gravar_bytes, gravar_csv, gravar_parquet
from src.comum.regras import (
    CONJUNTO_CADASTRO,
    CONJUNTO_EVT,
    CONJUNTO_PROGRAMACAO_DIARIA,
    CONJUNTOS_INDICADORES_ONS,
    PASTA_CADASTRO_RAW,
    PASTA_INDICADORES_RAW,
    PASTA_PROGRAMACAO_RAW,
)
from src.pipeline import CODIGO_DADO_NAO_OBTIDO, CODIGO_ERRO, CODIGO_SUCESSO, ResultadoEtapa

logger = setup_logger("coleta")

FORMATO_DATA = "%Y-%m-%d %H:%M:%S"
ARQ = caminhos.ARQUIVOS_COLETA
# Datas de obtenção por conjunto, só com os arquivos do escopo da usina (spec 006, decisão R22)
COLUNAS_DATAS_OBTENCAO = ["conjunto", "arquivos_registrados", "publicacao_mais_recente", "obtencao_mais_recente"]
# Unidades geradoras da usina (Capacidade de geração; data-model 6.1), todas as do CEG, com as datas
COLUNAS_CAPACIDADE_FICHA = ["cod_equipamento", "num_unidadegeradora", "nom_unidadegeradora", "val_potenciaefetiva",
                            "nom_combustivel", "dat_entradateste", "dat_entradaoperacao", "dat_desativacao",
                            "nom_agenteproprietario", "nom_agenteoperador"]
# As unidades das usinas da composição do conjunto (fase D), com o CEG e o nome de cada usina
COLUNAS_CAPACIDADE_MEMBROS = ["ceg", "nom_usina", *COLUNAS_CAPACIDADE_FICHA]


def datas_do_escopo(pasta: Path, arquivos: Iterable[str]) -> Dict[str, Any]:
    """Arquivos registrados no manifesto da pasta, publicação e obtenção mais recentes, só dos ``arquivos`` dados."""
    manifesto = load_manifest(Path(pasta) / caminhos.RAW_MANIFEST_FILE.name)
    entradas = [manifesto[nome] for nome in dict.fromkeys(arquivos) if isinstance(manifesto.get(nome), dict)]
    publicacoes = [str(e["ultima_modificacao"]) for e in entradas if e.get("ultima_modificacao")]
    registros = [str(e["registrado_em_utc"]) for e in entradas if e.get("registrado_em_utc")]
    return {"arquivos_registrados": len(entradas), "publicacao_mais_recente": max(publicacoes, default=""),
            "obtencao_mais_recente": max(registros, default="")}


def _obtidos(auditoria: pd.DataFrame) -> List[str]:
    if not len(auditoria):
        return []
    return auditoria.loc[auditoria["obtido"].astype(bool), "arquivo"].astype(str).tolist()


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
        self.datas: Dict[str, Dict[str, Any]] = {}
        # Conjuntos do tipo e da cobertura da usina, na ordem do registro (spec 006, decisão R8; FR-015)
        self.entradas = registro.conjuntos_da_usina(perfil)
        self.pacotes = registro.pacotes(self.entradas, registro.tipo_da_usina(perfil))  # só a variante do tipo
        # Série de referência (decisão R6), complemento horário e composição do conjunto (para os trechos, R7)
        self.escolha: Optional[serie_referencia.Escolha] = None
        self.complemento: Optional[pd.DataFrame] = None
        self.composicao = pd.DataFrame(columns=["id_conjunto", "ceg", "tipo", "inicio", "fim"])
        # Usina em conjunto (fase D): o tipo publicado na série do conjunto, para ``tipo_publicado.csv``
        self.serie_conjunto: Optional[pd.DataFrame] = None

    def recorta_pela_composicao(self) -> bool:
        """A série de referência é a do conjunto: as horas só contam com a usina na composição (rascunho 001,
        FR-054)."""
        return (self.escolha is not None and self.escolha.conjunto == "geracao" and "conjunto" in self.escolha.niveis
                and bool(getattr(self.perfil.identificacao, "id_conjunto", None)))

    def anotar_datas(self, pacote: str, pasta: Path, arquivos: Iterable[str]) -> None:
        """Datas de obtenção do conjunto, só com os arquivos do escopo da usina (``datas_obtencao.csv``)."""
        self.datas[pacote] = datas_do_escopo(pasta, arquivos)

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
    c.anotar_datas(CONJUNTO_EVT, c.raw, [a.nome_arquivo for a in audits if a.obtido])
    if c.registrar("energia-vertida-turbinavel", auditoria_evt_normalizada(audits), [c.raw]):
        return c.resultado(CODIGO_DADO_NAO_OBTIDO)
    if not consolidados:
        logger.error("A usina (cod_usina %s, %s) não foi encontrada na Energia Vertida Turbinável; os demais conjuntos "
                     "não são coletados.", ident.cod_usina, ident.nome_ons)
        return c.resultado(CODIGO_DADO_NAO_OBTIDO)
    instantes = pd.to_datetime([r.din_instante for r in consolidados])
    c.inicio, c.fim = instantes.min(), instantes.max()
    c.resumo["periodo"] = {"inicio": c.inicio.strftime(FORMATO_DATA), "fim": c.fim.strftime(FORMATO_DATA)}
    c.resumo["serie_referencia"] = serie_referencia.resumo(
        c.escolha, c.perfil, c.inicio, c.fim, pd.DataFrame({"arquivo": [a.nome_arquivo for a in audits if a.obtido]}))
    logger.info("Período da base de EVT: %s a %s (%d registros).", c.inicio, c.fim, len(consolidados))
    return None


def _coletar_referencia(c: _Coleta) -> Optional[ResultadoEtapa]:
    """Série de referência das usinas sem EVT (decisões R6 e R7): a Geração por usina, da usina ou do conjunto, ou, nas
    eólicas e solares em conjunto com série própria, a restrição com detalhe da usina (fase C), varrida em todos os
    arquivos publicados; o período vai da primeira à última hora (ou semi-hora) com valor."""
    perfil, escolha = c.perfil, c.escolha
    descricoes = serie_referencia.descricoes_referencia(perfil, escolha)
    primeira = next(iter(descricoes.values()))
    pasta = c.raw / primeira.pasta
    coluna = serie_referencia.COLUNA_VALOR[escolha.conjunto]
    fim_aberto = pd.Timestamp.today().normalize() + pd.DateOffset(years=1)
    falhas: List[Dict[str, Any]] = []
    for nivel, desc in descricoes.items():
        falhas += c.sincronizar(f"{desc.pacote}, série de referência ({nivel})", lambda d=desc: (
            conjuntos.sincronizar_conjunto(d, serie_referencia.INICIO_VARREDURA, fim_aberto, pasta, c.forcar))) or []
    series, auditoria = serie_referencia.extrair_referencia(perfil, escolha, c.raw, falhas)
    auditoria = auditoria.drop(columns=["nivel"], errors="ignore")
    if c.recorta_pela_composicao() and "conjunto" in series:  # fase D: só as horas com a usina na composição
        intervalos = serie_referencia.intervalos_da_usina(c.composicao, perfil.identificacao.ceg)
        if not intervalos:
            logger.error("A usina (CEG %s) não está na Composição dos conjuntos do conjunto %s declarado no perfil; a "
                         "série do conjunto não tem hora da usina e os demais conjuntos não são coletados.",
                         perfil.identificacao.ceg, perfil.identificacao.id_conjunto)
            c.gravar_csv(auditoria, f"auditoria_{escolha.conjunto}")
            c.registrar(primeira.pacote, auditoria, [pasta])
            return c.resultado(CODIGO_DADO_NAO_OBTIDO)
        series["conjunto"] = serie_referencia.no_intervalo(series["conjunto"], intervalos)
        c.resumo["composicao_da_usina"] = [{"inicio": i.strftime(FORMATO_DATA) if i > serie_referencia.INICIO_VARREDURA
                                            else "", "fim": f.strftime(FORMATO_DATA) if f is not None else ""}
                                           for i, f in intervalos]
    inicio, fim = serie_referencia.periodo(series, coluna)
    if "conjunto" in series and len(series["conjunto"]) and inicio is not None:
        conjunto = series["conjunto"]
        instantes = pd.to_datetime(conjunto["din_instante"])
        c.serie_conjunto = conjunto[(instantes >= inicio) & (instantes <= fim)][
            ["din_instante", *[col for col in serie_referencia.COLUNAS_TIPO_PUBLICADO if col in conjunto.columns]]]
    semi_horaria = escolha.conjunto == "restricao_detalhe"
    if semi_horaria:  # a série inteira da restrição com detalhe, no período, com todas as colunas extraídas
        c.gravar_parquet(serie_referencia.recortar(series["usina"], inicio, fim), escolha.conjunto)
    else:
        c.gravar_parquet(serie_referencia.combinar(series, inicio, fim), "geracao")
    c.gravar_csv(auditoria, f"auditoria_{escolha.conjunto}")
    complemento = serie_referencia.complemento(series, coluna, semi_horaria)
    if inicio is not None:
        complemento = complemento[(complemento["din_instante"] >= inicio.floor("h"))
                                  & (complemento["din_instante"] <= fim)]
    c.complemento = complemento.reset_index(drop=True)
    c.gravar_parquet(c.complemento, "geracao_complemento")
    c.anotar_datas(primeira.pacote, pasta, _obtidos(auditoria))
    if c.registrar(primeira.pacote, auditoria, [pasta]):
        return c.resultado(CODIGO_DADO_NAO_OBTIDO)
    if inicio is None:
        logger.error("A série de referência da usina '%s' (%s) não tem nenhuma hora com valor; os demais conjuntos "
                     "não são coletados.", perfil.usina.slug, escolha.motivo)
        return c.resultado(CODIGO_DADO_NAO_OBTIDO)
    c.inicio, c.fim = inicio, fim
    c.resumo["periodo"] = {"inicio": inicio.strftime(FORMATO_DATA), "fim": fim.strftime(FORMATO_DATA)}
    c.resumo["serie_referencia"] = serie_referencia.resumo(escolha, perfil, inicio, fim, auditoria)
    if escolha.conjunto == "geracao" and "usina" not in escolha.niveis and perfil.identificacao.id_ons:
        # linhas próprias sem valor (achado A3)
        proprias, _ = conjuntos.extrair_conjunto(registro.descricao_geracao(perfil, "usina"), pasta, inicio, fim)
        proprias = serie_referencia.recortar(proprias, inicio, fim)  # os arquivos mensais passam do período
        sem_valor = proprias.loc[proprias["val_geracao"].isna(), "din_instante"] if len(proprias) else pd.Series([])
        c.resumo["linhas_usina_sem_valor"] = int(len(sem_valor))
        if len(sem_valor):  # desde quando o ONS publica a linha da usina vazia (fase D; FR-047 e FR-048)
            instantes = pd.to_datetime(sem_valor)
            c.resumo["linhas_usina_sem_valor_periodo"] = {"inicio": instantes.min().strftime(FORMATO_DATA),
                                                          "fim": instantes.max().strftime(FORMATO_DATA)}
    logger.info("Período da série de referência (%s): %s a %s.", escolha.motivo, inicio, fim)
    return None


def _coletar_cadastral(c: _Coleta, chave: str) -> Optional[ResultadoEtapa]:
    """Composição do conjunto ou unidades geradoras da usina (estáticos), com a auditoria da leitura."""
    cadastral, ident = CADASTRAIS[chave], c.perfil.identificacao
    if chave == "composicao" and not getattr(ident, "id_conjunto", None):
        return None  # fora de conjunto, não há composição a coletar
    pasta = c.raw / cadastral.pasta
    linha = {coluna: "" for coluna in COLUNAS_AUDITORIA_COLETA}
    linha.update(formato="", periodo="estatico", obtido=True, linhas_lidas=0, linhas_formato_irregular=0, linhas_usina=0,
                 linhas_so_identificador=0, linhas_so_conferencia=0, valores_invalidos=0, recursos_duplicados_catalogo=0)
    try:
        c.sincronizar(cadastral.pacote, lambda: sincronizar_cadastral(chave, c.raw, c.forcar))
        tabela, arquivo = ler_cadastral(chave, c.raw)
    except CadastralNaoObtido as exc:
        linha.update(status="FALHA", mensagem=exc.motivo, obtido=False)
        auditoria = pd.DataFrame([linha], columns=COLUNAS_AUDITORIA_COLETA)
        c.gravar_csv(auditoria, f"auditoria_{chave}")
        c.registrar(cadastral.pacote, auditoria, [pasta])
        return c.resultado(CODIGO_DADO_NAO_OBTIDO)
    publicacao = str((load_manifest(pasta / caminhos.RAW_MANIFEST_FILE.name).get(arquivo.name) or {})
                     .get("ultima_modificacao") or "")
    estado = registro.normalizar_texto(c.perfil.usina.estado)
    if chave == "composicao":
        alvo = registro.normalizar_texto(ident.id_conjunto)
        identificador = tabela["id_ons_conjunto"].map(registro.normalizar_texto) == alvo
        conferencia = tabela["estad_id"].map(registro.normalizar_texto) == estado
    else:
        identificador = tabela["ceg"].map(registro.normalizar_texto) == registro.normalizar_texto(ident.ceg)
        conferencia = tabela["id_estado"].map(registro.normalizar_texto) == estado
    linha.update(arquivo=arquivo.name, formato=arquivo.suffix[1:].upper(), data_publicacao=publicacao,
                 linhas_lidas=len(tabela), linhas_usina=int((identificador & conferencia).sum()),
                 linhas_so_identificador=int((identificador & ~conferencia).sum()),
                 linhas_so_conferencia=0, status="PROCESSADO" if (identificador & conferencia).any() else "SEM_REGISTROS")
    selecionadas = tabela[identificador & conferencia]
    if chave == "composicao":
        c.composicao = montar_conjuntos(selecionadas)
        c.gravar_csv(c.composicao, "composicao")
    else:
        colunas = [col for col in COLUNAS_CAPACIDADE_FICHA if col in selecionadas.columns]
        c.gravar_csv(selecionadas[colunas].reset_index(drop=True), "capacidade")
        _gravar_capacidade_membros(c, tabela, linha)
    auditoria = pd.DataFrame([linha], columns=COLUNAS_AUDITORIA_COLETA)
    c.gravar_csv(auditoria, f"auditoria_{chave}")
    c.anotar_datas(cadastral.pacote, pasta, [arquivo.name])
    c.registrar(cadastral.pacote, auditoria, [pasta])
    return None


def _gravar_capacidade_membros(c: _Coleta, capacidade: pd.DataFrame, linha_capacidade: Dict[str, Any]) -> None:
    """``capacidade_membros.csv`` da usina em conjunto (fase D; rascunho 001, FR-060): as unidades geradoras de cada
    usina da composição no período, pelo CEG (identificador), conferidas pelo subsistema da linha da usina na
    composição (princípio IV). O estado não confere: o conjunto pode ter usinas cadastradas em outro estado (o Conj.
    Chapadão, de MS, teve duas UTE de GO). As linhas em que só o CEG confere vão para a auditoria
    (``auditoria_capacidade_membros.csv``), sem interrupção."""
    inicio, fim = getattr(c, "inicio", None), getattr(c, "fim", None)
    if not getattr(c.perfil.identificacao, "id_conjunto", None) or c.composicao.empty or inicio is None:
        return
    normalizar = registro.normalizar_texto
    membros = {normalizar(ceg) for ceg in serie_referencia.membros_no_periodo(c.composicao, inicio, fim)}
    subsistema = {normalizar(r["ceg"]): normalizar(r.get("subsistema", "")) for r in c.composicao.to_dict("records")}
    cegs = [normalizar(x) for x in capacidade["ceg"]]
    subsistemas = ([normalizar(x) for x in capacidade["id_subsistema"]] if "id_subsistema" in capacidade.columns
                   else [""] * len(capacidade))
    identificador = pd.Series([ceg in membros for ceg in cegs], index=capacidade.index)
    conferencia = pd.Series([bool(subsistema.get(ceg)) and subsistema.get(ceg) == s for ceg, s in zip(cegs, subsistemas)],
                            index=capacidade.index)
    selecionadas = capacidade[identificador & conferencia]
    colunas = [col for col in COLUNAS_CAPACIDADE_MEMBROS if col in capacidade.columns]
    c.gravar_csv(selecionadas[colunas].reset_index(drop=True), "capacidade_membros")
    com_unidades = len({normalizar(x) for x in selecionadas["ceg"]})
    auditoria = dict(linha_capacidade)
    auditoria.update(linhas_usina=int((identificador & conferencia).sum()),
                     linhas_so_identificador=int((identificador & ~conferencia).sum()), linhas_so_conferencia=0,
                     status="PROCESSADO" if com_unidades else "SEM_REGISTROS",
                     mensagem=f"usinas da composição no período: {len(membros)}; com unidades: {com_unidades}")
    c.gravar_csv(pd.DataFrame([auditoria], columns=COLUNAS_AUDITORIA_COLETA), "auditoria_capacidade_membros")
    if auditoria["linhas_so_identificador"]:
        logger.warning("Capacidade de geração: %d unidades das usinas do conjunto com o CEG e outro subsistema, não "
                       "extraídas; verificar mudança de cadastro no ONS.", auditoria["linhas_so_identificador"])
    c.resumo["capacidade_membros"] = {"usinas": len(membros), "com_unidades": com_unidades,
                                      "linhas_so_identificador": auditoria["linhas_so_identificador"]}


def _gravar_trechos(c: _Coleta) -> None:
    """``trechos.csv`` das usinas sem EVT (decisão R7), com a composição coletada e os códigos do perfil; na usina cuja
    série de referência é a do conjunto, também ``tipo_publicado.csv`` (fase D; rascunho 001, FR-061)."""
    if c.complemento is None:
        return
    ident = c.perfil.identificacao
    tabela = serie_referencia.trechos(c.complemento, c.composicao, getattr(ident, "planejamento", ()) or (),
                                      getattr(ident, "id_conjunto", None) or "")
    c.gravar_csv(tabela, "trechos")
    c.resumo["trechos"] = len(tabela)
    if c.recorta_pela_composicao():
        c.gravar_csv(serie_referencia.tipos_publicados(c.serie_conjunto, tabela), "tipo_publicado")


def _coletar_indicadores(c: _Coleta) -> Optional[ResultadoEtapa]:
    ident = c.perfil.identificacao
    raiz = c.raw / PASTA_INDICADORES_RAW
    falhas = c.sincronizar("indicadores e taxas", lambda: indicadores.sincronizar_indicadores(
        c.inicio.year, c.fim.year, raiz, c.forcar)) or []
    extraido, auditoria = indicadores.extrair_indicadores(raiz, c.inicio, c.fim, ident.ceg, ident.id_ons, falhas)
    c.gravar_parquet(extraido, "indicadores")
    c.gravar_csv(auditoria, "auditoria_indicadores")
    for conjunto in CONJUNTOS_INDICADORES_ONS:
        c.anotar_datas(conjunto, raiz / conjunto, _obtidos(auditoria[auditoria["conjunto"] == conjunto]))
    if c.registrar("indicadores", auditoria, [raiz / conjunto for conjunto in CONJUNTOS_INDICADORES_ONS]):
        return c.resultado(CODIGO_DADO_NAO_OBTIDO)
    return None


def _coletar_programacao(c: _Coleta) -> Optional[ResultadoEtapa]:
    ident, estado = c.perfil.identificacao, c.perfil.usina.estado
    pasta = c.raw / PASTA_PROGRAMACAO_RAW
    falhas = c.sincronizar("Programação diária", lambda: programacao.sincronizar_programacao(
        c.inicio, c.fim, pasta, c.forcar)) or []
    codigos = getattr(ident, "codigos_programacao", None) or ident.cod_programacao
    extraido, auditoria = programacao.extrair_programacao(pasta, c.inicio, c.fim, codigos, ident.nome_ons, estado,
                                                          falhas)
    c.gravar_parquet(extraido, "programacao")
    c.gravar_csv(auditoria, "auditoria_programacao", date_format=FORMATO_DATA)
    c.anotar_datas(CONJUNTO_PROGRAMACAO_DIARIA, pasta, _obtidos(auditoria))
    if c.registrar("programacao_diaria", auditoria.rename(columns={
            "linhas_codigo_sem_conferencia": "linhas_so_identificador"}), [pasta]):
        return c.resultado(CODIGO_DADO_NAO_OBTIDO)
    return None


def _coletar_horario(c: _Coleta, nome: str) -> Optional[ResultadoEtapa]:
    desc = registro.descricoes(c.perfil)[nome]
    pasta = c.raw / desc.pasta
    falhas = c.sincronizar(desc.pacote, lambda: conjuntos.sincronizar_conjunto(desc, c.inicio, c.fim, pasta,
                                                                                c.forcar)) or []
    extraido, auditoria = conjuntos.extrair_conjunto(desc, pasta, c.inicio, c.fim, falhas)
    if nome in ("fator_capacidade", "restricao_razao"):  # da usina ou do conjunto (data-model 6.1)
        extraido = extraido.assign(nivel=desc.nivel)
    c.gravar_parquet(extraido, nome)
    c.gravar_csv(auditoria, f"auditoria_{nome}")
    c.anotar_datas(desc.pacote, pasta, _obtidos(auditoria))
    if c.registrar(desc.pacote, auditoria, [pasta]):
        return c.resultado(CODIGO_DADO_NAO_OBTIDO)
    return None


def _coletar_membros(c: _Coleta) -> None:
    """Restrição com detalhe das outras usinas do conjunto (``[[identificacao.membros]]``), só para a G2 (fase C): pelo
    id ONS e pelo CEG de cada membro, no período, guardadas à parte como contexto identificado (princípio III)."""
    perfil = c.perfil
    proprio = registro.normalizar_texto(perfil.identificacao.id_ons or "")
    outros = [m for m in getattr(perfil.identificacao, "membros", ()) or ()
              if registro.normalizar_texto(m.id_ons) != proprio]
    if not outros or "restricao_detalhe" not in {e.chave for e in c.entradas}:
        return
    partes, auditorias = [], []
    for m in outros:
        desc = registro.descricao_restricao_detalhe(perfil, m.id_ons, m.ceg)
        extraido, auditoria = conjuntos.extrair_conjunto(desc, c.raw / desc.pasta, c.inicio, c.fim)
        partes.append(extraido.assign(id_ons=m.id_ons))
        auditorias.append(auditoria.assign(id_ons=m.id_ons))
    c.gravar_parquet(pd.concat(partes, ignore_index=True), "restricao_membros")
    c.gravar_csv(pd.concat(auditorias, ignore_index=True), "auditoria_restricao_membros")
    c.resumo["membros_restricao"] = {m.id_ons: int(len(p)) for m, p in zip(outros, partes)}


def _coletar_cadastro(c: _Coleta) -> Optional[ResultadoEtapa]:
    ident, estado = c.perfil.identificacao, c.perfil.usina.estado
    pasta = c.raw / PASTA_CADASTRO_RAW
    nome, falhas = c.sincronizar("Modalidade das usinas", lambda: cadastro.sincronizar_cadastro(pasta, c.forcar)) \
        or (None, [])
    # Homônimos pelo nome: o do ONS nas hidrelétricas; nos demais tipos, o nome curto do perfil
    nome_usina = ident.nome_ons or c.perfil.usina.nome_curto
    ficha, auditoria = cadastro.extrair_cadastro(pasta, ident.ceg, ident.id_ons or "", estado, nome_usina, nome, falhas)
    c.gravar_csv(ficha, "cadastro_ficha")
    c.gravar_csv(auditoria, "auditoria_cadastro")
    c.anotar_datas(CONJUNTO_CADASTRO, pasta, _obtidos(auditoria))
    if c.registrar("modalidade-usina", auditoria, [pasta]) or ficha.empty:
        if ficha.empty:
            logger.error("Coleta interrompida: a usina (CEG %s) não tem ficha no cadastro do ONS.", ident.ceg)
        return c.resultado(CODIGO_DADO_NAO_OBTIDO)
    return None


def _coletar_dicionarios(c: _Coleta) -> None:
    """Dicionários dos conjuntos da usina (só com o portal) e o registro, montado a partir dos manifestos locais."""
    if not c.sem_portal:
        try:
            sincronizar_dicionarios(list(c.pacotes), c.raw)
        except Exception as exc:  # FR-033: falha nos dicionários não interrompe a coleta nem muda o código
            logger.warning("Dicionários de dados não obtidos (%s); a coleta continua.", exc)
    tabela = exportar_registro(c.raw, c.pasta, NOME_REGISTRO, c.pacotes)
    c.arquivos.append(c.pasta / NOME_REGISTRO)
    c.resumo["dicionarios"] = {str(k): int(v) for k, v in
                               tabela["resultado_ultima_obtencao"].value_counts().sort_index().items()}


def _gravar_formato_2(c: _Coleta) -> None:
    """Arquivos que as etapas seguintes leem no lugar de ``data/raw/`` (spec 006, decisão R22).

    ``datas_obtencao.csv``: uma linha por conjunto coletado, na ordem do registro. ``dicionario_evt.json``:
    a cópia do dicionário de dados da EVT, quando a usina tem EVT e o dicionário existe em ``data/raw/``.
    """
    ordem = [p for p in registro.CONJUNTOS_PIPELINE if p in c.datas]
    ordem += [p for p in c.datas if p not in registro.CONJUNTOS_PIPELINE]
    tabela = pd.DataFrame([{"conjunto": p, **c.datas[p]} for p in ordem], columns=COLUNAS_DATAS_OBTENCAO)
    c.gravar_csv(tabela, "datas_obtencao")
    origem = caminhos.dicionario_evt()
    if CONJUNTO_EVT in c.datas:
        if origem.is_file():
            destino = c.pasta / ARQ["dicionario_evt"]
            gravar_bytes(origem.read_bytes(), destino)
            c.arquivos.append(destino)
        else:
            logger.warning("Dicionário de dados da EVT ausente em %s; o Tratamento vai recusar a base.", origem)


def _coletar(c: _Coleta, chave: str) -> Optional[ResultadoEtapa]:
    """Coleta de um conjunto do registro (spec 006, decisão R8): o motor comum nos que têm descrição e os módulos
    próprios nos demais."""
    if registro.entrada(chave).descricao is not None:
        return _coletar_horario(c, chave)
    proprios = {"evt": _coletar_evt, "indicadores": _coletar_indicadores, "programacao": _coletar_programacao,
                "cadastro": _coletar_cadastro, "composicao": lambda c: _coletar_cadastral(c, "composicao"),
                "capacidade": lambda c: _coletar_cadastral(c, "capacidade")}
    return proprios[chave](c)


def executar_coleta(perfil: Any, sem_portal: bool = False, forcar_download: bool = False) -> ResultadoEtapa:
    """Coleta os conjuntos do registro da usina do perfil e grava ``data/usinas/<slug>/coleta/``.

    Na UHE sem ``[cobertura]``, os dez conjuntos de hoje. Códigos: 0 (sucesso), 2 (arquivo não obtido ou não lido,
    ou usina sem registro na EVT ou no cadastro), 1 (usina sem a EVT, cuja série de referência ainda não é
    coletada); o erro (código 1, inclusive o catálogo inacessível) é tratado por ``src.pipeline``.
    """
    c = _Coleta(perfil, sem_portal, forcar_download)
    try:
        c.escolha = serie_referencia.escolher(perfil)
    except ValueError as exc:
        logger.error("Coleta recusada: %s.", exc)
        return c.resultado(CODIGO_ERRO)
    tipo, cobertura = registro.tipo_da_usina(perfil), registro.cobertura_da_usina(perfil)
    c.resumo.update(
        tipo=tipo, modalidade=getattr(perfil.usina, "modalidade", "") or "", trechos=0, linhas_usina_sem_valor=0,
        conjuntos_nao_aplicaveis=[k for k in registro.chaves_da_cobertura(tipo) if cobertura
                                  and k not in [e.chave for e in c.entradas]])
    chaves = [e.chave for e in c.entradas]
    c.pasta.mkdir(parents=True, exist_ok=True)
    if sem_portal:
        logger.info("Coleta sem consulta ao portal (--sem-portal): só os arquivos locais de %s.", c.raw)
    etapas: List[Callable[[_Coleta], Optional[ResultadoEtapa]]] = []
    if c.escolha.conjunto != "evt":  # a série de referência vem antes: ela define o período
        if c.recorta_pela_composicao() and "composicao" in chaves:  # fase D: a composição recorta o período
            etapas.append(lambda c: _coletar(c, "composicao"))
            chaves = [k for k in chaves if k != "composicao"]
        etapas.append(_coletar_referencia)
        chaves = [k for k in chaves if k != c.escolha.conjunto]
    etapas += [lambda c, k=k: _coletar(c, k) for k in chaves]
    for etapa in etapas:
        interrompida = etapa(c)
        if interrompida is not None:
            _coletar_dicionarios(c)  # a consulta ao portal obtém os dicionários mesmo com a coleta interrompida
            _gravar_formato_2(c)
            return c.resultado(interrompida.codigo)
    _coletar_membros(c)
    _gravar_trechos(c)
    _coletar_dicionarios(c)
    _gravar_formato_2(c)
    return c.resultado(CODIGO_SUCESSO)
