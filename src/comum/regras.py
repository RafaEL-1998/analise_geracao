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
# Tipos de usina e perfil (data-model da Coleta de dados, seção 5.3)
# ---------------------------------------------------------------------------

TIPOS_USINA: Tuple[str, ...] = ("UHE", "PCH", "CGH", "UTE", "UTN", "EOL", "UFV")
MODALIDADES_COM_PERFIL: Tuple[str, ...] = ("TIPO I", "TIPO II-A", "TIPO II-B", "TIPO II-C")
MODALIDADES_TIPO_III: Tuple[str, ...] = ("TIPO III", "TIPO III (EM DIT)")  # só o agregado: sem perfil
SUBSISTEMAS: Tuple[str, ...] = ("SE", "S", "NE", "N")
COBERTURAS: Tuple[str, ...] = ("proprio", "conjunto", "agregado", "ausente")
# Fator de capacidade nos indicadores anuais (plano das Análises, D21)
TIPOS_COM_FATOR_CAPACIDADE: Tuple[str, ...] = ("EOL", "UFV")
# Sazonalidade: meses distintos na série de referência (plano das Análises, D19)
PERIODO_MINIMO_SAZONALIDADE_MESES: int = 12

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
# Cadastrais do catálogo de usinas (plano da Coleta de dados, D20 e D33)
CONJUNTO_COMPOSICAO: str = "usina_conjunto"
CONJUNTO_CAPACIDADE: str = "capacidade-geracao"
CONJUNTO_RESERVATORIO: str = "reservatorio"
# Térmicas (plano da Coleta de dados, D27)
CONJUNTO_DESPACHO: str = "geracao-termica-despacho-2"
CONJUNTO_CVU: str = "cvu-usitermica"
CONJUNTO_CMO: str = "cmo-semanal"
# Eólicas e solares (plano da Coleta de dados, D27): a restrição tem uma variante por tipo
CONJUNTO_FATOR_CAPACIDADE: str = "fator-capacidade-2"
CONJUNTO_RESTRICAO_EOLICA_DETALHE: str = "restricao_coff_eolica_detail"
CONJUNTO_RESTRICAO_FOTOVOLTAICA_DETALHE: str = "restricao_coff_fotovoltaica_detail"
CONJUNTO_RESTRICAO_EOLICA: str = "restricao_coff_eolica_usi"
CONJUNTO_RESTRICAO_FOTOVOLTAICA: str = "restricao_coff_fotovoltaica"
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
PASTA_COMPOSICAO_RAW: str = "usina_conjunto"
PASTA_CAPACIDADE_RAW: str = "capacidade_geracao"
PASTA_RESERVATORIO_RAW: str = "reservatorio"
PASTA_DESPACHO_RAW: str = "geracao_termica_despacho_2"
PASTA_CVU_RAW: str = "cvu_usitermica"
PASTA_CMO_RAW: str = "cmo_semanal"
PASTA_FATOR_CAPACIDADE_RAW: str = "fator_capacidade_2"
PASTA_RESTRICAO_EOLICA_DETALHE_RAW: str = "restricao_coff_eolica_detail"
PASTA_RESTRICAO_FOTOVOLTAICA_DETALHE_RAW: str = "restricao_coff_fotovoltaica_detail"
PASTA_RESTRICAO_EOLICA_RAW: str = "restricao_coff_eolica_usi"
PASTA_RESTRICAO_FOTOVOLTAICA_RAW: str = "restricao_coff_fotovoltaica"
# Pacote -> pasta de todos os conjuntos: CONJUNTOS_PIPELINE, derivado do registro (src/coleta/registro.py)
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
# Catálogo de usinas (plano da Coleta de dados, D19 a D21)
# ---------------------------------------------------------------------------

MESES_AGREGADOS_CATALOGO: int = 12  # meses completos de geração no panorama dos agregados
# Modalidades da Geração por usina: grupos agregados do estado (Tipo III e MMGD) e linhas de conjunto de usinas
MODALIDADES_AGREGADAS_GERACAO: Tuple[str, ...] = ("PEQUENAS USINAS (TIPO III)", "PEQUENAS USINAS (MMGD)", "TIPO III")
MODALIDADES_PREVISAO_GERACAO: Tuple[str, ...] = ("PEQUENAS USINAS (TIPO III)", "TIPO III")  # valor previsto (FR-051)
PREFIXO_CONJUNTO: str = "CJU_"  # id ONS dos conjuntos de usinas
# Tipo publicado pelo ONS (sem acento, maiúsculas) -> tipos pelo prefixo do CEG que ele admite (D19)
TIPOS_ONS: Dict[str, Tuple[str, ...]] = {
    "HIDROELETRICA": ("UHE", "PCH", "CGH"), "TERMICA": ("UTE",), "NUCLEAR": ("UTN",), "EOLIELETRICA": ("EOL",),
    "FOTOVOLTAICA": ("UFV",), "UHE": ("UHE", "PCH", "CGH"), "UTE": ("UTE",), "UEE": ("EOL",), "UFV": ("UFV",),
}
# Datas sentinela de "vigente" ou "sem desativação" nos cadastrais do ONS
DATAS_SENTINELA: Tuple[str, ...] = ("9999-12-31", "2999-12-31", "0001-01-01", "31/12/9999", "31/12/2999",
                                    "01/01/0001")

# ---------------------------------------------------------------------------
# Figuras
# ---------------------------------------------------------------------------

DEFAULT_PLOT_DPI: int = 300
TAMANHO_FIGURA_PADRONIZADA: Tuple[float, float] = (11, 4.3)  # figuras 01, 02, 05 e 06, em polegadas
LARGURA_FIGURA_CARTEIRA: float = 7.5  # figuras do relatório de carteira (A4 retrato), em polegadas

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

# Térmicas (plano das Análises, D18 e D20): limiares calibrados na UTE William Arjona e aprovados pelo usuário em
# 20/10/2026
LIMIAR_DESVIO_DESPACHO_MW: float = 5.0  # atendimento ao despacho: |verificada − programada| acima disso
LIMIAR_CONCLUSAO_DESPACHO_ABAIXO_HORAS: int = 24  # C12: horas com a geração abaixo da programada
LIMIAR_CONCLUSAO_DISPONIVEL_CVU_HORAS: int = 168  # C13: horas disponíveis sem despacho com o CVU abaixo do CMO
LIMIAR_CONCLUSAO_INFLEXIBILIDADE_PCT: float = 5.0  # C14: inflexibilidade não verificada, em % da programada
LIMIAR_CONCLUSAO_SEM_PROGRAMACAO_HORAS: int = 24  # C15: horas com geração acima da programada, sem programação

# Eólicas e solares (plano das Análises, D18 e D21): limiares iniciais, calibrados na Seriemas 1 e na Praia Formosa
# e aprovados pelo usuário em 21/10/2026
LIMIAR_CONCLUSAO_ENERGIA_CORTADA_PCT: float = 5.0  # C16: energia cortada, em % da energia estimada
LIMIAR_CONCLUSAO_RECURSO_INVALIDO_PCT: float = 10.0  # C17: semi-horas com o recurso inválido, em % das semi-horas
# C19: desvio médio absoluto, em % da potência instalada; 15 % aprovado pelo usuário em 21/10/2026, pois
# os 10 % iniciais apontavam desvios usuais da previsão de vento (10,4 % na EOL Praia Formosa)
LIMIAR_CONCLUSAO_DESVIO_PROGRAMACAO_PCT: float = 15.0
DURACAO_SEMI_HORA_H: float = 0.5  # energia de uma semi-hora: potência média × 0,5 h (plano do Tratamento de dados, D17)
FAIXA_VENTO_MS: float = 2.0  # largura das faixas de vento (m/s) do recurso × geração (plano das Análises, D21)
FAIXA_IRRADIANCIA_WM2: float = 100.0  # largura das faixas de irradiância (W/m²)
# Limite físico do recurso (decisão do usuário de 21/10/2026): acima dele, falha de medição não marcada pelo ONS (a EOL
# Praia Formosa tem semi-horas com vento de até 246 m/s), fora das faixas do recurso × geração e contada
LIMITE_VENTO_PLAUSIVEL_MS: float = 40.0
LIMITE_IRRADIANCIA_PLAUSIVEL_WM2: float = 1500.0

# ---------------------------------------------------------------------------
# Resumo executivo: limites e glossário (iguais para todas as usinas)
# ---------------------------------------------------------------------------

RESUMO_MAXIMO_PAGINAS: int = 2  # páginas A4 do PDF do resumo
RESUMO_CORPO_PT: float = 10.0  # corpo do texto do resumo, em pontos
RESUMO_TABELA_PT: float = 9.0  # corpo das tabelas do resumo, em pontos
RESUMO_MAXIMO_PALAVRAS: int = 1000  # palavras fora das tabelas: leitura em até 5 minutos
RESUMO_MAXIMO_PALAVRAS_DADOS: int = 250  # palavras do bloco "Sobre os dados"
# Siglas e grandezas explicadas na linha de termos do resumo, só as que aparecem nele
GLOSSARIO_RESUMO: Dict[str, str] = {
    "EVT": "energia vertida turbinável, a que a água vertida poderia ter gerado nas turbinas disponíveis",
    "ONS": "Operador Nacional do Sistema Elétrico",
    "DISPF": "disponibilidade das unidades geradoras apurada pelo ONS",
    "TEIFa": "taxa de indisponibilidade forçada apurada pelo ONS em 60 meses",
    "TEIF": "taxa de indisponibilidade forçada de referência, usada no cálculo da garantia física",
    "TEIP": "taxa de indisponibilidade programada apurada pelo ONS em 60 meses",
    "UG": "unidade geradora",
    "GF": "garantia física",
    "Pinst": "potência instalada",
    "MWmed": "megawatt médio, a energia dividida pelas horas do período",
    # Térmicas (spec da Geração do relatório, FR-066): texto aprovado pelo usuário em 20/10/2026
    "CVU": "custo variável unitário da usina térmica, publicado pelo ONS por semana operativa",
    "CMO": "custo marginal de operação do subsistema, calculado pelo ONS por semana operativa",
    # Eólicas e solares (spec da Geração do relatório, FR-066): texto aprovado pelo usuário em 21/10/2026
    "constrained-off": "redução da geração da usina por comando do ONS, por razão externa a ela (indisponibilidade "
                       "externa, confiabilidade elétrica ou razão energética)",
}
