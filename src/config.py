"""Configurações globais, caminhos e parâmetros técnicos do pipeline ONS - UHE São Domingos."""

from pathlib import Path
from typing import Dict, List, Tuple

# Raiz do projeto
BASE_DIR: Path = Path(__file__).resolve().parent.parent

# Diretórios de dados
DATA_DIR: Path = BASE_DIR / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
PROCESSED_DATA_DIR: Path = DATA_DIR / "processed"

# Diretórios de relatórios e figuras (Feature 003)
REPORTS_DIR: Path = BASE_DIR / "reports"
REPORTS_FIGURES_DIR: Path = REPORTS_DIR / "figures"

# Dicionário de dados oficial ONS
DATA_DICTIONARY_JSON: Path = BASE_DIR / "DicionarioDados_EnergiaVertidaTurbinavel.json"

# Manifesto das versões baixadas (tamanho e last_modified publicados no catálogo CKAN)
RAW_MANIFEST_FILE: Path = RAW_DATA_DIR / "_manifesto_ons.json"

# Arquivos de saída consolidados (Feature 001)
CONSOLIDATED_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_energia_vertida_consolidado.csv"
AUDIT_REPORT_FILE: Path = PROCESSED_DATA_DIR / "relatorio_auditoria_varredura.csv"

# Arquivos de saída tratados multi-formato (Feature 002)
TREATED_FILE_XLSX: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_energia_vertida_tratado.xlsx"
TREATED_FILE_PARQUET: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_energia_vertida_tratado.parquet"
TREATED_FILE_CSV: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_energia_vertida_tratado.csv"
PHYSICAL_AUDIT_REPORT_MD: Path = PROCESSED_DATA_DIR / "relatorio_validacao_fisica.md"
PHYSICAL_AUDIT_REPORT_CSV: Path = PROCESSED_DATA_DIR / "relatorio_validacao_fisica.csv"

# Arquivos de saída analítica e relatórios (Feature 003)
STATISTICAL_REPORT_MD: Path = REPORTS_DIR / "relatorio_analise_estatistica.md"
STATISTICAL_REPORT_XLSX: Path = REPORTS_DIR / "perfil_estatistico_anual.xlsx"
STATISTICAL_REPORT_CSV: Path = REPORTS_DIR / "perfil_estatistico_anual.csv"
PDF_REPORT_PATH: Path = REPORTS_DIR / "relatorio_analise_estatistica.pdf"

# Endpoint oficial da API CKAN do ONS para o dataset de Energia Vertida Turbinável
ONS_CKAN_PACKAGE_URL: str = (
    "https://dados.ons.org.br/api/3/action/package_show?id=energia-vertida-turbinavel"
)
ONS_DATASET_URL: str = "https://dados.ons.org.br/dataset/energia-vertida-turbinavel"

# Identificação da usina nos arquivos do ONS. O cod_usina (código da usina nos modelos de
# otimização) é estável ao longo da série; o nome do agente não é (CGT ELETROSUL até
# fev/2026, AXIA SUL a partir de mar/2026). O nome do reservatório serve de conferência.
COD_USINA_ONS: int = 153
NOME_RESERVATORIO_REFERENCIA: str = "SAO DOMINGOS"

# -------------------------------------------------------------------------
# Indicadores oficiais de disponibilidade por unidade geradora (ONS)
# -------------------------------------------------------------------------

# Nos conjuntos de indicadores a usina é identificada pelo CEG da ANEEL (o cod_usina não
# aparece neles). O id_ons serve de conferência.
CEG_USINA: str = "UHE.PH.MS.028761-0.01"
ID_ONS_USINA: str = "MSUHSD"

# Endpoint CKAN genérico e página dos conjuntos no portal do ONS
ONS_CKAN_PACKAGE_SHOW_URL: str = "https://dados.ons.org.br/api/3/action/package_show?id="
ONS_PORTAL_DATASET_URL: str = "https://dados.ons.org.br/dataset/"

# Conjuntos baixados: identificador no CKAN -> descrição
CONJUNTOS_INDICADORES_ONS: Dict[str, str] = {
    "ind_disponibilidade_fgeracao_uge_mensal": "Indicadores de disponibilidade da função geração por unidade geradora (base mensal)",
    "ind_disponibilidade_fgeracao_uge_anual": "Indicadores de disponibilidade da função geração por unidade geradora (base anual)",
    "taxa_teif_teip_parametro": "Parâmetros (horas por estado operativo) das taxas TEIFa e TEIP",
    "taxa_teif_teip": "Taxas TEIFa e TEIP (janela de 60 meses, versão mais recente)",
}

# Pasta própria (fora de data/raw, que é varrida pelo filtro da base de EVT)
INDICADORES_RAW_DIR: Path = RAW_DATA_DIR / "indicadores_ons"

# Saídas tratadas, recortadas no período da base de EVT
INDICADORES_UG_MENSAL_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_ons_ug_indicadores_mensal.csv"
INDICADORES_UG_ANUAL_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_ons_ug_indicadores_anual.csv"
HORAS_ESTADO_UG_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_ons_ug_horas_estado_mensal.csv"
TAXAS_TEIFA_TEIP_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_ons_teifa_teip_mensal.csv"
DIVERGENCIAS_INDICADORES_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_ons_divergencias_indicadores.csv"
AUDITORIA_INDICADORES_FILE: Path = PROCESSED_DATA_DIR / "relatorio_auditoria_indicadores_ons.csv"
INDICADORES_XLSX_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_indicadores_ons.xlsx"

# Diferença (h) acima da qual as horas de um conjunto e o indicador do outro são tratados como divergentes
TOLERANCIA_DIVERGENCIA_HORAS: float = 1.0

# -------------------------------------------------------------------------
# Programação diária do ONS (spec 004, US1)
# -------------------------------------------------------------------------

# Conjunto "Dados dos Valores da Programação Diária": um arquivo por dia, desde 01/10/2024.
# O ONS publica cada dia em Parquet (~150 KB), CSV (~37 MB) e XLSX; usa-se o Parquet.
CONJUNTO_PROGRAMACAO_DIARIA: str = "programacao_diaria"
FORMATO_PROGRAMACAO_DIARIA: str = "PARQUET"
# Identificação da usina na programação (há homônimos em GO, SC e SP): código, nome e estado
COD_EXIBICAO_USINA_PROGRAMACAO: str = "PRUHSD"
ESTADO_USINA: str = "MS"
PATAMARES_POR_DIA: int = 48

PROGRAMACAO_RAW_DIR: Path = RAW_DATA_DIR / "programacao_diaria"
PROGRAMACAO_HORARIA_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_ons_programacao_horaria.csv"
PROGRAMACAO_DIAS_AUSENTES_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_ons_programacao_dias_ausentes.csv"
AUDITORIA_PROGRAMACAO_FILE: Path = PROCESSED_DATA_DIR / "relatorio_auditoria_programacao_ons.csv"

# Usina parada com programação acima deste valor caracteriza desvio relevante da programação
# (parâmetro de análise; programação "zero" usa o mesmo limiar de usina parada, 1 MW)
LIMIAR_DESVIO_PROGRAMACAO_MW: float = 5.0

# -------------------------------------------------------------------------
# Bases complementares do ONS e dicionários de dados (spec 006)
# -------------------------------------------------------------------------

# Identificadores dos conjuntos no catálogo CKAN do ONS
CONJUNTO_EVT: str = "energia-vertida-turbinavel"
CONJUNTO_DISPONIBILIDADE: str = "disponibilidade_usina"
CONJUNTO_HIDROLOGIA: str = "dados_hidrologicos_ho"
CONJUNTO_GERACAO: str = "geracao-usina-2"
CONJUNTO_CADASTRO: str = "modalidade-usina"

# Pastas brutas próprias (o filtro da EVT lê só os CSV da raiz de data/raw)
DISPONIBILIDADE_RAW_DIR: Path = RAW_DATA_DIR / "disponibilidade_usina"
HIDROLOGIA_RAW_DIR: Path = RAW_DATA_DIR / "dados_hidrologicos_ho"
GERACAO_RAW_DIR: Path = RAW_DATA_DIR / "geracao_usina_2"
CADASTRO_RAW_DIR: Path = RAW_DATA_DIR / "modalidade_usina"

# Subpasta, dentro da pasta bruta de cada conjunto, com os dicionários de dados publicados (PDF e JSON)
DIRETORIO_DICIONARIOS: str = "_dicionarios"

# Os 10 conjuntos do pipeline -> subpasta relativa à raiz dos dados brutos
CONJUNTOS_PIPELINE: Dict[str, str] = {
    CONJUNTO_EVT: "",
    **{conjunto: f"{INDICADORES_RAW_DIR.name}/{conjunto}" for conjunto in CONJUNTOS_INDICADORES_ONS},
    CONJUNTO_PROGRAMACAO_DIARIA: PROGRAMACAO_RAW_DIR.name,
    CONJUNTO_DISPONIBILIDADE: DISPONIBILIDADE_RAW_DIR.name,
    CONJUNTO_HIDROLOGIA: HIDROLOGIA_RAW_DIR.name,
    CONJUNTO_GERACAO: GERACAO_RAW_DIR.name,
    CONJUNTO_CADASTRO: CADASTRO_RAW_DIR.name,
}

# Saídas tratadas das bases novas (data-model da spec 006, seção 9)
DICIONARIOS_REGISTRO_FILE: Path = PROCESSED_DATA_DIR / "relatorio_dicionarios_ons.csv"
DISPONIBILIDADE_HORARIA_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_ons_disponibilidade_horaria.csv"
DISPONIBILIDADE_AUSENCIAS_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_ons_disponibilidade_ausencias.csv"
AUDITORIA_DISPONIBILIDADE_FILE: Path = PROCESSED_DATA_DIR / "relatorio_auditoria_disponibilidade_ons.csv"
HIDROLOGIA_HORARIA_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_ons_hidrologia_horaria.csv"
HIDROLOGIA_AUSENCIAS_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_ons_hidrologia_ausencias.csv"
HIDROLOGIA_ALINHAMENTO_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_ons_hidrologia_alinhamento.csv"
AUDITORIA_HIDROLOGIA_FILE: Path = PROCESSED_DATA_DIR / "relatorio_auditoria_hidrologia_ons.csv"
GERACAO_HORARIA_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_ons_geracao_horaria.csv"
GERACAO_AUSENCIAS_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_ons_geracao_ausencias.csv"
AUDITORIA_GERACAO_FILE: Path = PROCESSED_DATA_DIR / "relatorio_auditoria_geracao_ons.csv"
CADASTRO_FILE: Path = PROCESSED_DATA_DIR / "uhe_sao_domingos_ons_cadastro.csv"
AUDITORIA_CADASTRO_FILE: Path = PROCESSED_DATA_DIR / "relatorio_auditoria_cadastro_ons.csv"

# Identificação da usina nos dados hidrológicos (conferência do cod_usina 153)
ID_RESERVATORIO_ONS: str = "PNUHSD"

# Parâmetros de análise das bases novas (abertos à revisão do usuário)
# Disponibilidade sincronizada acima deste valor indica alguma unidade sincronizada à rede
LIMIAR_SINCRONIZADA_MW: float = 1.0
# Diferença até a qual valores de duas fontes são tratados como coincidentes (arredondamento publicado)
TOLERANCIA_COINCIDENCIA_MW: float = 0.01
TOLERANCIA_COINCIDENCIA_VAZAO_M3S: float = 0.5
# Spec 007: um mês de TEIFa/TEIP conta como reproduzido quando as duas taxas recalculadas diferem das publicadas
# por no máximo este valor (pontos percentuais)
TOLERANCIA_REPRODUCAO_TAXAS_PP: float = 0.001
# Coincidência mínima das vazões turbinada e vertida para confirmar o alinhamento das horas da hidrologia
META_ALINHAMENTO_HIDROLOGIA_PCT: float = 99.0
# Folga das regras de qualidade da disponibilidade (D1 e D2)
TOLERANCIA_QUALIDADE_DISPONIBILIDADE_MW: float = 0.01
# Afastamento máximo (m) da mediana da série para os níveis de montante e de jusante (regra H4 da hidrologia).
# Folgado o bastante para manter o rebaixamento real de ~2 m durante a parada total de 2019.
DESVIO_MAXIMO_NIVEL_M: float = 10.0

# Buffer de streaming para downloads (1 MB)
DOWNLOAD_CHUNK_SIZE: int = 1024 * 1024

# Timeouts e retentativas de rede
REQUEST_TIMEOUT: int = 60
MAX_DOWNLOAD_RETRIES: int = 3
RETRY_BACKOFF_FACTOR: float = 2.0

# -------------------------------------------------------------------------
# Definições de Tipagem e Validação Física (Feature 002)
# -------------------------------------------------------------------------

# Lista das 10 colunas operacionais contínuas
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

# Tolerância numérica para as identidades do ONS (regras R2 a R5)
PHYSICAL_TOLERANCE_EPSILON: float = 1e-4

# -------------------------------------------------------------------------
# Parâmetros técnicos da usina
# Fonte: RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3 (processo de autorização e dados
# informados pelo agente). Operação comercial das 2 UGs liberada pelos Despachos
# ANEEL nº 377/2013 e nº 2.692/2013. A garantia física vigente vem da ANEEL e
# substitui o valor de 36,9 MWmed que constava do relatório de 2017.
# -------------------------------------------------------------------------
FONTE_PARAMETROS_USINA: str = "RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3"
FONTE_GARANTIA_FISICA: str = "ANEEL, valor vigente consultado em 02/10/2026"
NOMINAL_INSTALLED_CAPACITY_MW: float = 48.0
NUMERO_UNIDADES_GERADORAS: int = 2
POTENCIA_UNITARIA_MW: float = 24.0
TIPO_TURBINA: str = "Kaplan de eixo vertical"
ENGOLIMENTO_NOMINAL_UG_M3S: float = 81.5
GARANTIA_FISICA_MWMED: float = 36.4
IP_REFERENCIA: float = 0.06861  # indisponibilidade programada de referência da GF (cálculo informado em 2017)
TEIF_REFERENCIA: float = 0.02333  # taxa equivalente de indisponibilidade forçada de referência da GF
QUEDA_BRUTA_M: float = 35.24
PERDA_HIDRAULICA_M: float = 0.747
RENDIMENTO_TURBINA_GERADOR: float = 0.9053
VAZAO_REMANESCENTE_M3S: float = 4.78
ANO_INICIO_OPERACAO_COMERCIAL: int = 2013

# Grandezas derivadas dos parâmetros acima
ENGOLIMENTO_MAXIMO_USINA_M3S: float = NUMERO_UNIDADES_GERADORAS * ENGOLIMENTO_NOMINAL_UG_M3S
# Potência que a ficha cadastral do ONS deve informar (spec 006, US6)
POTENCIA_AUTORIZADA_ESPERADA_MW: float = NOMINAL_INSTALLED_CAPACITY_MW
# Disponibilidade de referência da GF: (1 - IP) x (1 - TEIF)
DISPONIBILIDADE_REFERENCIA: float = (1.0 - IP_REFERENCIA) * (1.0 - TEIF_REFERENCIA)
# Produtividade nominal teórica: rho x g x queda líquida x rendimento, em MW/(m³/s)
PRODUTIVIDADE_NOMINAL_MW_M3S: float = (
    1000.0 * 9.81 * (QUEDA_BRUTA_M - PERDA_HIDRAULICA_M) * RENDIMENTO_TURBINA_GERADOR / 1e6
)

# -------------------------------------------------------------------------
# Limites de plausibilidade física (regras R6 a R9), derivados dos parâmetros da usina
# -------------------------------------------------------------------------

# Folga relativa sobre os valores nominais antes de sinalizar um registro
TOLERANCIA_LIMITES_FISICOS: float = 0.05
# Faixa aceita para a produtividade horária, relativa à produtividade nominal teórica
FAIXA_PRODUTIVIDADE_RELATIVA: Tuple[float, float] = (0.70, 1.30)
# Excesso de geração sobre a disponibilidade declarada tolerado antes de sinalizar
TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW: float = 1.0

_LIMITE_POTENCIA_MW: float = NOMINAL_INSTALLED_CAPACITY_MW * (1.0 + TOLERANCIA_LIMITES_FISICOS)
_LIMITE_VAZAO_TURBINAVEL_M3S: float = ENGOLIMENTO_MAXIMO_USINA_M3S * (1.0 + TOLERANCIA_LIMITES_FISICOS)

# Limite superior por grandeza. Vazões vertidas totais e energia vertida total não têm
# limite físico definido pela usina (dependem da cheia) e ficam apenas com a regra R1.
LIMITES_FISICOS_SUPERIORES: Dict[str, float] = {
    "val_geracao": _LIMITE_POTENCIA_MW,
    "val_disponibilidade": _LIMITE_POTENCIA_MW,
    "val_folgadegeracao": _LIMITE_POTENCIA_MW,
    "val_energiavertidaturbinavel": _LIMITE_POTENCIA_MW,
    "val_vazaoturbinada": _LIMITE_VAZAO_TURBINAVEL_M3S,
    "val_vazaovertidaturbinavel": _LIMITE_VAZAO_TURBINAVEL_M3S,
}

# -------------------------------------------------------------------------
# Parâmetros analíticos e gráficos (Feature 003)
# -------------------------------------------------------------------------

# Geração igual ou inferior a este valor caracteriza usina parada ou praticamente parada
LIMIAR_GERACAO_PARADA_MW: float = 1.0
# Geração a partir desta fração da potência instalada caracteriza operação próxima da plena carga
FRACAO_PLENA_CARGA: float = 0.90
# Patamar do vertimento contínuo observado na série (5 a 6 m³/s em quase todas as horas)
LIMIAR_VERTIMENTO_MINIMO_M3S: float = 6.0
# Disponibilidade igual ou inferior a este valor caracteriza indisponibilidade total
LIMIAR_INDISPONIBILIDADE_TOTAL_MW: float = 0.001
# Duração mínima dos eventos de indisponibilidade total listados no relatório
DURACAO_MINIMA_EVENTO_RELATORIO_H: int = 24
# Quantidade de eventos listados nas tabelas do relatório (a lista completa vai para a planilha)
NUMERO_EVENTOS_RELATORIO: int = 15
# Janelas horárias usadas na razão diurno/noturno
HORAS_DIURNAS: List[int] = list(range(9, 16))  # 09h às 15h
HORAS_NOTURNAS: List[int] = [20, 21, 22, 23, 0, 1, 2, 3, 4, 5]  # 20h às 05h

# Resolução padrão dos gráficos analíticos (DPI)
DEFAULT_PLOT_DPI: int = 300
