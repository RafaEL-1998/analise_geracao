# Research: Tratamento, Padronização e Validação Física dos Dados - UHE São Domingos

Este documento consolida as decisões técnicas, as regras de validação e as estratégias de persistência adotadas no tratamento dos dados da UHE São Domingos.

**Revisão retroativa (2026-10-05)**: decisões atualizadas para refletir a implementação após a auditoria de 30/09/2026. Quando uma decisão original foi substituída, ela é citada como "Decisão original (30/09/2026)". A versão anterior está em `research.md.2026-10-05.bak`.

---

## 1. Padronização e Tipagem das Colunas Numéricas *(revisado)*

- **Decisão**: Converter as 10 colunas métricas (`val_*`) para `float64` com `pd.to_numeric(errors='coerce')`, depois de trocar vírgula por ponto e remover espaços nas colunas lidas como texto. Valores ausentes ou não numéricos permanecem NaN e são contados em log por coluna. `cod_usina` é convertido para `Int64` (inteiro anulável); `din_instante` é convertido para data/hora e qualquer instante inválido interrompe o processamento com `ValueError`. As colunas de identificação e rastreabilidade são mantidas como texto, sem espaços nas bordas.
- **Decisão original (30/09/2026)**: a coerção com `errors='coerce'` era seguida do preenchimento dos ausentes com zero.
- **Justificativa**: O Excel em português usa vírgula decimal e o ONS publica com ponto; sem tipagem, números aparecem como texto ("Geral") e quebram somas e médias. Preencher ausentes com zero fabrica uma medição: uma hora sem dado passaria a valer geração zero, vertimento zero ou disponibilidade zero, distorcendo totais, médias e contagens de horas paradas. Um instante inválido não tem posição na série horária e não pode ser tratado em silêncio.
- **Alternativas consideradas**:
  - *Preencher ausentes com zero*: rejeitado pelo motivo acima (era a decisão original).
  - *Remover linhas com ausentes*: rejeitado; perderia horas da série e contraria o Princípio III da constituição.
  - *Interpolar ausentes*: rejeitado; também fabrica valores.
  - *Exportar apenas CSV com vírgula decimal*: rejeitado como única opção porque quebraria scripts externos em Python/R que esperam ponto decimal.

---

## 2. Estratégia de Exportação Multi-Formato (.xlsx, .parquet, .csv) *(revisado)*

- **Decisão**: Exportar a base tratada, já com as colunas de sinalização, em três formatos complementares em `data/processed/` (o usuário pode escolher um subconjunto):
  1. **Excel (`.xlsx`)**: gerado via `pandas.ExcelWriter` com `openpyxl`, aba `UHE_SAO_DOMINGOS`, cabeçalho congelado e largura de colunas ajustada. As métricas são gravadas como células numéricas nativas (formato "Geral" do Excel, sem número fixo de casas) e o instante como data/hora (`YYYY-MM-DD HH:MM:SS`).
  2. **Apache Parquet (`.parquet`)**: gerado via `pyarrow`, com `double` para as métricas, `int64` para `cod_usina`, `timestamp` para o instante e `bool` para as colunas de anomalia.
  3. **CSV (`.csv`)**: delimitador `;`, ponto decimal, UTF-8, datas `%Y-%m-%d %H:%M:%S` e precisão integral (sem arredondamento); ausentes ficam como célula vazia.
- **Decisão original (30/09/2026)**: CSV com as métricas arredondadas (o teste `test_exportar_csv_precisao_integral` registra a correção: "sem arredondar para 4 dígitos").
- **Justificativa**: Atende tanto os analistas que trabalham em Excel quanto quem usa Python/Pandas/PowerBI. O arredondamento do CSV descartava informação publicada pelo ONS e podia impedir a reprodução das identidades R4 e R5 a partir do CSV com a tolerância de $10^{-4}$.
- **Dependências**: `openpyxl>=3.1.0` e `pyarrow>=14.0.0` em `requirements.txt`.

---

## 3. Motor de Validação: Consistência Interna e Plausibilidade Física *(revisado)*

- **Decisão**: Avaliar 9 regras sobre 100% dos registros (`validar_regras_fisicas` em `src/validator.py`), em dois grupos:
  - **Consistência interna ONS (R1 a R5)**, tolerância $\epsilon = 10^{-4}$:
    1. **R1 - Não-negatividade**: nenhuma das 10 grandezas $< -\epsilon$; conta registros com ao menos uma grandeza negativa.
    2. **R2**: $val\_energiavertida \ge val\_energiavertidaturbinavel$.
    3. **R3**: $val\_vazaovertida \ge val\_vazaovertidaturbinavel + val\_vazaovertidanaoturbinavel$.
    4. **R4**: $val\_energiavertidaturbinavel = val\_vazaovertidaturbinavel \times val\_produtividade$.
    5. **R5**: $val\_folgadegeracao = \max(0, val\_disponibilidade - val\_geracao)$.
  - **Plausibilidade física (R6 a R9)**, com os parâmetros da usina (seção 4):
    6. **R6**: limites superiores de potência e de vazão turbinável.
    7. **R7**: geração não superior à disponibilidade declarada mais 1,0 MW.
    8. **R8**: produtividade entre 70% e 130% da nominal teórica, avaliada só quando há vazão turbinada.
    9. **R9**: geração de no máximo 1,0 MW quando a vazão turbinada é nula.
  - Valores ausentes não contam como violação em nenhuma regra.
  - As máscaras de R6 a R9 (`mascaras_plausibilidade`) são a fonte única tanto para a contagem de violações quanto para as colunas de sinalização.
- **Decisão original (30/09/2026)**: apenas as regras R1 a R5, apresentadas como "regras hidrotécnicas" cuja conformidade "certifica formalmente que a base histórica do ONS é coerente". A configuração original trazia faixas genéricas sem fonte (`EXPECTED_PHYSICAL_BOUNDS`, preservadas em `src/config.py.bak`; ex.: geração até 70 MW, produtividade até 5,0 MW/(m³/s)), que não apareciam no relatório.
- **Justificativa**: R2 a R5 são identidades de cálculo entre colunas publicadas (na base real, R4 e R5 têm desvio máximo nulo na precisão de 6 casas); a conformidade de 100% mostra coerência de cálculo, não a correção das medições. O registro de 15/05/2019 14h (68,743 MW, com 48 MW instalados) satisfaz R1 a R5 e ficava dentro da faixa genérica de 70 MW; só a comparação com os parâmetros da usina o detecta.
- **Alternativas consideradas**:
  - *Apenas calcular média e desvio padrão*: insuficiente para identificar valores fisicamente impossíveis.
  - *Detecção estatística de outliers*: não adotada; os limites derivados de parâmetros físicos são interpretáveis e verificáveis na fiscalização.

---

## 4. Parâmetros da Usina e Derivação dos Limites *(novo)*

- **Decisão**: Centralizar em `src/config.py` os parâmetros técnicos, com a fonte registrada em `FONTE_PARAMETROS_USINA = "RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3"`, e calcular os limites a partir deles:

| Parâmetro | Valor | Constante |
| :--- | ---: | :--- |
| Unidades geradoras × potência unitária | 2 × 24 MW (48 MW) | `NUMERO_UNIDADES_GERADORAS`, `POTENCIA_UNITARIA_MW`, `NOMINAL_INSTALLED_CAPACITY_MW` |
| Turbina | Kaplan de eixo vertical | `TIPO_TURBINA` |
| Engolimento nominal por unidade | 81,5 m³/s | `ENGOLIMENTO_NOMINAL_UG_M3S` |
| Queda bruta / perda hidráulica | 35,24 m / 0,747 m | `QUEDA_BRUTA_M`, `PERDA_HIDRAULICA_M` |
| Rendimento turbina-gerador | 0,9053 | `RENDIMENTO_TURBINA_GERADOR` |

| Grandeza derivada | Cálculo | Valor |
| :--- | :--- | ---: |
| Engolimento máximo da usina | 2 × 81,5 | 163,0 m³/s |
| Produtividade nominal teórica | $1000 \times 9{,}81 \times (35{,}24 - 0{,}747) \times 0{,}9053 / 10^6$ | 0,3063 MW/(m³/s) |
| Limite de potência (R6) | 48 × (1 + 0,05) | 50,4 MW |
| Limite de vazão turbinável (R6) | 163 × (1 + 0,05) | 171,15 m³/s (171,2 no relatório) |
| Faixa de produtividade (R8) | 0,70 a 1,30 × 0,3063 | 0,214 a 0,398 MW/(m³/s) |

- **Tolerâncias** (`TOLERANCIA_LIMITES_FISICOS = 0,05`, `FAIXA_PRODUTIVIDADE_RELATIVA = (0,70; 1,30)`, `TOLERANCIA_GERACAO_ACIMA_DISPONIBILIDADE_MW = 1,0`, `LIMIAR_GERACAO_PARADA_MW = 1,0`): critérios de triagem para não sinalizar variações de medição e arredondamento em torno dos valores nominais. Não são valores normativos.
- **Grandezas sem limite superior**: vazão vertida total, vazão vertida não turbinável e energia vertida total dependem da cheia e não têm limite físico definido pela usina; ficam sujeitas apenas a R1 a R3.
- **Justificativa**: Limites calculados a partir de parâmetros com fonte podem ser conferidos pelo fiscal e mudam de forma consistente se um parâmetro for corrigido.

---

## 5. Sinalizar em Vez de Remover *(novo)*

- **Decisão**: Manter na base tratada todos os registros que violam R6 a R9, acrescentando uma coluna booleana por regra (`anomalia_limite_fisico`, `anomalia_geracao_acima_disponibilidade`, `anomalia_produtividade`, `anomalia_geracao_sem_vazao_turbinada`) e a coluna-resumo `qualidade_registro` (`OK` ou os códigos violados separados por `;`).
- **Justificativa**: Um registro sinalizado é indício a verificar, não erro confirmado. Removê-lo alteraria os totais publicados pelo ONS e esconderia o problema de quem fiscaliza. Cada análise decide como tratá-lo: a Feature 003 mantém esses registros nos totais e os exclui do perfil estatístico e da tabela de extremos.
- **Alternativas consideradas**:
  - *Remover registros anômalos*: rejeitado pelo motivo acima.
  - *Corrigir ou imputar valores*: rejeitado; não há fonte para o valor correto dentro do conjunto de dados.

---

## 6. Uso do Dicionário de Dados *(novo)*

- **Decisão**: Ler `DicionarioDados_EnergiaVertidaTurbinavel.json` (`carregar_dicionario_dados`), conferir que as 10 colunas métricas constam dele (`verificar_colunas_no_dicionario`, que só emite aviso) e citar a versão no relatório (`versao_dicionario_dados`, "Versão 2.0 (06-06-2024)").
- **Justificativa**: O dicionário contém apenas código, descrição e unidade de cada coluna; não define faixas de valores. Serve para confirmar que as colunas tratadas são as publicadas e quais unidades usam (MWmed, m³/s, MW/(m³/s)), não para derivar limites.

---

## 7. Códigos de Saída e Opções da CLI *(novo)*

- **Decisão**: Código de saída 3 apenas quando R1 é violada, interrompendo antes da sinalização, dos relatórios e da exportação; violações de R2 a R9 não alteram o código de saída. As opções `--validate-physics` e `--generate-report` usam `argparse.BooleanOptionalAction` (padrão ativado, com `--no-validate-physics` e `--no-generate-report` para desligar).
- **Decisão original (30/09/2026)**: as duas opções tinham padrão verdadeiro sem forma de desligá-las.
- **Justificativa**: Grandeza negativa é impossível por definição e indica provável arquivo corrompido ou erro de leitura, o que põe em dúvida a base inteira. As violações de R2 a R9 atingem registros isolados e são tratadas por sinalização e relatório.

---

## 8. Perfilamento Estatístico e Relatório de Integridade *(substituído)*

- **Decisão original (30/09/2026)**: Gerar no relatório `data/processed/relatorio_validacao_fisica.md` e na tabela CSV estatísticas descritivas anuais e a "comprovação de 0 violações físicas", como artefato que comprovaria que a base "foi rigorosamente tratada e auditada".
- **Decisão atual**: O relatório de validação traz apenas o resultado das regras R1 a R9, a leitura de cada uma (texto gerado a partir dos números, com formatação brasileira por `src/formatacao.py`), a ressalva de que R1 a R5 não atestam a correção dos valores e a lista cronológica dos primeiros 40 registros sinalizados. O perfil estatístico anual é produzido pela Feature 003 (`src/analyzer.py`, `calcular_perfil_estatistico_anual`).
- **Justificativa**: Um relatório que anuncia a conclusão antes da execução não serve à fiscalização; o texto precisa refletir o que os dados mostram. Concentrar as estatísticas na Feature 003 evita duas fontes para os mesmos números.
