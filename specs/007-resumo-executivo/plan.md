# Implementation Plan: Resumo Executivo do Relatório de Desempenho

**Branch**: `007-resumo-executivo` | **Date**: 2026-10-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-resumo-executivo/spec.md`

## Summary

A etapa 5 passa a gerar, junto com o relatório completo de cada usina, um resumo executivo de no máximo duas páginas A4, em PDF e em Markdown, sem figuras. O resumo traz:
- a conclusão do relatório completo, copiada igual;
- os indicadores da capa;
- as colunas principais da tabela anual;
- um bloco "Sobre os dados", com cobertura, conferências, sinalizações, limites e fontes.

**Abordagem técnica**: o resumo não calcula nada.
- **Objeto único**: um módulo novo monta o `ResumoExecutivo` com as mesmas funções que o relatório completo usa (`listas_conclusao`, `indicadores_capa`, `linhas_tabela_anual`, `fontes.py`). Dele saem o PDF e o Markdown, com o mesmo conteúdo.
- **Na etapa 5**: o resumo é gerado depois do PDF do relatório, na mesma pasta temporária, e entra na mesma troca atômica das saídas.
- **Duas páginas**: as páginas são contadas depois de gerar o PDF. Se passar de duas, sai a evolução anual; se ainda passar, a etapa termina em erro sem trocar nada.
- **Medição**: o protótipo com os dados reais da São Domingos ocupa 81% das duas páginas, com texto em 10 pt e tabelas em 9 pt ([research.md](research.md)).

## Technical Context

**Language/Version**: Python 3.11 ou mais recente, no `venv` do projeto (hoje com CPython 3.14)

**Primary Dependencies**: reportlab (PDF), pandas; nenhuma dependência nova

**Storage**: arquivos: lê `data/usinas/<slug>/analises/resultados.pkl` e grava em `reports/<slug>/`

**Testing**: pytest, sem rede, com a usina fictícia de `tests/fixtures/`

**Target Platform**: Windows 11 com PowerShell

**Project Type**: linha de comando (`python -m src`), fluxo de cinco etapas

**Performance Goals**: o resumo acrescenta poucos segundos à etapa 5, que já gera o PDF completo e as figuras

**Constraints**:
- no máximo duas páginas A4 em retrato, com texto em 10 pt e tabelas em 9 pt;
- conclusão igual, caractere por caractere, à do relatório completo;
- PDF igual byte a byte com `--data-geracao`, para o `comparar`;
- relatório completo e planilha sem nenhuma mudança.

**Scale/Scope**: uma usina por execução. A conclusão tem no máximo 20 itens (cinco por lista); a da São Domingos tem 19. Código atual com cerca de 13.900 linhas em `src/`; a mudança acrescenta cerca de 400.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Conferência contra a constituição **3.1.0**, emendada em 13/10/2026 para esta mudança:

| Princípio ou requisito | Situação | Como o plano cumpre |
|---|---|---|
| I. Uma spec por etapa; cada etapa lê só as anteriores | Passa | Spec de mudança temporária, incorporada à 005 ao concluir (R1). O resumo é gerado dentro da etapa 5 e lê só os resultados das Análises (R2). Sem as Análises, a etapa para com o código 5, como hoje |
| II. Relatório fiel aos dados | Passa | Todo texto e número vem das funções do relatório completo, do perfil ou das regras gerais (R4 a R8). A conclusão é a mesma, gerada pelo mesmo catálogo. Teste de números contra o relatório e `test_literais.py` (R11). Bloco sem base é omitido |
| III. Uma usina por execução | Passa | O resumo é da usina do perfil ativo, na mesma execução |
| IV. Coleta completa e rastreável | Não se aplica | A Coleta não muda |
| V. Tratamento sem descarte | Não se aplica | O Tratamento não muda. Os registros sinalizados ficam fora dos extremos, como no relatório |
| VI. Conferência entre fontes | Passa | O resultado de cada conferência aparece em "Sobre os dados", em texto curto com os mesmos números das legendas (R7) |
| VII. Relatório padronizado | Passa | O resumo está entre os produtos (3.1.0). O bloco único "Sobre os dados" substitui as legendas, e cada tabela indica a seção de origem (R7). PDF e Markdown montados do mesmo objeto (R11). Sem figuras, portanto sem a regra do seaborn |
| VIII. Granularidade declarada | Passa | O resumo reaproveita os textos do relatório, que já identificam o nível. Nada é recalculado nem dividido |
| IX. Relatórios aprovados protegidos | Passa | `comparar --todas` deve acusar só os dois arquivos novos do resumo. O resumo vira referência só com a aprovação do usuário e depois do commit da referência atual (R12) |
| RT1. Python, `venv`, dependências | Passa | Nenhuma dependência nova (R14) |
| RT2. Windows e PowerShell | Passa | [quickstart](quickstart.md) em PowerShell |
| RT3. Gravação segura | Passa | Pasta temporária, conferência no disco e troca atômica da etapa 5, com as saídas anteriores restauradas em caso de falha (R2). Relatório sem `.bak`, como hoje |
| RT5. Cópias de segurança | Passa | Cópia antes do código, no máximo duas ([quickstart](quickstart.md)) |
| RT6. Pastas | Passa | Saídas em `reports/<slug>/` |
| RT7. Log | Passa | Logger `relatorio`: páginas do resumo, omissão da evolução anual e erro de excesso de páginas |
| Qualidade 1. Testes | Passa | Testes novos sem rede, com a usina fictícia; a cobertura atual não diminui (R11) |
| Qualidade 2 e 3. Entrega e recuperação | Passa | Suíte, execução real, log e `comparar --todas --coleta` antes da entrega |
| Governança 2. Mudanças | Passa, com ressalva | Spec e emenda 3.1.0 aprovadas em 13/10/2026. Dois ajustes na spec, A1 e A2 (abaixo), dependem de aprovação antes das tarefas |

**Resultado**: o gate passa, sem violação. Os ajustes A1 e A2 precisam da aprovação do usuário antes do `/speckit-tasks`.

**Reavaliação depois do desenho** (Phase 1):
- O data-model, o contrato e o quickstart mantêm as decisões acima.
- Dois riscos ficaram resolvidos no desenho:
  - **princípio IX**: o PDF do resumo usa o modo invariante com `--data-geracao`, senão o `comparar` acusaria diferença a cada execução (R10);
  - **ordem com a 006**: o código começa só depois do portão da fase A da 006, para não misturar as diferenças das duas mudanças no `comparar` (R13).

## Ajustes na spec (dependem de aprovação do usuário)

| Ajuste | Texto atual | Proposta | Motivo |
|---|---|---|---|
| A1 (R3) | FR-002 e US1, cenário 4: o fiscal "pede só o resumo" | "executa só a Geração do relatório", que refaz o relatório e o resumo a partir dos resultados gravados, sem refazer as etapas anteriores | um resumo gerado sozinho poderia ficar ao lado de um relatório de outra execução, o que o próprio caso de borda proíbe |
| A2 (R7) | FR-013: "Sobre os dados" com "no máximo quatro linhas" | "no máximo 250 palavras" | a constituição 3.1.0 exige no bloco as mesmas informações de fonte e de conferência das legendas; na São Domingos, são cerca de 220 palavras, e o resumo cabe em duas páginas |

## Project Structure

### Documentation (this feature)

```text
specs/007-resumo-executivo/
├── spec.md
├── plan.md              # este arquivo
├── research.md          # decisões R1 a R14 e a medição do protótipo
├── data-model.md        # ResumoExecutivo, regras gerais novas, saídas e referência
├── quickstart.md        # roteiro de validação em PowerShell
├── contracts/
│   └── resumo-executivo.md   # comandos, arquivos e documento
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
src/
├── comum/
│   ├── caminhos.py        ~ ARQUIVOS_RELATORIO ganha resumo_pdf e resumo_md
│   └── regras.py          ~ GLOSSARIO_RESUMO e limites do resumo (páginas, corpos, palavras)
└── relatorio/
    ├── resumo.py          + ResumoExecutivo: montagem dos blocos, COLUNAS_RESUMO_ANUAL e o Markdown
    ├── resumo_pdf.py      + PDF A4 retrato, contagem de páginas e regra das duas páginas
    ├── fontes.py          ~ texto curto de cada conferência; fontes agrupadas por identificador e data
    └── etapa.py           ~ gera o resumo depois do PDF, confere e troca junto; resumo do etapa.json
    (conteudo.py, markdown.py, pdf.py, planilha.py, estrutura.py: sem mudança; pdf.py só é importado)

tests/
├── relatorio/
│   └── test_resumo.py     + verificações da decisão R11
└── integracao/
    └── test_usina_ficticia.py   ~ os dois arquivos do resumo entre as saídas
```

**Structure Decision**: projeto único, como hoje. O resumo fica em `src/relatorio/`, porque faz parte da etapa 5. Segue o padrão do relatório: conteúdo montado uma vez e dois geradores, PDF e Markdown. O PDF do resumo fica num módulo à parte, para não mexer no `pdf.py` do relatório, que está protegido pela referência.

## Fases de implementação (para o `/speckit-tasks`)

| Fase | Conteúdo | Portão |
|---|---|---|
| 0 | depois do portão da fase A da 006: cópia de segurança; aprovação de A1, A2 e do texto do `GLOSSARIO_RESUMO` | aprovações registradas |
| 1 | testes da decisão R11 escritos antes do código, falhando | suíte com os testes novos falhando só por falta do resumo |
| 2 | regras gerais e caminhos; textos curtos das conferências; `resumo.py`; `resumo_pdf.py`; integração em `etapa.py` | suíte aprovada |
| 3 | execução real da São Domingos; leitura e perguntas da SC-005; `comparar --todas --coleta` com só os dois arquivos novos | aprovação do resumo pelo usuário; `referencia`; `comparar` com código 0 |
| 4 | colunas anuais do caminho sem EVT, quando a 006 definir a tabela anual dele; ajustes incorporados à spec 005; exclusão desta pasta | `/speckit-converge`; suíte; `comparar --todas --coleta` |

## Complexity Tracking

Sem violação da constituição a justificar.
