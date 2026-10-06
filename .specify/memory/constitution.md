<!--
SYNC IMPACT REPORT
- Version change: 1.1.1 → 1.2.0 (MINOR)
  Rationale: decisões do usuário em 2026-10-05 (spec 006). Amplia o princípio IV com os identificadores
  de três conjuntos do ONS e com a obtenção obrigatória dos dicionários de dados; redefine o escopo do
  Requisito Técnico 3: a cópia .bak passa a ser exigida só nos itens de maior impacto (dados
  processados e alterações em código, testes, specs aprovadas e constituição).
- Modified principles:
  - IV. Filtragem Precisa, Rastreabilidade & Validação Semântica — tabela de identificadores com
    Disponibilidade por usina, Dados hidrológicos horários e Modalidade das usinas; conferência da
    Geração por usina passa a CEG e estado MS; novo parágrafo sobre dicionários de dados.
- Modified sections: Requisitos Técnicos, item 3 (Persistência Segura) — escopo da cópia .bak.
- Added sections: None
- Removed sections: None
- Templates: plan-template.md, spec-template.md e tasks-template.md leem a constituição em tempo de
  execução (Constitution Check genérico); sem alteração necessária.
- Follow-up TODOs:
  - O pipeline ainda não obtém os dicionários de dados nem grava .bak em data/processed/;
    implementação prevista na spec 006 (specs/006-bases-complementares).
- Previous amendments: 1.1.0 → 1.1.1 (2026-10-05, PATCH) — exceção de .bak para reports/;
  1.0.0 → 1.1.0 (2026-10-05, MINOR) — princípio VI (escopo exclusivo da UHE São Domingos, MS);
  princípios III, IV e V ampliados; Requisitos Técnicos 1 e 5.
-->

# UHE São Domingos - Coleta e Processamento de Dados ONS Constitution

## Core Principles

### I. Spec-Driven Development (SDD) & Rigor Metodológico
O desenvolvimento do projeto DEVE ser estritamente orientado por especificações (Spec-Driven Development). Nenhuma linha de código ou script de automação DEVE ser escrita sem especificação prévia aprovada, planejamento e tarefas mapeadas no fluxo Spec Kit (`/speckit-specify` -> `/speckit-clarify` -> `/speckit-plan` -> `/speckit-tasks` -> `/speckit-implement`). Modificações de arquitetura ou lógica exigem atualização prévia da especificação correspondente.

### II. Ecossistema Python Exclusivo & Código Limpo
Todas as ferramentas, rotinas de extração, processamento, filtragem e testes DEVEM ser implementadas exclusivamente em Python (versão 3.10+). Scripts DEVEM ser modulares, com tratamento explícito de tipos, estruturados com docstrings e em estrita conformidade com as boas práticas (PEP 8 e Clean Code). É vedado o uso de scripts utilitários em bash/shell para regras de negócio ou manipulação de dados.

### III. Varredura Exaustiva & Integridade Temporal dos Dados
O pipeline de coleta DEVE inspecionar 100% dos arquivos disponibilizados na fonte de dados do ONS (Energia Vertida Turbinável), sem assumir premissas arbitrárias de data de início de operação da UHE São Domingos. Nenhum arquivo histórico DEVE ser descartado ou ignorado por heurísticas de ano ou ausência prévia de registros em exercícios anteriores (ex.: 2015). A verificação da presença da usina DEVE ser executada de ponta a ponta sobre a totalidade dos conjuntos de dados públicos disponíveis.

Para os conjuntos complementares do ONS (indicadores por unidade geradora, taxas TEIFa/TEIP, programação diária e outros que venham a ser incluídos por spec), o pipeline DEVE inspecionar todos os arquivos publicados que se sobrepõem ao período da base de Energia Vertida Turbinável; o recorte de período DEVE estar declarado na spec do conjunto, e os dias, meses ou arquivos ausentes no portal DEVEM ser listados, nunca presumidos ou interpolados.

### IV. Filtragem Precisa, Rastreabilidade & Validação Semântica
Cada conjunto de dados DEVE ter um identificador da usina declarado e conferido, de modo que nenhum registro de homônimo (ver princípio VI) seja extraído:

| Conjunto do ONS | Identificador de extração | Conferência |
|---|---|---|
| Energia Vertida Turbinável | `cod_usina` = 153 | nome do reservatório contém "SAO DOMINGOS" |
| Indicadores por unidade geradora; Taxas TEIFa e TEIP (e parâmetros) | CEG `UHE.PH.MS.028761-0.01` | id ONS `MSUHSD` |
| Programação diária | código de exibição `PRUHSD` | nome "SAO DOMINGOS" e estado `MS` |
| Geração por usina | id ONS `MSUHSD` | CEG e estado `MS` |
| Disponibilidade por usina | id ONS `MSUHSD` | CEG `UHE.PH.MS.028761-0.01` e estado `MS` |
| Dados hidrológicos horários | `cod_usina` = 153 | nome do reservatório "SAO DOMINGOS" e código do reservatório `PNUHSD` |
| Modalidade das usinas (cadastro) | CEG `UHE.PH.MS.028761-0.01` | id ONS `MSUHSD` e estado `MS` |

No conjunto Energia Vertida Turbinável, a chave canônica `"SE;SUDESTE;PARANA;VERDE;AXIA SUL;SAO DOMINGOS;"` é a referência de localização da usina naquele arquivo (subsistema, bacia, rio, agente e reservatório). Como o agente mudou de CGT ELETROSUL para AXIA SUL em março de 2026, a extração NÃO DEVE depender do nome do agente: aplica-se o identificador da tabela acima, e linhas em que apenas o código ou apenas o nome conferem DEVEM ser contadas na auditoria.

Toda linha extraída DEVE manter o arquivo de origem; a versão, a data de publicação no portal e a data de ingestão de cada arquivo DEVEM ficar registradas no manifesto de versões. Linhas com inconsistência de separadores, campos insuficientes ou formatação inválida DEVEM ser registradas em log e na auditoria, sem interrupção silenciosa da execução.

Os dicionários de dados publicados pelo ONS para cada conjunto usado (PDF e JSON) DEVEM ser obtidos a cada coleta e guardados junto aos dados brutos do conjunto. Como o catálogo não informa data nem tamanho desses arquivos, a mudança é detectada pelo conteúdo, e a versão anterior DEVE ser preservada quando o conteúdo mudar. A obtenção do dicionário não DEVE provocar novo download dos dados do conjunto.

### V. Idempotência, Resiliência & Observabilidade
As rotinas de download e processamento DEVEM ser idempotentes. Execuções repetidas não DEVEM duplicar registros nem corromper arquivos locais. Os arquivos brutos baixados DEVEM ser preservados como artefatos para auditoria; quando o ONS republicar um arquivo já baixado (nova versão), a versão anterior DEVE ser preservada, nunca sobrescrita, com registro de sua data de publicação e de arquivamento.

O sistema DEVE fornecer logging estruturado (arquivo processado, total de linhas, registros correspondentes ao filtro, tempo de resposta e tratamento explícito de exceções de rede ou parsing). O nível de log escolhido na linha de comando DEVE valer para todos os módulos executados naquela chamada.

### VI. Escopo Exclusivo: UHE São Domingos (MS)
Este projeto trata SOMENTE da UHE São Domingos, no rio Verde, bacia do Paraná, municípios de Água Clara e Ribas do Rio Pardo, Mato Grosso do Sul (MS), CEG `UHE.PH.MS.028761-0.01`, 48 MW (2 × 24 MW). Existem homônimos nos dados do ONS e da ANEEL — entre eles PCH São Domingos I e II (GO), CGH São Domingos (SC), CGH São Domingos do Prata (RS), UTE São Domingos (SP) e conjuntos eólicos e solares São Domingos (RN, BA) — que DEVEM ser excluídos. Toda extração, análise, tabela e texto do relatório DEVE referir-se exclusivamente a esta usina; qualquer dado de outra usina só pode aparecer como contexto explícito e identificado (ex.: agregado do subsistema).

## Requisitos Técnicos e Diretrizes de Ambiente

O ambiente operacional primário é Windows com PowerShell e ambiente virtual Python isolado (`venv`).
1. **Linguagem & Dependências**: Python 3 com dependências versionadas em `requirements.txt` (somente as efetivamente usadas), com download por biblioteca robusta (biblioteca padrão `urllib`, `requests` ou `httpx`), com retentativas e gravação atômica, e manipulação de dados estruturados com `pandas`/`csv`.
2. **Compatibilidade com Windows & PowerShell**: Todos os comandos automatizados e scripts DEVEM ser compatíveis com PowerShell e caminhos no padrão Windows (sem comandos Unix `rm`, `ls`, `grep` ou encadeamentos não suportados `&&`).
3. **Persistência Segura**: A cópia `.bak` existe para recuperar o estado anterior se o código falhar e é obrigatória nos itens de maior impacto: (a) os arquivos de `data/processed/` regravados pelo pipeline, com a cópia feita antes da escrita e validação física da gravação no disco depois dela; (b) as alterações em código-fonte, testes, especificações já aprovadas e nesta constituição, com cópia prévia do arquivo alterado ou, antes de mudanças amplas, cópia datada do conjunto afetado. Ficam dispensados: os relatórios em `reports/`, regenerados a partir dos dados (as versões aprovadas são preservadas por cópia datada antes de mudanças no pipeline); os rascunhos de especificação ainda em elaboração; os manifestos de versões, os dicionários de dados e os demais arquivos de controle de baixo impacto, cujas versões, quando aplicável, já são preservadas pelos princípios IV e V.
4. **Armazenamento de Dados**: Os dados brutos baixados (`raw data`) e os dados processados/filtrados (`processed data`) DEVEM residir em diretórios segregados e bem definidos, garantindo integridade e reprodutibilidade do fluxo.
5. **Visualização**: Qualquer gráfico do projeto DEVE ser produzido com `seaborn` (sobre `matplotlib`), com paleta, tipografia e resolução definidas de forma centralizada e consistente entre as figuras.

## Fluxo de Desenvolvimento e Garantia de Qualidade

1. **Ciclo de Entrega**:
   - Todo requisito ou funcionalidade DEVE iniciar com especificação (`.specify/`).
   - Casos de teste e validações sintáticas/unitárias DEVEM ser elaborados para validar a exatidão do filtro de texto e do parser CSV.
2. **Garantia de Qualidade & Não-Regressão**:
   - Execução de testes de integração e validação de formato contra amostras reais de CSV do portal do ONS antes de rodar varreduras completas.
   - Proibição estrita de entrega de código sem validação de execução prática e verificação de logs.
   - Em caso de falha de script ou corrupção de dados parciais, deve existir mecanismo de rollback ou recuperação limpa para o último estado íntegro.

## Governança

Esta Constituição é a lei suprema do projeto e tem precedência sobre qualquer convenção informal.
1. **Processo de Emenda**: Qualquer alteração, adição ou remoção de princípios ou seções exige justificativa explícita, atualização do versionamento semântico e registro no Relatório de Impacto (Sync Impact Report).
2. **Versionamento Semântico**:
   - **MAJOR**: Remoção ou redefinição incompatível de princípios fundamentais (ex.: mudança de linguagem base ou abandono do SDD).
   - **MINOR**: Adição de novos princípios, ferramentas corporativas ou expansão significativa de diretrizes de qualidade.
   - **PATCH**: Ajustes redacionais, correções de digitação ou esclarecimentos sem alteração de escopo.
3. **Auditoria Contínua**: Cada plano de implementação (`plan.md`) e conjunto de tarefas (`tasks.md`) gerado no âmbito do Spec Kit DEVE validar sua aderência estrita a estes princípios constitucionais antes de iniciar a codificação.

**Version**: 1.2.0 | **Ratified**: 2026-09-30 | **Last Amended**: 2026-10-05
