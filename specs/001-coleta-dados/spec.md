# Spec da Etapa 1: Coleta de dados

**Etapa**: 1 de 5 · **Status**: aprovada · **Atualizada em**: 2026-10-23

**Fluxo**: Coleta de dados → Tratamento de dados → Conferência → Análises → Geração do relatório

## Objetivo

A Coleta de dados obtém do portal de dados abertos do ONS os arquivos dos conjuntos que cobrem a usina definida no perfil, guarda-os com as versões anteriores e os dicionários de dados, e extrai deles só as linhas dessa usina. Atende qualquer usina que os dados abertos do ONS cobrem: UHE, PCH, CGH, UTE, UTN, EOL e UFV. O tipo e a cobertura declarados no perfil definem os conjuntos obtidos e a série de referência, que define o período; na UHE, são os dez conjuntos usados desde o início do projeto, com a Energia Vertida Turbinável (EVT) como série de referência. Cada linha é extraída pelo identificador da usina no conjunto e conferida por um segundo campo, e cada arquivo lido entra na auditoria. A Coleta também monta o catálogo de usinas do ONS (comando `usinas`) e, a partir dele, o rascunho do perfil de uma usina (comando `perfil`). É a única etapa que acessa o portal. Esta spec reúne também as regras comuns às cinco etapas: linha de comando, códigos de saída, perfil da usina, manifesto da etapa (`etapa.json`), comando `completo` e cópia de segurança do projeto.

## Entradas e saídas

**Lê**
- o perfil da usina, em `usinas/<slug>/perfil.toml` (FR-006 a FR-009 e FR-056);
- o catálogo e os arquivos do portal de dados abertos do ONS, exceto com `--sem-portal`;
- os arquivos já baixados em `data/raw/`;
- no comando `perfil`, só o catálogo de usinas, em `data/catalogo/` (FR-053).

**Grava em `data/raw/`**, pasta compartilhada por todas as usinas (FR-030):
- os arquivos de dados de cada conjunto, na pasta do conjunto (FR-016 e FR-049);
- o manifesto de versões `_manifesto_ons.json`, em cada pasta (FR-027);
- `_dicionarios/`, com os dicionários de dados e o manifesto deles (FR-031);
- `_versoes_anteriores/`, com no máximo duas versões anteriores por arquivo (FR-028 e FR-029).

**Grava em `data/catalogo/`**, com o comando `usinas` (FR-051): `usinas.csv`, `conjuntos.csv`, `cobertura.csv`, `planejamento.csv`, `programacao.csv`, `agregados.csv` e `catalogo.json`, por inteiro e sem `.bak`.

**Grava `usinas/<slug>/perfil.toml`**, com o comando `perfil`, só quando o perfil não existe: o rascunho, com `situacao = "rascunho"` (FR-053).

**Grava em `data/usinas/<slug>/coleta/`**, pasta da usina (FR-047). Cada usina tem só os arquivos dos conjuntos que a Coleta obtém para ela (FR-016):

| Arquivo | Conteúdo | Usinas |
|---|---|---|
| `evt_extraido.csv` | linhas da usina na EVT, consolidadas (FR-041) | hidrelétrica com EVT |
| `indicadores_extraido.parquet` | linhas da usina nos dois conjuntos de indicadores por unidade geradora e nos dois de taxas TEIFa e TEIP, com o conjunto de origem (FR-042) | com os indicadores |
| `programacao_extraido.parquet` | geração programada da usina, ou do conjunto, por dia e patamar (FR-043) | com a programação |
| `disponibilidade_extraido.parquet`, `hidrologia_extraido.parquet`, `geracao_extraido.parquet` | linhas da usina nos conjuntos horários, com o instante como publicado (FR-044); na Geração por usina, a série da usina ou do conjunto (FR-054) | com o conjunto |
| `despacho_extraido.parquet`, `cvu_extraido.parquet`, `cmo_extraido.parquet` | despacho térmico por motivo, CVU e CMO semanal do subsistema (FR-055) | UTE e UTN |
| `fator_capacidade_extraido.parquet`, `restricao_detalhe_extraido.parquet`, `restricao_razao_extraido.parquet` | fator de capacidade e restrição por constrained-off, com detalhe e com a razão (FR-057) | EOL e UFV |
| `restricao_membros_extraido.parquet` | restrição com detalhe das outras usinas do conjunto, como contexto identificado (FR-057) | EOL e UFV com `[[identificacao.membros]]` |
| `cadastro_ficha.csv` | ficha da usina no cadastro do ONS (FR-045) | todas |
| `capacidade_ficha.csv` | unidades geradoras da usina na Capacidade de geração (FR-054) | com `[cobertura]` |
| `composicao_conjunto.csv` | composição do conjunto da usina, com as datas de entrada e de saída (FR-054) | em conjunto |
| `capacidade_membros.csv` | unidades geradoras das usinas da composição no período (FR-060) | em conjunto |
| `tipo_publicado.csv` | tipo e combustível publicados na série do conjunto, por trecho (FR-061) | série de referência do conjunto |
| `geracao_complemento.parquet`, `trechos.csv` | modalidade e nível de cada hora; trechos do período (FR-054) | sem EVT |
| `auditoria_evt.csv` | auditoria da EVT, uma linha por arquivo (FR-046) | hidrelétrica com EVT |
| `auditoria_indicadores.csv` | auditoria dos quatro conjuntos de indicadores e taxas, uma linha por arquivo, com o conjunto (FR-046) | com os indicadores |
| `auditoria_programacao.csv` | auditoria da Programação diária, uma linha por dia com arquivo publicado no período (FR-046) | com a programação |
| `auditoria_disponibilidade.csv`, `auditoria_hidrologia.csv`, `auditoria_geracao.csv` | auditoria dos conjuntos horários, uma linha por arquivo, com o período e a data de publicação (FR-046) | com o conjunto |
| `auditoria_despacho.csv`, `auditoria_cvu.csv`, `auditoria_cmo.csv`, `auditoria_fator_capacidade.csv`, `auditoria_restricao_detalhe.csv`, `auditoria_restricao_razao.csv`, `auditoria_restricao_membros.csv` | auditoria de cada conjunto, com as colunas da auditoria dos conjuntos horários (FR-046) | com o arquivo extraído |
| `auditoria_composicao.csv`, `auditoria_capacidade.csv`, `auditoria_capacidade_membros.csv` | auditoria da leitura do arquivo único de cada cadastral (FR-046 e FR-060) | com o arquivo extraído |
| `auditoria_cadastro.csv` | auditoria da leitura do cadastro, com as linhas que têm o CEG do perfil (FR-046) | todas |
| `dicionarios.csv` | registro dos dicionários de dados dos conjuntos da usina (FR-032) | todas |
| `datas_obtencao.csv` | por conjunto, os arquivos registrados, a publicação e a obtenção mais recentes, só do escopo da usina (FR-050) | todas |
| `dicionario_evt.json` | cópia do dicionário de dados da EVT (FR-050) | hidrelétrica com EVT |
| `etapa.json` | manifesto da etapa, com o resumo da coleta (FR-011 e FR-048) | todas |

**Comandos**
- `python -m src coleta --usina <slug> [--sem-portal] [--forcar-download] [--log-level <nível>]`:
  - `--sem-portal`: não consulta o portal e extrai só dos arquivos locais (FR-021);
  - `--forcar-download`: baixa de novo todos os arquivos de dados (FR-022).
- `python -m src usinas [--estado <UF>] [--tipo <tipo>] [--modalidade <modalidade>] [--sem-portal] [--forcar-download] [--log-level <nível>]`: monta o catálogo de usinas e lista as usinas do filtro (FR-051).
- `python -m src perfil --ceg <CEG> [--slug <slug>] [--log-level <nível>]`: grava o rascunho do perfil, só a partir do catálogo (FR-053).

**Códigos de saída**: a coleta termina com 0 (sucesso), 1 (erro), 2 (arquivo de dados não obtido ou não lido, ou usina sem registro na série de referência, no cadastro ou na composição do conjunto declarado) ou 4 (perfil inválido); o `usinas`, com 0, 1 ou 2; o `perfil`, com 0, 1, 2, 5 ou 6. A tabela completa, comum às cinco etapas, está na FR-005.

**Quem usa as saídas**: o Tratamento de dados lê os extraídos, as auditorias, os trechos e a cópia do dicionário da EVT. As Análises e a Geração do relatório leem as datas de obtenção, o registro dos dicionários, as auditorias, a ficha do cadastro, os trechos, a composição do conjunto e as unidades geradoras, que alimentam a cobertura dos dados, as legendas de fonte e as notas do relatório. As etapas 2 a 5 não leem `data/raw/` (FR-050). O comando `perfil` e o relatório de carteira (spec da Geração do relatório) leem o catálogo de usinas.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Coletar os dez conjuntos e extrair a usina do perfil (Priority: P1)

Como fiscal da AGEMS, quero um comando que obtenha do portal do ONS só o que é novo ou mudou nos dez conjuntos usados no relatório e extraia deles as linhas da minha usina, identificada pelo perfil. Assim as etapas seguintes trabalham sobre dados completos, da usina certa e com origem rastreável.

**Why this priority**: tudo o que o relatório mostra vem destes dados. Um registro perdido, ou de outra usina, compromete todos os números.

**Independent Test**: com o catálogo e os arquivos simulados, sem rede, executar a coleta duas vezes e conferir os arquivos baixados, os manifestos e os extraídos, e que a segunda execução não baixa nenhum arquivo de dados.

**Acceptance Scenarios**:

1. **Given** o catálogo com arquivos novos e arquivos já baixados na versão publicada, **When** a coleta é executada, **Then** só os novos e os que mudaram são baixados, os demais são reaproveitados, e todos ficam registrados no manifesto da pasta.
2. **Given** nenhuma novidade no portal, **When** a coleta é executada de novo, **Then** nenhum arquivo de dados é baixado, só os dicionários são obtidos, e os extraídos têm o mesmo conteúdo.
3. **Given** a opção `--sem-portal`, **When** a coleta é executada, **Then** o portal não é consultado, a extração usa só os arquivos locais e nada muda em `data/raw/`.
4. **Given** arquivos com linhas de homônimos (perfil da São Domingos: PCH São Domingos I e II, em GO, e CGH São Domingos, em SC, entre outras), **When** a usina é extraída, **Then** só entram as linhas com o identificador e a conferência do perfil.
5. **Given** a mesma usina sob dois nomes de agente (perfil da São Domingos: CGT ELETROSUL até 02/2026 e AXIA SUL a partir de 03/2026), **When** a EVT é extraída, **Then** a série é contínua, porque o nome do agente não entra na identificação.
6. **Given** o mesmo instante da EVT em dois arquivos, **When** a EVT é consolidada, **Then** fica um único registro, o do arquivo lido por último, e a duplicata com valores diferentes é avisada no log, com os dois arquivos.
7. **Given** um conjunto publicado em dois formatos, com o formato compacto ausente em parte dos meses (perfil da São Domingos: Disponibilidade por usina de 08/2018 a 12/2022), **When** a coleta é executada, **Then** cada mês do período é obtido num formato que o contém.
8. **Given** um conjunto com arquivos antes e depois do período da EVT, **When** a coleta é executada, **Then** só os arquivos que se sobrepõem ao período são obtidos e lidos.
9. **Given** o cadastro de Modalidade das usinas, **When** a usina é extraída, **Then** a ficha traz a data da consulta e a quantidade de homônimos, e nenhum homônimo é extraído.
10. **Given** um arquivo que não pode ser baixado depois das três tentativas, **When** a coleta termina, **Then** o arquivo fica na auditoria como `FALHA`, com o motivo, o manifesto guarda o que foi sincronizado e a coleta termina com código 2; com o catálogo inacessível, ela termina com código 1.
11. **Given** duas usinas com perfil, **When** a coleta de cada uma é executada, **Then** os arquivos brutos baixados para a primeira servem à segunda sem novo download, e os resultados ficam na pasta `data/usinas/<slug>/coleta/` de cada uma.

---

### User Story 2 - Auditoria de cada arquivo lido (Priority: P1)

Como fiscal, quero uma auditoria com uma linha por arquivo lido, com as contagens de linhas e a situação do arquivo. Assim comprovo que todos os arquivos publicados foram verificados, inclusive os que não têm a usina, e vejo qualquer linha que confere só em parte ou que veio em formato irregular.

**Why this priority**: é a prova de varredura completa exigida na fiscalização e a forma de detectar identificador errado no perfil ou mudança de cadastro no ONS.

**Independent Test**: processar arquivos sintéticos com linhas da usina, de homônimos e que conferem só em parte, linhas curtas e longas, um arquivo em Latin-1 e um corrompido, e conferir cada contagem da auditoria e o código de saída.

**Acceptance Scenarios**:

1. **Given** a coleta concluída, **When** a auditoria é aberta, **Then** cada arquivo lido tem uma linha com linhas lidas, linhas irregulares, linhas da usina, linhas só com o identificador, linhas só com a conferência, valores inválidos e situação, onde cada contagem se aplica.
2. **Given** um arquivo sem nenhuma linha da usina (perfil da São Domingos: EVT de 2015, 2016 e 2017), **When** é lido, **Then** fica na auditoria como `SEM_REGISTROS`, e a coleta segue, sem falha.
3. **Given** uma linha com só o identificador ou só a conferência, **When** a extração termina, **Then** a linha não é extraída, entra na contagem do seu caso, e o log avisa, com o nome do arquivo, para verificar mudança de cadastro no ONS.
4. **Given** linhas não vazias com número de campos diferente do cabeçalho, **When** o arquivo é lido, **Then** elas não são extraídas, são contadas, e o log informa o arquivo, a quantidade e o número das primeiras.
5. **Given** um arquivo vazio, corrompido ou sem as colunas de identificação, **When** é lido, **Then** fica como `FALHA`, os demais arquivos são lidos, os resultados são gravados e a coleta termina com código 2.
6. **Given** um arquivo CSV que não está em UTF-8, **When** é lido, **Then** é relido inteiro em Latin-1, e a auditoria da EVT registra a codificação usada.
7. **Given** um arquivo da Programação diária com número de patamares da usina diferente de 48, ou com a data interna diferente da do nome, **When** é lido, **Then** a auditoria o marca como `INCOMPLETO` ou registra a divergência da data.

---

### User Story 3 - Perfil da usina como entrada, com recusa do perfil inválido (Priority: P1)

Como fiscal, quero informar a usina por um perfil com o tipo, a modalidade, os identificadores dela em cada conjunto do ONS, a cobertura de cada conjunto e os parâmetros técnicos com a fonte. Quero que um perfil incompleto ou incoerente seja recusado antes da coleta, com a lista de todos os problemas. Assim uso o mesmo fluxo para outra usina, de qualquer tipo, sem mexer no código e sem produzir um relatório com dados errados.

**Why this priority**: o perfil é a entrada de todas as etapas; um erro nele contamina tudo o que vem depois.

**Independent Test**: executar a coleta com o perfil válido de uma usina fictícia de cada tipo e com perfis com problemas, e conferir o código 4, a mensagem e que nada foi gravado.

**Acceptance Scenarios**:

1. **Given** um perfil válido (perfil da São Domingos), **When** um comando com `--usina sao_domingos` é executado, **Then** o perfil é aceito e a etapa segue.
2. **Given** o perfil de uma UHE sem `parametros.garantia_fisica_mwmed`, **When** qualquer comando com `--usina` começa, **Then** ele termina com código 4 antes da coleta, sem gravar nada, e a mensagem cita o campo.
3. **Given** um perfil em que a potência unitária vezes o número de unidades geradoras difere da potência instalada em mais de 0,1 MW, **When** o comando começa, **Then** o perfil é recusado com código 4, e a mensagem cita a incoerência.
4. **Given** um perfil com vários problemas, **When** o comando começa, **Then** a mensagem lista todos de uma vez, um por linha.
5. **Given** um slug sem pasta em `usinas/`, ou diferente do `usina.slug` do perfil, **When** o comando começa, **Then** o perfil é recusado com código 4.
6. **Given** um perfil sem os campos de texto opcionais, **When** o comando começa, **Then** o perfil é aceito; **Given** um campo de texto opcional presente mas vazio, **Then** o perfil é recusado com código 4.
7. **Given** um perfil em rascunho, **When** qualquer comando com `--usina` começa, **Then** ele termina com código 4, e a mensagem lista os pendentes e os demais problemas.
8. **Given** um perfil com modalidade Tipo III, com um campo que não se aplica ao tipo, com uma chave de `[cobertura]` que não serve ao tipo ou, fora da UHE, sem a `[cobertura]`, **When** o comando começa, **Then** o perfil é recusado com código 4.

---

### User Story 4 - Fluxo de cinco etapas, com um comando e pré-requisitos (Priority: P1)

Como fiscal, quero executar o fluxo inteiro com um comando ou cada etapa sozinha, e quero que uma etapa se recuse a rodar sem o resultado concluído da anterior. Quero também escolher o nível de detalhe do log. Assim refaço só o que preciso, sem misturar resultados de execuções diferentes.

**Why this priority**: é a organização pedida para o projeto; sem ela, uma etapa pode usar dados velhos sem que ninguém perceba.

**Independent Test**: com uma usina fictícia e dados sintéticos, executar `completo`, depois uma etapa sem a anterior, e conferir os códigos de saída, as mensagens e os `etapa.json`.

**Acceptance Scenarios**:

1. **Given** um perfil válido e os dados locais, **When** `python -m src completo --usina <slug> --sem-portal` é executado, **Then** as cinco etapas rodam na ordem, cada uma grava o seu `etapa.json` como `concluida`, e o comando termina com 0.
2. **Given** uma etapa que termina com código diferente de 0 dentro do `completo`, **When** isso ocorre, **Then** o `completo` para ali e termina com o código dela; com o código 3, o `etapa.json` da etapa fica `concluida`, com o código, e a etapa seguinte pode ser executada à parte.
3. **Given** uma usina sem coleta concluída, **When** `python -m src tratamento --usina <slug>` é executado, **Then** ele termina com código 5, nada é gravado, e a mensagem manda executar antes a coleta.
4. **Given** as cinco etapas concluídas, **When** a coleta é executada de novo, **Then** os `etapa.json` das quatro seguintes ficam `desatualizada`, e cada uma recusa rodar (código 5) enquanto a anterior não for refeita.
5. **Given** uma etapa concluída, **When** o `etapa.json` é aberto, **Then** traz a etapa, a usina, a situação, o código de saída, as datas, a etapa anterior usada, os arquivos gravados com o SHA-256 e o resumo.
6. **Given** `--log-level WARNING`, **When** qualquer comando é executado, **Then** nenhuma mensagem informativa aparece, de nenhum módulo; com `DEBUG`, mensagens de depuração podem aparecer em qualquer módulo.
7. **Given** um nível de log ou uma opção inválida, **When** o comando é chamado, **Then** ele é recusado antes de qualquer execução.

---

### User Story 5 - Versões dos arquivos republicados e dicionários de dados (Priority: P2)

Como fiscal, quero que, quando o ONS republicar um arquivo já baixado, a versão anterior seja guardada com a data de publicação, até duas por arquivo. Quero também os dicionários de dados de cada conjunto, obtidos a cada coleta. Assim demonstro com que dados um relatório foi gerado, comparo versões se um número mudar e consulto a definição de cada campo sem acessar o portal.

**Why this priority**: o ONS revisa arquivos já publicados, e sem a versão anterior um relatório entregue não pode ser reproduzido. Os números de uma execução não mudam com isso.

**Independent Test**: simular três republicações de um arquivo com conteúdos diferentes e uma com conteúdo igual, e três obtenções de um dicionário (novo, igual e alterado), conferindo as pastas e os manifestos depois de cada uma.

**Acceptance Scenarios**:

1. **Given** um arquivo registrado no manifesto, **When** o catálogo traz nova data de publicação e o arquivo baixado tem conteúdo diferente, **Then** a cópia anterior vai para `_versoes_anteriores/`, com nome que identifica o arquivo e a data de publicação, e o manifesto registra a versão preservada.
2. **Given** um arquivo republicado com conteúdo idêntico ao local, **When** a coleta é executada, **Then** nenhuma versão é criada, e só o registro do manifesto é atualizado.
3. **Given** um arquivo que já tem duas versões anteriores, **When** uma terceira é preservada, **Then** a mais antiga é excluída, ficam as duas mais recentes, e a exclusão fica registrada no manifesto.
4. **Given** a opção `--forcar-download`, **When** a coleta é executada, **Then** todos os arquivos de dados são baixados de novo, e só os de conteúdo diferente geram versão anterior.
5. **Given** versões anteriores preservadas, **When** a usina é extraída, **Then** só as versões correntes são lidas.
6. **Given** um dicionário de dados igual à cópia local, **When** obtido de novo, **Then** nenhuma versão é criada e o registro indica `INALTERADO`; com o conteúdo alterado, a versão anterior é preservada e o log avisa.
7. **Given** uma falha ao obter um dicionário, ou um conjunto sem dicionário num dos formatos, **When** a coleta termina, **Then** a situação fica no registro, o código de saída não muda, e nenhum arquivo de dados é baixado por causa dos dicionários.

---

### User Story 6 - No máximo duas cópias de segurança do projeto (Priority: P3)

Como fiscal, quero criar com um comando uma cópia de segurança do projeto antes de uma mudança, mantendo no máximo duas cópias, as mais recentes. Assim preservo as versões aprovadas sem acumular cópias.

**Why this priority**: protege o trabalho aprovado, mas não afeta os dados nem o relatório.

**Independent Test**: criar uma cópia quando já existem duas e simular uma falha na criação, conferindo as pastas `_backup_*` depois de cada passo.

**Acceptance Scenarios**:

1. **Given** duas cópias existentes, **When** `python -m src copia-seguranca --motivo <texto>` cria e confere uma nova, **Then** a mais antiga é excluída e ficam duas.
2. **Given** uma falha na criação ou na conferência da nova cópia, **When** ela ocorre, **Then** a cópia incompleta é apagada, nenhuma cópia existente é excluída, e o comando termina com código 1.
3. **Given** uma cópia criada, **When** aberta, **Then** traz o código, os testes, as specs, os relatórios, os relatórios de referência, as configurações do Spec Kit, os perfis, o README e a lista de dependências, mais `LEIA-ME.txt`, `conftest.py` e `copia.json`, e não traz dados nem documentos.

---

### User Story 7 - Catálogo de usinas e rascunho do perfil (Priority: P1)

Como fiscal, quero consultar um catálogo com as usinas do cadastro do ONS, o tipo de cada uma e o que o ONS publica sobre ela, e gerar a partir dele o rascunho do perfil de uma usina, para conferir e completar. Assim começo a análise de uma térmica, eólica, solar ou PCH sem escrever o perfil do zero e sem mexer no código.

**Why this priority**: o catálogo mostra que usinas têm dados para um relatório, e o rascunho traz os identificadores que o ONS publica; o fiscal completa só os parâmetros técnicos e confere.

**Independent Test**: com o cadastro e os conjuntos simulados, sem rede, montar o catálogo, gerar o rascunho de uma UTE e de uma PCH em conjunto, completá-los e conferir que passam na validação do perfil; pedir o rascunho de uma usina Tipo III e o de uma usina que já tem perfil.

**Acceptance Scenarios**:

1. **Given** os dados do ONS, **When** `python -m src usinas --estado MS` é executado, **Then** o catálogo lista as entradas do cadastro do estado (171 em 19/10/2026: UHE 5, PCH 16, CGH 9, UTE 33, UFV 86 e 22 linhas de conjunto), cada uma com nome, CEG, id ONS, tipo, modalidade, potência autorizada, conjunto e a cobertura de cada conjunto de série: própria, do conjunto, agregada ou ausente.
2. **Given** a UTE William Arjona no catálogo, **When** o fiscal gera o perfil pelo CEG, **Then** o rascunho traz tipo, modalidade, nome, estado, subsistema, os identificadores achados, os códigos de programação e de planejamento e as unidades ativas, e os parâmetros técnicos ficam pendentes, cada um pedindo a fonte.
3. **Given** um perfil em rascunho, **When** o fiscal executa qualquer etapa, **Then** a execução é recusada com código 4 antes da coleta, com a lista do que falta conferir ou preencher.
4. **Given** uma usina Tipo III, ou sem dado próprio nem de conjunto no ONS, **When** o fiscal pede o rascunho, **Then** nenhum perfil é criado (código 2), e a mensagem explica que o ONS só publica o agregado e indica o panorama da carteira.
5. **Given** um perfil existente com o mesmo CEG, **When** o fiscal pede o rascunho de novo, **Then** nada é gravado, e o comando mostra as diferenças entre o perfil e o catálogo (código 6, ou 0 sem diferença).
6. **Given** um conjunto que trocou os códigos de programação (Conj. Chapadão, em 07/2025), **When** o rascunho de uma usina dele é gerado, **Then** ele traz os códigos de todo o período, com o primeiro e o último dia de cada um em comentário.

---

### User Story 8 - Coleta de qualquer tipo de usina, pela cobertura do perfil (Priority: P1)

Como fiscal, quero que a Coleta obtenha, para a usina do perfil, só os conjuntos do ONS do tipo dela e com a cobertura declarada, com o período definido pela série de referência do tipo e dividido em trechos quando muda o nível do dado ou a composição do conjunto. Assim a térmica, a eólica, a solar e a PCH em conjunto têm dados completos e identificados pelo nível, e a coleta da UHE não muda.

**Why this priority**: é a base das seções comuns e das próprias de cada tipo; um conjunto de outro tipo ou de outro nível misturaria dados de usinas diferentes.

**Independent Test**: com uma usina fictícia de cada tipo (UHE, PCH, CGH, UTE, UTN, EOL e UFV) e brutos sintéticos, sem rede, executar a coleta e conferir os conjuntos coletados, a série de referência, o período, os trechos e os arquivos de cada tipo.

**Acceptance Scenarios**:

1. **Given** uma UHE sem `[cobertura]` (perfil da São Domingos), **When** a coleta é executada, **Then** ela obtém os dez conjuntos da UHE, e mais nenhum, com os mesmos arquivos e colunas, mais `datas_obtencao.csv` e `dicionario_evt.json`.
2. **Given** uma UTE com geração própria (perfil da William Arjona), **When** a coleta é executada, **Then** a série de referência é a Geração por usina pelo id ONS, varrida em todos os arquivos publicados, o período vai da primeira à última hora com valor, e o despacho, o CVU e o CMO são obtidos, sem a EVT nem a hidrologia.
3. **Given** uma PCH em conjunto sem série própria (perfil da Bandeirante), **When** a coleta é executada, **Then** a série de referência é a Geração por usina do conjunto, só nas horas com a usina na composição (desde 22/08/2019), e `trechos.csv` corta o período em cada mudança da composição.
4. **Given** uma UFV em conjunto com série própria na restrição com detalhe (perfil da Seriemas 1), **When** a coleta é executada, **Then** a série de referência é a geração verificada da usina nessa base, semi-horária, e o fator de capacidade e a razão da restrição vêm do conjunto, com o nível em cada linha.
5. **Given** uma usina em conjunto ausente da composição do conjunto declarado no perfil, **When** a coleta é executada, **Then** ela termina com código 2, sem coletar os demais conjuntos, e a mensagem cita o id do conjunto e o CEG.
6. **Given** um arquivo sem a coluna de conferência de um conjunto que a declara, **When** o arquivo é lido, **Then** ele fica como `FALHA`, com o motivo, e a coleta termina com código 2.

---

### Edge Cases

- **Perfil ausente ou com problema**: o comando termina com código 4 antes de qualquer ação e lista todos os problemas (FR-009).
- **Perfil em rascunho**: toda etapa o recusa com código 4 e lista os pendentes (FR-009).
- **Etapa sem a anterior concluída**: termina com código 5, sem gravar nada, e indica a etapa a executar antes (FR-012).
- **Coleta refeita depois das demais etapas**: as etapas seguintes ficam `desatualizada` e precisam ser refeitas, na ordem (FR-013).
- **ONS republica um arquivo entre duas coletas**:
  - a coleta baixa a nova versão e preserva a anterior, até duas por arquivo (FR-028 e FR-029);
  - as etapas seguintes ficam desatualizadas e refazem o que depende do arquivo;
  - a mudança no relatório é esperada e não conta como regressão.
- **Republicação com o mesmo tamanho**: é detectada pela data de publicação; o conteúdo decide se há versão a preservar.
- **Primeira coleta com arquivos já baixados e sem manifesto**: a cópia com o tamanho publicado é aceita e registrada como arquivo existente, sem versão anterior.
- **Falha ao baixar a nova versão de um arquivo**: a versão local fica intacta, nenhuma versão é movida, e o arquivo vai para a auditoria como `FALHA` (código 2).
- **Arquivos do portal sem linhas da usina** (perfil da São Domingos: EVT de 2015 a 2017): são lidos, ficam na auditoria como `SEM_REGISTROS` e continuam guardados, porque servem a outras usinas.
- **Homônimos e troca de agente**: a extração usa o identificador e a conferência do perfil, nunca o nome do agente; as linhas em que só um dos dois confere vão para a auditoria (FR-036).
- **Nomes e tipos instáveis no ONS** (grafias "Willian" e "William Arjona", "230kV" e "230 kV"; nomes e ids da Geração por usina mudados em 05/2026; o Conj. Chapadão publicado como térmico): a identificação é só pelos códigos, e o tipo vem do prefixo do CEG (FR-035, FR-051 e FR-061).
- **Id publicado com espaços nas pontas** (cadastro do ONS: "CEUFM "): os ids são comparados sem os espaços das pontas, também na ligação dos códigos de programação no catálogo (FR-035 e FR-051).
- **Conjunto sem a usina** (por exemplo, usina fora da Programação diária): os arquivos são lidos e auditados como `SEM_REGISTROS`, o extraído fica vazio e a coleta não falha; as etapas seguintes omitem o que depende dele.
- **Usina sem nenhuma linha na EVT** (identificador errado no perfil, por exemplo): não há período para os demais conjuntos. A coleta grava a auditoria da EVT, que mostra as linhas que conferem só em parte, avisa no log, não coleta os demais conjuntos e termina com código 2.
- **Série de referência sem nenhuma hora com valor**, ou **usina ausente da composição do conjunto declarado no perfil**: a coleta grava a auditoria da série, não coleta os demais conjuntos e termina com código 2 (FR-054).
- **Usina sem série de referência na `[cobertura]`** (nem EVT, nem Geração por usina, nem a restrição com detalhe da usina): a coleta é recusada com código 1, sem coletar nada (FR-054).
- **Usina que mudou de modalidade, de nível ou de conjunto no período**: o período é dividido em trechos, e cada hora traz o nível dela (FR-054).
- **Conjunto cuja composição mudou no período** (Conj. Chapadão: cinco UTE até 30/06/2025): os trechos cortam o período nas datas da composição, com os tipos de cada trecho, e as unidades das usinas da composição dão a potência de cada uma em cada trecho (FR-054 e FR-060).
- **Usina em conjunto com linhas próprias sem valor** (PCH em conjunto na Geração por usina, desde 05/2026): a cobertura é do conjunto, e as linhas sem valor são contadas no resumo, com a primeira e a última hora (FR-048 e FR-052).
- **Térmica com mais de um código de planejamento ou com o código trocado no tempo** (William Arjona: 34 até 08/2018, 334 desde 07/2021 e 434 de 08/2021 a 01/2026): o perfil traz cada código com o período, e a linha do despacho só confere com o código vigente no instante dela (FR-055 e FR-056).
- **Conjunto que troca os códigos de programação** (Conj. Chapadão, em 07/2025): o catálogo lê todos os arquivos da Programação diária, e o rascunho traz os códigos de todo o período (FR-051 e FR-053).
- **Código de programação sem ligação com a usina** (perfil da São Domingos: `PRUHSD` para o id `MSUHSD`): o rascunho deixa o campo pendente e lista os códigos do estado (FR-053).
- **Unidade de uma usina do conjunto com o CEG e outro subsistema**: não é extraída e é contada na auditoria das unidades, com aviso no log (FR-060).
- **Coluna de conferência ausente num arquivo**: o arquivo fica `FALHA`, com o motivo (FR-036).
- **Coluna de valor ausente em parte dos arquivos** (as cinco colunas da fotovoltaica de 05 a 12/2024): a coluna fica vazia, e a ausência vai para a mensagem da auditoria, sem falha do arquivo (FR-058).
- **Usina fora do cadastro**: a coleta grava a auditoria do cadastro e termina com código 2.
- **Cabeçalho com as colunas em outra ordem**: as colunas são localizadas pelo nome.
- **Formato compacto ausente em parte dos meses** (perfil da São Domingos: Disponibilidade por usina de 08/2018 a 12/2022): o mês vem do CSV. A ausência da usina num mês nunca é tirada de um arquivo que não cobre o mês.
- **Mesmo arquivo listado duas vezes no catálogo** (Dados hidrológicos horários de 10/2026, com tamanhos diferentes): fica o recurso com data de publicação ou, em empate, o maior; a repetição vai para o manifesto e, nos conjuntos lidos pelo motor comum, para a auditoria (FR-019).
- **Números publicados como texto em alguns arquivos**: são lidos como número, com vírgula ou ponto decimal; o que não for número fica ausente e é contado como valor inválido.
- **Campos vazios** (nível de jusante e vazão vertida não turbinável, por exemplo): ficam ausentes, nunca zero.
- **Horas ausentes na fonte** (perfil da São Domingos: 04/11/2018 00h, início do horário de verão, ausente na EVT): a coleta não cria nem preenche horas.
- **Série de referência mais curta que a dos outros conjuntos** (restrição eólica desde 10/2021; UFV de MS só desde 08/2026): o período é o da série de referência, e os outros conjuntos são recortados nele.
- **Programação diária**: data interna publicada em dois formatos; dia com patamares faltando (`INCOMPLETO`); patamar repetido no mesmo arquivo (fica a última ocorrência).
- **Dicionário não publicado num formato, ou catálogo de dicionários inacessível**: a situação vai para o registro, sem falha.
- **Perfil existente quando se pede um rascunho novo**: nada é sobrescrito; o comando mostra as diferenças entre o perfil e o catálogo (FR-053).
- **Cópia de segurança com falha**: a cópia incompleta é apagada, e nenhuma cópia existente é excluída.

---

## Requirements *(mandatory)*

### Functional Requirements

As FR-001 a FR-015 e a FR-056 são regras comuns às cinco etapas. As specs das demais etapas trazem só o seu comando, as suas opções, os seus códigos de saída, as suas pastas e o resumo do seu `etapa.json`.

**Fluxo e linha de comando (US4)**

- **FR-001**: O projeto DEVE ter um único fluxo, com cinco etapas nesta ordem: Coleta de dados, Tratamento de dados, Conferência, Análises e Geração do relatório. Cada etapa DEVE usar só os resultados gravados pelas anteriores e gravar os seus para as seguintes. Só a Coleta de dados DEVE acessar o portal do ONS.
- **FR-002**: O fluxo DEVE ter uma única linha de comando, `python -m src <comando> [opções]`, que roda sem interação com o usuário. O slug é o nome da pasta da usina em `usinas/`, e `--usina <slug>` é obrigatório nos comandos de etapa, no `completo`, no `referencia` e no `comparar` com `--referencia`. Os comandos são:

  | Comando | Faz | Opções próprias |
  |---|---|---|
  | `coleta` | Coleta de dados (esta spec) | `--sem-portal`, `--forcar-download` |
  | `tratamento` | Tratamento de dados | nenhuma |
  | `conferencia` | Conferência | nenhuma |
  | `analises` | Análises | nenhuma |
  | `relatorio` | Geração do relatório | `--data-geracao` (spec da Geração do relatório) |
  | `completo` | as cinco etapas, na ordem (FR-003) | as da `coleta` e as do `relatorio` |
  | `usinas` | catálogo de usinas (FR-051); não usa `--usina` | `--estado`, `--tipo`, `--modalidade`, `--sem-portal`, `--forcar-download` |
  | `perfil --ceg <CEG>` | rascunho do perfil, só a partir do catálogo (FR-053); não usa `--usina` | `--slug` |
  | `carteira` | relatório de carteira de um estado, de um tipo ou dos dois, só com os resultados gravados (spec da Geração do relatório); não usa `--usina` | `--estado`, `--tipo` (pelo menos uma das duas), `--data-geracao` |
  | `referencia --usina <slug>` | registra o relatório aprovado da usina como referência (spec da Geração do relatório) | `--data-geracao`, `--aprovado-em` (obrigatórias) |
  | `copia-seguranca --motivo <texto>` | cópia de segurança do projeto (FR-014); não usa `--usina` | nenhuma |
  | `comparar --usina <slug> --referencia <pasta>` | compara o relatório da usina com o de outra pasta (spec da Geração do relatório) | nenhuma |
  | `comparar --todas [--coleta]` | refaz e compara cada relatório de referência; com `--coleta`, refaz também a Coleta (spec da Geração do relatório); não usa `--usina` | `--coleta` |

  NÃO DEVE haver outro ponto de entrada, nem opção para executar ou pular um conjunto do ONS ou parte de uma etapa: os conjuntos da usina fazem parte da coleta.
- **FR-003**: O comando `completo` DEVE executar as cinco etapas na ordem e parar na primeira que não terminar com 0, saindo com o código dela.
- **FR-004**: A opção `--log-level`, comum a todos os comandos, DEVE aceitar `DEBUG`, `INFO`, `WARNING` e `ERROR` (padrão `INFO`) e valer para todos os módulos executados na chamada. O log DEVE sair só na saída padrão, no formato `AAAA-MM-DD HH:MM:SS [NÍVEL] módulo - mensagem`, sem arquivo de log. Ao final de cada etapa, o log DEVE mostrar o resumo da etapa (FR-011) e o caminho da pasta de saída.
- **FR-005**: Os comandos DEVEM terminar com estes códigos de saída, sem códigos além deles:

  | Código | Significado |
  |---|---|
  | 0 | sucesso (no `comparar`, nenhuma diferença; no `perfil`, rascunho gravado ou perfil existente igual ao catálogo) |
  | 1 | erro: catálogo do ONS inacessível, dado que impede a etapa, falha de gravação (com o arquivo restaurado), erro inesperado ou interrupção pelo usuário |
  | 2 | arquivo de dados não obtido ou não lido, ou usina sem registro na série de referência, no cadastro ou na composição do conjunto declarado (Coleta de dados); conjunto cadastral não obtido (`usinas`); CEG fora do catálogo, tipo fora dos sete ou usina só com agregado no ONS (`perfil`); também opção inválida na linha de comando, recusada antes de qualquer execução |
  | 3 | conferência das vazões com a hidrologia abaixo da meta (Conferência) |
  | 4 | perfil da usina inválido, inclusive em rascunho; a mensagem lista os problemas e os pendentes (FR-009) |
  | 5 | etapa anterior sem resultado concluído: ausente, ilegível, com falha, desatualizada ou em formato antigo; nada é gravado (FR-012). No `perfil`, catálogo de usinas ausente ou em formato antigo |
  | 6 | o `comparar` encontrou diferenças; o `perfil` encontrou um perfil existente com diferenças em relação ao catálogo (nada é gravado) |

  Os comandos sem etapa usam os mesmos códigos, assim:

  | Comando | 0 | 1 | 2 | 4 | 5 | 6 |
  |---|---|---|---|---|---|---|
  | `usinas` | catálogo montado e listado, inclusive com o filtro vazio | erro, inclusive o catálogo do ONS inacessível | opção inválida; Modalidade das usinas, Composição dos conjuntos, Capacidade de geração ou Reservatórios não obtido | — | — | — |
  | `perfil` | rascunho gravado, ou perfil existente igual ao catálogo | erro, inclusive o perfil existente ilegível | opção inválida, inclusive o slug; CEG fora do catálogo; tipo fora dos sete; usina Tipo III ou só com agregado | — | catálogo ausente ou em formato antigo | perfil existente com diferenças |
  | `carteira` | carteira gerada | erro | opção inválida, inclusive sem `--estado` nem `--tipo` | — | catálogo ausente, ou nenhuma usina do recorte com as Análises concluídas | — |
  | `referencia` | referência registrada | erro; relatório gerado com outra data; referência atual não commitada; falha na gravação ou na conferência | opção inválida | perfil inválido | relatório ou Coleta da usina ausente ou não concluída | — |
  | `comparar --todas` | nenhuma diferença | erro, inclusive sem referências ou com a Coleta congelada ausente | opção inválida | — | — | alguma diferença |

**Perfil da usina (US3)**

- **FR-006**: Todo valor próprio de uma usina DEVE estar no perfil dela, `usinas/<slug>/perfil.toml`, em UTF-8 e no formato TOML, com comentários (`#`) para registrar a origem de cada valor. O fluxo DEVE receber o perfil como entrada. O perfil declara o tipo e a modalidade da usina, os identificadores dela nos conjuntos do ONS, a cobertura de cada conjunto e os parâmetros técnicos com a fonte. Os campos e a validação de cada um:

  | Campo | Tipo | Validação |
  |---|---|---|
  | `usina.slug` | texto | letras minúsculas, algarismos e `_`; igual ao nome da pasta; não pode ser `carteiras`, que é a pasta das carteiras em `reports/` |
  | `usina.nome` | texto | não vazio; é o nome usado no título e nos textos |
  | `usina.nome_curto` | texto | não vazio; é o nome da usina sem o tipo, usado nas frases sobre homônimos |
  | `usina.estado` | texto | 2 letras maiúsculas |
  | `usina.inicio_operacao_comercial` | inteiro | de 1900 até o ano atual |
  | `usina.tipo` | texto | `UHE`, `PCH`, `CGH`, `UTE`, `UTN`, `EOL` ou `UFV`; igual ao prefixo do CEG |
  | `usina.modalidade` | texto | `TIPO I`, `TIPO II-A`, `TIPO II-B` ou `TIPO II-C`, como no cadastro do ONS; `TIPO III` e `TIPO III (EM DIT)` são recusadas: o ONS só publica o agregado |
  | `usina.situacao` | texto | opcional: `rascunho` ou `conferido`; ausente vale `conferido`; `rascunho` é sempre recusado (FR-009) |
  | `usina.pendentes` | lista de texto | opcional: os campos ainda a preencher; vazia ou ausente quando `conferido` |
  | `usina.subsistema` | texto | `SE`, `S`, `NE` ou `N` (FR-056) |
  | `identificacao.ceg` | texto | no padrão da ANEEL `<tipo>.<2 letras>.<UF>.<6 algarismos>-<1 algarismo>.<2 algarismos>`, com o tipo entre os sete |
  | `identificacao.cod_programacao` ou `identificacao.codigos_programacao` | texto ou lista de texto | um dos dois, não vazio; a lista quando a usina ou o conjunto é programado em mais de um código (FR-043) |
  | `identificacao.cod_usina` | inteiro | > 0 |
  | `identificacao.nome_ons` | texto | não vazio, em maiúsculas e sem acento; nome da usina e do reservatório nos conjuntos do ONS |
  | `identificacao.id_ons` | texto | não vazio |
  | `identificacao.id_reservatorio` | texto | não vazio |
  | `identificacao.id_conjunto` | texto | não vazio; id ONS do conjunto de usinas (`CJU_...`) |
  | `[[identificacao.planejamento]]` | lista de tabelas | `codigo`, `inicio` e `fim` (FR-056) |
  | `[[identificacao.membros]]` | lista de tabelas | `id_ons`, `ceg` (no padrão), `inicio` e `fim` (`AAAA-MM-DD`; `fim` vazio = vigente): as usinas do conjunto, só para a conferência da soma das usinas com o conjunto (FR-057) |
  | `[cobertura]` | tabela | uma chave por conjunto de série do registro que serve ao tipo (FR-049): `evt`, `indicadores`, `programacao`, `disponibilidade`, `hidrologia`, `geracao`, `despacho`, `cvu`, `fator_capacidade`, `restricao_detalhe` e `restricao_razao`; valor `proprio`, `conjunto`, `agregado`, `ausente` ou a lista `["proprio", "conjunto"]` |
  | `parametros.potencia_instalada_mw` | real | > 0; em EOL e UFV, é a capacidade instalada |
  | `parametros.unidades_geradoras` | inteiro | ≥ 1 |
  | `parametros.potencia_unitaria_mw` ou `parametros.potencias_unidades_mw` | real ou lista de reais | um dos dois: a potência única das unidades ou a lista, um valor > 0 por unidade, quando diferem; a soma das unidades igual a `potencia_instalada_mw`, com tolerância de 0,1 MW; na UHE, só a potência unitária |
  | `parametros.tipo_turbina` | texto | não vazio |
  | `parametros.engolimento_nominal_ug_m3s` | real | > 0 |
  | `parametros.garantia_fisica_mwmed` | real | > 0 e ≤ `potencia_instalada_mw` |
  | `parametros.ip_referencia` | real | ≥ 0 e < 1 |
  | `parametros.teif_referencia` | real | ≥ 0 e < 1 |
  | `parametros.queda_bruta_m` | real | > 0 |
  | `parametros.perda_hidraulica_m` | real | ≥ 0 e < `queda_bruta_m` |
  | `parametros.rendimento_turbina_gerador` | real | > 0 e ≤ 1 |
  | `parametros.vazao_remanescente_m3s` | real | ≥ 0 |
  | `parametros.combustivel` | texto | não vazio |
  | `parametros.fontes.geral` | texto | obrigatório em todos os tipos; não vazio; fonte e data dos parâmetros |
  | `parametros.fontes.garantia_fisica` | texto | obrigatório quando há garantia física; não vazio; fonte e data da garantia física |
  | `analises.vertimento_minimo_m3s` | real | ≥ 0 (0 = usina sem vertimento contínuo) |
  | `analises.faixas_geracao_mw` | lista de reais | crescente; cada valor acima do limiar de usina parada (1 MW) e abaixo da plena carga (90 % da potência instalada) |

  São obrigatórios em todos os tipos: `usina.slug`, `nome`, `nome_curto`, `estado`, `inicio_operacao_comercial`, `tipo` e `modalidade`, `identificacao.ceg`, o código ou a lista de códigos de programação, `parametros.potencia_instalada_mw`, `unidades_geradoras`, a potência das unidades e `parametros.fontes.geral`. A exigência dos demais campos depende do tipo (`O` = obrigatório; `C` = obrigatório quando um conjunto do ONS que usa o campo tem cobertura `proprio` ou `conjunto`, conforme indicado; `—` = não se aplica, e a presença é recusada):

  | Campo | UHE | PCH e CGH | UTE e UTN | EOL e UFV |
  |---|---|---|---|---|
  | `identificacao.id_ons` | O | C: `proprio` na geração ou na disponibilidade | O | C: `proprio` na geração, no fator de capacidade ou nas restrições |
  | `identificacao.cod_usina`, `identificacao.nome_ons` | O | C: EVT ou hidrologia | — | — |
  | `identificacao.id_reservatorio` | O | C: hidrologia | — | — |
  | `identificacao.id_conjunto` | — | C: `conjunto` na geração, no fator de capacidade ou na razão da restrição | idem | idem |
  | `[[identificacao.planejamento]]` | — | — | C: despacho ou CVU (FR-056) | — |
  | `[[identificacao.membros]]` | — | opcional | — | opcional |
  | `usina.subsistema` | opcional | opcional | C: CVU (FR-056) | opcional |
  | `[cobertura]` | opcional; sem ela, os dez conjuntos da UHE (FR-016) | O | O | O |
  | `parametros.tipo_turbina`, `engolimento_nominal_ug_m3s`, `queda_bruta_m`, `perda_hidraulica_m`, `rendimento_turbina_gerador`, `vazao_remanescente_m3s` | O | C: EVT ou hidrologia | — | — |
  | `parametros.garantia_fisica_mwmed` | O | opcional | opcional | opcional |
  | `parametros.ip_referencia`, `parametros.teif_referencia` | O | opcional | opcional | — |
  | `parametros.combustivel` | — | — | O | — |
  | `[analises]` (`vertimento_minimo_m3s`, `faixas_geracao_mw`) | O | C: EVT | — | — |
  | textos opcionais (tabela seguinte) | opcional | opcional | opcional | opcional |

  O perfil da São Domingos ganha só `usina.tipo = "UHE"` e `usina.modalidade = "TIPO II-A"`; na UHE, os demais campos e regras não mudam.

  Os campos de texto desta tabela são opcionais e, quando presentes, NÃO DEVEM estar vazios. Eles levam ao relatório os trechos próprios da usina; sem um deles, o relatório omite o trecho correspondente (spec da Geração do relatório):

  | Campo | Onde o texto aparece | Exemplo (perfil da São Domingos) |
  |---|---|---|
  | `parametros.fontes.inicio_operacao_comercial` | origem do ano de início da operação comercial, na tabela de parâmetros | "Despachos ANEEL nº 377/2013 e nº 2.692/2013, citados no RF 0009/2017-AGEPAN-SFG" |
  | `parametros.fontes.ip_teif` | nota "O IP e o TEIF de referência são os do <texto>; a revisão posterior pode ter alterado esses parâmetros e, com eles, a disponibilidade de referência." | "cálculo de garantia física registrado no RF 0009/2017-AGEPAN-SFG, quando a garantia física era de 36,9 MWmed" |
  | `analises.fontes.vertimento_minimo` | origem do limiar de vertimento mínimo, na tabela de parâmetros | "patamar de 5 a 6 m³/s observado na série" |
  | `analises.descricao_vertimento_minimo` | nota de definições: "vertimento mínimo = vazão vertida ≤ <limiar> m³/s (<texto> de <vazão remanescente> m³/s)" | "patamar contínuo da série, da ordem da vazão remanescente" |
  | `textos.ressalva_volume_util` | ressalva própria da usina, nas notas da hidrologia | "O volume útil é apresentado como informado; ele varia entre os anos sem variação correspondente do nível de montante, por isso o comportamento do reservatório é descrito pelo nível." |

  Exemplo de uso do `usina.nome_curto` (perfil da São Domingos, com o valor "São Domingos"): `O cadastro tem N outras usinas com "São Domingos" no nome, excluídas pelo CEG.`
- **FR-007**: O perfil DEVE trazer só valores próprios da usina. NÃO DEVE trazer valores derivados dos parâmetros, como o engolimento máximo da usina e a disponibilidade de referência da garantia física, que as etapas calculam a partir dele. Também NÃO DEVE alterar as regras gerais do projeto (limiares, tolerâncias e metas), que são iguais para qualquer usina e estão nas specs das etapas que as aplicam; os únicos limiares próprios da usina são os da seção `analises`.
- **FR-008**: Todo comando com `--usina` DEVE ler e validar o perfil antes de qualquer outra ação, inclusive antes de consultar o portal.
- **FR-009**: Um perfil ausente, ilegível, com campo obrigatório faltante, com texto opcional vazio, com tipo ou faixa errados, com incoerência, com campo que não se aplica ao tipo, com chave de `[cobertura]` desconhecida ou que não serve ao tipo, com modalidade Tipo III ou em rascunho DEVE ser recusado com código 4, sem gravar nada. A mensagem DEVE listar todos os problemas de uma vez, um por linha, depois do cabeçalho `Perfil da usina '<slug>' inválido (usinas/<slug>/perfil.toml):`. No perfil em rascunho, a mensagem traz também uma linha `pendente: <campo>` por pendente. Os textos das mensagens estão no contrato do perfil (`contracts/perfil-usina.md`).
- **FR-056** (perfil das térmicas): Em UTE e UTN, `usina.subsistema` DEVE estar no perfil quando a `[cobertura]` traz `cvu`, e `[[identificacao.planejamento]]` DEVE trazer pelo menos um código quando a `[cobertura]` traz `despacho` ou `cvu`. Cada entrada de planejamento tem `codigo` (inteiro > 0, comparado como número no despacho e no CVU), `inicio` (`AAAA-MM`) e `fim` (`AAAA-MM`, ≥ `inicio`; vazio = vigente). Dois códigos diferentes podem valer ao mesmo tempo, como uma unidade por combustível; o mesmo código NÃO DEVE ter períodos sobrepostos.

**Pastas e manifesto da etapa (US4)**

- **FR-010**: Os arquivos do fluxo DEVEM ficar nestas pastas:

  | Pasta | Conteúdo |
  |---|---|
  | `usinas/<slug>/` | perfil da usina (`perfil.toml`) e, fora do controle de versões, os documentos de referência da usina (`documentos/`) |
  | `data/raw/` | dados brutos do ONS, compartilhados por todas as usinas e gravados só pela Coleta de dados |
  | `data/catalogo/` | catálogo de usinas, gravado só pelo comando `usinas` da Coleta de dados, sem `.bak` (FR-051) |
  | `data/usinas/<slug>/coleta/`, `tratamento/`, `conferencia/` e `analises/` | resultados de cada etapa, separados por usina |
  | `reports/<slug>/` | relatório da usina |
  | `reports/carteiras/<nome>/` | relatórios de carteira (spec da Geração do relatório) |
  | `relatorios_referencia/<slug>/` | relatório aprovado da usina, com a Coleta e o perfil congelados (spec da Geração do relatório) |

  Cada etapa DEVE gravar só na sua pasta (a Coleta de dados também em `data/raw/`; o comando `usinas`, em `data/catalogo/`; o comando `perfil`, só o perfil novo em `usinas/<slug>/`), sem tocar nos resultados de outra usina.
- **FR-011**: Cada etapa DEVE gravar, na sua pasta, o manifesto `etapa.json`, com:

  | Campo | Conteúdo |
  |---|---|
  | `etapa` | `coleta`, `tratamento`, `conferencia`, `analises` ou `relatorio` |
  | `usina` | slug |
  | `versao_formato` | inteiro que muda quando um arquivo que a etapa já grava muda de formato, ou quando a etapa seguinte passa a exigir um arquivo novo; arquivo novo opcional não muda o formato. Valores atuais: Coleta 2, Tratamento 2, Conferência 2, Análises 3 e Geração do relatório 1 |
  | `iniciada_em`, `concluida_em` | data e hora (UTC) |
  | `status` | `concluida`, `falha` ou `desatualizada` |
  | `codigo_saida` | código de saída da execução |
  | `etapa_anterior` | etapa e data de conclusão do resultado usado como entrada (vazio na Coleta de dados) |
  | `arquivos` | nome, tamanho em bytes e SHA-256 de cada arquivo gravado |
  | `resumo` | números principais da etapa, definidos na spec de cada uma; quando a etapa termina por erro inesperado ou por interrupção do usuário, só a mensagem do erro |

- **FR-012**: Antes de gravar qualquer arquivo, cada etapa a partir do Tratamento de dados DEVE conferir o `etapa.json` da etapa anterior. A anterior com `status` `concluida` e com o `versao_formato` atual DEVE ser aceita, qualquer que seja o código de saída registrado nela. Se o `etapa.json` não existir, não puder ser lido, estiver `falha` ou `desatualizada` ou tiver outro `versao_formato`, a etapa DEVE terminar com código 5, sem gravar nada, com a mensagem `A etapa '<etapa>' precisa da etapa '<anterior>' concluída para a usina '<slug>'. Execute antes: python -m src <anterior> --usina <slug>`.
- **FR-013**: O `status` do `etapa.json` DEVE seguir o código de saída:

  | Código | `status` gravado | Etapas seguintes |
  |---|---|---|
  | 0 | `concluida` | as que já existirem ficam `desatualizada` |
  | 3 | `concluida`, com `codigo_saida` 3: todos os resultados gravados e a meta não atingida registrada | idem; o `completo` para nesse código, mas a etapa seguinte, executada à parte, aceita a anterior (com o código 3 da Conferência, as Análises omitem os cruzamentos com a hidrologia) |
  | 1 ou 2 | `falha`, com o código | a seguinte recusa rodar, com código 5 |
  | 4 ou 5, ou opção inválida | nada é gravado | nada muda |

**Cópia de segurança do projeto (US6)**

- **FR-014**: O comando `copia-seguranca --motivo <texto>` DEVE criar a pasta `_backup_<AAAA-MM-DD>_<motivo>/` com:
  - `src/`, `tests/`, `specs/`, `reports/`, `.specify/`, os perfis `usinas/*/perfil.toml` (sem `documentos/`), `README.md` e `requirements.txt`;
  - `relatorios_referencia/` inteira, com a Coleta e o perfil congelados de cada usina, sem as pastas temporárias do comando `referencia`;
  - `LEIA-ME.txt`, com a data, o motivo, o que foi copiado e as referências levadas;
  - `conftest.py`, que impede os testes de varrerem a cópia;
  - `copia.json`, com o nome, o tamanho e o SHA-256 de cada arquivo copiado.

  A cópia NÃO DEVE incluir os dados brutos, o catálogo de usinas, os dados das etapas nem os documentos de referência.
- **FR-015**: Depois de criar a cópia, o comando DEVE conferi-la (quantidade de arquivos e SHA-256 de cada um, contra `copia.json`; em cada referência copiada, os SHA-256 do `referencia.json` dela) e só então excluir as cópias mais antigas, pela data do nome da pasta e, no empate, pela data de criação, até ficarem duas. Se a criação ou a conferência falhar, DEVE apagar a cópia incompleta, não excluir nenhuma outra e terminar com código 1. Um motivo com caractere que não seja letra, algarismo, `_` ou `-`, ou uma cópia com o mesmo nome já existente, DEVE terminar com código 1, sem criar nem excluir nada.

**Conjuntos, período e opções da coleta (US1 e US8)**

- **FR-016**: Os conjuntos da Coleta de dados DEVEM vir do registro (FR-049), filtrados pelo tipo e pela `[cobertura]` da usina. O registro tem estes conjuntos do ONS, e só eles:

  | Conjunto do ONS | Chave no registro | Id no catálogo | Pasta em `data/raw/` | Como o ONS publica | Formato obtido |
  |---|---|---|---|---|---|
  | Energia Vertida Turbinável | `evt` | `energia-vertida-turbinavel` | a própria `data/raw/` | um arquivo por ano até 2023 e um por mês desde 2024 | CSV |
  | Indicadores de disponibilidade por unidade geradora, base mensal | `indicadores` | `ind_disponibilidade_fgeracao_uge_mensal` | `indicadores_ons/ind_disponibilidade_fgeracao_uge_mensal/` | um arquivo por ano | CSV |
  | Indicadores de disponibilidade por unidade geradora, base anual | `indicadores` | `ind_disponibilidade_fgeracao_uge_anual` | `indicadores_ons/ind_disponibilidade_fgeracao_uge_anual/` | arquivo único | CSV |
  | Parâmetros das taxas TEIFa e TEIP | `indicadores` | `taxa_teif_teip_parametro` | `indicadores_ons/taxa_teif_teip_parametro/` | um arquivo por ano | CSV |
  | Taxas TEIFa e TEIP | `indicadores` | `taxa_teif_teip` | `indicadores_ons/taxa_teif_teip/` | arquivo único | CSV |
  | Programação diária | `programacao` | `programacao_diaria` | `programacao_diaria/` | um arquivo por dia, em três formatos | Parquet |
  | Disponibilidade por usina | `disponibilidade` | `disponibilidade_usina` | `disponibilidade_usina/` | um arquivo por mês, em CSV; em Parquet só em parte dos meses | Parquet; CSV no mês sem Parquet |
  | Dados hidrológicos horários | `hidrologia` | `dados_hidrologicos_ho` | `dados_hidrologicos_ho/` | um arquivo por mês, em Parquet; alguns meses só em CSV | Parquet; CSV no mês sem Parquet |
  | Geração por usina | `geracao` | `geracao-usina-2` | `geracao_usina_2/` | um arquivo por ano até 2021 e um por mês desde 2022 | Parquet; CSV no período sem Parquet |
  | Modalidade das usinas | `cadastro` | `modalidade-usina` | `modalidade_usina/` | arquivo único, regravado pelo ONS, sem série histórica | CSV |
  | Composição dos conjuntos de usinas | `composicao` | `usina_conjunto` | `usina_conjunto/` | arquivo único, com as datas de entrada e de saída de cada usina | Parquet; CSV sem Parquet |
  | Capacidade de geração | `capacidade` | `capacidade-geracao` | `capacidade_geracao/` | arquivo único, uma linha por unidade geradora | Parquet; CSV sem Parquet |
  | Geração térmica por motivo de despacho | `despacho` | `geracao-termica-despacho-2` | `geracao_termica_despacho_2/` | um arquivo por ano de 2013 a 2024 e um por mês desde 2022 | Parquet; CSV no período sem Parquet |
  | CVU das usinas térmicas | `cvu` | `cvu-usitermica` | `cvu_usitermica/` | um arquivo por ano | Parquet; CSV no período sem Parquet |
  | CMO semanal | `cmo` | `cmo-semanal` | `cmo_semanal/` | um arquivo por ano | Parquet; CSV no período sem Parquet |
  | Fator de capacidade | `fator_capacidade` | `fator-capacidade-2` | `fator_capacidade_2/` | um arquivo por ano até 2021 e um por mês desde 2022 | Parquet; CSV no período sem Parquet |
  | Restrição por constrained-off com detalhe por usina, eólica e fotovoltaica | `restricao_detalhe` | `restricao_coff_eolica_detail`, `restricao_coff_fotovoltaica_detail` | pasta com o nome do id | um arquivo por mês (eólica desde 10/2021; fotovoltaica desde 04/2024) | Parquet; CSV no período sem Parquet |
  | Restrição por constrained-off com a razão da restrição, eólica e fotovoltaica | `restricao_razao` | `restricao_coff_eolica_usi`, `restricao_coff_fotovoltaica` | pasta com o nome do id | um arquivo por mês | Parquet; CSV no período sem Parquet |
  | Reservatórios | `reservatorio` | `reservatorio` | `reservatorio/` | arquivo único | Parquet; CSV sem Parquet |

  Para a usina, a Coleta DEVE obter só os conjuntos que servem ao tipo dela (tabela "Aplicabilidade por tipo") e:
  - os conjuntos de série com `proprio` ou `conjunto` na `[cobertura]` (ou a lista dos dois), pelo identificador do nível declarado: o da usina com `proprio`, o do conjunto com `conjunto`; nas restrições, só a variante do tipo (eólica na EOL, fotovoltaica na UFV);
  - sempre, os cadastrais da usina: a Modalidade das usinas, a Capacidade de geração e, na usina em conjunto (com `identificacao.id_conjunto`), a Composição dos conjuntos;
  - nas térmicas com `usina.subsistema`, o CMO semanal, contexto do subsistema (FR-055).

  Na UHE sem `[cobertura]`, a Coleta DEVE obter as dez primeiras linhas da tabela (os dez conjuntos da UHE), na mesma ordem, e mais nenhum conjunto. Os Reservatórios só servem ao catálogo de usinas (FR-051). Conjunto com `agregado` ou `ausente` na cobertura não é obtido e vai para o resumo, entre os não aplicáveis (FR-048).
- **FR-017**: O período DEVE vir da série de referência do tipo (FR-054). Na hidrelétrica com EVT, a coleta DEVE tratar primeiro a EVT, que define o período: do primeiro ao último instante extraído da usina; na EVT, DEVE obter e ler todos os arquivos publicados, sem supor data de início de operação da usina. Nos demais conjuntos, DEVE obter e ler os arquivos cujo ano, mês ou dia, pelo nome do arquivo, se sobrepõe ao período e, nos conjuntos publicados em arquivo único, esse arquivo.
- **FR-018**: Nos conjuntos publicados em dois formatos, a coleta DEVE obter cada período (ano ou mês) no formato compacto (Parquet), quando ele é publicado para aquele período, e senão no CSV. Na Programação diária, DEVE obter um arquivo por dia, no formato compacto.
- **FR-019**: Quando o catálogo lista o mesmo arquivo mais de uma vez, em qualquer conjunto (inclusive a EVT, os indicadores e a Programação diária), a coleta DEVE usar o recurso com data de publicação e, em empate, o maior, e registrar a quantidade de repetições no manifesto e, nos conjuntos lidos pelo motor comum, na auditoria. O arquivo temporário do download DEVE levar o id do recurso, de modo que dois downloads simultâneos nunca usem o mesmo temporário.
- **FR-020**: A coleta DEVE tratar primeiro a série de referência (na hidrelétrica com EVT, a EVT; na usina em conjunto sem série própria, antes dela a Composição dos conjuntos, que recorta o período) e depois os demais conjuntos da usina, na ordem do registro (FR-049), e parar no primeiro conjunto com falha (código 1 ou 2), depois de gravar o que dele já foi lido e a auditoria; os conjuntos seguintes não são coletados nessa execução. Os quatro conjuntos de indicadores e taxas formam um bloco: são sincronizados e lidos juntos, e a falha em qualquer um deles para a coleta depois do bloco.
- **FR-021**: Com `--sem-portal`, a coleta NÃO DEVE consultar o portal. DEVE extrair só dos arquivos locais, com as mesmas regras de período e formato, e NÃO DEVE criar, alterar nem excluir nada em `data/raw/`. Os dicionários não são obtidos, e o registro deles é montado a partir dos manifestos locais.
- **FR-022**: Com `--forcar-download`, a coleta DEVE baixar de novo todos os arquivos de dados dos conjuntos da usina, sem o reaproveitamento da FR-024. Com `--sem-portal`, a opção não tem efeito.

**Sincronização com o portal, manifesto e versões (US1 e US5)**

- **FR-023**: Sem `--sem-portal`, a coleta DEVE consultar, a cada execução, o catálogo de cada conjunto no portal (API CKAN, `https://dados.ons.org.br/api/3/action/package_show?id=<id do conjunto>`) e aceitar os recursos do formato esperado, pelo formato declarado ou pela extensão da URL. O arquivo local leva o nome do arquivo na URL.
- **FR-024**: Uma cópia local DEVE ser reaproveitada, sem novo download, só quando corresponder à versão publicada:
  - com registro no manifesto: tamanho local igual ao registrado e data de publicação igual à do catálogo (ou só o tamanho, se o catálogo não informar a data);
  - sem registro (primeira coleta com arquivos já existentes): tamanho local igual ao publicado, ou arquivo não vazio, se o catálogo não informar o tamanho; a cópia é registrada como arquivo existente.

  Nos demais casos, o arquivo DEVE ser baixado de novo.
- **FR-025**: O download DEVE ser feito em partes, para um arquivo temporário que só substitui o arquivo local quando completo. A consulta ao catálogo e cada download DEVEM ter 3 tentativas, com espera de 2 s e de 4 s entre elas e limite de 60 s por tentativa. Tamanho baixado diferente do publicado DEVE ser avisado no log.
- **FR-026**: Catálogo inacessível depois das tentativas DEVE encerrar a coleta com código 1. Arquivo de dados não obtido depois das tentativas DEVE ficar na auditoria do conjunto como `FALHA`, com o motivo; os demais arquivos do conjunto continuam, o manifesto guarda o que foi sincronizado, e a coleta termina com código 2.
- **FR-027**: Cada pasta de conjunto DEVE ter o manifesto `_manifesto_ons.json`, gravado de forma atômica ao fim da sincronização, mesmo quando ela é interrompida. Para cada arquivo, o manifesto registra: URL, data de publicação no portal, tamanho publicado, tamanho local, data e hora do registro (UTC), origem do registro (download ou arquivo existente), versões anteriores preservadas e excluídas e, quando houver, repetições no catálogo. A data de obtenção de um conjunto é a data de registro mais recente do manifesto da pasta dele.
- **FR-028**: Antes de substituir um arquivo por uma versão republicada com conteúdo diferente (SHA-256), a coleta DEVE mover a cópia anterior para `_versoes_anteriores/`, na mesma pasta, com o nome `<nome sem extensão>__pub_<AAAAMMDDTHHMMSS><extensão>`, pela data de publicação registrada, ou `<nome sem extensão>__arq_<AAAAMMDDTHHMMSS><extensão>`, pela data do arquivamento, quando a de publicação não for conhecida; se o nome já existir, acrescenta `_2`, `_3` e assim por diante, sem sobrescrever outra versão. A cópia só é movida depois de a nova versão estar completa. O manifesto registra o arquivo preservado, a data de publicação, o tamanho, o SHA-256 e a data do arquivamento. Conteúdo idêntico NÃO DEVE gerar versão.
- **FR-029**: Cada arquivo DEVE ter no máximo duas versões anteriores, as mais recentes. Ao preservar uma terceira, a coleta DEVE excluir a mais antiga e registrar a exclusão no manifesto, com o arquivo e a data. A regra vale para os arquivos de dados e para os dicionários.
- **FR-030**: Os dados brutos DEVEM seguir estas regras:
  - nenhum arquivo bruto é editado: só é substituído inteiro por uma versão publicada;
  - as versões anteriores e os dicionários nunca são lidos como dados;
  - os arquivos sem linhas da usina continuam guardados, porque servem a outras usinas;
  - os arquivos baixados uma vez servem a qualquer usina e ao catálogo de usinas;
  - arquivos brutos, manifestos e dicionários não têm cópia `.bak`: as versões anteriores cumprem esse papel.

**Dicionários de dados (US5)**

- **FR-031**: Sempre que consulta o portal, a coleta DEVE obter os dicionários de dados publicados dos conjuntos da usina (FR-016), em PDF e em JSON (os recursos desses formatos cujo nome, sem acento, contém "dicionario"), também quando a coleta para num conjunto com falha (código 2). Na UHE sem `[cobertura]`, são os dos dez conjuntos da UHE, na mesma ordem. Eles são sempre baixados, porque o catálogo não informa data nem tamanho deles, e ficam em `<pasta do conjunto>/_dicionarios/` (os da EVT, em `data/raw/_dicionarios/`), com manifesto próprio.
- **FR-032**: Cada dicionário obtido DEVE ser comparado pelo conteúdo (SHA-256) com a cópia local, com o resultado `NOVO`, `INALTERADO`, `ALTERADO` (versão anterior preservada, como na FR-028, e aviso no log) ou `FALHA` (cópia local mantida). O registro `dicionarios.csv` DEVE ter uma linha por conjunto da usina e formato, na ordem do registro (na UHE sem `[cobertura]`, 20 linhas), com: conjunto, pasta, formato, arquivo, URL, resultado da última obtenção, data e hora dela, SHA-256, tamanho, quantidade de versões anteriores e a mais recente delas. No registro, `NAO_PUBLICADO` indica formato ausente do catálogo, e `NAO_OBTIDO`, conjunto cujos dicionários nunca foram procurados no catálogo.
- **FR-033**: A obtenção dos dicionários NÃO DEVE baixar arquivos de dados. Uma falha nela DEVE ir para o log e para o registro, sem interromper a coleta nem mudar o código de saída.

**Identificação da usina e leitura dos arquivos (US1 e US2)**

- **FR-034**: A usina DEVE ser identificada em cada conjunto por um identificador de extração e conferida por um segundo campo, com os valores do perfil:

  | Conjunto do ONS | Identificador de extração | Conferência |
  |---|---|---|
  | Energia Vertida Turbinável | `cod_usina` = `identificacao.cod_usina` | `nom_reservatorio` contém `identificacao.nome_ons` |
  | Indicadores de disponibilidade por unidade geradora, bases mensal e anual | `ceg` = `identificacao.ceg` | `id_usina` = `identificacao.id_ons` |
  | Taxas TEIFa e TEIP; Parâmetros das taxas TEIFa e TEIP | `cod_ceg` = `identificacao.ceg` | não há: os dois conjuntos não publicam o id ONS |
  | Programação diária | `cod_exibicaousina` entre os códigos do perfil (`identificacao.cod_programacao` ou `codigos_programacao`) | `id_estado` = `usina.estado` e, nas hidrelétricas, `nom_usina` contém `identificacao.nome_ons` |
  | Disponibilidade por usina | `id_ons` = `identificacao.id_ons` | `ceg` = `identificacao.ceg`, e `id_estado` = `usina.estado` |
  | Dados hidrológicos horários | `cod_usina` = `identificacao.cod_usina` | `nom_reservatorio` contém `identificacao.nome_ons`, e `id_reservatorio` = `identificacao.id_reservatorio` |
  | Geração por usina, da usina | `id_ons` = `identificacao.id_ons` | `ceg` = `identificacao.ceg`, e `id_estado` = `usina.estado` |
  | Geração por usina, do conjunto | `id_ons` = `identificacao.id_conjunto` | `id_estado` = `usina.estado` (o ONS publica o CEG "-" nas linhas de conjunto desde 05/2026) |
  | Modalidade das usinas | `ceg` = `identificacao.ceg` | `id_ons` = `identificacao.id_ons`, e `id_estado` = `usina.estado` |
  | Composição dos conjuntos | `id_ons_conjunto` = `identificacao.id_conjunto` | `estad_id` = `usina.estado` |
  | Capacidade de geração | `ceg` = `identificacao.ceg` | `id_estado` = `usina.estado` |

  A identificação nos conjuntos das térmicas e das eólicas e solares está nas FR-055 e FR-057; a das unidades das usinas do conjunto, na FR-060.
- **FR-035**: Na comparação, os textos DEVEM ser tomados sem acento, sem espaços nas pontas e em maiúsculas, e os códigos numéricos como número. A mesma normalização DEVE valer na extração e nos pré-filtros de todos os conjuntos; o filtro empurrado à leitura do Parquet DEVE usar o valor como está no perfil e a forma normalizada. "Contém" exige o valor do perfil dentro do texto do campo. O nome do agente, o nome da usina fora das conferências declaradas e os demais campos de cadastro (subsistema, bacia e rio) NÃO DEVEM ser usados na identificação.
- **FR-036**: Só DEVEM ser extraídas as linhas em que o identificador e a conferência conferem. As linhas em que só um dos dois confere NÃO DEVEM ser extraídas: DEVEM ser contadas por arquivo, em "só identificador" e "só conferência", com aviso no log que cita o arquivo. Num conjunto com conferência declarada, a coluna de conferência ausente torna o arquivo `FALHA`, com o motivo, e a coleta termina com código 2. Há três exceções:
  - Taxas TEIFa e TEIP e Parâmetros das taxas TEIFa e TEIP: sem campo de conferência publicado, a extração usa só o identificador, e as contagens parciais não se aplicam;
  - CMO semanal: contexto do subsistema, sem conferência; não há linha "só conferência" (FR-055);
  - Modalidade das usinas: a ficha é localizada pelo identificador; id ONS ou estado diferente do perfil não exclui a linha, que é extraída e examinada pela Conferência, e as contagens parciais ficam na auditoria.
- **FR-037**: Os arquivos CSV DEVEM ser lidos com separador `;`, em UTF-8; com erro de decodificação, o arquivo inteiro DEVE ser relido em Latin-1. As colunas DEVEM ser localizadas pelo nome no cabeçalho, e não pela posição; nos arquivos Parquet, também pelo nome. Arquivo vazio, corrompido ou sem as colunas de identificação DEVE ficar como `FALHA`, com o motivo, sem interromper a leitura dos demais; a coleta termina com código 2.
- **FR-038**: Nos arquivos CSV, as linhas não vazias com número de campos diferente do cabeçalho NÃO DEVEM ser extraídas: DEVEM ser contadas por arquivo e avisadas no log, com o arquivo, a quantidade e o número das cinco primeiras. Linhas vazias são ignoradas.
- **FR-039**: Na EVT, na Programação diária e nos conjuntos lidos pelo motor comum (horários, semi-horários e semanais), os valores numéricos DEVEM ser lidos como publicados, sem arredondamento, com a vírgula ou o ponto decimal aceitos em todos esses conjuntos e na potência autorizada da ficha do cadastro. Campo vazio fica ausente; valor que não é número fica ausente e é contado na auditoria como valor inválido; nenhum dos dois vira zero. As marcas publicadas como booleano são lidas como 1 e 0. Nos indicadores e nas taxas, as colunas ficam como publicadas, e a conversão em número é do Tratamento de dados.
- **FR-040**: Toda linha extraída DEVE guardar o arquivo de origem, com os textos sem espaços nas pontas e o instante como publicado. A Coleta de dados NÃO DEVE converter a convenção de hora, juntar duplicatas entre arquivos (exceto na EVT, FR-041), recortar o período (exceto na série de referência, FR-054), listar ausências, converter patamares ou semi-horas em horas, escolher a versão mais recente dos indicadores ou a revisão do CVU nem sinalizar a qualidade dos valores: isso é do Tratamento de dados.

**Extração por conjunto (US1)**

- **FR-041**: Na EVT, a coleta DEVE extrair as linhas da usina com as 18 colunas publicadas (identificação, `din_instante` e as dez grandezas `val_*`), mais o arquivo de origem e o critério de identificação aplicado (`CODIGO_E_NOME`), e consolidá-las em `evt_extraido.csv`:
  - arquivos lidos em ordem de nome, os anuais antes dos mensais;
  - um registro por par (`cod_usina`, `din_instante`); na duplicata, fica o do arquivo lido por último; as duplicatas idênticas e as conflitantes são contadas no log, e cada conflitante é avisada com os dois arquivos;
  - registros sem instante descartados;
  - ordem cronológica, sem criar nem preencher horas;
  - CSV com `;`, ponto decimal, UTF-8 sem BOM e valores ausentes em branco.

  Sem nenhuma linha da usina na EVT, a coleta DEVE gravar a auditoria da EVT, avisar no log que a usina não foi encontrada, não coletar os demais conjuntos e terminar com código 2.
- **FR-042**: Nos indicadores por unidade geradora e nas taxas TEIFa e TEIP, a coleta DEVE extrair as linhas da usina com todas as colunas publicadas, com o conjunto e o arquivo de origem, em `indicadores_extraido.parquet`.
- **FR-043**: Na Programação diária, a coleta DEVE:
  - identificar a usina pelos códigos de exibição do perfil: `cod_programacao` ou, quando a usina ou o conjunto é programado em mais de um código (um por barra), a lista `codigos_programacao`; a conferência é pelo estado e, nas hidrelétricas, também pelo nome (`nome_ons`); nos demais tipos, que não têm `nome_ons`, só pelo estado;
  - tomar o dia do nome do arquivo (`..._AAAA_MM_DD`) e conferir a data interna, aceitando `AAAA-MM-DD` e `DD/MM/AAAA`; a divergência vai para a auditoria e para o log;
  - extrair, para cada patamar de 30 minutos (1 a 48), a geração programada da usina, com o dia e o arquivo de origem, em `programacao_extraido.parquet`; com mais de um código, cada linha traz o código (`cod_exibicaousina`), e a soma por patamar fica com o Tratamento de dados;
  - num patamar repetido no mesmo arquivo (do mesmo código), manter a última ocorrência, com aviso no log;
  - marcar o arquivo como `INCOMPLETO` quando a usina não tiver os 48 patamares.
- **FR-044**: Nos conjuntos horários, a coleta DEVE extrair, com o instante como publicado e o arquivo de origem:
  - Disponibilidade por usina: potência instalada, disponibilidade operacional e disponibilidade sincronizada;
  - Dados hidrológicos horários: vazões afluente, defluente, turbinada, vertida, vertida não turbinável e por outras estruturas, níveis de montante e de jusante e volume útil;
  - Geração por usina: geração.

  Os valores são lidos sem arredondamento (FR-039), e cada linha DEVE trazer a marca de valor não numérico na fonte, que o Tratamento de dados transforma em sinalização de qualidade. A linha da usina com instante não interpretável NÃO DEVE ser extraída: ela DEVE ser contada nas linhas da usina e como valor inválido. Os conjuntos das térmicas e das eólicas e solares seguem as mesmas regras (FR-055, FR-057 e FR-058).
- **FR-045**: Na Modalidade das usinas, a coleta DEVE gravar em `cadastro_ficha.csv` a ficha da usina: nome, CEG, id ONS, modalidade de operação, centro de operação, ponto de conexão, potência autorizada (número), estado, situação na ANEEL, data da consulta (a data de obtenção do arquivo, pelo manifesto) e arquivo de origem. A ficha DEVE trazer também a quantidade de homônimos (linhas com `identificacao.nome_ons` no nome da usina e outro CEG; nos tipos sem `nome_ons`, com `usina.nome_curto`), as contagens parciais e a quantidade de linhas com o CEG; havendo mais de uma, usa a primeira. Usina ausente do cadastro DEVE encerrar a coleta com código 2.

**Auditoria, saídas e resumo (US2)**

- **FR-046**: Cada conjunto DEVE ter uma auditoria com uma linha por arquivo lido ou não obtido, inclusive os sem linhas da usina, com:
  - arquivo, formato, período (ano, mês ou dia, pelo nome) e data de publicação no portal (pelo manifesto) e se o arquivo foi obtido nesta execução;
  - linhas lidas, linhas irregulares (FR-038), linhas da usina, linhas só com o identificador, linhas só com a conferência (FR-036) e valores inválidos (FR-039), onde cada contagem se aplica: a Programação diária, em Parquet, não tem linhas irregulares; os indicadores, as taxas e o cadastro, que ficam como texto, não contam valores inválidos; nas taxas e nos parâmetros, sem campo de conferência, as contagens parciais ficam vazias;
  - situação: `PROCESSADO` (com linhas da usina), `SEM_REGISTROS` (lido, sem linhas da usina) ou `FALHA` (não obtido ou não lido), com o motivo da falha; o CSV vazio da EVT fica `FALHA` com o motivo "arquivo vazio".

  Por conjunto, a auditoria traz ainda:
  - EVT: a codificação de leitura e a data e hora (UTC) da leitura; o período é o nome do arquivo sem a extensão;
  - indicadores e taxas: o conjunto de cada arquivo, numa só auditoria para os quatro conjuntos;
  - Programação diária: uma linha por dia do período com arquivo publicado, lido ou não obtido, com o dia, as linhas da usina, os patamares distintos, se a data interna confere e a situação `INCOMPLETO`; os dias sem linha são os dias sem arquivo, que o Tratamento de dados lista;
  - conjuntos lidos pelo motor comum (os horários, os das térmicas, os das eólicas e solares e a série de referência das usinas sem EVT): as repetições do arquivo no catálogo e, nas colunas de valor ausentes em parte dos arquivos, a mensagem com as colunas ausentes (FR-058). O período e a data de publicação de cada arquivo servem ao Tratamento de dados para escolher o valor de uma hora repetida e para separar o mês sem arquivo do mês sem a usina;
  - restrição com detalhe das outras usinas do conjunto: uma linha por arquivo e usina, com o id ONS dela;
  - Composição dos conjuntos, Capacidade de geração e unidades das usinas do conjunto: uma linha pela leitura do arquivo único, com o período `estatico` (FR-060);
  - Modalidade das usinas: as linhas da usina são as linhas com o CEG do perfil; mais de uma indica CEG repetido no cadastro.

  Nos conjuntos horários, o Tratamento de dados completa a auditoria com as horas da usina e as duplicatas entre arquivos.
- **FR-047**: Os resultados da usina DEVEM ficar em `data/usinas/<slug>/coleta/`, com os nomes da seção "Entradas e saídas". Os arquivos de dados DEVEM ser gravados como os do Tratamento de dados: só a cópia `.bak` da versão imediatamente anterior, conteúdo idêntico sem regravação, gravação conferida e, em falha, o arquivo restaurado e código 1. O `etapa.json` não tem `.bak`. A Coleta grava no formato 2 (FR-050): os arquivos da UHE mantêm os nomes e as colunas do formato 1, mais `datas_obtencao.csv` e `dicionario_evt.json`.
- **FR-048**: O `resumo` do `etapa.json` da coleta DEVE trazer as opções da execução (`--sem-portal` e o `--forcar-download` efetivo, que não vale com `--sem-portal`) e:
  - o tipo e a modalidade da usina;
  - a série de referência (conjunto, identificador, primeira e última hora com valor, arquivos varridos e o motivo da escolha) e o período (primeiro e último instante), quando a série tem valor;
  - por conjunto tratado, com os quatro conjuntos de indicadores e taxas numa só entrada: arquivos no escopo e, nesta execução, baixados, reaproveitados e não obtidos; arquivos lidos, sem linhas da usina e com falha; linhas extraídas, só com o identificador, só com a conferência e irregulares; valores inválidos; arquivos registrados no manifesto; a data de publicação mais recente; e a data de obtenção (FR-027);
  - a quantidade de dicionários por resultado;
  - a quantidade de trechos (0 na hidrelétrica com EVT) e os conjuntos de série do tipo que a `[cobertura]` declara `agregado` ou `ausente`;
  - as linhas próprias da usina sem valor na Geração por usina, no período, quando a série de referência é a do conjunto e o perfil traz o id ONS, com a primeira e a última hora delas, para a qualidade dos dados dizer desde quando o ONS publica a linha da usina vazia (Bandeirante: 4.152 linhas, de 01/05/2026 a 20/10/2026);
  - na usina em conjunto, os intervalos da usina na composição e o resumo das unidades das usinas da composição (FR-060); com `[[identificacao.membros]]`, as linhas da restrição com detalhe de cada membro (FR-057).
- **FR-050** (formato 2): A Coleta DEVE gravar, para todas as usinas:
  - `datas_obtencao.csv`: uma linha por conjunto coletado (os quatro de indicadores e taxas em linhas separadas), na ordem do registro, com `arquivos_registrados`, `publicacao_mais_recente` e `obtencao_mais_recente`, contados só nos arquivos do escopo da usina que a auditoria do conjunto registra como obtidos;
  - nas usinas com EVT, `dicionario_evt.json`, a cópia do dicionário de dados JSON da EVT; sem o dicionário em `data/raw/_dicionarios/`, a Coleta avisa no log, e o Tratamento de dados recusa a base.

  As etapas seguintes DEVEM ler esses arquivos, o `dicionarios.csv` e os demais resultados da Coleta, e nunca `data/raw/`. A etapa seguinte recusa a Coleta no formato 1 com o código 5 (FR-012).

**Registro dos conjuntos (US8)**

- **FR-049** (registro dos conjuntos): Um registro único dos conjuntos do ONS (`src/coleta/registro.py`) DEVE declarar, para cada conjunto:
  - a chave, o pacote no portal e a pasta em `data/raw/`; nos conjuntos que mudam de pacote com o tipo (as restrições), a variante de cada tipo;
  - os tipos de usina a que serve;
  - os níveis do dado: usina, conjunto ou agregado;
  - a resolução: horária, semi-horária (inclusive os 48 patamares da programação), semanal, mensal e anual, ou estática;
  - os formatos preferidos (Parquet, depois CSV);
  - o identificador e as conferências, montados a partir do perfil;
  - as colunas de valor e a convenção de hora;
  - se pode ser a série de referência;
  - se é obtido só pelo catálogo de usinas (os Reservatórios).

  A Coleta DEVE percorrer o registro filtrado pelo tipo e pela cobertura da usina (FR-016). A lista dos conjuntos do fluxo, usada pelos dicionários, pelas datas de obtenção e pelas fontes do relatório, DEVE ser derivada do registro. A EVT, os indicadores, a programação e o cadastro mantêm a leitura própria, mas ficam registrados, para o filtro por tipo e os dicionários.

**Catálogo de usinas e rascunho do perfil (US7)**

- **FR-051** (catálogo de usinas): O comando `python -m src usinas [--estado <UF>] [--tipo <tipo>] [--modalidade <modalidade>] [--sem-portal] [--forcar-download]` DEVE:
  - sincronizar com o portal, sem `--sem-portal`, com o mesmo catálogo CKAN, o cache e as versões da coleta (FR-023 a FR-029):
    - os quatro cadastrais: Modalidade das usinas, Composição dos conjuntos, Capacidade de geração e Reservatórios (estes ligam o CEG ao `cod_usina` e ao reservatório da EVT e dos dados hidrológicos);
    - o arquivo mais recente de cada conjunto de série do registro (nos indicadores, o da base mensal; nas restrições, o de cada variante);
    - todos os arquivos da Geração térmica por motivo de despacho, para os códigos de planejamento de cada CEG;
    - todos os arquivos da Programação diária, para os códigos de exibição de todo o período (em 22/10/2026, 733 arquivos diários desde 01/10/2024, com 109 MB), porque um conjunto pode trocar os códigos: o Conj. Chapadão trocou os quatro em 07/2025, e só com o arquivo mais recente o perfil perderia a programação de 10/2024 a 07/2025;
    - a Geração por usina dos últimos 12 meses completos, para o panorama dos agregados;
    - os dicionários de dados desses conjuntos;
  - gravar `data/catalogo/` por inteiro, sem `.bak`, numa pasta temporária conferida antes da troca: `usinas.csv`, `conjuntos.csv`, `cobertura.csv`, `planejamento.csv`, `programacao.csv`, `agregados.csv` e `catalogo.json` (data-model, seção 2.5);
  - listar na tela, sempre a partir dos arquivos gravados, as usinas do filtro, com uma coluna de cobertura por conjunto de série (`contracts/cli-usinas.md`).

  O catálogo DEVE seguir estas regras:
  - uma linha por linha do cadastro do ONS, sem filtro;
  - o tipo vem do prefixo do CEG; a linha sem CEG é de conjunto de usinas; o prefixo fora dos sete tipos é `outro`. O tipo publicado pelo ONS só é conferido, e a divergência vai para a coluna `divergencias`, com a potência autorizada diferente da soma das unidades ativas;
  - os códigos de exibição da programação são ligados à usina pelo id ONS (o código igual a ele) ou ao conjunto pelo id dele sem o prefixo `CJU_` (o código começa por ele), sempre sem os espaços das pontas; `programacao.csv` traz o primeiro e o último dia de cada código;
  - os códigos de planejamento de cada CEG vêm de todos os arquivos do despacho, com o primeiro e o último mês de cada um (`planejamento.csv`);
  - o panorama dos agregados (`agregados.csv`) soma, por estado, mês e grupo, a geração dos grupos agregados (Tipo III e MMGD), escolhidos pela modalidade publicada, nunca pelo nome ou pelo id, com as regras de duplicatas e de ausências do Tratamento de dados (FR-036 da spec do Tratamento de dados); os valores das usinas Tipo III são marcados como previsão do ONS.

  O comando termina com 0, 1 ou 2 (FR-005). Ele não usa `--usina` nem lê perfil, salvo para mostrar o slug do perfil de cada usina, achado pelo CEG em `usinas/*/perfil.toml`.
- **FR-052** (cobertura): Para cada usina (linha com CEG de um dos sete tipos) e cada conjunto de série do registro que serve ao tipo, o catálogo DEVE gravar em `cobertura.csv` o nível:
  - `proprio`: linhas com o identificador da usina e valor preenchido;
  - `conjunto`: linhas com valor do conjunto da usina, inclusive quando a usina tem linhas próprias sem valor;
  - `agregado`: usina Tipo III, que só existe no grupo agregado do estado;
  - `ausente`.

  Junto, o identificador usado, as linhas, as linhas sem valor, o arquivo e a data de publicação verificados. A verificação usa o arquivo mais recente de cada conjunto de série e sempre os códigos, nunca o nome: o CEG nos indicadores e no despacho; o id ONS na disponibilidade, na geração, no fator de capacidade e nas restrições; o id do conjunto na geração, no fator de capacidade e na razão da restrição; o `cod_usina` dos Reservatórios na EVT e nos dados hidrológicos (sem linha nos Reservatórios, `ausente`); na programação, os códigos ligados à usina ou ao conjunto presentes no arquivo; no CVU, os códigos de planejamento do CEG presentes no último mês do despacho. A restrição com detalhe só tem o nível da usina. `usinas.csv` traz o melhor nível da usina em `cobertura_resumo`.
- **FR-053** (rascunho do perfil): O comando `python -m src perfil --ceg <CEG> [--slug <slug>]` DEVE ler só `data/catalogo/`, sem acessar o portal, sem ler os brutos e sem executar etapa, e:
  - recusar, sem gravar: o slug fora do padrão ou `carteiras` (código 2); o catálogo ausente ou em formato antigo (código 5); o CEG fora do catálogo (código 2); o tipo fora dos sete (código 2); a usina Tipo III, ou só com cobertura agregada ou ausente, com a mensagem que indica o panorama da carteira do estado (código 2);
  - com perfil existente, na pasta do slug ou em outra com o mesmo CEG, nunca sobrescrever: só mostrar as diferenças entre o perfil e o catálogo (tipo, modalidade, estado, CEG, os identificadores que o perfil traz, os códigos de programação, nas térmicas o subsistema e os códigos de planejamento, e a `[cobertura]`, inclusive as chaves que o perfil não tem) e sair com 6, ou com 0 sem diferença;
  - gravar o rascunho, com o slug informado ou derivado do nome da usina (sem acento, em minúsculas e com `_`), `situacao = "rascunho"`, a lista `pendentes` e a origem de cada valor em comentário (`contracts/perfil-usina.md`, seção "Rascunho"), com:
    - os identificadores (CEG, id ONS quando há e id do conjunto) e o subsistema; nas hidrelétricas com linha nos Reservatórios, `cod_usina`, `nome_ons` (o nome do reservatório, sem acento e em maiúsculas) e `id_reservatorio`;
    - a `[cobertura]` do catálogo, só com os conjuntos de série do registro;
    - `codigos_programacao`: todos os códigos ligados à usina ou ao conjunto, de qualquer arquivo, com o primeiro e o último dia de cada um em comentário, para o fiscal conferir. A lista é simples, sem período por código; o Tratamento de dados soma por patamar os códigos vigentes em cada dia. Sem código ligado, o campo fica pendente, com a lista dos códigos do estado para o fiscal escolher;
    - nas térmicas, `[[identificacao.planejamento]]`, de `planejamento.csv`, com o nome publicado em comentário;
    - os `[[identificacao.membros]]` da composição vigente do conjunto;
    - as unidades ativas da Capacidade de geração (potência instalada, unidades e a potência unitária, ou a lista quando diferem; nas térmicas, o combustível), com a fonte; a potência autorizada do cadastro diferente da soma das unidades vai para um comentário, para o fiscal decidir com a fonte;
    - o ano de início da operação comercial pela primeira unidade ativa, a conferir;
    - os demais campos do tipo como pendentes, em linhas comentadas, cada uma com o campo da fonte;
  - conferir a gravação no disco e que o rascunho é TOML válido.

**Série de referência, período e trechos (US8)**

- **FR-054** (série de referência e trechos): A série de referência DEVE ser escolhida pelo tipo e pela cobertura do perfil:

  | Situação | Série de referência | Identificador |
  |---|---|---|
  | UHE, PCH ou CGH com a EVT coletada | Energia Vertida Turbinável (FR-041) | `cod_usina` |
  | usina com geração própria (`geracao = "proprio"`) | Geração por usina | id ONS da usina |
  | usina em conjunto, sem série própria (`geracao = "conjunto"`) | Geração por usina do conjunto | id do conjunto |
  | usina que mudou de nível no período (`geracao = ["proprio", "conjunto"]`) | as duas séries da Geração por usina; cada hora vale pela da usina quando ela tem valor | id ONS e id do conjunto |
  | EOL ou UFV sem geração própria, com série própria na restrição com detalhe (FR-059) | restrição com detalhe | id ONS da usina |

  - Fora da EVT, a série é varrida em todos os arquivos publicados, com o filtro do identificador na leitura do Parquet. O período vai da primeira à última hora com valor; linha sem valor não conta. Com a cobertura `["proprio", "conjunto"]`, o período é a união das duas séries.
  - Na usina em conjunto sem série própria, as horas do conjunto só DEVEM contar enquanto a usina está na composição, entre a data de entrada e a de saída da linha dela na Composição dos conjuntos, coletada antes da série. O período vai da primeira à última hora com valor nesse intervalo. Na Bandeirante, o período começa em 22/08/2019, e não em 01/08/2012: antes da entrada, a geração do conjunto não tem a usina. Com a cobertura `["proprio", "conjunto"]`, o recorte vale só para as horas do nível do conjunto.
  - Sem nenhuma hora com valor na série de referência, ou com a usina ausente da composição do conjunto declarado no perfil, a Coleta DEVE gravar a auditoria da série, não coletar os demais conjuntos e terminar com código 2; na usina fora da composição, a mensagem cita o CEG e o id do conjunto. Sem série de referência possível na `[cobertura]`, a Coleta DEVE ser recusada com código 1, sem coletar nada.
  - Fora da hidrelétrica com EVT, DEVEM ser gravados:
    - a série de referência no período: `geracao_extraido.parquet`, uma linha por hora, a da usina quando ela tem valor e senão a do conjunto, com as colunas da Geração por usina da UHE; ou `restricao_detalhe_extraido.parquet`, na restrição com detalhe; com a auditoria do conjunto;
    - `geracao_complemento.parquet`, com a modalidade de operação e o nível (`usina` ou `conjunto`) de cada hora;
    - `trechos.csv`: o período dividido a cada mudança de modalidade, de nível, de composição do conjunto ou de código de planejamento, com a composição e os tipos da composição de cada trecho, os códigos vigentes e a marca `mostrar`, verdadeira no trecho que muda o nível ou a composição em relação ao vizinho (só esses aparecem no relatório; a mudança só de modalidade ou de código fica na planilha);
    - `capacidade_ficha.csv`, as unidades geradoras do CEG da usina na Capacidade de geração, com as datas e os agentes;
    - na usina em conjunto (com `id_conjunto`), `composicao_conjunto.csv`, a composição do conjunto, com as datas de cada usina.
  - Na Bandeirante, com o recorte, os trechos são três: com as cinco UTE e sem a Areado, até 26/09/2019; com a Areado, até 30/06/2025; só com as quatro PCH, desde 01/07/2025.
  - A hidrelétrica com EVT segue o caminho da EVT, sem trechos (FR-017).
- **FR-059** (série de referência das eólicas e solares em conjunto): EOL ou UFV sem geração própria e com série própria na restrição com detalhe DEVEM ter como série de referência a geração verificada da usina nessa base (`val_geracaoverificada`), pelo id ONS, varrida em todos os arquivos publicados; o período vai da primeira à última semi-hora com valor. O complemento horário e os trechos ficam por hora cheia, com a primeira meia-hora com valor de cada hora.

**Conjuntos das térmicas (US8)**

- **FR-055** (conjuntos das térmicas): Em UTE e UTN, conforme a `[cobertura]`, a Coleta DEVE obter:
  - **Geração térmica por motivo de despacho** (`geracao-termica-despacho-2`): identificador o CEG; conferência o código de planejamento entre os do perfil, no período de cada um, comparado como número (o ONS o publica ora inteiro, ora decimal); linha com o CEG e código fora da lista ou fora do período conta como "só identificador";
  - **CVU das usinas térmicas** (`cvu-usitermica`): identificador o código de planejamento entre os do perfil, comparado como número (o CVU não tem CEG); conferência o subsistema do perfil; todas as revisões, cuja escolha fica com o Tratamento de dados; o instante gravado é o início da semana operativa;
  - **CMO semanal** (`cmo-semanal`): identificador o subsistema do perfil, sem conferência; nível agregado (contexto do subsistema); obtido sempre que o perfil traz `usina.subsistema`, sem entrar na `[cobertura]`.

  Grava `despacho_extraido.parquet`, `cvu_extraido.parquet` e `cmo_extraido.parquet`, com as auditorias dos conjuntos horários (FR-046). Nomes nunca identificam nem conferem: o ONS grafa "Willian" e "William".

**Conjuntos das eólicas e solares (US8)**

- **FR-057** (conjuntos das renováveis): Em EOL e UFV, conforme a `[cobertura]`, a Coleta DEVE obter:
  - **Fator de capacidade** (`fator-capacidade-2`, horário): da usina, pelo id ONS, conferido pelo CEG; do conjunto, pelo id do conjunto, conferido pelo estado (o CEG das linhas de conjunto é "-");
  - **Restrição com detalhe** (`restricao_coff_eolica_detail` ou `restricao_coff_fotovoltaica_detail`, pela variante do tipo; semi-horária): pelo id ONS da usina, conferida pelo CEG. O id do conjunto (`id_ons_conjuntousina`) é guardado como texto, sem servir de conferência, porque falta de 05 a 12/2024 na fotovoltaica;
  - **Restrição com a razão** (`restricao_coff_eolica_usi` ou `restricao_coff_fotovoltaica`, semi-horária): da usina, pelo id ONS, conferida pelo CEG; do conjunto, pelo id do conjunto, conferida pelo estado;
  - com `[[identificacao.membros]]`, também as linhas das outras usinas do conjunto na restrição com detalhe, pelo id ONS e pelo CEG de cada uma, guardadas à parte, como contexto identificado (princípio III), só para a conferência da soma das usinas com a geração do conjunto (spec da Conferência).

  Grava `fator_capacidade_extraido.parquet` e `restricao_razao_extraido.parquet`, com o nível (`usina` ou `conjunto`) em cada linha, `restricao_detalhe_extraido.parquet` e `restricao_membros_extraido.parquet`, com o id ONS de cada membro, e as auditorias dos conjuntos horários (FR-046). Nomes nunca identificam nem conferem: o ONS grafa "230kV" e "230 kV".
- **FR-058** (motor semi-horário): O motor comum DEVE ler as séries semi-horárias como publicadas, sem levar à hora (isso é do Tratamento de dados). Coluna de valor ausente num arquivo (as cinco colunas da fotovoltaica de 05 a 12/2024) fica vazia e é citada na mensagem da auditoria, sem falha do arquivo; a ausência da coluna do identificador ou da conferência continua falha (FR-036). A extração dos conjuntos horários da UHE não muda.

**Usinas em conjunto (US8)**

- **FR-060** (unidades das usinas do conjunto): Na usina em conjunto, a Coleta DEVE gravar `capacidade_membros.csv`: as unidades geradoras da Capacidade de geração de cada usina que esteve na composição em algum momento do período, com o CEG e o nome da usina, a potência efetiva e as datas de entrada em operação e de desativação. Elas dão a potência de cada usina em cada trecho, sem dividir número do conjunto.
  - Identificação: o CEG da usina na composição; conferência: o subsistema da linha da usina na composição. O estado não serve: o Conj. Chapadão, de MS, teve duas UTE cadastradas em GO.
  - As linhas em que só o CEG confere não são extraídas: vão para `auditoria_capacidade_membros.csv`, com aviso no log. A auditoria traz também a quantidade de usinas da composição no período e a das que têm unidades.
  - O arquivo é novo; `capacidade_ficha.csv` continua só com as unidades da usina.
- **FR-061** (tipo publicado da série do conjunto): Na usina cuja série de referência é a Geração por usina do conjunto, a Coleta DEVE gravar `tipo_publicado.csv`: por trecho, o tipo e o combustível publicados (`nom_tipousina` e `nom_tipocombustivel`), com as horas de cada um. A comparação com os tipos da composição fica com as Análises, na qualidade dos dados: o tipo da usina vem do CEG, e a divergência é registrada (FR-060 da spec das Análises). O arquivo é novo; os arquivos existentes não mudam.

### Aplicabilidade por tipo

`S` = coletado quando a `[cobertura]` declara `proprio` ou `conjunto`; `sempre` = coletado sem entrar na `[cobertura]`; `—` = não se aplica. Na UHE sem `[cobertura]`, valem os dez conjuntos da UHE (FR-016). A exigência dos campos do perfil por tipo está na FR-006.

**Conjuntos coletados**

| Conjunto | UHE | PCH e CGH | UTE e UTN | EOL e UFV |
|---|---|---|---|---|
| Energia Vertida Turbinável | S | S | — | — |
| Indicadores e taxas (quatro conjuntos) | S | S | S | — |
| Programação diária | S | S | S | S |
| Disponibilidade por usina | S | S | S | — |
| Dados hidrológicos horários | S | S | — | — |
| Geração por usina (da usina ou do conjunto) | S | S | S | S |
| Modalidade das usinas | sempre | sempre | sempre | sempre |
| Capacidade de geração | sempre, com `[cobertura]` | sempre | sempre | sempre |
| Composição dos conjuntos | — | sempre, em conjunto | sempre, em conjunto | sempre, em conjunto |
| Geração térmica por motivo de despacho | — | — | S | — |
| CVU das usinas térmicas | — | — | S | — |
| CMO semanal | — | — | sempre, com `usina.subsistema` | — |
| Fator de capacidade | — | — | — | S |
| Restrição com detalhe | — | — | — | S (variante eólica na EOL, fotovoltaica na UFV) |
| Restrição com a razão | — | — | — | S (variante do tipo) |
| Reservatórios | só no catálogo | só no catálogo | — | — |

**Série de referência, período e arquivos da usina**

| Regra ou arquivo | UHE | PCH e CGH | UTE e UTN | EOL e UFV |
|---|---|---|---|---|
| Série de referência na EVT, sem trechos | com EVT | com EVT | — | — |
| Série de referência na Geração por usina da usina | com geração própria | com geração própria | com geração própria | com geração própria |
| Série de referência na Geração por usina do conjunto | — | em conjunto, sem série própria | em conjunto, sem série própria | em conjunto, sem série própria nem restrição com detalhe |
| Série de referência na restrição com detalhe (FR-059) | — | — | — | em conjunto, com série própria na restrição |
| Período recortado pela composição (FR-054) | — | em conjunto, sem série própria | em conjunto, sem série própria | em conjunto, sem série própria |
| `trechos.csv` e `geracao_complemento.parquet` | sem EVT | sem EVT | sempre | sempre |
| `composicao_conjunto.csv` e `capacidade_membros.csv` (FR-060) | — | em conjunto | em conjunto | em conjunto |
| `tipo_publicado.csv` (FR-061) | — | série do conjunto | série do conjunto | série do conjunto |
| `restricao_membros_extraido.parquet` | — | — | — | com `[[identificacao.membros]]` |
| `datas_obtencao.csv` | sempre | sempre | sempre | sempre |
| `dicionario_evt.json` | com EVT | com EVT | — | — |
| Programação diária com os códigos de todo o período (catálogo e rascunho) | S | S | S | S |

---

### Key Entities

- **Perfil da usina**: tipo, modalidade, situação (rascunho ou conferido), nome, nome curto, estado, início da operação comercial, identificadores nos conjuntos do ONS (inclusive o conjunto de usinas, os códigos de programação e, nas térmicas, os de planejamento), a cobertura de cada conjunto de série, os parâmetros técnicos do tipo com a fonte, os limiares próprios das análises e os textos próprios da usina para o relatório.
- **Manifesto da etapa** (`etapa.json`): etapa, usina, situação, código de saída, datas, etapa anterior usada, arquivos gravados com SHA-256 e resumo.
- **Registro dos conjuntos**: para cada conjunto do ONS, a chave, o pacote, a pasta, os tipos, os níveis, a resolução, os formatos, o identificador e as conferências e se pode ser a série de referência.
- **Conjunto do ONS**: nome, id no catálogo, pasta em `data/raw/`, formatos, identificador de extração e conferência.
- **Cobertura**: para uma usina e um conjunto de série, o nível em que o ONS a publica: próprio, do conjunto, agregado ou ausente.
- **Catálogo de usinas**: as linhas do cadastro do ONS, com tipo, modalidade, estado, potência, conjunto, unidades, códigos e a cobertura de cada conjunto, com a data do cadastro e dos arquivos verificados.
- **Rascunho do perfil**: o perfil montado do catálogo, em `rascunho`, com a origem de cada valor e os pendentes, a conferir e completar pelo fiscal.
- **Série de referência**: a série que define o período da análise, escolhida pelo tipo e pela cobertura.
- **Trecho**: intervalo do período sem mudança de modalidade, de nível do dado, de composição do conjunto nem de código de planejamento.
- **Manifesto de versões** (`_manifesto_ons.json`): por arquivo bruto, a versão obtida, as datas de publicação e de registro, os tamanhos, a origem do registro e as versões anteriores preservadas e excluídas.
- **Versão anterior preservada**: cópia de uma versão substituída, com data de publicação, tamanho, SHA-256 e data do arquivamento; no máximo duas por arquivo.
- **Dicionário de dados**: PDF ou JSON de um conjunto, com o resultado e a data da última obtenção, o SHA-256 e as versões anteriores.
- **Linha extraída**: linha da usina num conjunto, com as colunas publicadas, o instante como publicado e o arquivo de origem.
- **Base de EVT extraída**: linhas da usina na EVT, uma por instante, em ordem cronológica; define o período dos demais conjuntos na hidrelétrica com EVT.
- **Ficha cadastral**: dados de identificação da usina no cadastro do ONS, com a data da consulta e a contagem de homônimos.
- **Auditoria da extração**: uma linha por arquivo de cada conjunto, com as contagens e a situação.
- **Datas de obtenção**: por conjunto da usina, os arquivos registrados, a publicação e a obtenção mais recentes, que as etapas seguintes leem no lugar dos manifestos.
- **Cópia de segurança**: pasta datada com o código, os documentos do projeto e os relatórios de referência, com a lista conferida dos arquivos; no máximo duas.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100 % dos arquivos no escopo de cada conjunto (FR-017) são obtidos ou registrados como não obtidos, e 100 % dos arquivos lidos têm uma linha na auditoria, inclusive os sem linhas da usina.
- **SC-002**: 100 % das linhas extraídas têm o identificador e a conferência do perfil, salvo as exceções da FR-036; nenhuma linha de homônimo é extraída; 100 % das linhas que conferem só em parte estão contadas na auditoria. Num teste com a mesma usina sob dois nomes de agente, nenhuma linha se perde.
- **SC-003**: Em cada conjunto, exceto no cadastro, a soma das linhas da usina na auditoria é igual à quantidade de linhas extraídas, contadas antes de juntar as repetições, mais as linhas da usina sem instante válido, que não são extraídas (instante vazio, na EVT; não interpretável, nos conjuntos horários). A EVT extraída não tem dois registros no mesmo instante e está em ordem cronológica.
- **SC-004**: Uma segunda coleta sem novidade no portal não baixa nenhum arquivo de dados e gera extraídos com o mesmo conteúdo. Com `--sem-portal`, nenhum arquivo de `data/raw/` é criado, alterado ou excluído.
- **SC-005**: No teste de republicação, 100 % das versões substituídas por conteúdo diferente ficam preservadas e registradas, até o limite: nenhum arquivo passa de duas versões anteriores, e as que ficam são as duas mais recentes. Os extraídos são iguais aos obtidos só com as versões correntes.
- **SC-006**: Depois de cada coleta que consulta o portal, os dicionários dos conjuntos da usina, em PDF e JSON (na UHE sem `[cobertura]`, os 20 dos dez conjuntos), estão obtidos ou com a situação registrada. No teste com dicionário alterado, a versão anterior fica preservada em 100 % dos casos.
- **SC-007**: Num arquivo de teste com 1 linha curta e 1 longa, a auditoria registra 2 linhas irregulares, e o log as avisa; nos arquivos atuais da EVT, a contagem é 0.
- **SC-008**: Com `--log-level WARNING`, nenhum comando emite mensagem informativa, de nenhum módulo.
- **SC-009**: 100 % dos perfis inválidos dos testes (campo obrigatório faltante, texto opcional vazio, tipo ou faixa errados, incoerência e slug diferente da pasta) são recusados com código 4, antes de gravar qualquer arquivo, com todos os problemas na mensagem.
- **SC-010**: O fluxo completo roda com um único comando, e cada uma das cinco etapas roda sozinha. Em 100 % das tentativas de rodar uma etapa sem a anterior concluída, ela termina com código 5, mostra a mensagem e não grava nada.
- **SC-011**: Nunca existem mais de duas cópias de segurança. No teste de falha na criação, a cópia incompleta é apagada e as existentes ficam intactas.
- **SC-012**: Com os arquivos já baixados, `python -m src coleta --usina <slug> --sem-portal` termina em menos de 10 minutos, e a leitura e a consolidação da EVT, em menos de 3 minutos.
- **SC-013**: Com o perfil de uma usina fictícia e arquivos sintéticos, sem rede, a coleta extrai só as linhas dela, os arquivos brutos já baixados servem a ela sem novo download, e cada usina tem a sua pasta `data/usinas/<slug>/coleta/`.
- **SC-014** (não regressão): Com o perfil da São Domingos e os dados locais, `python -m src coleta --usina sao_domingos --sem-portal` termina com 0, e:
  - a EVT extraída tem os mesmos 70.895 registros da base consolidada atual, de 28/08/2018 00h a 28/09/2026 23h, com os mesmos valores;
  - a auditoria da EVT lista os 42 arquivos, com 2015, 2016 e 2017 sem linhas da usina, nenhum com falha e nenhuma linha que confere só em parte ou irregular;
  - nos demais conjuntos, as linhas lidas, as linhas da usina e a situação de cada arquivo coincidem com as das auditorias atuais;
  - a ficha do cadastro traz os mesmos dados de identificação, data da consulta e homônimos da ficha atual;
  - nenhum arquivo de `data/raw/` é baixado, alterado ou excluído.
- **SC-015**: O catálogo lista 100 % das linhas do cadastro do ONS, cada uma com tipo, modalidade e, nas usinas, a cobertura dos conjuntos de série.
- **SC-016**: O rascunho do perfil de uma usina com dado próprio sai em menos de 1 minuto.
- **SC-017**: Com `data/raw/` vazio, as etapas 2 a 5 rodam a partir da Coleta e geram o mesmo relatório.

---

## Decisões do usuário

| Data | Decisão | Onde se aplica |
|---|---|---|
| 30/09/2026 | Os parâmetros técnicos citam a fonte registrada, o RF 0009/2017-AGEPAN-SFG; o modelo de RF de 2026 da AGEMS não é citado como fonte. No perfil da São Domingos, isso fica em `parametros.fontes`. | FR-006 |
| 02/10/2026 | Garantia física de 36,4 MWmed (ANEEL, valor vigente), no lugar dos 36,9 MWmed do RF de 2017; no perfil da São Domingos, em `parametros.garantia_fisica_mwmed`, com a fonte em `parametros.fontes.garantia_fisica`. | FR-006 |
| 02/10/2026 (reafirmada em 05/10/2026) | Manter a base de EVT local, conferida com a publicada pelo ONS (idêntica de 08/2018 a 08/2026), sem novo download. Para reproduzir o relatório, a coleta roda com `--sem-portal`. | FR-021; SC-014 |
| 02/10/2026 | Restringir os demais conjuntos ao período da base de EVT; a Geração por usina não é estendida para antes de 28/08/2018. | FR-017 |
| 05/10/2026 | Identificar a usina na EVT pelo código da usina, conferido pelo nome do reservatório, sem depender do nome do agente (que mudou em 03/2026), no lugar da linha de texto `SE;SUDESTE;PARANA;VERDE;AXIA SUL;SAO DOMINGOS;` pedida no início; aprovado com a constituição. | FR-034 a FR-036 |
| 05/10/2026 | Obter sempre, a cada coleta, os dicionários de dados (PDF e JSON) de todos os conjuntos, para consulta sem acesso ao portal. | FR-031 a FR-033 |
| 05/10/2026 | A cópia `.bak` vale para os arquivos de dados das etapas; manifestos, dicionários e demais arquivos de controle ficam dispensados. | FR-030; FR-047 |
| 05/10/2026 | A conferência externa da base de EVT com os dados do ONS, feita em 02/10/2026, não ganha script nem arquivo de saída no projeto. | Assumptions |
| 07/10/2026 | As dez bases do ONS atuais bastam; nenhuma base nova é incluída. | FR-016 |
| 07/10/2026 | Usar a mesma lógica com outras usinas hidrelétricas, com tudo o que é próprio da usina num perfil. | FR-006 a FR-009 |
| 07/10/2026 | No máximo duas cópias de segurança do projeto, as mais recentes, com a mais antiga excluída só depois de a nova estar conferida; o mesmo limite vale para as versões anteriores de cada arquivo bruto. | FR-014; FR-015; FR-029 |
| 08/10/2026 | A auditoria da Programação diária mantém o nome `linhas_codigo_sem_conferencia` para as linhas só com o código de exibição, como aparece na planilha do relatório. | FR-046 |
| 09/10/2026 | Ampliar o fluxo para todos os tipos de usina que os dados abertos do ONS cobrem (UHE, PCH, CGH, UTE, UTN, EOL e UFV), com o catálogo de usinas e o rascunho do perfil na Coleta, os conjuntos de cada tipo vindos do registro e o tipo e a cobertura no perfil; o perfil da São Domingos ganha só o tipo e a modalidade, e o relatório dela não muda. As cinco limitações da Coleta que só aparecem com outras usinas (recursos repetidos fora dos conjuntos horários, vírgula decimal, normalização dos textos, coluna de conferência ausente e CSV vazio da EVT sem motivo) são corrigidas antes dos conjuntos novos e antes de qualquer download de outra usina. Os comandos novos usam os códigos de saída 0 a 6. Fora da UHE sem `[cobertura]`, esta decisão substitui a de 07/10/2026 sobre as dez bases. | Objetivo; FR-002; FR-005; FR-006 a FR-009; FR-016; FR-019; FR-035; FR-036; FR-039; FR-046; FR-049 a FR-054 |
| 19/10/2026 | O catálogo usa os Reservatórios do ONS para ligar o CEG ao `cod_usina` e ao reservatório da EVT e dos dados hidrológicos; conferido na São Domingos: CEG `UHE.PH.MS.028761-0.01` → `cod_usina` 153 e `id_reservatorio` PNUHSD, os mesmos do perfil aprovado. | FR-051; FR-052; FR-053 |
| 19/10/2026 | Ajustes ao texto a partir do código construído, aprovados: vários códigos de programação por usina, com a conferência só pelo estado fora das hidrelétricas; o panorama dos agregados somado pelo catálogo, com as regras do Tratamento de dados. | FR-043; FR-051 |
| 19/10/2026 | Aprovada a coleta das térmicas: despacho pelo CEG, conferido pelo código de planejamento no período; CVU pelos códigos de planejamento, conferido pelo subsistema; CMO pelo subsistema, como contexto agregado; o subsistema e os códigos de planejamento no perfil e no rascunho. | FR-051; FR-053; FR-055; FR-056 |
| 20/10/2026 | Aprovada a coleta das eólicas e solares: fator de capacidade e restrição com detalhe e com a razão, na variante do tipo, da usina ou do conjunto; as séries semi-horárias lidas como publicadas, com as colunas ausentes contadas sem falha; a restrição com detalhe da usina como série de referência da eólica ou solar em conjunto. | FR-051; FR-053; FR-057 a FR-059 |
| 22/10/2026 | Na usina em conjunto sem série própria, o período é recortado pela entrada e pela saída da usina na composição do conjunto (Bandeirante desde 22/08/2019, e não desde 01/08/2012). | FR-054 |
| 22/10/2026 | A potência das usinas da composição entra na Coleta (`capacidade_membros.csv`), sem dividir número do conjunto. | FR-060 |
| 22/10/2026 | Aprovados: os códigos de programação de todo o período no catálogo e no rascunho, com o primeiro e o último dia de cada um; o tipo publicado da série do conjunto, por trecho; o período das linhas próprias sem valor no resumo. | FR-048; FR-051; FR-053; FR-061 |
| 22/10/2026 | A geração da usina pela CCEE (dados abertos, com download manual) fica como proposta para uma avaliação futura, que pede mudança do princípio IV da constituição; a Coleta continua só com o portal do ONS. | Assumptions |

---

## Assumptions

- **Portal do ONS**: catálogo público no padrão CKAN, sem autenticação. Para cada arquivo de dados, o catálogo informa o tamanho e a data de publicação; para os dicionários, não informa nenhum dos dois.
- **Revisões do ONS**: o ONS republica arquivos já publicados, às vezes com o mesmo tamanho (caso real: o arquivo de 09/2026 da EVT, republicado em 30/09/2026).
- **Publicação**: a estrutura da tabela da FR-016 é a observada em 05/10/2026 nos dez conjuntos da UHE e, nos demais, nos dados abertos consultados em 09/10/2026 (cadastro e conjuntos novos), 19/10/2026 (térmicas), 20/10/2026 (eólicas e solares) e 22/10/2026 (Geração por usina, Programação diária e Composição dos conjuntos do Conj. Chapadão). Os arquivos CSV usam `;` e vêm em UTF-8 ou Latin-1.
- **O que o ONS publica de cada tipo** (cadastro de 09/10/2026, 6.017 linhas, 171 em MS):
  - UHE: da usina (Tipo I, II-A e II-B), com a EVT e os dados hidrológicos;
  - UTE e UTN: da usina, com o despacho por motivo, o CVU e o CMO do subsistema; DISPF e TEIFa/TEIP só de parte delas;
  - EOL e UFV: da usina nos conjuntos de restrição (eólica desde 10/2021; as UFV de MS só desde 08/2026) e, em geral, pelo conjunto de usinas (Tipo II-C) na geração e no fator de capacidade;
  - PCH e CGH: pelo conjunto de usinas (Tipo II-C), com a geração da usina vazia; a maioria é Tipo III;
  - MMGD e Tipo III: só em agregado, por área do estado; aparecem no catálogo (panorama dos agregados), sem perfil.
- **Dados brutos**: cerca de 5,8 GB em `data/raw/` em 23/10/2026 (4,1 GB com os conjuntos da UHE), fora do controle de versões e das cópias de segurança. Em CSV, os conjuntos dos demais tipos passariam de 20 GB; por isso, o Parquet sempre que publicado.
- **Rede**: só a Coleta de dados usa a rede. Os testes rodam sem rede, com o catálogo e os arquivos simulados.
- **Parâmetros que o ONS não publica** (garantia física, IP e TEIF de referência, engolimento e tipo de turbina): o usuário os informa no perfil, com a fonte e a data.
- **Fora da coleta**: conjuntos só com agregados do SIN (como a classificação da EVT), bases da CCEE e da ANEEL e o motivo das paradas, que nenhuma base aberta do ONS informa. Conferências feitas por consulta interativa aos dados do ONS não fazem parte do fluxo.
- **Ambiente**: Windows com PowerShell; os exemplos de comando usam essa sintaxe.
