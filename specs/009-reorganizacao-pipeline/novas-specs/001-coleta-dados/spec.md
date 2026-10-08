# Spec da Etapa 1: Coleta de dados

**Etapa**: 1 de 5 · **Status**: aprovada · **Atualizada em**: 2026-10-08

**Fluxo**: Coleta de dados → Tratamento de dados → Conferência → Análises → Geração do relatório

## Objetivo

A Coleta de dados obtém do portal de dados abertos do ONS os arquivos dos dez conjuntos usados no relatório, guarda-os com as versões anteriores e os dicionários de dados, e extrai deles só as linhas da usina definida no perfil. Cada linha é extraída pelo identificador da usina no conjunto e conferida por um segundo campo, e cada arquivo lido entra na auditoria. É a única etapa que acessa o portal. Esta spec reúne também as regras comuns às cinco etapas: linha de comando, códigos de saída, perfil da usina, manifesto da etapa (`etapa.json`), comando `completo` e cópia de segurança do projeto.

## Entradas e saídas

**Lê**
- o perfil da usina, em `usinas/<slug>/perfil.toml` (FR-006 a FR-009);
- o catálogo e os arquivos do portal de dados abertos do ONS, exceto com `--sem-portal`;
- os arquivos já baixados em `data/raw/`.

**Grava em `data/raw/`**, pasta compartilhada por todas as usinas (FR-030):
- os arquivos de dados de cada conjunto, na pasta do conjunto (FR-016);
- o manifesto de versões `_manifesto_ons.json`, em cada pasta (FR-027);
- `_dicionarios/`, com os dicionários de dados e o manifesto deles (FR-031);
- `_versoes_anteriores/`, com no máximo duas versões anteriores por arquivo (FR-028 e FR-029).

**Grava em `data/usinas/<slug>/coleta/`**, pasta da usina (FR-047):

| Arquivo | Conteúdo |
|---|---|
| `evt_extraido.csv` | linhas da usina na Energia Vertida Turbinável (EVT), consolidadas (FR-041) |
| `indicadores_extraido.parquet` | linhas da usina nos dois conjuntos de indicadores por unidade geradora e nos dois de taxas TEIFa e TEIP, com o conjunto de origem (FR-042) |
| `programacao_extraido.parquet` | geração programada da usina por dia e patamar (FR-043) |
| `disponibilidade_extraido.parquet`, `hidrologia_extraido.parquet`, `geracao_extraido.parquet` | linhas da usina nos conjuntos horários, com o instante como publicado (FR-044) |
| `cadastro_ficha.csv` | ficha da usina no cadastro do ONS (FR-045) |
| `auditoria_evt.csv` | auditoria da EVT, uma linha por arquivo (FR-046) |
| `auditoria_indicadores.csv` | auditoria dos quatro conjuntos de indicadores e taxas, uma linha por arquivo, com o conjunto (FR-046) |
| `auditoria_programacao.csv` | auditoria da Programação diária, uma linha por dia com arquivo publicado no período (FR-046) |
| `auditoria_disponibilidade.csv`, `auditoria_hidrologia.csv`, `auditoria_geracao.csv` | auditoria dos conjuntos horários, uma linha por arquivo, com o período e a data de publicação (FR-046) |
| `auditoria_cadastro.csv` | auditoria da leitura do cadastro, com as linhas que têm o CEG do perfil (FR-046) |
| `dicionarios.csv` | registro dos dicionários de dados dos dez conjuntos (FR-032) |
| `etapa.json` | manifesto da etapa, com o resumo da coleta (FR-011 e FR-048) |

**Comando**: `python -m src coleta --usina <slug> [--sem-portal] [--forcar-download] [--log-level <nível>]`
- `--sem-portal`: não consulta o portal e extrai só dos arquivos locais (FR-021);
- `--forcar-download`: baixa de novo todos os arquivos de dados (FR-022).

**Códigos de saída da coleta**: 0 (sucesso), 1 (erro), 2 (arquivo de dados não obtido ou não lido, ou usina sem registro na EVT ou no cadastro) e 4 (perfil inválido). A tabela completa, comum às cinco etapas, está na FR-005.

**Quem usa as saídas**: o Tratamento de dados lê os extraídos e as auditorias. A auditoria da EVT, os manifestos de versões (datas de obtenção e de publicação) e o registro dos dicionários alimentam a cobertura dos dados, as legendas de fonte e as notas do relatório.

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

Como fiscal, quero informar a usina por um perfil com os identificadores dela em cada conjunto do ONS e os parâmetros técnicos com a fonte. Quero que um perfil incompleto ou incoerente seja recusado antes da coleta, com a lista de todos os problemas. Assim uso o mesmo fluxo para outra usina hidrelétrica sem mexer no código e sem produzir um relatório com dados errados.

**Why this priority**: o perfil é a entrada de todas as etapas; um erro nele contamina tudo o que vem depois.

**Independent Test**: executar a coleta com o perfil válido de uma usina fictícia e com perfis com problemas, e conferir o código 4, a mensagem e que nada foi gravado.

**Acceptance Scenarios**:

1. **Given** um perfil válido (perfil da São Domingos), **When** um comando com `--usina sao_domingos` é executado, **Then** o perfil é aceito e a etapa segue.
2. **Given** um perfil sem `parametros.garantia_fisica_mwmed`, **When** qualquer comando com `--usina` começa, **Then** ele termina com código 4 antes da coleta, sem gravar nada, e a mensagem cita o campo.
3. **Given** um perfil em que a potência unitária vezes o número de unidades geradoras difere da potência instalada em mais de 0,1 MW, **When** o comando começa, **Then** o perfil é recusado com código 4, e a mensagem cita a incoerência.
4. **Given** um perfil com vários problemas, **When** o comando começa, **Then** a mensagem lista todos de uma vez, um por linha.
5. **Given** um slug sem pasta em `usinas/`, ou diferente do `usina.slug` do perfil, **When** o comando começa, **Then** o perfil é recusado com código 4.
6. **Given** um perfil sem os campos de texto opcionais, **When** o comando começa, **Then** o perfil é aceito; **Given** um campo de texto opcional presente mas vazio, **Then** o perfil é recusado com código 4.

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
3. **Given** uma cópia criada, **When** aberta, **Then** traz o código, os testes, as specs, os relatórios, as configurações do Spec Kit, os perfis, o README e a lista de dependências, mais `LEIA-ME.txt`, `conftest.py` e `copia.json`, e não traz dados nem documentos.

---

### Edge Cases

- **Perfil ausente ou com problema**: o comando termina com código 4 antes de qualquer ação e lista todos os problemas (FR-009).
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
- **Conjunto sem a usina** (por exemplo, usina fora da Programação diária): os arquivos são lidos e auditados como `SEM_REGISTROS`, o extraído fica vazio e a coleta não falha; as etapas seguintes omitem o que depende dele.
- **Usina sem nenhuma linha na EVT** (identificador errado no perfil, por exemplo): não há período para os demais conjuntos. A coleta grava a auditoria da EVT, que mostra as linhas que conferem só em parte, avisa no log, não coleta os demais conjuntos e termina com código 2.
- **Usina fora do cadastro**: a coleta grava a auditoria do cadastro e termina com código 2.
- **Cabeçalho com as colunas em outra ordem**: as colunas são localizadas pelo nome.
- **Formato compacto ausente em parte dos meses** (perfil da São Domingos: Disponibilidade por usina de 08/2018 a 12/2022): o mês vem do CSV. A ausência da usina num mês nunca é tirada de um arquivo que não cobre o mês.
- **Mesmo arquivo listado duas vezes no catálogo** (Dados hidrológicos horários de 10/2026, com tamanhos diferentes): fica o recurso com data de publicação ou, em empate, o maior; a repetição vai para o manifesto e para a auditoria.
- **Números publicados como texto em alguns arquivos**: são lidos como número; o que não for número fica ausente e é contado como valor inválido.
- **Campos vazios** (nível de jusante e vazão vertida não turbinável, por exemplo): ficam ausentes, nunca zero.
- **Horas ausentes na fonte** (perfil da São Domingos: 04/11/2018 00h, início do horário de verão, ausente na EVT): a coleta não cria nem preenche horas.
- **Programação diária**: data interna publicada em dois formatos; dia com patamares faltando (`INCOMPLETO`); patamar repetido no mesmo arquivo (fica a última ocorrência).
- **Dicionário não publicado num formato, ou catálogo de dicionários inacessível**: a situação vai para o registro, sem falha.
- **Cópia de segurança com falha**: a cópia incompleta é apagada, e nenhuma cópia existente é excluída.

---

## Requirements *(mandatory)*

### Functional Requirements

As FR-001 a FR-015 são regras comuns às cinco etapas. As specs das demais etapas trazem só o seu comando, as suas opções, os seus códigos de saída, as suas pastas e o resumo do seu `etapa.json`.

**Fluxo e linha de comando (US4)**

- **FR-001**: O projeto DEVE ter um único fluxo, com cinco etapas nesta ordem: Coleta de dados, Tratamento de dados, Conferência, Análises e Geração do relatório. Cada etapa DEVE usar só os resultados gravados pelas anteriores e gravar os seus para as seguintes. Só a Coleta de dados DEVE acessar o portal do ONS.
- **FR-002**: O fluxo DEVE ter uma única linha de comando, `python -m src <comando> --usina <slug> [opções]`, que roda sem interação com o usuário. O slug é o nome da pasta da usina em `usinas/`, e `--usina` é obrigatório nos comandos de etapa e no `comparar`. Os comandos são:

  | Comando | Faz | Opções próprias |
  |---|---|---|
  | `coleta` | Coleta de dados (esta spec) | `--sem-portal`, `--forcar-download` |
  | `tratamento` | Tratamento de dados | nenhuma |
  | `conferencia` | Conferência | nenhuma |
  | `analises` | Análises | nenhuma |
  | `relatorio` | Geração do relatório | `--data-geracao` (spec da Geração do relatório) |
  | `completo` | as cinco etapas, na ordem (FR-003) | as da `coleta` e as do `relatorio` |
  | `copia-seguranca --motivo <texto>` | cópia de segurança do projeto (FR-014); não usa `--usina` | nenhuma |
  | `comparar --usina <slug> --referencia <pasta>` | compara o relatório da usina com o de outra pasta (spec da Geração do relatório) | nenhuma |

  NÃO DEVE haver outro ponto de entrada, nem opção para executar ou pular um conjunto do ONS ou parte de uma etapa: os dez conjuntos fazem parte da coleta.
- **FR-003**: O comando `completo` DEVE executar as cinco etapas na ordem e parar na primeira que não terminar com 0, saindo com o código dela.
- **FR-004**: A opção `--log-level`, comum a todos os comandos, DEVE aceitar `DEBUG`, `INFO`, `WARNING` e `ERROR` (padrão `INFO`) e valer para todos os módulos executados na chamada. O log DEVE sair só na saída padrão, no formato `AAAA-MM-DD HH:MM:SS [NÍVEL] módulo - mensagem`, sem arquivo de log. Ao final de cada etapa, o log DEVE mostrar o resumo da etapa (FR-011) e o caminho da pasta de saída.
- **FR-005**: Os comandos DEVEM terminar com estes códigos de saída:

  | Código | Significado |
  |---|---|
  | 0 | sucesso (no `comparar`, nenhuma diferença) |
  | 1 | erro: catálogo do ONS inacessível, dado que impede a etapa, falha de gravação (com o arquivo restaurado), erro inesperado ou interrupção pelo usuário |
  | 2 | arquivo de dados não obtido ou não lido, ou usina sem registro na EVT ou no cadastro (Coleta de dados); também opção inválida na linha de comando, recusada antes de qualquer execução |
  | 3 | conferência das vazões com a hidrologia abaixo da meta (Conferência) |
  | 4 | perfil da usina inválido; a mensagem lista os problemas (FR-009) |
  | 5 | etapa anterior sem resultado concluído: ausente, ilegível, com falha, desatualizada ou em formato antigo; nada é gravado (FR-012) |
  | 6 | o `comparar` encontrou diferenças |

**Perfil da usina (US3)**

- **FR-006**: Todo valor próprio de uma usina DEVE estar no perfil dela, `usinas/<slug>/perfil.toml`, em UTF-8 e no formato TOML, com comentários (`#`) para registrar a origem de cada valor. O fluxo DEVE receber o perfil como entrada. Os campos desta tabela são obrigatórios:

  | Campo | Tipo | Validação |
  |---|---|---|
  | `usina.slug` | texto | letras minúsculas, algarismos e `_`; igual ao nome da pasta |
  | `usina.nome` | texto | não vazio; é o nome usado no título e nos textos |
  | `usina.nome_curto` | texto | não vazio; é o nome da usina sem o tipo, usado nas frases sobre homônimos |
  | `usina.estado` | texto | 2 letras maiúsculas |
  | `usina.inicio_operacao_comercial` | inteiro | de 1900 até o ano atual |
  | `identificacao.cod_usina` | inteiro | > 0 |
  | `identificacao.nome_ons` | texto | não vazio, em maiúsculas e sem acento; nome da usina e do reservatório nos conjuntos do ONS |
  | `identificacao.ceg` | texto | no padrão da ANEEL `UHE.PH.UF.NNNNNN-D.DD` |
  | `identificacao.id_ons` | texto | não vazio |
  | `identificacao.cod_programacao` | texto | não vazio |
  | `identificacao.id_reservatorio` | texto | não vazio |
  | `parametros.potencia_instalada_mw` | real | > 0 |
  | `parametros.unidades_geradoras` | inteiro | ≥ 1 |
  | `parametros.potencia_unitaria_mw` | real | > 0; vezes `unidades_geradoras`, igual a `potencia_instalada_mw`, com tolerância de 0,1 MW |
  | `parametros.tipo_turbina` | texto | não vazio |
  | `parametros.engolimento_nominal_ug_m3s` | real | > 0 |
  | `parametros.garantia_fisica_mwmed` | real | > 0 e ≤ `potencia_instalada_mw` |
  | `parametros.ip_referencia` | real | ≥ 0 e < 1 |
  | `parametros.teif_referencia` | real | ≥ 0 e < 1 |
  | `parametros.queda_bruta_m` | real | > 0 |
  | `parametros.perda_hidraulica_m` | real | ≥ 0 e < `queda_bruta_m` |
  | `parametros.rendimento_turbina_gerador` | real | > 0 e ≤ 1 |
  | `parametros.vazao_remanescente_m3s` | real | ≥ 0 |
  | `parametros.fontes.geral` | texto | não vazio; fonte e data dos parâmetros |
  | `parametros.fontes.garantia_fisica` | texto | não vazio; fonte e data da garantia física |
  | `analises.vertimento_minimo_m3s` | real | ≥ 0 (0 = usina sem vertimento contínuo) |
  | `analises.faixas_geracao_mw` | lista de reais | crescente; cada valor acima do limiar de usina parada (1 MW) e abaixo da plena carga (90 % da potência instalada) |

  Os campos de texto desta segunda tabela são opcionais e, quando presentes, NÃO DEVEM estar vazios. Eles levam ao relatório os trechos próprios da usina; sem um deles, o relatório omite o trecho correspondente (spec da Geração do relatório):

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
- **FR-009**: Um perfil ausente, ilegível, com campo obrigatório faltante, com texto opcional vazio, com tipo ou faixa errados ou com incoerência DEVE ser recusado com código 4, sem gravar nada. A mensagem DEVE listar todos os problemas de uma vez, um por linha, depois do cabeçalho `Perfil da usina '<slug>' inválido (usinas/<slug>/perfil.toml):`.

**Pastas e manifesto da etapa (US4)**

- **FR-010**: Os arquivos do fluxo DEVEM ficar nestas pastas:

  | Pasta | Conteúdo |
  |---|---|
  | `usinas/<slug>/` | perfil da usina (`perfil.toml`) e, fora do controle de versões, os documentos de referência da usina (`documentos/`) |
  | `data/raw/` | dados brutos do ONS, compartilhados por todas as usinas e gravados só pela Coleta de dados |
  | `data/usinas/<slug>/coleta/`, `tratamento/`, `conferencia/` e `analises/` | resultados de cada etapa, separados por usina |
  | `reports/<slug>/` | relatório da usina |

  Cada etapa DEVE gravar só na sua pasta (a Coleta de dados também em `data/raw/`), sem tocar nos resultados de outra usina.
- **FR-011**: Cada etapa DEVE gravar, na sua pasta, o manifesto `etapa.json`, com:

  | Campo | Conteúdo |
  |---|---|
  | `etapa` | `coleta`, `tratamento`, `conferencia`, `analises` ou `relatorio` |
  | `usina` | slug |
  | `versao_formato` | inteiro que muda quando os arquivos da etapa mudam de formato |
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
  - `LEIA-ME.txt`, com a data, o motivo e o que foi copiado;
  - `conftest.py`, que impede os testes de varrerem a cópia;
  - `copia.json`, com o nome, o tamanho e o SHA-256 de cada arquivo copiado.

  A cópia NÃO DEVE incluir os dados brutos, os dados das etapas nem os documentos de referência.
- **FR-015**: Depois de criar a cópia, o comando DEVE conferi-la (quantidade de arquivos e SHA-256 de cada um, contra `copia.json`) e só então excluir as cópias mais antigas, pela data do nome da pasta e, no empate, pela data de criação, até ficarem duas. Se a criação ou a conferência falhar, DEVE apagar a cópia incompleta, não excluir nenhuma outra e terminar com código 1. Um motivo com caractere que não seja letra, algarismo, `_` ou `-`, ou uma cópia com o mesmo nome já existente, DEVE terminar com código 1, sem criar nem excluir nada.

**Conjuntos, período e opções da coleta (US1)**

- **FR-016**: A Coleta de dados DEVE cobrir estes dez conjuntos do ONS, e só eles:

  | Conjunto do ONS | Id no catálogo | Pasta em `data/raw/` | Como o ONS publica | Formato obtido |
  |---|---|---|---|---|
  | Energia Vertida Turbinável | `energia-vertida-turbinavel` | a própria `data/raw/` | um arquivo por ano até 2023 e um por mês desde 2024 | CSV |
  | Indicadores de disponibilidade por unidade geradora, base mensal | `ind_disponibilidade_fgeracao_uge_mensal` | `indicadores_ons/ind_disponibilidade_fgeracao_uge_mensal/` | um arquivo por ano | CSV |
  | Indicadores de disponibilidade por unidade geradora, base anual | `ind_disponibilidade_fgeracao_uge_anual` | `indicadores_ons/ind_disponibilidade_fgeracao_uge_anual/` | arquivo único | CSV |
  | Parâmetros das taxas TEIFa e TEIP | `taxa_teif_teip_parametro` | `indicadores_ons/taxa_teif_teip_parametro/` | um arquivo por ano | CSV |
  | Taxas TEIFa e TEIP | `taxa_teif_teip` | `indicadores_ons/taxa_teif_teip/` | arquivo único | CSV |
  | Programação diária | `programacao_diaria` | `programacao_diaria/` | um arquivo por dia, em três formatos | Parquet |
  | Disponibilidade por usina | `disponibilidade_usina` | `disponibilidade_usina/` | um arquivo por mês, em CSV; em Parquet só em parte dos meses | Parquet; CSV no mês sem Parquet |
  | Dados hidrológicos horários | `dados_hidrologicos_ho` | `dados_hidrologicos_ho/` | um arquivo por mês, em Parquet; alguns meses só em CSV | Parquet; CSV no mês sem Parquet |
  | Geração por usina | `geracao-usina-2` | `geracao_usina_2/` | um arquivo por ano até 2021 e um por mês desde 2022 | Parquet; CSV no período sem Parquet |
  | Modalidade das usinas | `modalidade-usina` | `modalidade_usina/` | arquivo único, regravado pelo ONS, sem série histórica | CSV |

- **FR-017**: A coleta DEVE tratar primeiro a EVT, que define o período da base de EVT: do primeiro ao último instante extraído da usina. Na EVT, DEVE obter e ler todos os arquivos publicados, sem supor data de início de operação da usina. Nos demais conjuntos, DEVE obter e ler os arquivos cujo ano, mês ou dia, pelo nome do arquivo, se sobrepõe ao período e, nos conjuntos publicados em arquivo único, esse arquivo.
- **FR-018**: Nos conjuntos publicados em dois formatos, a coleta DEVE obter cada período (ano ou mês) no formato compacto (Parquet), quando ele é publicado para aquele período, e senão no CSV. Na Programação diária, DEVE obter um arquivo por dia, no formato compacto.
- **FR-019**: Quando o catálogo lista o mesmo arquivo mais de uma vez, a coleta DEVE usar o recurso com data de publicação e, em empate, o maior, e registrar a quantidade de repetições no manifesto e na auditoria.
- **FR-020**: A coleta DEVE tratar os conjuntos na ordem da tabela da FR-016 e parar no primeiro conjunto com falha (código 1 ou 2), depois de gravar o que dele já foi lido e a auditoria; os conjuntos seguintes não são coletados nessa execução. Os quatro conjuntos de indicadores e taxas formam um bloco: são sincronizados e lidos juntos, e a falha em qualquer um deles para a coleta depois do bloco.
- **FR-021**: Com `--sem-portal`, a coleta NÃO DEVE consultar o portal. DEVE extrair só dos arquivos locais, com as mesmas regras de período e formato, e NÃO DEVE criar, alterar nem excluir nada em `data/raw/`. Os dicionários não são obtidos, e o registro deles é montado a partir dos manifestos locais.
- **FR-022**: Com `--forcar-download`, a coleta DEVE baixar de novo todos os arquivos de dados dos dez conjuntos, sem o reaproveitamento da FR-024. Com `--sem-portal`, a opção não tem efeito.

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
  - os arquivos baixados uma vez servem a qualquer usina;
  - arquivos brutos, manifestos e dicionários não têm cópia `.bak`: as versões anteriores cumprem esse papel.

**Dicionários de dados (US5)**

- **FR-031**: Sempre que consulta o portal, a coleta DEVE obter os dicionários de dados publicados dos dez conjuntos, em PDF e em JSON (os recursos desses formatos cujo nome, sem acento, contém "dicionario"), também quando a coleta para num conjunto com falha (código 2). Eles são sempre baixados, porque o catálogo não informa data nem tamanho deles, e ficam em `<pasta do conjunto>/_dicionarios/` (os da EVT, em `data/raw/_dicionarios/`), com manifesto próprio.
- **FR-032**: Cada dicionário obtido DEVE ser comparado pelo conteúdo (SHA-256) com a cópia local, com o resultado `NOVO`, `INALTERADO`, `ALTERADO` (versão anterior preservada, como na FR-028, e aviso no log) ou `FALHA` (cópia local mantida). O registro `dicionarios.csv` DEVE ter uma linha por conjunto e formato (20 linhas), com: conjunto, pasta, formato, arquivo, URL, resultado da última obtenção, data e hora dela, SHA-256, tamanho, quantidade de versões anteriores e a mais recente delas. No registro, `NAO_PUBLICADO` indica formato ausente do catálogo, e `NAO_OBTIDO`, conjunto cujos dicionários nunca foram procurados no catálogo.
- **FR-033**: A obtenção dos dicionários NÃO DEVE baixar arquivos de dados. Uma falha nela DEVE ir para o log e para o registro, sem interromper a coleta nem mudar o código de saída.

**Identificação da usina e leitura dos arquivos (US1 e US2)**

- **FR-034**: A usina DEVE ser identificada em cada conjunto por um identificador de extração e conferida por um segundo campo, com os valores do perfil:

  | Conjunto do ONS | Identificador de extração | Conferência |
  |---|---|---|
  | Energia Vertida Turbinável | `cod_usina` = `identificacao.cod_usina` | `nom_reservatorio` contém `identificacao.nome_ons` |
  | Indicadores de disponibilidade por unidade geradora, bases mensal e anual | `ceg` = `identificacao.ceg` | `id_usina` = `identificacao.id_ons` |
  | Taxas TEIFa e TEIP; Parâmetros das taxas TEIFa e TEIP | `cod_ceg` = `identificacao.ceg` | não há: os dois conjuntos não publicam o id ONS |
  | Programação diária | `cod_exibicaousina` = `identificacao.cod_programacao` | `nom_usina` contém `identificacao.nome_ons`, e `id_estado` = `usina.estado` |
  | Disponibilidade por usina | `id_ons` = `identificacao.id_ons` | `ceg` = `identificacao.ceg`, e `id_estado` = `usina.estado` |
  | Dados hidrológicos horários | `cod_usina` = `identificacao.cod_usina` | `nom_reservatorio` contém `identificacao.nome_ons`, e `id_reservatorio` = `identificacao.id_reservatorio` |
  | Geração por usina | `id_ons` = `identificacao.id_ons` | `ceg` = `identificacao.ceg`, e `id_estado` = `usina.estado` |
  | Modalidade das usinas | `ceg` = `identificacao.ceg` | `id_ons` = `identificacao.id_ons`, e `id_estado` = `usina.estado` |

- **FR-035**: Na comparação, os textos DEVEM ser tomados sem acento, sem espaços nas pontas e em maiúsculas, e os códigos numéricos como número. "Contém" exige o valor do perfil dentro do texto do campo. O nome do agente e os demais campos de cadastro (subsistema, bacia e rio) NÃO DEVEM ser usados na identificação.
- **FR-036**: Só DEVEM ser extraídas as linhas em que o identificador e a conferência conferem. As linhas em que só um dos dois confere NÃO DEVEM ser extraídas: DEVEM ser contadas por arquivo, em "só identificador" e "só conferência", com aviso no log que cita o arquivo. Há duas exceções:
  - Taxas TEIFa e TEIP e Parâmetros das taxas TEIFa e TEIP: sem campo de conferência publicado, a extração usa só o identificador, e as contagens parciais não se aplicam;
  - Modalidade das usinas: a ficha é localizada pelo identificador; id ONS ou estado diferente do perfil não exclui a linha, que é extraída e examinada pela Conferência, e as contagens parciais ficam na auditoria.
- **FR-037**: Os arquivos CSV DEVEM ser lidos com separador `;`, em UTF-8; com erro de decodificação, o arquivo inteiro DEVE ser relido em Latin-1. As colunas DEVEM ser localizadas pelo nome no cabeçalho, e não pela posição; nos arquivos Parquet, também pelo nome. Arquivo vazio, corrompido ou sem as colunas de identificação DEVE ficar como `FALHA`, com o motivo, sem interromper a leitura dos demais; a coleta termina com código 2.
- **FR-038**: Nos arquivos CSV, as linhas não vazias com número de campos diferente do cabeçalho NÃO DEVEM ser extraídas: DEVEM ser contadas por arquivo e avisadas no log, com o arquivo, a quantidade e o número das cinco primeiras. Linhas vazias são ignoradas.
- **FR-039**: Na EVT, na Programação diária e nos conjuntos horários, os valores numéricos DEVEM ser lidos como publicados, sem arredondamento, com a vírgula decimal aceita. Campo vazio fica ausente; valor que não é número fica ausente e é contado na auditoria como valor inválido; nenhum dos dois vira zero. Nos indicadores e nas taxas, as colunas ficam como publicadas, e a conversão em número é do Tratamento de dados.
- **FR-040**: Toda linha extraída DEVE guardar o arquivo de origem, com os textos sem espaços nas pontas e o instante como publicado. A Coleta de dados NÃO DEVE converter a convenção de hora, juntar duplicatas entre arquivos (exceto na EVT, FR-041), recortar o período, listar ausências, converter patamares em horas, escolher a versão mais recente dos indicadores nem sinalizar a qualidade dos valores: isso é do Tratamento de dados.

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
  - tomar o dia do nome do arquivo (`..._AAAA_MM_DD`) e conferir a data interna, aceitando `AAAA-MM-DD` e `DD/MM/AAAA`; a divergência vai para a auditoria e para o log;
  - extrair, para cada patamar de 30 minutos (1 a 48), a geração programada da usina, com o dia e o arquivo de origem, em `programacao_extraido.parquet`;
  - num patamar repetido no mesmo arquivo, manter a última ocorrência, com aviso no log;
  - marcar o arquivo como `INCOMPLETO` quando a usina não tiver os 48 patamares.
- **FR-044**: Nos conjuntos horários, a coleta DEVE extrair, com o instante como publicado e o arquivo de origem:
  - Disponibilidade por usina: potência instalada, disponibilidade operacional e disponibilidade sincronizada;
  - Dados hidrológicos horários: vazões afluente, defluente, turbinada, vertida, vertida não turbinável e por outras estruturas, níveis de montante e de jusante e volume útil;
  - Geração por usina: geração.

  Os valores são lidos sem arredondamento (FR-039), e cada linha DEVE trazer a marca de valor não numérico na fonte, que o Tratamento de dados transforma em sinalização de qualidade. A linha da usina com instante não interpretável NÃO DEVE ser extraída: ela DEVE ser contada nas linhas da usina e como valor inválido.
- **FR-045**: Na Modalidade das usinas, a coleta DEVE gravar em `cadastro_ficha.csv` a ficha da usina: nome, CEG, id ONS, modalidade de operação, centro de operação, ponto de conexão, potência autorizada (número), estado, situação na ANEEL, data da consulta (a data de obtenção do arquivo, pelo manifesto) e arquivo de origem. A ficha DEVE trazer também a quantidade de homônimos (linhas com `identificacao.nome_ons` no nome da usina e outro CEG), as contagens parciais e a quantidade de linhas com o CEG; havendo mais de uma, usa a primeira. Usina ausente do cadastro DEVE encerrar a coleta com código 2.

**Auditoria, saídas e resumo (US2)**

- **FR-046**: Cada conjunto DEVE ter uma auditoria com uma linha por arquivo lido ou não obtido, inclusive os sem linhas da usina, com:
  - arquivo, formato, período (ano, mês ou dia, pelo nome), data de publicação no portal (pelo manifesto) e se o arquivo foi obtido nesta execução;
  - linhas lidas, linhas irregulares (FR-038), linhas da usina, linhas só com o identificador, linhas só com a conferência (FR-036) e valores inválidos (FR-039), onde cada contagem se aplica: a Programação diária, em Parquet, não tem linhas irregulares; os indicadores, as taxas e o cadastro, que ficam como texto, não contam valores inválidos; nas taxas e nos parâmetros, sem campo de conferência, as contagens parciais ficam vazias;
  - situação: `PROCESSADO` (com linhas da usina), `SEM_REGISTROS` (lido, sem linhas da usina) ou `FALHA` (não obtido ou não lido), com o motivo da falha.

  Por conjunto, a auditoria traz ainda:
  - EVT: a codificação de leitura e a data e hora (UTC) da leitura; o período é o nome do arquivo sem a extensão;
  - indicadores e taxas: o conjunto de cada arquivo, numa só auditoria para os quatro conjuntos;
  - Programação diária: uma linha por dia do período com arquivo publicado, lido ou não obtido, com o dia, as linhas da usina, os patamares distintos, se a data interna confere e a situação `INCOMPLETO`; os dias sem linha são os dias sem arquivo, que o Tratamento de dados lista;
  - conjuntos horários: as repetições do arquivo no catálogo. O período e a data de publicação de cada arquivo servem ao Tratamento de dados para escolher o valor de uma hora repetida e para separar o mês sem arquivo do mês sem a usina;
  - Modalidade das usinas: as linhas da usina são as linhas com o CEG do perfil; mais de uma indica CEG repetido no cadastro.

  Nos conjuntos horários, o Tratamento de dados completa a auditoria com as horas da usina e as duplicatas entre arquivos.
- **FR-047**: Os resultados da usina DEVEM ficar em `data/usinas/<slug>/coleta/`, com os nomes da seção "Entradas e saídas". Os arquivos de dados DEVEM ser gravados como os do Tratamento de dados: só a cópia `.bak` da versão imediatamente anterior, conteúdo idêntico sem regravação, gravação conferida e, em falha, o arquivo restaurado e código 1. O `etapa.json` não tem `.bak`.
- **FR-048**: O `resumo` do `etapa.json` da coleta DEVE trazer as opções da execução (`--sem-portal` e o `--forcar-download` efetivo, que não vale com `--sem-portal`) e:
  - o período da base de EVT (primeiro e último instante), quando a EVT tem linhas da usina;
  - por conjunto tratado, com os quatro conjuntos de indicadores e taxas numa só entrada: arquivos no escopo e, nesta execução, baixados, reaproveitados e não obtidos; arquivos lidos, sem linhas da usina e com falha; linhas extraídas, só com o identificador, só com a conferência e irregulares; valores inválidos; arquivos registrados no manifesto; a data de publicação mais recente; e a data de obtenção (FR-027);
  - a quantidade de dicionários por resultado.

### Key Entities

- **Perfil da usina**: nome, nome curto, estado, início da operação comercial, identificadores nos conjuntos do ONS, parâmetros técnicos com a fonte, limiares próprios das análises e textos próprios da usina para o relatório.
- **Manifesto da etapa** (`etapa.json`): etapa, usina, situação, código de saída, datas, etapa anterior usada, arquivos gravados com SHA-256 e resumo.
- **Conjunto do ONS**: nome, id no catálogo, pasta em `data/raw/`, formatos, identificador de extração e conferência.
- **Manifesto de versões** (`_manifesto_ons.json`): por arquivo bruto, a versão obtida, as datas de publicação e de registro, os tamanhos, a origem do registro e as versões anteriores preservadas e excluídas.
- **Versão anterior preservada**: cópia de uma versão substituída, com data de publicação, tamanho, SHA-256 e data do arquivamento; no máximo duas por arquivo.
- **Dicionário de dados**: PDF ou JSON de um conjunto, com o resultado e a data da última obtenção, o SHA-256 e as versões anteriores.
- **Linha extraída**: linha da usina num conjunto, com as colunas publicadas, o instante como publicado e o arquivo de origem.
- **Base de EVT extraída**: linhas da usina na EVT, uma por instante, em ordem cronológica; define o período dos demais conjuntos.
- **Ficha cadastral**: dados de identificação da usina no cadastro do ONS, com a data da consulta e a contagem de homônimos.
- **Auditoria da extração**: uma linha por arquivo de cada conjunto, com as contagens e a situação.
- **Cópia de segurança**: pasta datada com o código e os documentos do projeto, com a lista conferida dos arquivos; no máximo duas.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100 % dos arquivos no escopo de cada conjunto (FR-017) são obtidos ou registrados como não obtidos, e 100 % dos arquivos lidos têm uma linha na auditoria, inclusive os sem linhas da usina.
- **SC-002**: 100 % das linhas extraídas têm o identificador e a conferência do perfil, salvo as exceções da FR-036; nenhuma linha de homônimo é extraída; 100 % das linhas que conferem só em parte estão contadas na auditoria. Num teste com a mesma usina sob dois nomes de agente, nenhuma linha se perde.
- **SC-003**: Em cada conjunto, exceto no cadastro, a soma das linhas da usina na auditoria é igual à quantidade de linhas extraídas, contadas antes de juntar as repetições, mais as linhas da usina sem instante válido, que não são extraídas (instante vazio, na EVT; não interpretável, nos conjuntos horários). A EVT extraída não tem dois registros no mesmo instante e está em ordem cronológica.
- **SC-004**: Uma segunda coleta sem novidade no portal não baixa nenhum arquivo de dados e gera extraídos com o mesmo conteúdo. Com `--sem-portal`, nenhum arquivo de `data/raw/` é criado, alterado ou excluído.
- **SC-005**: No teste de republicação, 100 % das versões substituídas por conteúdo diferente ficam preservadas e registradas, até o limite: nenhum arquivo passa de duas versões anteriores, e as que ficam são as duas mais recentes. Os extraídos são iguais aos obtidos só com as versões correntes.
- **SC-006**: Depois de cada coleta que consulta o portal, os 20 dicionários (dez conjuntos, em PDF e JSON) estão obtidos ou com a situação registrada. No teste com dicionário alterado, a versão anterior fica preservada em 100 % dos casos.
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

---

## Assumptions

- **Portal do ONS**: catálogo público no padrão CKAN, sem autenticação. Para cada arquivo de dados, o catálogo informa o tamanho e a data de publicação; para os dicionários, não informa nenhum dos dois.
- **Revisões do ONS**: o ONS republica arquivos já publicados, às vezes com o mesmo tamanho (caso real: o arquivo de 09/2026 da EVT, republicado em 30/09/2026).
- **Publicação**: a estrutura da tabela da FR-016 é a observada em 05/10/2026. Os arquivos CSV usam `;` e vêm em UTF-8 ou Latin-1.
- **Dados brutos**: cerca de 4,1 GB em `data/raw/`, fora do controle de versões e das cópias de segurança.
- **Rede**: só a Coleta de dados usa a rede. Os testes rodam sem rede, com o catálogo e os arquivos simulados.
- **Parâmetros que o ONS não publica** (garantia física, IP e TEIF de referência, engolimento e tipo de turbina): o usuário os informa no perfil, com a fonte e a data.
- **Fora da coleta**: conjuntos só com agregados do SIN (como a classificação da EVT), bases da CCEE e da ANEEL e o motivo das paradas, que nenhuma base aberta do ONS informa. Conferências feitas por consulta interativa aos dados do ONS não fazem parte do fluxo.
- **Ambiente**: Windows com PowerShell; os exemplos de comando usam essa sintaxe.
