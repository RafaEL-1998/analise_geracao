# Emenda da constituição 3.1.0 → 3.2.0: dados públicos, anexos fora do fluxo e spec de mudança mantida

**Situação**: aprovada pelo usuário e aplicada à constituição em 23/10/2026 · **Data**: 23/10/2026 · **Arquivo**: `.specify/memory/constitution.md`

Decisões do usuário em 23/10/2026 que a emenda leva para a constituição:

- "Esse projeto busca usar tudo e qualquer dado disponível pelos meios públicos; queremos descobrir se conseguimos o SAGER dessa forma; se não tiver como, usar como anexo mesmo, fora do pipeline." A pesquisa do SAGER concluiu que ele não é público (`.specify/assessments/sager-eventos-ug/research.md`); daí o anexo.
- "Poderia excluir só a 006, pois foi algo do projeto." A 007 fica como registro, o que hoje contraria a Governança 2 e 3.

Versão **3.2.0** (MINOR): amplia o princípio IV e cria o princípio X, sem redefinir nenhum princípio de forma incompatível. O código atual continua conforme: hoje a Coleta só usa o ONS, o que a nova regra permite.

## 1. Título e apresentação

| Hoje | Proposto |
|---|---|
| Análise de Desempenho de Usinas com Dados Abertos do ONS — Constituição | Análise de Desempenho de Usinas com Dados Públicos — Constituição |
| "… um relatório de desempenho operacional a partir dos dados abertos do Operador Nacional do Sistema Elétrico (ONS), para subsidiar a fiscalização." | "… um relatório de desempenho operacional a partir dos dados públicos sobre ela, a começar pelos dados abertos do Operador Nacional do Sistema Elétrico (ONS), para subsidiar a fiscalização." |
| Produtos: relatório, resumo executivo e carteira | Acrescenta: "os anexos de uma usina, fora do fluxo, com arquivos não públicos recebidos pela AGEMS (princípio X)." |

## 2. Princípio I, último item

| Hoje | Proposto |
|---|---|
| "Só a Coleta, que também monta o catálogo de usinas, acessa o portal do ONS." | "Só a Coleta, que também monta o catálogo de usinas, acessa as fontes de dados." |

## 3. Princípio IV, item "Fonte"

Hoje:

> **Fonte**: a Coleta DEVE acessar só o portal de dados abertos do ONS. Fontes de outras instituições, como ANEEL e CCEE, só podem entrar no fluxo com mudança desta constituição.

Proposto:

> - **Fontes públicas**: a Coleta DEVE usar só dados públicos, isto é, publicados por uma instituição e acessíveis a qualquer pessoa, sem pedido nem acesso restrito. O portal de dados abertos do ONS é a fonte principal. Outra fonte pública, como ANEEL e CCEE, entra no fluxo por mudança da spec da Coleta aprovada pelo usuário, que declara a instituição, o endereço, o método de acesso, os conjuntos usados, a identificação da usina em cada um e os termos de uso.
> - **Mesmas regras para todas**: a varredura, as ausências, o download e as versões, os dicionários e a extração valem para toda fonte pública. O que uma fonte não oferece, como um dicionário de dados, é declarado na spec da Coleta.
> - **Dados não públicos**: um arquivo obtido por pedido, por ofício ou por acesso restrito, como o SAGER entregue pelo agente, NÃO DEVE entrar no fluxo. Ele só pode ser usado num anexo fora do fluxo (princípio X).

Os demais itens do princípio IV ficam iguais; onde dizem "portal" ou "ONS" em sentido geral, passam a valer para a fonte de cada conjunto.

## 4. Princípio VII, item "Legendas"

| Hoje | Proposto |
|---|---|
| "os conjuntos do ONS usados, com o identificador da usina e a data de obtenção, e as conferências com o resultado" | "os conjuntos usados, com a instituição que os publica, o identificador da usina e a data de obtenção, e as conferências com o resultado" |

## 5. Princípio novo: X. Anexos fora do fluxo

> ### X. Anexos fora do fluxo
>
> - **O que é**: um anexo usa um arquivo não público recebido pela AGEMS, por pedido ou por ofício, para complementar o relatório de uma usina. Ele é gerado por um script em `anexos/<nome>/`, fora das cinco etapas.
> - **Isolamento**: o script DEVE ler só o arquivo recebido e os resultados já gravados pelo fluxo, e NÃO DEVE gravar em `data/` nem em `reports/`. O anexo não muda o relatório, a conclusão nem o relatório de referência da usina, e o relatório não o cita (princípio VI).
> - **Guarda**: o arquivo recebido e o anexo gerado ficam em `usinas/<slug>/documentos/`, fora do controle de versões; o script fica no controle de versões.
> - **Mesmas regras de conteúdo**: o anexo segue o princípio II (fatos dos dados, sem parecer) e o VII (legenda com a fonte em cada tabela e figura, figuras com `seaborn`, PDF e Markdown com o mesmo conteúdo, planilha com a aba de origens). A fonte DEVE dizer o que é o arquivo, quem o entregou, em resposta a quê e a data de recebimento.
> - **Dados pessoais**: nomes, logins e e-mails do arquivo recebido DEVEM ser removidos antes da gravação do anexo, e a remoção DEVE ser conferida.
> - **Descrição**: o cabeçalho do script DEVE trazer o uso, as entradas, as saídas e as regras de cálculo. O anexo não tem spec de etapa; o documento gerado é aprovado pelo usuário.

## 6. Requisitos Técnicos, item 6 "Pastas"

Acrescenta:

> - Dados brutos de outra fonte pública numa pasta própria dela dentro de `data/raw/`.
> - Scripts de anexos em `anexos/<nome>/`; os anexos gerados, em `usinas/<slug>/documentos/`.

## 7. Governança 2 e 3

| Hoje | Proposto |
|---|---|
| "Ao concluir, os ajustes DEVEM estar incorporados às specs das etapas, e a spec de mudança é excluída." | "Ao concluir, os ajustes DEVEM estar incorporados às specs das etapas, e a spec de mudança é excluída, salvo se o usuário decidir mantê-la como registro. Nesse caso, ela recebe no início a situação "concluída e incorporada", com a data e as specs de etapa que a absorveram, e deixa de valer como fonte de requisitos: vale a spec da etapa." |
| "Histórico: fica no controle de versões do projeto, não neste arquivo nem nas specs." | "Histórico: fica no controle de versões do projeto e nas specs de mudança mantidas como registro, não neste arquivo nem nas specs das etapas." |

A spec 007 já atende a regra nova: a linha de situação dela diz "Concluída e incorporada em 2026-10-23", com a spec 005 como destino.

## 8. Rodapé

`**Version**: 3.2.0 | **Ratified**: 2026-09-30 | **Last Amended**: 2026-10-23`

## Efeito em outros arquivos

- **Specs das etapas**: nenhuma mudança agora. A spec da Coleta só muda quando uma fonte nova entrar (por exemplo, a CCEE, se a avaliação dela seguir).
- **`anexos/sager/gerar_anexo_sager.py`**: já atende o princípio X (lê o arquivo e os dados tratados, grava em `usinas/sao_domingos/documentos/anexo_sager/`, remove nomes, logins e e-mails e confere a remoção). Falta só o cabeçalho com as regras de cálculo, que entra junto com a emenda.
- **`README.md`**: o título e a frase de abertura acompanham o título novo; uma linha sobre `anexos/`.
- **Memória de trabalho**: as notas sobre fonte única do ONS passam a citar a 3.2.0.
