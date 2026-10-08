"""Regras gerais do projeto: limiares, tolerâncias, metas, conjuntos do ONS e padrões das figuras.

São as mesmas para qualquer usina; o perfil da usina não as altera (constituição, princípio III). Os valores próprios de
uma usina ficam no perfil dela (``usinas/<slug>/perfil.toml``, lido por ``src.comum.perfil``). Este módulo não importa
nada do projeto, para poder ser usado por qualquer etapa.
"""

from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Classificação das horas e eventos
# ---------------------------------------------------------------------------

LIMIAR_GERACAO_PARADA_MW: float = 1.0  # usina parada: geração ≤ 1 MW (também a "programação zero")
LIMIAR_SINCRONIZADA_MW: float = 1.0  # alguma unidade sincronizada: disponibilidade sincronizada > 1 MW
LIMIAR_DESVIO_PROGRAMACAO_MW: float = 5.0  # desvio: usina parada com programação > 5 MW
LIMIAR_INDISPONIBILIDADE_TOTAL_MW: float = 0.001  # indisponibilidade total: disponibilidade ≤ 0,001 MW
FRACAO_PLENA_CARGA: float = 0.90  # plena carga: geração ≥ 90 % da potência instalada
DURACAO_MINIMA_EVENTO_RELATORIO_H: int = 24  # indisponibilidade total listada no relatório
NUMERO_EVENTOS_RELATORIO: int = 15  # eventos listados nas tabelas do relatório (a lista completa vai para a planilha)
HORAS_DIURNAS: List[int] = list(range(9, 16))  # 09h às 15h
HORAS_NOTURNAS: List[int] = [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]  # 20h às 05h
RAZAO_DIURNA_RELEVANTE: float = 2.0  # concentração diurna da EVT: razão diurna/noturna ≥ 2

# ---------------------------------------------------------------------------
# Tolerâncias e metas
# ---------------------------------------------------------------------------

TOLERANCIA_DIVERGENCIA_HORAS: float = 1.0  # DISPF × horas por estado operativo
TOLERANCIA_COINCIDENCIA_MW: float = 0.01  # coincidência entre fontes (arredondamento publicado)
TOLERANCIA_COINCIDENCIA_VAZAO_M3S: float = 0.5
TOLERANCIA_REPRODUCAO_TAXAS_PP: float = 0.001  # TEIFa e TEIP recalculadas × publicadas, em p.p.
JANELA_TAXAS_MESES: int = 60  # janela móvel da TEIFa e da TEIP publicada pelo ONS
META_ALINHAMENTO_HIDROLOGIA_PCT: float = 99.0  # coincidência mínima das vazões turbinada e vertida
TOLERANCIA_QUALIDADE_DISPONIBILIDADE_MW: float = 0.01  # regras D1 e D2 da disponibilidade
DESVIO_MAXIMO_NIVEL_M: float = 10.0  # regra H4: nível muito afastado da mediana da série
PHYSICAL_TOLERANCE_EPSILON: float = 1e-4  # identidades do ONS (regras R2 a R5)
TOLERANCIA_LIMITES_FISICOS: float = 0.05  # folga sobre os valores nominais (regra R6)
FAIXA_PRODUTIVIDADE_RELATIVA: Tuple[float, float] = (0.70, 1.30)  # regra R8, relativa à produtividade nominal
TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW: float = 1.0  # regra R7
TOLERANCIA_POTENCIA_PERFIL_MW: float = 0.1  # perfil: potência unitária × unidades = potência instalada
TOLERANCIA_POTENCIA_CADASTRO_MW: float = 0.001  # conferência do cadastro: potência autorizada × perfil
TOLERANCIA_IDENTIDADE_HORAS: float = 0.1  # horas por estado operativo: HP = soma das parcelas

# ---------------------------------------------------------------------------
# Conjuntos do ONS e leitura
# ---------------------------------------------------------------------------

ONS_CKAN_PACKAGE_URL: str = "https://dados.ons.org.br/api/3/action/package_show?id=energia-vertida-turbinavel"
ONS_DATASET_URL: str = "https://dados.ons.org.br/dataset/energia-vertida-turbinavel"
ONS_CKAN_PACKAGE_SHOW_URL: str = "https://dados.ons.org.br/api/3/action/package_show?id="
ONS_PORTAL_DATASET_URL: str = "https://dados.ons.org.br/dataset/"

CONJUNTO_EVT: str = "energia-vertida-turbinavel"
CONJUNTO_PROGRAMACAO_DIARIA: str = "programacao_diaria"
CONJUNTO_DISPONIBILIDADE: str = "disponibilidade_usina"
CONJUNTO_HIDROLOGIA: str = "dados_hidrologicos_ho"
CONJUNTO_GERACAO: str = "geracao-usina-2"
CONJUNTO_CADASTRO: str = "modalidade-usina"
CONJUNTOS_INDICADORES_ONS: Dict[str, str] = {
    "ind_disponibilidade_fgeracao_uge_mensal": "Indicadores de disponibilidade da função geração por unidade geradora (base mensal)",
    "ind_disponibilidade_fgeracao_uge_anual": "Indicadores de disponibilidade da função geração por unidade geradora (base anual)",
    "taxa_teif_teip_parametro": "Parâmetros (horas por estado operativo) das taxas TEIFa e TEIP",
    "taxa_teif_teip": "Taxas TEIFa e TEIP (janela de 60 meses, versão mais recente)",
}

# Pasta de cada conjunto dentro de data/raw/ (a EVT fica na própria raiz)
PASTA_INDICADORES_RAW: str = "indicadores_ons"
PASTA_PROGRAMACAO_RAW: str = "programacao_diaria"
PASTA_DISPONIBILIDADE_RAW: str = "disponibilidade_usina"
PASTA_HIDROLOGIA_RAW: str = "dados_hidrologicos_ho"
PASTA_GERACAO_RAW: str = "geracao_usina_2"
PASTA_CADASTRO_RAW: str = "modalidade_usina"
CONJUNTOS_PIPELINE: Dict[str, str] = {
    CONJUNTO_EVT: "",
    **{conjunto: f"{PASTA_INDICADORES_RAW}/{conjunto}" for conjunto in CONJUNTOS_INDICADORES_ONS},
    CONJUNTO_PROGRAMACAO_DIARIA: PASTA_PROGRAMACAO_RAW,
    CONJUNTO_DISPONIBILIDADE: PASTA_DISPONIBILIDADE_RAW,
    CONJUNTO_HIDROLOGIA: PASTA_HIDROLOGIA_RAW,
    CONJUNTO_GERACAO: PASTA_GERACAO_RAW,
    CONJUNTO_CADASTRO: PASTA_CADASTRO_RAW,
}
DIRETORIO_DICIONARIOS: str = "_dicionarios"  # subpasta com os dicionários de dados de cada conjunto

FORMATO_PROGRAMACAO_DIARIA: str = "PARQUET"
PATAMARES_POR_DIA: int = 48

# As 10 grandezas contínuas da base de EVT
OPERATIONAL_METRIC_COLUMNS: List[str] = [
    "val_geracao",
    "val_disponibilidade",
    "val_vazaoturbinada",
    "val_vazaovertida",
    "val_vazaovertidanaoturbinavel",
    "val_produtividade",
    "val_folgadegeracao",
    "val_energiavertida",
    "val_vazaovertidaturbinavel",
    "val_energiavertidaturbinavel",
]

# Download: buffer de 1 MB, limite por tentativa (s), tentativas e fator de espera entre elas
DOWNLOAD_CHUNK_SIZE: int = 1024 * 1024
REQUEST_TIMEOUT: int = 60
MAX_DOWNLOAD_RETRIES: int = 3
RETRY_BACKOFF_FACTOR: float = 2.0

# Versões anteriores de cada arquivo bruto republicado (dados e dicionários): ficam as mais recentes
MAXIMO_VERSOES_ANTERIORES: int = 2

# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------

DEFAULT_PLOT_DPI: int = 300
TAMANHO_FIGURA_PADRONIZADA: Tuple[float, float] = (11, 4.3)  # figuras 01, 02, 05 e 06, em polegadas

# ---------------------------------------------------------------------------
# Conclusão do relatório: limiares do catálogo de regras C1 a C11
# ---------------------------------------------------------------------------

LIMIAR_CONCLUSAO_EVT_PARADA_PCT: float = 10.0  # C1: EVT com a usina parada, em % da EVT
LIMIAR_CONCLUSAO_PROGRAMACAO_ZERO_PCT: float = 50.0  # C1: horas paradas com EVT e programação até 1 MW
LIMIAR_CONCLUSAO_AFLUENCIA_ENGOLIMENTO_PCT: float = 80.0  # C3: horas com EVT e afluência até o engolimento
LIMIAR_CONCLUSAO_PARTICIPACAO_TEIFA: float = 2.0 / 3.0  # C2: parcela da TEIFa de uma unidade
LIMIAR_CONCLUSAO_MESES_LIMITACAO_PCT: float = 50.0  # C2: meses com limitação forçada de potência (HEDF)
LIMIAR_CONCLUSAO_DIFERENCA_RESERVA_GWH: float = 5.0  # C7: não sincronizada × reserva desligada, por ano
LIMIAR_CONCLUSAO_R7_HORAS: int = 100  # C8: geração acima da disponibilidade declarada
LIMIAR_CONCLUSAO_INDISPONIBILIDADE_DIAS: int = 30  # C10: indisponibilidade total
LIMIAR_CONCLUSAO_PROGRAMADA_UG_PCT: float = 20.0  # C10: indisponibilidade programada de uma unidade num ano
LIMIAR_CONCLUSAO_R9_HORAS: int = 24  # C11: geração com vazão turbinada nula
MAXIMO_ITENS_CONCLUSAO: int = 5  # itens por lista no PDF e no Markdown (a planilha traz todos)
