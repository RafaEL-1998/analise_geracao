"""Conferência: compara entre si as bases do ONS que trazem a mesma grandeza e refaz os indicadores recalculáveis.

Lê os dados tratados (e a ficha do cadastro, que vem da Coleta) e grava ``data/usinas/<slug>/conferencia/``: os seis
resultados em ``conferencias.pkl`` e um CSV por conferência, sem cópia ``.bak``. Termina com o código 3 quando as
vazões não atingem a meta de alinhamento (spec da Conferência).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from src.comum import caminhos
from src.comum.logger import setup_logger
from src.comum.persistencia import gravar_csv, registrar_gravacoes
from src.conferencia.cadastro import conferencia_cadastro
from src.conferencia.disponibilidade import conferencia_disponibilidade
from src.conferencia.geracao import conferencia_geracao
from src.conferencia.indicadores import conferencia_dispf_horas, conferencia_teifa_teip
from src.conferencia.resultado import ResultadoConferencia, salvar_conferencias
from src.conferencia.vazoes import conferencia_vazoes
from src.pipeline import CODIGO_META_HIDROLOGIA, CODIGO_SUCESSO, ResultadoEtapa
from src.tratamento.disponibilidade import carregar_disponibilidade_tratada
from src.tratamento.geracao import carregar_geracao_tratada
from src.tratamento.hidrologia import carregar_hidrologia_tratada
from src.tratamento.indicadores import carregar_indicadores_tratados

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
}


def carregar_ficha_cadastro(pasta_coleta: Path) -> pd.DataFrame:
    """Ficha do cadastro gravada pela Coleta (vazia se a usina não tem ficha)."""
    caminho = Path(pasta_coleta) / caminhos.ARQUIVOS_COLETA["cadastro_ficha"]
    try:
        return pd.read_csv(caminho, sep=";", keep_default_na=False)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()


def conferir(perfil: Any) -> Dict[str, ResultadoConferencia]:
    """Os seis resultados de conferência da usina, a partir dos dados tratados e da ficha do cadastro."""
    slug = perfil.usina.slug
    tratamento = caminhos.pasta_etapa(slug, "tratamento")
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
    """Executa as seis conferências e grava os resultados (código 0, ou 3 com a meta das vazões não atingida)."""
    pasta = caminhos.pasta_etapa(perfil.usina.slug, "conferencia")
    pasta.mkdir(parents=True, exist_ok=True)
    resultados = conferir(perfil)
    with registrar_gravacoes() as gravacoes:
        salvar_conferencias(resultados, pasta / caminhos.ARQUIVOS_CONFERENCIA["resultados"])
        for id_conferencia, saidas in CSV_CONFERENCIA.items():
            r = resultados[id_conferencia]
            for chave, tabela in saidas:
                destino = pasta / caminhos.ARQUIVOS_CONFERENCIA[chave]
                if tabela in r.tabelas:
                    gravar_csv(_tabela(r.tabelas[tabela]), destino, copia=False)
                elif destino.exists():
                    destino.unlink()  # resultado de uma execução anterior em que a conferência era aplicável
    vazoes = resultados["vazoes"]
    codigo = CODIGO_SUCESSO
    if vazoes.aplicavel and not vazoes.meta_atingida:
        pct = 100.0 * vazoes.coincidentes / vazoes.comparados if vazoes.comparados else 0.0
        logger.error("Alinhamento das vazões abaixo da meta: %.2f%% de %d horas comuns (meta %.0f%%); os cruzamentos "
                     "hidrológicos não serão publicados.", pct, vazoes.comparados, vazoes.meta)
        codigo = CODIGO_META_HIDROLOGIA
    resumo = {id_conferencia: r.resumo() for id_conferencia, r in resultados.items()}
    return ResultadoEtapa(codigo=codigo, arquivos=[p for p, _ in gravacoes], resumo=resumo)
