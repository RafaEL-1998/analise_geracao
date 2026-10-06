# Research: Conferência com Outras Fontes do ONS e Programação Diária

**Feature**: `004-conferencia-outros` | **Date**: 2026-10-05

## Parte A — Decisões de design (US1)

### R1. Formato dos arquivos diários
- **Decision**: usar o formato compacto publicado (Parquet, ~150 KB por dia).
- **Rationale**: o ONS publica cada dia em Parquet, CSV (~37 MB) e XLSX (~8 MB); em CSV o período inteiro somaria ~26 GB. O Parquet de todo o período ocupa ~106 MB.
- **Alternatives considered**: CSV (volume inviável); consulta remota via servidor MCP do ONS (limite de 50 s por consulta, sem reprodutibilidade — usada só na exploração).

### R2. Data de cada dia
- **Decision**: a data vem do nome do arquivo (`PROGRAMACAO_DIARIA_AAAA_MM_DD`); a coluna interna `din_programacaodia` é apenas conferida.
- **Rationale**: a coluna interna aparece como `AAAA-MM-DD` em alguns arquivos e `DD/MM/AAAA` em outros. Conferência feita em 05/10/2026 nos 712 arquivos: lida com o formato correto de cada um, a data interna coincide com a do nome em 100% dos casos.
- **Alternatives considered**: parse automático da coluna interna (inverteu dia e mês em ISO com `dayfirst`, gerando 12.288 falsas divergências na exploração).

### R3. Conversão para base horária
- **Decision**: hora = (patamar − 1) ÷ 2 (divisão inteira); programação horária = média dos dois patamares; convenção de hora de início, igual à base de EVT.
- **Rationale**: o patamar 1 é 00:00–00:30. Validação empírica em jul/2026: 222 das 232 horas de usina parada com EVT coincidem com programação zero, e a geração acompanha a programação nas demais horas, o que confirma o alinhamento (defasagem de 1 h produziria descasamento sistemático nas bordas das paradas).
- **Alternatives considered**: usar só o primeiro patamar de cada hora (perde as reprogramações de meia hora).

### R4. Identificação da usina
- **Decision**: `cod_exibicaousina == "PRUHSD"`, conferido por `nom_usina` contendo "SAO DOMINGOS" e `id_estado == "MS"`; linhas com só um dos critérios são contadas na auditoria.
- **Rationale**: há homônimos na programação (UHE São Domingos em GO, CGH em SC, UTE em SP, entre outras). O código `PRUHSD`, modalidade TIPO II-A, subsistema SE, foi verificado em todos os arquivos.
- **Alternatives considered**: nome da usina sozinho (homônimos).

### R5. Limiares da classificação
- **Decision**: usina parada e programação zero = até 1 MW (`LIMIAR_GERACAO_PARADA_MW`, já usado na spec 003); desvio relevante = usina parada com programação acima de 5 MW.
- **Rationale**: o mesmo limiar de parada mantém a comparabilidade com as constatações existentes; 5 MW separa desvios operacionais de arredondamentos e rampas. Parâmetros abertos à revisão do usuário (`src/config.py`).
- **Alternatives considered**: comparação estrita com zero (sensível a valores residuais de 0,0x MW).

### R6. Cache e reaproveitamento
- **Decision**: manifesto de versões em `data/raw/programacao_diaria/`, reutilizando `download_resource` de `src/collector.py`; ajuste em `_local_filename` para preservar a extensão do formato compacto.
- **Rationale**: mesma garantia de idempotência das specs 001 e 004/US2. Os 712 arquivos obtidos na exploração de 02/10/2026 podem ser reaproveitados se o tamanho coincidir com o publicado.
- **Alternatives considered**: módulo de download próprio (duplicaria a lógica de retentativas e manifesto).

### R7. Limites do que a programação explica
- **Decision**: o relatório afirma apenas se a parada seguiu ou não a programação diária; não atribui motivo.
- **Rationale**: para usinas hidráulicas, os campos de motivo (ordem de mérito, inflexibilidade, razão elétrica) vêm vazios e a disponibilidade programada vem zerada; reprogramações em tempo real não são publicadas.

### R8. Fora do escopo (avaliado e não incluído)
- Classificação de EVT do SIN (`classificacao-evt`): agregada para o sistema, só 2024–2025 e com lacunas; serve como indício (2º semestre de 2025 registrado como 100% razão energética), não como prova.
- Disponibilidade horária por usina (`disponibilidade_usina`): existe para a usina desde 01/01/2023 (operacional e sincronizada); candidata a uma feature futura.
- CMO semi-horário, curtailment eólico/solar: contexto sistêmico; candidatos futuros.

## Parte B — Registro das conferências com outras fontes (US3)

| Data | Fonte | Período conferido | Resultado | Decisão |
|---|---|---|---|---|
| 02/10/2026 | Energia Vertida Turbinável no S3 do ONS (via servidor MCP) | ago/2018 a set/2026 | Totais mensais idênticos à base local em todos os meses de ago/2018 a ago/2026; 01 a 28/09/2026 idênticos; o portal já tinha até 30/09 | Base local mantida (decisão do usuário) |
| 02/10/2026 | Geração por usina (`geracao-usina-2`, id ONS `MSUHSD`) | 2018 a 2026, hora a hora | Zero divergências na geração horária; série estende-se até 18/06/2015 | Apenas consultada (extensão a 2015 recusada pelo usuário) |
| 02/10/2026 | Dados hidrológicos horários (`dados_hidrologicos_ho`, `PNUHSD`) | 2025 | Convenção de fim de hora (EVT t ↔ hidro t + 1 h; meia-noite gravada como 23:59); vazão vertida 100% e turbinada 99,9% iguais | Apenas consultada |
| 02/10/2026 | Modalidade das usinas | cadastro | UHE São Domingos: TIPO II-A, COSR-S, SE Água Clara 138 kV, CEG UHE.PH.MS.028761-0.01 | Usada como identificação |
| 02/10/2026 | Indicadores por unidade geradora (mensal e anual), Taxas TEIFa e TEIP, Parâmetros | ago/2018 a set/2026 | TEIFa e TEIP reproduzidas a partir das horas em 21 de 21 meses; 4 meses-unidade com divergência DISPF × TEIP | Incluídas no pipeline (US2) |
| 02/10/2026 | Classificação de EVT do SIN | 2024–2025 | Só agregado do sistema, sem usina | Descartada do pipeline |
| 02/10/2026 | Interrupção de carga; providências ECPA/PCPA | — | Cortes de carga ≥ 100 MW; indicadores por agente, não por usina | Descartadas |
| 02/10/2026 | Catálogo do ONS (85 conjuntos) e portal de dados abertos da ANEEL | — | Nenhum conjunto com eventos individuais de desligamento de geração (motivo, início, fim) nem com TEIFa/TEIP na ANEEL | Lacuna: solicitar ao agente |
| 02/10/2026 | Programação diária (`programacao_diaria`, `PRUHSD`) | out/2024 a set/2026 | 1.739 de 1.908 h de usina parada com EVT (91%) com programação zero; 57% da EVT do período nessas horas | Incluída no pipeline (US1) |
| 01/10/2026 | CCEE (amostra jul/2026) | jul/2026 | Geração no centro de gravidade = geração ONS × fator de perda interna; confirma que o registro de 68,7 MW (15/05/2019) é erro do ONS | Apenas consultada |
| 02/10/2026 | BI da ANEEL (exportações em `data/aneel_bi/`) | 2013 a 2025 | Geração "Verificada" idêntica à do ONS; série da CCEE desde 2013 | Apenas consultada |

### O que nenhuma fonte aberta oferece (solicitar ao agente)
- Registro de ocorrências de cada unidade geradora (início, fim, tipo, motivo).
- Ordens de despacho e reprogramações do centro de operação do ONS nas horas de usina parada com EVT.
- Causa da limitação de potência da UG2 (horas equivalentes de desligamento forçado em 78 de 80 meses).
- Classificação correta dos 4 meses-unidade em que o DISPF e as horas do TEIP divergem.
