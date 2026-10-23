"""Conferência: compara entre si as bases do ONS que trazem a mesma grandeza e refaz os indicadores recalculáveis.

Lê os dados tratados (e a ficha do cadastro, que vem da Coleta) e grava ``data/usinas/<slug>/conferencia/``: os seis
resultados em ``conferencias.pkl`` e um CSV por conferência, sem cópia ``.bak``. Termina com o código 3 quando as
vazões não atingem a meta de alinhamento (spec da Conferência).

Para todas as usinas, ``nao_aplicaveis.csv`` lista as conferências do catálogo que não se aplicam, com o motivo
(decisões D11 e D12). Nas hidrelétricas com EVT, as seis de hoje continuam todas em ``conferencias.pkl``; nas
usinas sem EVT, só as aplicadas, inclusive a G3 e a G4 das térmicas com o despacho (FR-020 e FR-021) e a G1, a G2
e a G5 das eólicas e solares (FR-023 a FR-025).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.coleta import registro
from src.coleta.serie_referencia import escolher
from src.comum import caminhos
from src.comum.logger import setup_logger
from src.comum.persistencia import gravar_csv, registrar_gravacoes
from src.conferencia.aplicabilidade import aplicaveis, tabela_nao_aplicaveis
from src.conferencia.cadastro import conferencia_cadastro
from src.conferencia.disponibilidade import conferencia_disponibilidade
from src.conferencia.fontes import (
    conferencia_geracao_fontes,
    conferencia_programacao_despacho,
    conferencia_programacao_renovaveis,
    conferencia_soma_conjunto,
    conferencia_verificada_despacho,
    soma_do_conjunto,
)
from src.conferencia.geracao import conferencia_geracao
from src.conferencia.indicadores import conferencia_dispf_horas, conferencia_teifa_teip
from src.conferencia.resultado import ResultadoConferencia, salvar_conferencias
from src.conferencia.vazoes import conferencia_alinhamento_hidrologia, conferencia_vazoes
from src.pipeline import CODIGO_META_HIDROLOGIA, CODIGO_SUCESSO, ResultadoEtapa
from src.tratamento.base_horaria import carregar_base_horaria
from src.tratamento.disponibilidade import carregar_disponibilidade_tratada
from src.tratamento.geracao import carregar_geracao_tratada
from src.tratamento.hidrologia import carregar_hidrologia_tratada
from src.tratamento.indicadores import carregar_indicadores_tratados
from src.tratamento.programacao import carregar_programacao_tratada
from src.tratamento.renovavel import carregar_renovavel, em_hora_cheia
from src.tratamento.termica import carregar_despacho_tratado

logger = setup_logger("conferencia")

COLUNAS_EVT = ["din_instante", "val_geracao", "val_disponibilidade", "val_vazaoturbinada", "val_vazaovertida"]

# CSV de cada conferência: (chave do arquivo, tabela do resultado)
CSV_CONFERENCIA: Dict[str, List[tuple]] = {
    "geracao": [("geracao", "mensal"), ("geracao_divergencias", "divergencias")],
    "disponibilidade": [("disponibilidade", "resumo"), ("disponibilidade_divergencias", "divergencias")],
    "vazoes": [("vazoes", "alinhamento")],
    "dispf_horas": [("dispf_horas", "divergencias")],
    "teifa_teip": [("teifa_teip", "recalculo")],
    "cadastro": [("cadastro", "campos")],
    "programacao_despacho": [("programacao_despacho", "mensal")],
    "verificada_despacho": [("verificada_despacho", "mensal")],
    "geracao_fontes": [("geracao_fontes", "mensal")],
    "soma_conjunto": [("soma_conjunto", "mensal")],
    "programacao_renovaveis": [("programacao_renovaveis", "mensal")],
    "alinhamento_hidrologia": [("alinhamento_hidrologia", "deslocamentos")],
}


def carregar_ficha_cadastro(pasta_coleta: Path) -> pd.DataFrame:
    """Ficha do cadastro gravada pela Coleta (vazia se a usina não tem ficha)."""
    caminho = Path(pasta_coleta) / caminhos.ARQUIVOS_COLETA["cadastro_ficha"]
    try:
        return pd.read_csv(caminho, sep=";", keep_default_na=False)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()


def _com_evt(perfil: Any) -> bool:
    return escolher(perfil).conjunto == "evt"


def fontes_da_geracao(perfil: Any, tratamento: Path) -> Dict[str, Optional[pd.DataFrame]]:
    """A geração da usina em cada fonte, em hora cheia, com o nível de cada hora (G1 e G2; FR-023 e FR-024): a
    Geração por usina (da base horária, quando é a série de referência), o Fator de capacidade e as duas restrições."""
    renovavel = carregar_renovavel(tratamento)
    fontes: Dict[str, Optional[pd.DataFrame]] = {}
    if escolher(perfil).conjunto == "geracao":
        base = carregar_base_horaria(tratamento)
        if base is not None:
            fontes["geracao"] = base[["din_instante", "geracao_mw", "nivel"]].rename(columns={"geracao_mw": "valor"})
    else:
        geracao = carregar_geracao_tratada(tratamento)
        if geracao is not None and len(geracao.horaria):
            fontes["geracao"] = pd.DataFrame({"din_instante": pd.to_datetime(geracao.horaria["din_instante"]),
                                              "valor": geracao.horaria["val_geracao"],
                                              "nivel": registro.nivel_coletado(perfil, "geracao")})
    fc = renovavel["fator_capacidade_horario"]
    if fc is not None and len(fc):
        fontes["fator_capacidade"] = fc[["din_instante", "val_geracaoverificada", "nivel"]].rename(
            columns={"val_geracaoverificada": "valor"})
    detalhe = renovavel["restricao_horaria"]
    if detalhe is not None and len(detalhe):
        fontes["restricao_detalhe"] = pd.DataFrame({"din_instante": detalhe["din_instante"],
                                                    "valor": detalhe["val_geracaoverificada"], "nivel": "usina"})
    razao = renovavel["restricao_razao_semi_horaria"]
    if razao is not None and len(razao):
        horaria = em_hora_cheia(razao, ["val_geracao"], completa="val_geracao")
        fontes["restricao_razao"] = pd.DataFrame({"din_instante": horaria["din_instante"],
                                                  "valor": horaria["val_geracao"], "nivel": razao["nivel"].iloc[0]})
    return fontes


def _soma_conjunto(perfil: Any, tratamento: Path) -> ResultadoConferencia:
    """G2 com as tabelas tratadas: a restrição com detalhe da usina e dos membros × a geração do conjunto."""
    renovavel = carregar_renovavel(tratamento)
    soma, incompletas = soma_do_conjunto(renovavel["restricao_horaria"], perfil.identificacao.id_ons,
                                         renovavel["restricao_membros_horaria"], perfil.identificacao.membros)
    geracao = fontes_da_geracao(perfil, tratamento).get("geracao")
    conjunto = None
    if geracao is not None:
        conjunto = geracao[geracao["nivel"] == "conjunto"].rename(columns={"valor": "valor_b"})
    return conferencia_soma_conjunto(soma, incompletas, conjunto)


def conferir(perfil: Any) -> Dict[str, ResultadoConferencia]:
    """Resultados de conferência da usina, a partir dos dados tratados e da ficha do cadastro: nas hidrelétricas com
    EVT, os seis de hoje; nas demais, só as conferências aplicáveis (decisão D12)."""
    slug = perfil.usina.slug
    tratamento = caminhos.pasta_etapa(slug, "tratamento")
    if _com_evt(perfil):
        evt = pd.read_parquet(tratamento / caminhos.ARQUIVOS_TRATAMENTO["evt_parquet"], columns=COLUNAS_EVT)
        indicadores = carregar_indicadores_tratados(tratamento)
        resultados = [
            conferencia_geracao(carregar_geracao_tratada(tratamento), evt),
            conferencia_disponibilidade(carregar_disponibilidade_tratada(tratamento), evt),
            conferencia_vazoes(carregar_hidrologia_tratada(tratamento), evt),
            conferencia_dispf_horas(indicadores),
            conferencia_teifa_teip(indicadores),
            conferencia_cadastro(carregar_ficha_cadastro(caminhos.pasta_etapa(slug, "coleta")), perfil),
        ]
    else:
        ids = aplicaveis(perfil)
        indicadores = carregar_indicadores_tratados(tratamento) if {"dispf_horas", "teifa_teip"} & set(ids) else None
        executores = {
            "dispf_horas": lambda: conferencia_dispf_horas(indicadores),
            "teifa_teip": lambda: conferencia_teifa_teip(indicadores),
            "cadastro": lambda: conferencia_cadastro(carregar_ficha_cadastro(caminhos.pasta_etapa(slug, "coleta")),
                                                     perfil),
            "programacao_despacho": lambda: conferencia_programacao_despacho(
                carregar_programacao_tratada(tratamento), carregar_despacho_tratado(tratamento)),
            "verificada_despacho": lambda: conferencia_verificada_despacho(
                carregar_base_horaria(tratamento), carregar_despacho_tratado(tratamento)),
            "geracao_fontes": lambda: conferencia_geracao_fontes(fontes_da_geracao(perfil, tratamento)),
            "soma_conjunto": lambda: _soma_conjunto(perfil, tratamento),
            "programacao_renovaveis": lambda: conferencia_programacao_renovaveis(
                carregar_programacao_tratada(tratamento), carregar_renovavel(tratamento)["fator_capacidade_horario"]),
            "alinhamento_hidrologia": lambda: conferencia_alinhamento_hidrologia(
                carregar_hidrologia_tratada(tratamento), carregar_base_horaria(tratamento)),
        }
        resultados = [executores[i]() for i in ids if i in executores]
    for r in resultados:
        if not r.aplicavel:
            logger.warning("Conferência '%s' não aplicável: %s.", r.id, r.motivo)
        else:
            logger.info("Conferência '%s': %d de %d %s coincidentes; %d divergentes.", r.id, r.coincidentes,
                        r.comparados, r.unidade, r.divergentes)
    return {r.id: r for r in resultados}


def _tabela(valor: Any) -> pd.DataFrame:
    return pd.DataFrame([valor]) if isinstance(valor, dict) else valor


def executar_conferencia(perfil: Any) -> ResultadoEtapa:
    """Executa as conferências e grava os resultados (código 0, ou 3 com a meta das vazões não atingida)."""
    pasta = caminhos.pasta_etapa(perfil.usina.slug, "conferencia")
    pasta.mkdir(parents=True, exist_ok=True)
    conferidos = conferir(perfil)
    nao_aplicaveis = tabela_nao_aplicaveis(perfil, conferidos)
    # Nas usinas sem EVT, as não aplicáveis ficam só no arquivo (data-model da Conferência, seção 2.12)
    resultados = conferidos if _com_evt(perfil) else {i: r for i, r in conferidos.items() if r.aplicavel}
    with registrar_gravacoes() as gravacoes:
        salvar_conferencias(resultados, pasta / caminhos.ARQUIVOS_CONFERENCIA["resultados"])
        for id_conferencia, saidas in CSV_CONFERENCIA.items():
            r = resultados.get(id_conferencia)
            for chave, tabela in saidas:
                destino = pasta / caminhos.ARQUIVOS_CONFERENCIA[chave]
                if r is not None and tabela in r.tabelas:
                    gravar_csv(_tabela(r.tabelas[tabela]), destino, copia=False)
                elif destino.exists():
                    destino.unlink()  # resultado de uma execução anterior em que a conferência era aplicável
        gravar_csv(nao_aplicaveis, pasta / caminhos.ARQUIVOS_CONFERENCIA["nao_aplicaveis"], copia=False)
    vazoes = resultados.get("vazoes")
    codigo = CODIGO_SUCESSO
    if vazoes is not None and vazoes.aplicavel and not vazoes.meta_atingida:
        pct = 100.0 * vazoes.coincidentes / vazoes.comparados if vazoes.comparados else 0.0
        logger.error("Alinhamento das vazões abaixo da meta: %.2f%% de %d horas comuns (meta %.0f%%); os cruzamentos "
                     "hidrológicos não serão publicados.", pct, vazoes.comparados, vazoes.meta)
        codigo = CODIGO_META_HIDROLOGIA
    resumo: Dict[str, Any] = {id_conferencia: r.resumo() for id_conferencia, r in resultados.items()}
    resumo["nao_aplicaveis"] = list(nao_aplicaveis["conferencia"])
    return ResultadoEtapa(codigo=codigo, arquivos=[p for p, _ in gravacoes], resumo=resumo)
