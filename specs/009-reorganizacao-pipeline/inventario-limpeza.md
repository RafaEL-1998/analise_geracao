# Inventário de limpeza (spec 009, US5)

Gerado em 07/10/2026 por um script de conferência (tamanhos medidos na hora). Nada é excluído ou movido antes da decisão do usuário na última coluna (FR-031). Documentos são movidos, nunca excluídos, sem aprovação explícita (FR-033). As cópias de segurança (`_backup_*`) seguem a regra de duas cópias e não entram aqui.

Uso atual: arquivos de código, testes, specs vigentes (sem `.bak`), constituição e README que citam o item.

Se tudo for aprovado: 209,9 MB excluídos e 165,8 MB movidos para `usinas/sao_domingos/documentos/` e `referencias/`, que ficam fora do git.

| # | Item | Tamanho | Uso atual | Ação proposta | Motivo | Decisão do usuário |
|---|---|---|---|---|---|---|
| 1 | `.bak` soltos na raiz: 3 arquivos (`README.md.2026-10-05-spec005.bak`, `README.md.bak`, `requirements.txt.bak`) | 14,8 KB | nenhum | excluir | cópias de edições já guardadas no git (commit a8315cc); a regra nova só exige `.bak` em `data/processed/` | aprovado |
| 2 | `.bak` soltos em `.specify/`: 8 arquivos (`feature.json.2026-10-05-spec006.bak`, `feature.json.2026-10-05.bak`, `feature.json.2026-10-05b.bak` …) | 27,9 KB | nenhum | excluir | cópias de edições já guardadas no git (commit a8315cc); a regra nova só exige `.bak` em `data/processed/` | aprovado |
| 3 | `.bak` soltos em `specs/`: 48 arquivos (`requirements.md.2026-10-05.bak`, `cli-contract.md.2026-10-05.bak`, `data-model.md.2026-10-05.bak` …) | 611,3 KB | nenhum | excluir | cópias de edições já guardadas no git (commit a8315cc); a regra nova só exige `.bak` em `data/processed/` | aprovado |
| 4 | `.bak` soltos em `src/`: 4 arquivos (`analyzer.py.bak`, `config.py.bak`, `models.py.bak` …) | 70,8 KB | nenhum | excluir | cópias de edições já guardadas no git (commit a8315cc); a regra nova só exige `.bak` em `data/processed/` | aprovado |
| 5 | `.bak` soltos em `tests/`: 1 arquivo (`test_analyzer.py.bak`) | 5,4 KB | nenhum | excluir | cópias de edições já guardadas no git (commit a8315cc); a regra nova só exige `.bak` em `data/processed/` | aprovado |
| 6 | `reports/_versao_anterior_2026-09-30/` | 6,2 MB | README.md, specs (9) | excluir | relatórios de 30/09/2026, com informações já corrigidas, guardados só para comparação; as citações no README e nas specs antigas saem com a reescrita (US1 e US2) | aprovado |
| 7 | `.pytest_cache/` e `__pycache__/` (5 pastas) | 1,7 MB | nenhum | excluir | gerados de novo pelo Python e pelo pytest a cada execução | aprovado |
| 8 | `DicionarioDados_EnergiaVertidaTurbinavel.json` (raiz) | 2,4 KB | `src/config.py` (`DATA_DICTIONARY_JSON`), lido por `src/validator.py` | excluir depois de apontar `DATA_DICTIONARY_JSON` para o baixado | idêntico byte a byte ao baixado em `data/raw/_dicionarios/`; o validador passa a ler a cópia que a coleta mantém atualizada | aprovado |
| 9 | `Docs_usina/Docs_usina.rar` | 142,8 MB | nenhum | excluir | os 23 arquivos do .rar estão soltos na pasta, com o mesmo conteúdo (SHA-256 conferido) | aprovado |
| 10 | `Docs_usina/` (23 PDFs: relatórios semestrais, RAPAs, PAE, licença de operação, outorga e estações hidrométricas) | 160,6 MB | nenhum | mover para `usinas/sao_domingos/documentos/` | documentos da usina, fora do git; ficam junto do perfil | aprovado |
| 11 | `Docs_usina/Anexo6-UHSD-PARE-RQ-Imasul-000216.2016-Outorga de agua.pdf` | 40,0 KB | nenhum | excluir (decisão do usuário) | cópia idêntica (SHA-256) de `Anexo 6 - UHSD-PARE-RQ-Imasul-000216.2016-Outorga de agua.pdf`, que fica | aprovado |
| 12 | `51.006.927-2026 Minuta de Ofício - Agenda Fiscalização Presencial - UHE São Domingos.docx` | 875,8 KB | nenhum | mover para `usinas/sao_domingos/documentos/` | ofício da agenda da fiscalização presencial | aprovado |
| 13 | `RF - UHE São Domingos 0009 2017 AGEPAN SFG.doc` | 1,5 MB | nenhum | mover para `usinas/sao_domingos/documentos/` | RF 0009/2017-AGEPAN-SFG, fonte dos parâmetros da usina (citado como fonte no relatório, não lido pelo fluxo) | aprovado |
| 14 | `RF xxx 2026 AGEMS SFT - Desempenho Operacional UHE São Domingos - Modelo.docx` | 97,3 KB | nenhum | mover para `usinas/sao_domingos/documentos/` | modelo do RF 2026 (não é citado como fonte) | aprovado |
| 15 | `Resolucao-normativa-1029-2022-Aneel-BR-consolidada-[02-06-2026].pdf`; `Resolucao-normativa-1032-2022-Aneel-BR-consolidada-[09-12-2025].pdf`; `Resolucao-normativa-1033-2022-Aneel-BR-consolidada-[30-01-2026].pdf`; `Resolução Normativa N° 964_2021 - Leis.org.pdf`; `RESOLUÇÃO NORMATIVA Nº 846, DE 11 de junho de 2019 - RESOLUÇÃO NORMATIVA Nº 846, DE 11 de junho de 2019 - DOU - Imprensa Nacional.pdf` | 1,4 MB | nenhum | mover para `referencias/` | resoluções normativas da ANEEL (846/2019, 964/2021, 1.029, 1.032 e 1.033/2022), legislação geral de consulta | aprovado |
| 16 | `SEI_0407709_RF___Monitoramento_da_Geracao_12 UHE não despachadas.pdf`; `SEI_0461990_RF___Analise_da_Geracao_103 Fiscalizações Hidrelétricas 2026.pdf` | 1,1 MB | nenhum | mover para `referencias/` | RFs SEI de monitoramento e de análise da geração, material de consulta | aprovado |
| 17 | `Usinas de geração por tipo de despacho de energia.docx`; `Usinas de Geração por Tipo de Despacho I, II-B e II-C - Afetadas pelo Curtailment.jpg.jpeg` | 60,4 KB | nenhum | mover para `referencias/` | material de consulta sobre tipos de despacho e curtailment | aprovado |
| 18 | `WhatsApp Image 2026-10-01 at 11.23.31.jpeg` | 178,7 KB | nenhum | mover para `referencias/` (decisão do usuário) | captura de uma tabela de priorização de usinas (fila "1-urgente", perfil "subperformance crônica"), com a São Domingos (score 0,91; déficit de 204,27 GWh); material de contexto da fiscalização | aprovado |
| 19 | `data/ccee/` (`geracao_horaria_usina_202607.csv.gz`) | 58,2 MB | nenhum | excluir (decisão do usuário) | conferência manual de 01/10/2026 com a CCEE, fora do relatório; o resultado está registrado na spec 004 | aprovado |
| 20 | `data/aneel_bi/` (3 exportações `data*.xlsx`) | 155,2 KB | specs | excluir (decisão do usuário) | conferência manual de 02/10/2026 com o BI da ANEEL, fora do relatório; o resultado está registrado na spec 004 | aprovado |
| 21 | `.agents/skills/` (10 skills do Spec Kit) | 134,7 KB | nenhum | excluir (decisão do usuário) | cópias antigas do Spec Kit para outro agente (Antigravity); as skills em uso estão em `.claude/skills/`, mais novas | aprovado |
| 22 | `venv/` | — | fluxo e ferramentas | manter | ambiente Python do projeto | aprovado |
| 23 | `.mcp.json` | 0,1 KB | fluxo e ferramentas | manter | servidor MCP do ONS | aprovado |
| 24 | `.claude/` | 194,4 KB | fluxo e ferramentas | manter | skills do Spec Kit em uso | aprovado |
| 25 | `.specify/` | 175,2 KB | fluxo e ferramentas | manter | constituição, modelos e scripts do Spec Kit (sem os `.bak`) | aprovado |
| 26 | `data/processed/*.bak` | 16,0 MB | fluxo e ferramentas | manter | 10 cópias exigidas pela regra de gravação segura | aprovado |

## Conferência do `Docs_usina.rar`

Listagem e leitura com o bsdtar, sem extrair para o disco: 23 arquivos; 23 com o mesmo SHA-256 dos soltos na pasta; 0 só no .rar; 0 só na pasta; 0 com conteúdo diferente. Os nomes acentuados foram comparados sem os acentos, que o bsdtar lê em outra página de código.

## `.bak` soltos

- `.specify/feature.json.2026-10-05-spec006.bak`
- `.specify/feature.json.2026-10-05.bak`
- `.specify/feature.json.2026-10-05b.bak`
- `.specify/feature.json.bak`
- `.specify/memory/constitution.md.2026-10-05-t064.bak`
- `.specify/memory/constitution.md.2026-10-05-v120.bak`
- `.specify/memory/constitution.md.2026-10-05.bak`
- `.specify/memory/constitution.md.bak`
- `README.md.2026-10-05-spec005.bak`
- `README.md.bak`
- `requirements.txt.bak`
- `specs/001-ons-coleta-sao-domingos/checklists/requirements.md.2026-10-05.bak`
- `specs/001-ons-coleta-sao-domingos/contracts/cli-contract.md.2026-10-05.bak`
- `specs/001-ons-coleta-sao-domingos/data-model.md.2026-10-05.bak`
- `specs/001-ons-coleta-sao-domingos/plan.md.2026-10-05.bak`
- `specs/001-ons-coleta-sao-domingos/plan.md.bak`
- `specs/001-ons-coleta-sao-domingos/quickstart.md.2026-10-05.bak`
- `specs/001-ons-coleta-sao-domingos/research.md.2026-10-05.bak`
- `specs/001-ons-coleta-sao-domingos/spec.md.2026-10-05-spec005.bak`
- `specs/001-ons-coleta-sao-domingos/spec.md.2026-10-05-spec006.bak`
- `specs/001-ons-coleta-sao-domingos/spec.md.2026-10-05-t043.bak`
- `specs/001-ons-coleta-sao-domingos/spec.md.2026-10-05.bak`
- `specs/001-ons-coleta-sao-domingos/tasks.md.2026-10-05-spec005.bak`
- `specs/001-ons-coleta-sao-domingos/tasks.md.2026-10-05-t043.bak`
- `specs/001-ons-coleta-sao-domingos/tasks.md.2026-10-05.bak`
- `specs/001-ons-coleta-sao-domingos/tasks.md.bak`
- `specs/002-tratamento-dados/checklists/requirements.md.2026-10-05.bak`
- `specs/002-tratamento-dados/contracts/cli-contract.md.2026-10-05.bak`
- `specs/002-tratamento-dados/data-model.md.2026-10-05.bak`
- `specs/002-tratamento-dados/plan.md.2026-10-05.bak`
- `specs/002-tratamento-dados/plan.md.bak`
- `specs/002-tratamento-dados/quickstart.md.2026-10-05.bak`
- `specs/002-tratamento-dados/research.md.2026-10-05.bak`
- `specs/002-tratamento-dados/spec.md.2026-10-05-spec005.bak`
- `specs/002-tratamento-dados/spec.md.2026-10-05-spec006.bak`
- `specs/002-tratamento-dados/spec.md.2026-10-05.bak`
- `specs/002-tratamento-dados/tasks.md.2026-10-05-spec005.bak`
- `specs/002-tratamento-dados/tasks.md.2026-10-05.bak`
- `specs/002-tratamento-dados/tasks.md.bak`
- `specs/003-analise-dados/checklists/requirements.md.2026-10-05.bak`
- `specs/003-analise-dados/contracts/cli-contract.md.2026-10-05.bak`
- `specs/003-analise-dados/data-model.md.2026-10-05.bak`
- `specs/003-analise-dados/plan.md.2026-10-05.bak`
- `specs/003-analise-dados/plan.md.bak`
- `specs/003-analise-dados/quickstart.md.2026-10-05.bak`
- `specs/003-analise-dados/research.md.2026-10-05.bak`
- `specs/003-analise-dados/spec.md.2026-10-05-spec005.bak`
- `specs/003-analise-dados/spec.md.2026-10-05-spec006.bak`
- `specs/003-analise-dados/spec.md.2026-10-05-t064.bak`
- `specs/003-analise-dados/spec.md.2026-10-05.bak`
- `specs/003-analise-dados/tasks.md.2026-10-05-spec005.bak`
- `specs/003-analise-dados/tasks.md.2026-10-05-t064.bak`
- `specs/003-analise-dados/tasks.md.2026-10-05.bak`
- `specs/003-analise-dados/tasks.md.bak`
- `specs/004-conferencia-outros/spec.md.2026-10-05-spec006.bak`
- `specs/006-bases-complementares/contracts/cli-contract.md.2026-10-05-impl.bak`
- `specs/006-bases-complementares/data-model.md.2026-10-05-impl.bak`
- `specs/006-bases-complementares/research.md.2026-10-05-impl.bak`
- `specs/006-bases-complementares/spec.md.2026-10-05-impl.bak`
- `src/analyzer.py.bak`
- `src/config.py.bak`
- `src/models.py.bak`
- `src/pdf_generator.py.bak`
- `tests/test_analyzer.py.bak`

## Aplicação (07/10/2026)

Decisão do usuário em 07/10/2026: "aprovo o inventário", todos os itens como propostos.

- **Excluídos**: 76 caminhos, 209,9 MB.
- **Movidos**: 35 arquivos, 165,8 MB, cada um conferido por SHA-256 no destino: 25 para `usinas/sao_domingos/documentos/` e 10 para `referencias/`. A pasta `Docs_usina/`, vazia, foi removida.
- **Dicionário da raiz** (item 8): `DATA_DICTIONARY_JSON` passou a apontar para `data/raw/_dicionarios/DicionarioDados_EnergiaVertidaTurbinavel.json`; `tests/test_validator.py` passou antes da exclusão.
- **Correção do motivo dos itens 1 a 5**: os `.bak` não estavam no git, que os ignora (`*.bak` no `.gitignore`); o git guarda só as versões vigentes desses arquivos. Das 64 cópias, 61 continuam em `_backup_2026-10-07_antes_conclusao/`, inclusive as versões de 30/09/2026 de `src/` e `tests/`, anteriores à auditoria, até essa cópia sair pela regra das duas cópias. As outras três (`README.md.bak`, `README.md.2026-10-05-spec005.bak` e `requirements.txt.bak`) não tinham outra cópia.
- **Fora do git**: `reports/_versao_anterior_2026-09-30/` (13 arquivos), o dicionário da raiz, `.agents/` (10 arquivos) e as duas imagens movidas para `referencias/` estavam no git e continuam recuperáveis pelo histórico (commit a8315cc). O `.rar`, o Anexo 6 duplicado, `data/ccee/` e `data/aneel_bi/` não estavam.

| Item | Ação | Caminho | Destino | Tamanho |
|---|---|---|---|---|
| 10 | movido | `Docs_usina/11 Relatório Semestral da UHE São Domingos.pdf` | `usinas/sao_domingos/documentos/11 Relatório Semestral da UHE São Domingos.pdf` | 11,5 MB |
| 10 | movido | `Docs_usina/14-Relatorios-Semestral-e-seus-Anexos-2019.pdf` | `usinas/sao_domingos/documentos/14-Relatorios-Semestral-e-seus-Anexos-2019.pdf` | 29,0 MB |
| 10 | movido | `Docs_usina/Anexo 6 - UHSD-PARE-RQ-Imasul-000216.2016-Outorga de agua.pdf` | `usinas/sao_domingos/documentos/Anexo 6 - UHSD-PARE-RQ-Imasul-000216.2016-Outorga de agua.pdf` | 40,0 KB |
| 10 | movido | `Docs_usina/Anexo3 -UHSD-PARE-RE-BD-Instalaçãoes das estações Hidrométricas.pdf` | `usinas/sao_domingos/documentos/Anexo3 -UHSD-PARE-RE-BD-Instalaçãoes das estações Hidrométricas.pdf` | 4,2 MB |
| 10 | movido | `Docs_usina/Anexo7-UHSD-PARF-MP-Imasul-Rib.Tamanduá-Mar.2016-R1.pdf` | `usinas/sao_domingos/documentos/Anexo7-UHSD-PARF-MP-Imasul-Rib.Tamanduá-Mar.2016-R1.pdf` | 22,5 MB |
| 10 | movido | `Docs_usina/PAE_Público_SAODOMINGOS_R4.pdf` | `usinas/sao_domingos/documentos/PAE_Público_SAODOMINGOS_R4.pdf` | 4,4 MB |
| 10 | movido | `Docs_usina/Renovacao Licenca Operacao.pdf` | `usinas/sao_domingos/documentos/Renovacao Licenca Operacao.pdf` | 1,6 MB |
| 10 | movido | `Docs_usina/UHSD-PAGE-CE-DEA-0115.2018-Entrega do 11o RAPA.pdf` | `usinas/sao_domingos/documentos/UHSD-PAGE-CE-DEA-0115.2018-Entrega do 11o RAPA.pdf` | 694,2 KB |
| 10 | movido | `Docs_usina/UHSD-PAGE-CE-DEA-0263.2013-Entrega do 1o RAPA.pdf` | `usinas/sao_domingos/documentos/UHSD-PAGE-CE-DEA-0263.2013-Entrega do 1o RAPA.pdf` | 474,0 KB |
| 10 | movido | `Docs_usina/UHSD-PAGE-CE-DEA-0460.2013-Entrega do 2o RAPA.pdf` | `usinas/sao_domingos/documentos/UHSD-PAGE-CE-DEA-0460.2013-Entrega do 2o RAPA.pdf` | 234,2 KB |
| 10 | movido | `Docs_usina/UHSD-PAGE-CE-DMO-0043.2014-Entrega do 3o RAPA.pdf` | `usinas/sao_domingos/documentos/UHSD-PAGE-CE-DMO-0043.2014-Entrega do 3o RAPA.pdf` | 585,8 KB |
| 10 | movido | `Docs_usina/UHSD-PAGE-CE-DMO-0061.2015-Entrega do 5o RAPA.PDF` | `usinas/sao_domingos/documentos/UHSD-PAGE-CE-DMO-0061.2015-Entrega do 5o RAPA.PDF` | 218,1 KB |
| 10 | movido | `Docs_usina/UHSD-PAGE-CE-DMO-0123.2014-Entrega do 4o RAPA.PDF` | `usinas/sao_domingos/documentos/UHSD-PAGE-CE-DMO-0123.2014-Entrega do 4o RAPA.PDF` | 272,9 KB |
| 10 | movido | `Docs_usina/UHSD-PAGE-CE-DMO-0173.2015-Entrega  do 6º RAPA.PDF` | `usinas/sao_domingos/documentos/UHSD-PAGE-CE-DMO-0173.2015-Entrega  do 6º RAPA.PDF` | 214,9 KB |
| 10 | movido | `Docs_usina/UHSD-PAGE-CE-DRMS-0009.2017-Entrega do 9o RAPA.pdf` | `usinas/sao_domingos/documentos/UHSD-PAGE-CE-DRMS-0009.2017-Entrega do 9o RAPA.pdf` | 516,8 KB |
| 10 | movido | `Docs_usina/UHSD-PAGE-CE-DRMS-0031.2016-Entrega do 7o RAPA.PDF` | `usinas/sao_domingos/documentos/UHSD-PAGE-CE-DRMS-0031.2016-Entrega do 7o RAPA.PDF` | 318,4 KB |
| 10 | movido | `Docs_usina/UHSD-PAGE-CE-DRMS-0074.2016-Entrega do 8o RAPA.PDF` | `usinas/sao_domingos/documentos/UHSD-PAGE-CE-DRMS-0074.2016-Entrega do 8o RAPA.PDF` | 323,7 KB |
| 10 | movido | `Docs_usina/UHSD-PAGE-CE-RMMS-0017.2017-Entrega do 10o RAPA.pdf` | `usinas/sao_domingos/documentos/UHSD-PAGE-CE-RMMS-0017.2017-Entrega do 10o RAPA.pdf` | 554,8 KB |
| 10 | movido | `Docs_usina/UHSD-PAGE-RE-DEA-12.RAPA-12.2018.pdf` | `usinas/sao_domingos/documentos/UHSD-PAGE-RE-DEA-12.RAPA-12.2018.pdf` | 3,2 MB |
| 10 | movido | `Docs_usina/UHSD-PAGE-RE-DEA-14.RAPA-09.2019.pdf` | `usinas/sao_domingos/documentos/UHSD-PAGE-RE-DEA-14.RAPA-09.2019.pdf` | 2,4 MB |
| 10 | movido | `Docs_usina/UHSD-PAGE-RE-DEA-RAPA-07.2022.final.pdf` | `usinas/sao_domingos/documentos/UHSD-PAGE-RE-DEA-RAPA-07.2022.final.pdf` | 75,1 MB |
| 10 | movido | `Docs_usina/UHSD_Relat_Sem_5_mar_2015_Volume_I.pdf` | `usinas/sao_domingos/documentos/UHSD_Relat_Sem_5_mar_2015_Volume_I.pdf` | 2,2 MB |
| 12 | movido | `51.006.927-2026 Minuta de Ofício - Agenda Fiscalização Presencial - UHE São Domingos.docx` | `usinas/sao_domingos/documentos/51.006.927-2026 Minuta de Ofício - Agenda Fiscalização Presencial - UHE São Domingos.docx` | 875,8 KB |
| 13 | movido | `RF - UHE São Domingos 0009 2017 AGEPAN SFG.doc` | `usinas/sao_domingos/documentos/RF - UHE São Domingos 0009 2017 AGEPAN SFG.doc` | 1,5 MB |
| 14 | movido | `RF xxx 2026 AGEMS SFT - Desempenho Operacional UHE São Domingos - Modelo.docx` | `usinas/sao_domingos/documentos/RF xxx 2026 AGEMS SFT - Desempenho Operacional UHE São Domingos - Modelo.docx` | 97,3 KB |
| 15 | movido | `Resolucao-normativa-1029-2022-Aneel-BR-consolidada-[02-06-2026].pdf` | `referencias/Resolucao-normativa-1029-2022-Aneel-BR-consolidada-[02-06-2026].pdf` | 238,1 KB |
| 15 | movido | `Resolucao-normativa-1032-2022-Aneel-BR-consolidada-[09-12-2025].pdf` | `referencias/Resolucao-normativa-1032-2022-Aneel-BR-consolidada-[09-12-2025].pdf` | 204,1 KB |
| 15 | movido | `Resolucao-normativa-1033-2022-Aneel-BR-consolidada-[30-01-2026].pdf` | `referencias/Resolucao-normativa-1033-2022-Aneel-BR-consolidada-[30-01-2026].pdf` | 326,1 KB |
| 15 | movido | `Resolução Normativa N° 964_2021 - Leis.org.pdf` | `referencias/Resolução Normativa N° 964_2021 - Leis.org.pdf` | 282,0 KB |
| 15 | movido | `RESOLUÇÃO NORMATIVA Nº 846, DE 11 de junho de 2019 - RESOLUÇÃO NORMATIVA Nº 846, DE 11 de junho de 2019 - DOU - Imprensa Nacional.pdf` | `referencias/RESOLUÇÃO NORMATIVA Nº 846, DE 11 de junho de 2019 - RESOLUÇÃO NORMATIVA Nº 846, DE 11 de junho de 2019 - DOU - Imprensa Nacional.pdf` | 348,5 KB |
| 16 | movido | `SEI_0407709_RF___Monitoramento_da_Geracao_12 UHE não despachadas.pdf` | `referencias/SEI_0407709_RF___Monitoramento_da_Geracao_12 UHE não despachadas.pdf` | 817,1 KB |
| 16 | movido | `SEI_0461990_RF___Analise_da_Geracao_103 Fiscalizações Hidrelétricas 2026.pdf` | `referencias/SEI_0461990_RF___Analise_da_Geracao_103 Fiscalizações Hidrelétricas 2026.pdf` | 307,3 KB |
| 17 | movido | `Usinas de geração por tipo de despacho de energia.docx` | `referencias/Usinas de geração por tipo de despacho de energia.docx` | 19,2 KB |
| 17 | movido | `Usinas de Geração por Tipo de Despacho I, II-B e II-C - Afetadas pelo Curtailment.jpg.jpeg` | `referencias/Usinas de Geração por Tipo de Despacho I, II-B e II-C - Afetadas pelo Curtailment.jpg.jpeg` | 41,3 KB |
| 18 | movido | `WhatsApp Image 2026-10-01 at 11.23.31.jpeg` | `referencias/WhatsApp Image 2026-10-01 at 11.23.31.jpeg` | 178,7 KB |
| 6 | excluído | `reports/_versao_anterior_2026-09-30` | — | 6,2 MB |
| 7 | excluído | `.pytest_cache` | — | 2,4 KB |
| 7 | excluído | `src/__pycache__` | — | 788,8 KB |
| 7 | excluído | `tests/__pycache__` | — | 755,1 KB |
| 7 | excluído | `tests/integration/__pycache__` | — | 27,5 KB |
| 7 | excluído | `tests/unit/__pycache__` | — | 141,9 KB |
| 8 | excluído | `DicionarioDados_EnergiaVertidaTurbinavel.json` | — | 2,4 KB |
| 9 | excluído | `Docs_usina/Docs_usina.rar` | — | 142,8 MB |
| 11 | excluído | `Docs_usina/Anexo6-UHSD-PARE-RQ-Imasul-000216.2016-Outorga de agua.pdf` | — | 40,0 KB |
| 19 | excluído | `data/ccee` | — | 58,2 MB |
| 20 | excluído | `data/aneel_bi` | — | 155,2 KB |
| 21 | excluído | `.agents` | — | 134,7 KB |
| 10 | excluída (vazia) | `Docs_usina` | — | — |
| 1 a 5 | excluídos | os 64 `.bak` listados na seção "`.bak` soltos" | — | 730,2 KB |

## Inventário final do layout antigo (T074)

Gerado em 08/10/2026, depois da migração das cinco etapas.

- **Uso atual**: nenhum arquivo de código ou de teste lê os itens abaixo. Dois docstrings de `src/comum/persistencia.py` ainda citam `data/processed/` e são corrigidos junto.
- **Se tudo for aprovado**: 82,6 MB excluídos.
- **Itens sem ação**: as cópias de segurança seguem a regra de duas cópias. As specs antigas e a 009 saem na troca das specs (T076), com aprovação própria. O único `.bak` que fica é `data/usinas/sao_domingos/coleta/auditoria_evt.csv.bak`, cópia exigida pela regra de gravação.

| # | Item | Tamanho | Uso atual | Ação proposta | Motivo | Decisão do usuário |
|---|---|---|---|---|---|---|
| 27 | `data/processed/`: 30 arquivos de dados e 10 `.bak` | 76,0 MB | nenhum | excluir | Saídas do fluxo antigo. Cada arquivo tem equivalente em `data/usinas/sao_domingos/` (tabela abaixo): 20 são idênticos byte a byte e 10 trazem os mesmos dados, reorganizados entre as etapas. Os `.bak` são versões anteriores desses arquivos. | aprovado |
| 28 | Relatório solto em `reports/`: `relatorio_analise_estatistica.pdf` e `.md`, `perfil_estatistico_anual.xlsx` e `.csv`, `figures/` (8 figuras) | 6,7 MB | nenhum | excluir (11 deles estão no git: `git rm`) | Relatório gerado pelo fluxo antigo; o atual fica em `reports/sao_domingos/`. O `comparar` com a linha de base não acusa diferença nesses arquivos: PDF, Markdown, CSV e figuras são idênticos byte a byte, e a planilha tem as mesmas células. | aprovado |

### Equivalência dos arquivos de `data/processed/` que não são idênticos byte a byte

Os outros 20 arquivos são idênticos aos novos (SHA-256), entre eles:
- a EVT extraída e a tratada, em CSV e Parquet;
- a validação física;
- os indicadores por unidade, as horas por estado e a TEIFa/TEIP mensal;
- a programação horária;
- as séries horárias e as ausências de disponibilidade, geração e hidrologia;
- o alinhamento das vazões;
- o registro dos dicionários.

| Arquivo antigo | Equivalente novo | Diferença |
|---|---|---|
| `relatorio_auditoria_varredura.csv` | `coleta/auditoria_evt.csv` | colunas novas `formato`, `data_publicacao`, `obtido` e `mensagem`; `data_hora_processamento` é a da nova execução |
| `uhe_sao_domingos_energia_vertida_tratado.xlsx` | `tratamento/evt_tratado.xlsx` | mesmos dados (os bytes da planilha mudam a cada gravação) |
| `relatorio_auditoria_indicadores_ons.csv` | `coleta/auditoria_indicadores.csv` | colunas novas da auditoria da Coleta (formato, período, publicação, obtido, linhas irregulares, só identificador, só conferência, mensagem) |
| `uhe_sao_domingos_indicadores_ons.xlsx` (8 abas) | `tratamento/indicadores.xlsx` (5 abas) | `AUDITORIA_ARQUIVOS` foi para `coleta/auditoria_indicadores.csv`; `DIVERGENCIAS` foi para `conferencia/dispf_horas.csv` (idêntico ao antigo `..._ons_divergencias_indicadores.csv`); `TEIFA_TEIP_RECALCULO` foi para `conferencia/teifa_teip.csv` |
| `relatorio_auditoria_programacao_ons.csv` | `coleta/auditoria_programacao.csv` | colunas novas `formato`, `data_publicacao`, `obtido`, `linhas_so_conferencia`, `valores_invalidos` e `mensagem` |
| `relatorio_auditoria_{disponibilidade,geracao,hidrologia}_ons.csv` | `coleta/auditoria_{...}.csv` e `tratamento/auditoria_{...}.csv` | `horas_usina` e `duplicatas_conflitantes` passaram para a auditoria do Tratamento; a da Coleta ganhou `data_publicacao` e `obtido` |
| `uhe_sao_domingos_ons_cadastro.csv` | `coleta/cadastro_ficha.csv` | a coluna `divergencias` virou a conferência `conferencia/cadastro.csv`; a ficha ganhou `linhas_ceg` |
| `relatorio_auditoria_cadastro_ons.csv` | `coleta/auditoria_cadastro.csv` | colunas novas `data_publicacao` e `obtido` |

### Execução (08/10/2026)

Aprovado pelo usuário em 08/10/2026 (itens 27 e 28).

| # | Ação | Item | Tamanho |
|---|---|---|---|
| 27 | excluído | `data/processed/` (30 arquivos de dados e 10 `.bak`) | 76,0 MB |
| 28 | excluídos com `git rm` | `reports/figures/` (8 figuras), `reports/perfil_estatistico_anual.csv` e `.xlsx`, `reports/relatorio_analise_estatistica.md` | 4,4 MB |
| 28 | excluído (fora do git) | `reports/relatorio_analise_estatistica.pdf` | 2,2 MB |

Depois da limpeza:
- `data/` tem só `raw/` e `usinas/`;
- `reports/` tem só `sao_domingos/`.
