# Análise de Desempenho de Usinas com Dados Abertos do ONS — Constituição

Este projeto gera, para uma usina de cada vez, um relatório de desempenho operacional a partir dos dados abertos do
Operador Nacional do Sistema Elétrico (ONS), para subsidiar a fiscalização.

- **Usinas atendidas**: as que esses dados cobrem, ou seja, hidrelétricas (UHE, PCH e CGH), térmicas (UTE), nucleares
  (UTN), eólicas (EOL) e solares (UFV).
- **Geração distribuída** (MMGD): o ONS a publica só em agregado, por isso entra apenas como panorama.
- **Produtos**:
  - o relatório de uma usina, em PDF, em Markdown e em planilha, com as figuras;
  - o relatório de carteira, que reúne as usinas de um estado ou de um tipo.
- **Origem do conteúdo**: todo o conteúdo vem dos dados, do perfil da usina e das regras gerais do projeto.

O trabalho segue um único fluxo de cinco etapas. Cada etapa tem uma spec, na mesma ordem:

| Etapa | O que faz | Spec |
|---|---|---|
| 1. Coleta de dados | varre o portal do ONS, baixa e versiona os arquivos e os dicionários de dados, mantém o catálogo de usinas, extrai a usina e audita a extração | `specs/001-coleta-dados/` |
| 2. Tratamento de dados | padroniza, valida, alinha os horários e grava os dados tratados | `specs/002-tratamento-dados/` |
| 3. Conferência | confere as bases entre si e refaz os indicadores oficiais | `specs/003-conferencia/` |
| 4. Análises | calcula indicadores, eventos, perfis, constatações, a conclusão e os dados de cada figura | `specs/004-analises/` |
| 5. Geração do relatório | produz as figuras, o PDF, o Markdown, a planilha e o relatório de carteira | `specs/005-geracao-relatorio/` |

## Core Principles

### I. Desenvolvimento orientado por especificação, uma spec por etapa

- Nenhum código DEVE ser escrito sem spec aprovada. O ciclo é o do Spec Kit: especificar, planejar, dividir em
  tarefas, implementar e convergir.
- Cada etapa do fluxo DEVE ter uma única spec. Ela descreve o funcionamento atual completo da etapa, para todos os
  tipos de usina: objetivo, entradas e saídas, requisitos, critérios de aceitação e decisões do usuário.
- O que vale só para um tipo de usina DEVE ficar na spec da etapa, identificado pelo tipo. NÃO DEVE haver spec por
  tipo de usina nem spec que remende outra.
- Cada etapa DEVE ler só os resultados gravados pelas etapas anteriores e gravar os seus. Só a Coleta, que também
  monta o catálogo de usinas, acessa o portal do ONS. Uma etapa sem os resultados das anteriores DEVE parar sem gravar
  nada e indicar a etapa a executar antes.

### II. Relatório fiel aos dados

- Todo número, nome e frase do relatório DEVE ser gerado a partir dos dados, do perfil da usina ou das regras gerais.
  Nenhum valor, nome de usina ou conclusão fica fixo no código ou no texto.
- As constatações DEVEM descrever fatos dos dados, sem parecer: nada de "satisfatório", "insatisfatório", "cumpre",
  "descumpre" ou equivalentes. Cada constatação aparece uma única vez, no início da sua seção.
- **Conclusão**:
  - DEVE ser gerada por um catálogo de regras declaradas, com os limiares descritos nas notas metodológicas. As regras
    comuns valem para todas as usinas; as próprias de um tipo valem igualmente para todas as usinas desse tipo;
  - aponta indícios, o que confirmar com o agente e o que verificar em campo;
  - NÃO DEVE afirmar causa nem avaliar o desempenho da usina.
- Uma seção, figura, conferência ou regra cuja base não existe para a usina, para o seu tipo ou para a sua modalidade
  de operação DEVE ser omitida, nunca preenchida com suposição.
- Nenhum documento em elaboração ou modelo de documento DEVE ser citado como fonte.

### III. Uma usina por execução, definida pelo perfil

- Cada execução das cinco etapas DEVE tratar de uma única usina, definida pelo seu perfil
  (`usinas/<slug>/perfil.toml`).
- O perfil DEVE declarar o tipo da usina (UHE, PCH, CGH, UTE, UTN, EOL ou UFV) e reunir tudo o que é próprio dela:
  - nome, estado e modalidade de operação no ONS;
  - o identificador de extração e o campo de conferência em cada conjunto do ONS que a cobre e, quando ela pertence a
    um conjunto de usinas, o identificador do conjunto;
  - os campos próprios do tipo e os parâmetros técnicos que o ONS não publica, cada um com a fonte e a data;
  - as características da usina usadas nas análises.
- O tipo DEVE definir os conjuntos coletados, as seções do relatório e as regras da conclusão que se aplicam, conforme
  as specs das etapas.
- As regras gerais (limiares, tolerâncias, metas, catálogos da conclusão) DEVEM ser as mesmas para todas as usinas do
  mesmo tipo e ficar separadas do perfil.
- Um perfil incompleto ou incoerente DEVE ser recusado antes da coleta, com a lista de todos os problemas.
- **Catálogo de usinas**: DEVE ser montado a partir do cadastro e dos conjuntos do ONS e mostrar, para cada usina, o
  tipo, a modalidade de operação, o estado e os conjuntos que a cobrem. O catálogo serve para escolher a usina e para
  montar o rascunho do perfil.
- **Perfil montado do cadastro**: DEVE ser conferido pelo usuário antes do primeiro uso. Ele confirma os
  identificadores e completa os parâmetros técnicos com a fonte.
- Os homônimos DEVEM ser excluídos pelos identificadores do perfil, nunca pelo nome. Dados de outra usina só podem
  aparecer como contexto explícito e identificado, como um agregado do subsistema.
- **Relatório de carteira**: é um produto próprio, que reúne as usinas de um estado ou de um tipo a partir dos
  resultados já gravados de cada uma, sem refazer as etapas de nenhuma. Ele compara e ordena indicadores e indícios,
  sem atribuir nota ou parecer de desempenho.

### IV. Coleta completa e rastreável

- **Fonte**: a Coleta DEVE acessar só o portal de dados abertos do ONS. Fontes de outras instituições, como ANEEL e
  CCEE, só podem entrar no fluxo com mudança desta constituição.
- **Varredura**: a Coleta DEVE inspecionar todos os arquivos publicados de cada conjunto do ONS usado, sem supor data
  de início de operação nem descartar arquivo por heurística de ano.
- **Período da análise**: DEVE ser definido pela série de referência do tipo da usina, declarada na spec da Coleta.
  Quando o tipo não tem base própria, a referência é a série de geração verificada da usina. Nos demais conjuntos,
  entram todos os arquivos que se sobrepõem a esse período.
- **Ausências**: dias, meses ou arquivos ausentes no portal DEVEM ser listados, nunca presumidos ou interpolados.
- **Download e versões**: só o que é novo ou mudou no portal DEVE ser baixado, conforme o manifesto de versões do
  catálogo. Os arquivos brutos DEVEM ser preservados; quando o ONS republica um arquivo, a versão anterior é guardada.
- **Dicionários**: os dicionários de dados publicados pelo ONS (PDF e JSON) DEVEM ser obtidos a cada coleta e
  guardados com os dados brutos, com a versão anterior preservada quando o conteúdo mudar, sem novo download dos dados
  do conjunto.
- **Extração**:
  - DEVE usar o identificador e o campo de conferência do perfil, nunca o nome do agente;
  - as linhas em que só um dos dois confere, as linhas irregulares e os valores inválidos DEVEM ser contados na
    auditoria da extração, sem interrupção silenciosa;
  - toda linha extraída mantém o arquivo de origem.

### V. Tratamento sem descarte

- As regras de consistência e de plausibilidade DEVEM sinalizar os registros, nunca excluí-los dos dados tratados.
  A spec de cada etapa declara o que um registro ou um campo sinalizado deixa de alimentar, e o relatório informa as
  sinalizações.
- A convenção de horário de cada conjunto, o tratamento de duplicatas e o recorte do período DEVEM estar declarados
  na spec do Tratamento e ser aplicados a todos os conjuntos, de modo que as bases fiquem alinhadas no mesmo intervalo
  de tempo.
- As ausências DEVEM ser listadas por conjunto.

### VI. Conferência entre fontes

- Sempre que duas bases trazem a mesma grandeza, ou que um indicador oficial pode ser refeito a partir dos dados, a
  etapa de Conferência DEVE comparar as duas e registrar o resultado: bases, período, quantidade comparada,
  coincidências, divergências e tolerância.
- Uma conferência cuja base não existe para a usina, para o seu tipo ou para o nível em que o ONS publica os dados
  dela DEVE ser registrada como não aplicável, com o motivo.
- Uma conferência com meta declarada que não a atinge DEVE interromper o fluxo completo. Se as etapas seguintes forem
  executadas à parte, elas omitem o que depende dessa conferência.
- O relatório DEVE citar os resultados das conferências nas legendas. Conferências feitas fora do fluxo, que ele não
  reproduz, NÃO DEVEM ser citadas no relatório.

### VII. Relatório padronizado

- **Estrutura**: o relatório de uma usina DEVE ter a estrutura fixa definida na spec da Geração do relatório:
  - capa com identificação, parâmetros, indicadores e sumário;
  - as seções comuns a todos os tipos e as seções próprias do tipo, numeradas em ordem fixa;
  - a conclusão antes das notas metodológicas.
- **Legendas**: cada figura e cada tabela DEVE ter, logo abaixo, a legenda com a fonte dos dados:
  - os conjuntos do ONS usados, com o identificador da usina e a data de obtenção, e as conferências com o resultado;
  - ou "calculado neste relatório a partir de", quando for derivada.
- **Formatos**: o PDF e o Markdown DEVEM ter o mesmo conteúdo, na mesma ordem. A planilha DEVE trazer todas as tabelas
  calculadas e uma aba com a origem de cada aba.
- **Figuras**: toda figura DEVE ser produzida com `seaborn`, com paleta, tipografia, tamanhos e resolução definidos de
  forma centralizada; a paleta DEVE ser conferida para leitores com deficiência de visão de cores.
- **Carteira**: o relatório de carteira DEVE seguir as mesmas regras de fonte, legendas, formatos e figuras.

### VIII. Granularidade declarada

- **Nível do dado**: o ONS publica cada série num de três níveis: da usina, do conjunto de usinas (modalidade Tipo
  II-C) ou de um agregado (Tipo III e MMGD). Todo número do relatório DEVE ser identificado pelo nível em que é
  publicado.
- **Sem extrapolação**: um número de conjunto ou de agregado NÃO DEVE ser apresentado como da usina nem dividido entre
  as usinas por suposição. Quando a grandeza só existe num nível superior, o relatório DEVE dizer isso.
- **Análise sem dado da usina**: o que o tipo ou a modalidade não permite analisar com dados da própria usina DEVE ser
  omitido, com a explicação nas notas metodológicas.
- **MMGD**: aparece só como panorama agregado, do subsistema ou da área em que o ONS a publica, nunca como relatório
  de uma usina.

### IX. Relatórios aprovados protegidos

- **Referência**: todo relatório aprovado pelo usuário passa a ser a referência daquela usina e DEVE ser guardado,
  com a data de geração fixa, junto às cópias de segurança do projeto.
- **Comparação**: toda mudança de código DEVE ser conferida com a comparação dos relatórios de referência com os
  gerados pela mudança. A conferência é feita ao fim de cada fase e antes de cada entrega.
- **Diferença**: só é aceita com aprovação do usuário. Com a aprovação, o relatório novo passa a ser a referência, e a
  anterior permanece no controle de versões.

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
   - Os resultados da Conferência e das Análises, os relatórios e o catálogo de usinas não têm `.bak`, porque são
     regenerados. Manifestos e dicionários também não, porque as versões deles já são preservadas pela Coleta.
4. **Versões dos arquivos brutos**: no máximo duas versões anteriores por arquivo republicado pelo ONS, as mais
   recentes.
5. **Cópias de segurança do projeto**:
   - No máximo duas, as mais recentes, sem os dados brutos, com os relatórios de referência.
   - A mais antiga só sai depois de a nova estar completa e conferida; se a criação falhar, nenhuma é excluída.
   - Nenhum outro arquivo `.bak` fica solto no projeto.
6. **Pastas**:
   - Dados brutos do ONS compartilhados por todas as usinas, em `data/raw/`; catálogo de usinas em `data/catalogo/`.
   - Resultados de cada etapa separados por usina, em `data/usinas/<slug>/<etapa>/`; relatórios em `reports/<slug>/`;
     relatórios de carteira em `reports/carteiras/<nome>/`.
   - Documentos de referência fora do controle de versões: os da usina em `usinas/<slug>/documentos/`, os gerais em
     `referencias/`.
7. **Log**: log estruturado na saída padrão, com o arquivo processado, as linhas lidas, os registros extraídos, o
   tempo e as exceções de rede e de leitura. O nível escolhido na linha de comando DEVE valer para todos os módulos
   executados na chamada.

## Fluxo de Desenvolvimento e Qualidade

1. **Testes**:
   - Testes automatizados DEVEM cobrir cada etapa, o perfil e o catálogo de usinas e rodar sem rede, com dados
     sintéticos.
   - Cada tipo de usina suportado DEVE ter uma usina fictícia testada de ponta a ponta, sem valores de usina real no
     código.
   - Nenhum comportamento coberto por teste DEVE perder a cobertura.
2. **Entrega**:
   - Nenhuma entrega sem a suíte aprovada e sem conferir a execução real e o log.
   - Toda entrega DEVE incluir a comparação dos relatórios de referência (princípio IX).
3. **Recuperação**: o último estado íntegro DEVE ser recuperável pela gravação segura, pelas cópias de segurança e
   pelo controle de versões.

## Governança

1. **Precedência**: esta constituição prevalece sobre as specs, e as specs sobre o código. Um conflito se resolve
   mudando o documento de menor precedência ou, quando o princípio deve mudar, alterando antes a constituição.
2. **Mudanças**:
   - Toda mudança começa pela spec da etapa afetada, e pela constituição quando um princípio muda. Depois seguem o
     plano, as tarefas, a implementação e a convergência.
   - **Spec de mudança temporária**: uma mudança que atinge várias etapas PODE usar uma spec de mudança, numerada
     depois das specs das etapas. Ela descreve a mudança, os ajustes em cada spec de etapa, o plano e as tarefas. Ao
     concluir, os ajustes DEVEM estar incorporados às specs das etapas, e a spec de mudança é excluída.
   - Spec nova permanente só para uma etapa nova.
   - Ao concluir, as tarefas saem da spec.
   - Mudanças na constituição e nas specs, a aceitação de diferença num relatório de referência e a exclusão de
     arquivos do usuário dependem da aprovação do usuário.
3. **Histórico**: fica no controle de versões do projeto, não neste arquivo nem nas specs.
4. **Versionamento semântico**:
   - **MAJOR**: remoção ou redefinição incompatível de um princípio.
   - **MINOR**: princípio ou seção nova, ou ampliação relevante de uma regra.
   - **PATCH**: redação e esclarecimentos sem mudança de escopo.
5. **Conformidade**: todo plano de implementação DEVE conferir a aderência a esta constituição antes do código.

**Version**: 3.0.0 | **Ratified**: 2026-09-30 | **Last Amended**: 2026-10-09
