# Análise de Desempenho de Usinas Hidrelétricas com Dados do ONS — Constituição

Este projeto gera, para uma usina hidrelétrica de cada vez, um relatório de desempenho operacional a partir dos dados
abertos do Operador Nacional do Sistema Elétrico (ONS), para subsidiar a fiscalização. O relatório sai em PDF, em
Markdown e em planilha, com as figuras, e todo o conteúdo dele vem dos dados, do perfil da usina e das regras gerais do
projeto.

O trabalho segue um único fluxo de cinco etapas. Cada etapa tem uma spec, na mesma ordem:

| Etapa | O que faz | Spec |
|---|---|---|
| 1. Coleta de dados | varre o portal do ONS, baixa e versiona os arquivos e os dicionários de dados, extrai a usina e audita a extração | `specs/001-coleta-dados/` |
| 2. Tratamento de dados | padroniza, valida, alinha os horários e grava os dados tratados | `specs/002-tratamento-dados/` |
| 3. Conferência | confere as bases entre si e refaz os indicadores oficiais | `specs/003-conferencia/` |
| 4. Análises | calcula indicadores, eventos, perfis, constatações, a conclusão e os dados de cada figura | `specs/004-analises/` |
| 5. Geração do relatório | produz as figuras, o PDF, o Markdown e a planilha | `specs/005-geracao-relatorio/` |

## Core Principles

### I. Desenvolvimento orientado por especificação, uma spec por etapa

- Nenhum código DEVE ser escrito sem spec aprovada. O ciclo é o do Spec Kit: especificar, planejar, dividir em tarefas
  e implementar.
- Cada etapa do fluxo DEVE ter uma única spec, que descreve o funcionamento atual completo da etapa: objetivo,
  entradas e saídas, requisitos, critérios de aceitação e decisões do usuário.
- Uma mudança DEVE atualizar a spec da etapa afetada antes do código. NÃO DEVE ser criada spec que remende outra.
- Cada etapa DEVE ler só os resultados gravados pelas etapas anteriores e gravar os seus. Só a Coleta acessa o portal
  do ONS. Uma etapa sem os resultados das anteriores DEVE parar sem gravar nada e indicar a etapa a executar antes.

### II. Relatório fiel aos dados

- Todo número, nome e frase do relatório DEVE ser gerado a partir dos dados, do perfil da usina ou das regras gerais.
  Nenhum valor, nome de usina ou conclusão fica fixo no código ou no texto.
- As constatações DEVEM descrever fatos dos dados, sem parecer: nada de "satisfatório", "insatisfatório",
  "cumpre", "descumpre" ou equivalentes. Cada constatação aparece uma única vez, no início da sua seção.
- A conclusão DEVE ser gerada por um catálogo de regras declaradas, iguais para qualquer usina, com os limiares
  descritos nas notas metodológicas. Ela aponta indícios, o que confirmar com o agente e o que verificar em campo, e
  NÃO DEVE afirmar causa nem avaliar o desempenho da usina.
- Uma seção, figura ou regra cuja base não existe para a usina DEVE ser omitida, nunca preenchida com suposição.
- Nenhum documento em elaboração ou modelo de documento DEVE ser citado como fonte.

### III. Uma usina por execução, definida pelo perfil

- Cada execução DEVE tratar de uma única usina, definida pelo seu perfil (`usinas/<slug>/perfil.toml`).
- O perfil DEVE reunir tudo o que é próprio da usina:
  - nome e estado;
  - o identificador de extração e o campo de conferência em cada conjunto do ONS;
  - os parâmetros técnicos que o ONS não publica, cada um com a fonte e a data;
  - as características da usina usadas nas análises.
- As regras gerais (limiares, tolerâncias, metas, catálogo da conclusão) DEVEM ser as mesmas para qualquer usina e
  ficar separadas do perfil.
- Um perfil incompleto ou incoerente DEVE ser recusado antes da coleta, com a lista de todos os problemas.
- Os homônimos DEVEM ser excluídos pelos identificadores do perfil, nunca pelo nome. Dados de outra usina só podem
  aparecer como contexto explícito e identificado, como um agregado do subsistema.

### IV. Coleta completa e rastreável

- A Coleta DEVE inspecionar todos os arquivos publicados de cada conjunto do ONS usado, sem supor data de início de
  operação nem descartar arquivo por heurística de ano. Nos conjuntos complementares, entram todos os arquivos que se
  sobrepõem ao período da base de energia vertida turbinável.
- Dias, meses ou arquivos ausentes no portal DEVEM ser listados, nunca presumidos ou interpolados.
- Só o que é novo ou mudou no portal DEVE ser baixado, conforme o manifesto de versões do catálogo. Os arquivos
  brutos DEVEM ser preservados; quando o ONS republica um arquivo, a versão anterior é guardada.
- Os dicionários de dados publicados pelo ONS (PDF e JSON) DEVEM ser obtidos a cada coleta e guardados com os dados
  brutos, com a versão anterior preservada quando o conteúdo mudar, sem novo download dos dados do conjunto.
- A extração DEVE usar o identificador e o campo de conferência do perfil, nunca o nome do agente. As linhas em que
  só um dos dois confere, as linhas irregulares e os valores inválidos DEVEM ser contados na auditoria da extração,
  sem interrupção silenciosa. Toda linha extraída mantém o arquivo de origem.

### V. Tratamento sem descarte

- As regras de consistência e de plausibilidade DEVEM sinalizar os registros, nunca excluí-los dos dados tratados.
  A spec de cada etapa declara o que um registro ou um campo sinalizado deixa de alimentar, e o relatório informa as
  sinalizações.
- A convenção de horário de cada conjunto, o tratamento de duplicatas e o recorte do período DEVEM estar declarados
  na spec do Tratamento e ser aplicados a todos os conjuntos, de modo que as bases fiquem alinhadas hora a hora.
- As ausências DEVEM ser listadas por conjunto.

### VI. Conferência entre fontes

- Sempre que duas bases trazem a mesma grandeza, ou que um indicador oficial pode ser refeito a partir dos dados, a
  etapa de Conferência DEVE comparar as duas e registrar o resultado: bases, período, quantidade comparada,
  coincidências, divergências e tolerância.
- Uma conferência cuja base não existe para a usina DEVE ser registrada como não aplicável, com o motivo.
- Uma conferência com meta declarada que não a atinge DEVE interromper o fluxo completo. Se as etapas seguintes forem
  executadas à parte, elas omitem o que depende dessa conferência.
- O relatório DEVE citar os resultados das conferências nas legendas. Conferências feitas fora do fluxo, que ele não
  reproduz, NÃO DEVEM ser citadas no relatório.

### VII. Relatório padronizado

- O relatório DEVE ter a estrutura fixa definida na spec da Geração do relatório: capa com identificação, parâmetros,
  indicadores e sumário; seções numeradas em ordem fixa; conclusão antes das notas metodológicas.
- Cada figura e cada tabela DEVE ter, logo abaixo, a legenda com a fonte dos dados: os conjuntos do ONS usados, com o
  identificador da usina e a data de obtenção, e as conferências com o resultado; ou "calculado neste relatório a
  partir de", quando for derivada.
- O PDF e o Markdown DEVEM ter o mesmo conteúdo, na mesma ordem. A planilha DEVE trazer todas as tabelas calculadas e
  uma aba com a origem de cada aba.
- Toda figura DEVE ser produzida com `seaborn`, com paleta, tipografia, tamanhos e resolução definidos de forma
  centralizada; a paleta DEVE ser conferida para leitores com deficiência de visão de cores.

## Requisitos Técnicos

1. **Linguagem e dependências**:
   - Python 3.11 ou mais recente, em ambiente virtual (`venv`), com código modular, tipado, documentado e conforme a
     PEP 8.
   - Só as dependências efetivamente usadas, versionadas em `requirements.txt`.
   - Regras de negócio e manipulação de dados só em Python, nunca em scripts de shell.
2. **Windows e PowerShell**: comandos, exemplos e caminhos DEVEM funcionar no Windows com PowerShell.
3. **Gravação segura**:
   - Cada arquivo de dados da usina gravado pela Coleta ou pelo Tratamento DEVE manter uma cópia `.bak` da versão
     imediatamente anterior, feita antes da escrita.
   - A gravação DEVE ser conferida no disco; se falhar, o arquivo anterior é restaurado.
   - Os resultados da Conferência e das Análises e os relatórios não têm `.bak`, porque são regenerados a partir dos
     dados tratados. Manifestos e dicionários também não, porque as versões deles já são preservadas pela Coleta.
4. **Versões dos arquivos brutos**: no máximo duas versões anteriores por arquivo republicado pelo ONS, as mais
   recentes.
5. **Cópias de segurança do projeto**:
   - No máximo duas, as mais recentes, sem os dados brutos.
   - A mais antiga só sai depois de a nova estar completa e conferida; se a criação falhar, nenhuma é excluída.
   - Nenhum outro arquivo `.bak` fica solto no projeto.
6. **Pastas**:
   - Dados brutos do ONS compartilhados por todas as usinas, em `data/raw/`.
   - Resultados de cada etapa separados por usina, em `data/usinas/<slug>/<etapa>/`; relatórios em `reports/<slug>/`.
   - Documentos de referência fora do controle de versões: os da usina em `usinas/<slug>/documentos/`, os gerais em
     `referencias/`.
7. **Log**: log estruturado na saída padrão, com o arquivo processado, as linhas lidas, os registros extraídos, o tempo e
   as exceções de rede e de leitura. O nível escolhido na linha de comando DEVE valer para todos os módulos executados
   na chamada.

## Fluxo de Desenvolvimento e Qualidade

1. **Testes**:
   - Testes automatizados DEVEM cobrir cada etapa e o perfil da usina e rodar sem rede, com dados sintéticos.
   - Nenhum comportamento coberto por teste DEVE perder a cobertura.
2. **Entrega**:
   - Nenhuma entrega sem a suíte aprovada e sem conferir a execução real e o log.
   - Uma mudança que não deveria alterar o relatório DEVE ser conferida com a comparação do relatório novo com o de
     referência.
3. **Recuperação**: o último estado íntegro DEVE ser recuperável pela gravação segura, pelas cópias de segurança e pelo
   controle de versões.

## Governança

1. **Precedência**: esta constituição prevalece sobre as specs, e as specs sobre o código. Um conflito se resolve
   mudando o documento de menor precedência ou, quando o princípio deve mudar, alterando antes a constituição.
2. **Mudanças**:
   - Toda mudança começa pela spec da etapa afetada, e pela constituição quando um princípio muda. Depois seguem o
     plano, as tarefas e a implementação.
   - Spec nova só para uma etapa nova.
   - Ao concluir, as tarefas saem da spec.
   - Mudanças na constituição e nas specs, e a exclusão de arquivos do usuário, dependem da aprovação do usuário.
3. **Histórico**: fica no controle de versões do projeto, não neste arquivo nem nas specs.
4. **Versionamento semântico**:
   - **MAJOR**: remoção ou redefinição incompatível de um princípio.
   - **MINOR**: princípio ou seção nova, ou ampliação relevante de uma regra.
   - **PATCH**: redação e esclarecimentos sem mudança de escopo.
5. **Conformidade**: todo plano de implementação DEVE conferir a aderência a esta constituição antes do código.

**Version**: 2.0.0 | **Ratified**: 2026-09-30 | **Last Amended**: 2026-10-07
