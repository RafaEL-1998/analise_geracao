# Análise de Usinas com Dados Abertos do ONS

Pipeline em Python que gera, para uma usina, um relatório de apoio à fiscalização a partir do [Portal de Dados Abertos do ONS](https://dados.ons.org.br). Ele:

- coleta os conjuntos do ONS que o tipo da usina tem, pelos identificadores do perfil;
- trata e confere os dados;
- analisa a operação: geração, disponibilidade, programação, indicadores oficiais e o que é próprio de cada tipo;
- gera o relatório, com PDF, Markdown, planilha, figuras e um resumo executivo de até duas páginas.

Tipos atendidos: **UHE, PCH, CGH, UTE, UTN, EOL e UFV**. Cada usina é descrita por um **perfil** (`usinas/<slug>/perfil.toml`). As usinas de um estado ou de um tipo podem ser reunidas num **relatório de carteira**.

O projeto segue o Spec-Driven Development (Spec Kit):

- a constituição fica em `.specify/memory/constitution.md`;
- cada etapa do fluxo tem uma spec em `specs/`.

Os resultados não são repetidos aqui, para não ficarem desatualizados. Veja `reports/<slug>/relatorio_analise_estatistica.pdf` e `reports/<slug>/resumo_executivo.pdf`, gerados a partir dos dados a cada execução.

---

## Fluxo de cinco etapas

**Coleta de dados → Tratamento de dados → Conferência → Análises → Geração do relatório**

| Etapa | Comando | O que faz | Grava em | Spec |
|---|---|---|---|---|
| 1. Coleta de dados | `coleta` | Monta o catálogo de usinas do ONS e o rascunho do perfil. Baixa só o que é novo ou mudou, guardando as versões anteriores e os dicionários de dados. Extrai a usina de cada conjunto pelos identificadores do perfil, escolhe a série de referência e audita cada arquivo lido. | `data/raw/` e `data/catalogo/` (compartilhados) e `data/usinas/<slug>/coleta/` | `specs/001-coleta-dados/` |
| 2. Tratamento de dados | `tratamento` | Padroniza tipos e horários e valida as regras físicas: sinaliza os registros, sem descartar nenhum. Lista as ausências e monta as séries horárias. | `data/usinas/<slug>/tratamento/` | `specs/002-tratamento-dados/` |
| 3. Conferência | `conferencia` | Confere as fontes entre si (por exemplo geração × disponibilidade, programação × despacho, a usina × a soma do conjunto) e registra as conferências que não se aplicam ao tipo, com o motivo. | `data/usinas/<slug>/conferencia/` | `specs/003-conferencia/` |
| 4. Análises | `analises` | Calcula indicadores, eventos, seções do tipo e os indicadores da carteira, e monta as constatações e a conclusão. | `data/usinas/<slug>/analises/` | `specs/004-analises/` |
| 5. Geração do relatório | `relatorio` | Gera as figuras (seaborn), o PDF, o Markdown, a planilha e o resumo executivo. Também o relatório de carteira e os relatórios de referência. | `reports/<slug>/` | `specs/005-geracao-relatorio/` |

Cada etapa:

- grava um `etapa.json` na sua pasta, com a situação, o código de saída, os arquivos gravados (com SHA-256) e o resumo da execução;
- só roda se a anterior estiver `concluida` para a mesma usina; refazer uma etapa marca as seguintes como `desatualizada`.

Só a Coleta acessa o portal do ONS. As etapas 2 a 5 leem só o que as anteriores gravaram.

### Níveis dos dados

O ONS publica cada série num de três níveis, e todo número do relatório é identificado pelo seu:

| Nível | O que é | Exemplo |
|---|---|---|
| usina | a série da própria usina | a geração de uma UHE ou de uma UTE |
| conjunto | a soma das usinas de um conjunto (modalidade Tipo II-C) | a geração do Conj. Chapadão, de que a PCH Bandeirante faz parte |
| agregado | grupos de pequenas usinas (Tipo III) e da MMGD, por área do estado | "PQU MSMS MMGD" |

Um número de conjunto ou de agregado nunca é apresentado como da usina nem dividido entre as usinas. A MMGD e as usinas Tipo III aparecem só no panorama do relatório de carteira.

### Conjuntos do ONS

A usina é extraída de cada conjunto por um identificador e conferida por um segundo campo, ambos com os valores do perfil (CEG, id ONS, código da usina, códigos de programação e de planejamento, conforme o conjunto). As linhas em que só um dos dois confere, por exemplo de usinas homônimas, não são extraídas; elas são contadas na auditoria da Coleta. Os identificadores de cada conjunto estão no data-model da spec da Coleta.

| Conjunto do ONS | Tipos | Nível |
|---|---|---|
| [Energia vertida turbinável](https://dados.ons.org.br/dataset/energia-vertida-turbinavel) | UHE, PCH, CGH | usina |
| [Indicadores de disponibilidade por unidade geradora](https://dados.ons.org.br/dataset/ind_disponibilidade_fgeracao_uge_mensal), [Taxas TEIFa e TEIP](https://dados.ons.org.br/dataset/taxa_teif_teip) e parâmetros das taxas | UHE, PCH, CGH, UTE, UTN | usina |
| [Disponibilidade por usina](https://dados.ons.org.br/dataset/disponibilidade_usina) | UHE, PCH, CGH, UTE, UTN | usina |
| [Dados hidrológicos horários](https://dados.ons.org.br/dataset/dados_hidrologicos_ho) e Reservatórios | UHE, PCH, CGH | usina |
| [Programação diária](https://dados.ons.org.br/dataset/programacao_diaria) | todos | usina ou conjunto |
| [Geração por usina](https://dados.ons.org.br/dataset/geracao-usina-2) | todos | usina ou conjunto (e os agregados do panorama) |
| [Modalidade das usinas](https://dados.ons.org.br/dataset/modalidade-usina) e Capacidade de geração (cadastro) | todos | usina |
| Composição dos conjuntos de usinas | todos | conjunto |
| [Geração térmica por motivo de despacho](https://dados.ons.org.br/dataset/geracao-termica-despacho-2) e CVU das usinas térmicas | UTE, UTN | usina |
| CMO semanal | UTE, UTN | agregado (subsistema) |
| [Fator de capacidade](https://dados.ons.org.br/dataset/fator-capacidade-2) | EOL, UFV | usina ou conjunto |
| Restrição de operação por constrained-off, com detalhe e por razão | EOL, UFV | usina (a razão, também conjunto) |

Os dicionários de dados (PDF e JSON) são obtidos a cada coleta e guardados em `data/raw/_dicionarios/`.

---

## Instalação

Ambiente: Windows 10/11 com PowerShell e Python 3.11 ou mais recente. O projeto usa o 3.14.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Como executar

```powershell
# Catálogo de usinas do ONS: monta data/catalogo/ e lista as usinas do filtro
python -m src usinas --estado MS
python -m src usinas --estado MS --tipo UFV --sem-portal

# Rascunho do perfil de uma usina, a partir do catálogo (nunca sobrescreve um perfil)
python -m src perfil --ceg UTE.GN.MS.027075-0.01 --slug william_arjona

# Fluxo completo de uma usina, com consulta ao portal do ONS
python -m src completo --usina sao_domingos

# Fluxo completo sem internet, só com os arquivos já baixados
python -m src completo --usina sao_domingos --sem-portal

# Uma etapa de cada vez
python -m src coleta      --usina sao_domingos
python -m src tratamento  --usina sao_domingos
python -m src conferencia --usina sao_domingos
python -m src analises    --usina sao_domingos
python -m src relatorio   --usina sao_domingos

# Relatório de carteira: de um estado, de um tipo ou de um tipo num estado
python -m src carteira --estado MS
python -m src carteira --tipo UTE
```

`completo` executa as cinco etapas na ordem e para na primeira que não terminar com código 0.

**Opções**

| Opção | Comandos | Efeito |
|---|---|---|
| `--usina <slug>` | etapas, `completo`, `referencia` e `comparar` | usina: nome da pasta em `usinas/` |
| `--sem-portal` | `coleta`, `completo` e `usinas` | não consulta o portal; usa só os arquivos locais |
| `--forcar-download` | `coleta`, `completo` e `usinas` | baixa de novo todos os arquivos de dados |
| `--data-geracao "DD/MM/AAAA HH:MM"` | `relatorio`, `completo`, `carteira` e `referencia` | fixa a data de geração e torna o PDF reproduzível byte a byte |
| `--estado <UF>`, `--tipo <tipo>` | `usinas` e `carteira` | recorte por estado (sigla) e por tipo (`UHE`, `PCH`, `CGH`, `UTE`, `UTN`, `EOL`, `UFV`); a carteira exige pelo menos um dos dois |
| `--modalidade <modalidade>` | `usinas` | recorte pela modalidade de operação ("TIPO I" a "TIPO III") |
| `--ceg <CEG>`, `--slug <slug>` | `perfil` | usina do catálogo e nome da pasta do perfil |
| `--log-level {DEBUG,INFO,WARNING,ERROR}` | todos | nível de log de todos os módulos (padrão `INFO`); o log sai só na tela |

**Ferramentas**

```powershell
# Cópia de segurança do projeto (no máximo duas; a mais antiga sai depois de a nova ser conferida)
python -m src copia-seguranca --motivo antes_ajuste_x

# Registra o relatório aprovado pelo usuário em relatorios_referencia/<slug>/
python -m src referencia --usina sao_domingos --data-geracao "07/10/2026 08:53" --aprovado-em "19/10/2026"

# Refaz, num espaço isolado, as etapas 2 a 5 de cada referência a partir da Coleta e do perfil congelados e compara
# o relatório com o aprovado; com --coleta, refaz também a Coleta (sem portal) e a compara com a congelada
python -m src comparar --todas --coleta

# Compara o relatório atual da usina com o de outra pasta
# (PDF, Markdown, CSV e figuras byte a byte; a planilha, célula a célula)
python -m src comparar --usina sao_domingos --referencia <pasta>
```

**Códigos de saída**

| Código | Significado |
|---|---|
| 0 | sucesso (no `comparar`, nenhuma diferença) |
| 1 | erro: portal do ONS inacessível, dado que impede a etapa, falha de gravação (com o arquivo restaurado), erro inesperado ou interrupção |
| 2 | arquivo de dados não obtido ou não lido, ou usina sem registro nos conjuntos exigidos (Coleta); no `perfil`, CEG fora do catálogo ou usina só com agregado; também opção inválida na linha de comando |
| 3 | conferência das vazões com a hidrologia abaixo da meta de 99 % (Conferência). A etapa fica `concluida`, mas o `completo` para |
| 4 | perfil da usina inválido ou em rascunho; a mensagem lista os problemas |
| 5 | etapa anterior sem resultado concluído (ausente, com falha, desatualizada ou em formato antigo); no `perfil` e na `carteira`, catálogo ausente; na `carteira`, nenhuma usina do recorte com resultado. Nada é gravado |
| 6 | o `comparar` encontrou diferenças; no `perfil`, perfil existente diferente do catálogo |

Uma falha ao obter um dicionário de dados não muda o código de saída. Com `--sem-portal`, o fluxo completo de uma usina leva de 1 a 5 minutos; a carteira de um estado, poucos segundos.

---

## Estrutura de pastas

```text
.
├── src/                        código; ponto de entrada único: python -m src
│   ├── __main__.py             linha de comando
│   ├── pipeline.py             execução das etapas, etapa.json e pré-requisitos
│   ├── comum/                  perfil, caminhos, regras gerais, persistência, log, referências, comparação e cópia
│   ├── coleta/                 1. Coleta de dados, catálogo de usinas, rascunho do perfil e registro dos conjuntos
│   ├── tratamento/             2. Tratamento de dados
│   ├── conferencia/            3. Conferência
│   ├── analises/               4. Análises
│   └── relatorio/              5. Geração do relatório, resumo executivo e carteira
├── tests/                      testes sem rede: uma pasta por etapa, mais comum/, integracao/ e fixtures/
│                               (uma usina fictícia por tipo em fixtures/usinas_ficticias/)
├── usinas/<slug>/
│   ├── perfil.toml             perfil da usina
│   └── documentos/             documentos da usina (fora do git)
├── data/                       dados (fora do git)
│   ├── raw/                    arquivos do ONS, compartilhados por todas as usinas, com manifestos,
│   │                           _versoes_anteriores/ e _dicionarios/
│   ├── catalogo/               catálogo de usinas: usinas.csv, conjuntos.csv, cobertura.csv, planejamento.csv,
│   │                           programacao.csv, agregados.csv e catalogo.json
│   └── usinas/<slug>/          coleta/, tratamento/, conferencia/ e analises/, cada uma com o seu etapa.json
├── reports/
│   ├── <slug>/                 relatorio_analise_estatistica.pdf e .md, resumo_executivo.pdf e .md,
│   │                           perfil_estatistico_anual.xlsx e .csv, figures/ e etapa.json
│   └── carteiras/<nome>/       relatorio_carteira.pdf e .md, carteira.xlsx e figures/
│                               (<nome> = <uf>, <uf>_<tipo> ou brasil_<tipo>)
├── relatorios_referencia/<slug>/  relatório aprovado pelo usuário, com o perfil usado e referencia.json;
│                               a Coleta congelada (coleta/) fica fora do git
├── specs/                      uma spec por etapa (001-coleta-dados a 005-geracao-relatorio)
├── .specify/                   constituição e modelos do Spec Kit
├── referencias/                documentos gerais de consulta (fora do git)
├── _backup_<data>_<motivo>/    cópias de segurança (no máximo duas; fora do git)
├── requirements.txt
└── README.md
```

---

## Relatório da usina

O caminho do relatório segue a presença da série de energia vertida turbinável (EVT):

- **hidrelétrica com EVT** (como a UHE São Domingos): as análises da EVT, dos eventos de parada, da afluência e do nível do reservatório;
- **demais usinas**: as seções comuns sobre a base horária da série de referência (indicadores anuais, série temporal, geração mensal e sazonalidade, perfil horário, programação × verificada, disponibilidade, indicadores oficiais e qualidade dos dados), mais as seções do tipo:
  - térmicas: despacho por motivo, inflexibilidade, atendimento ao despacho, disponível sem despacho e CVU × CMO;
  - eólicas e solares: fator de capacidade, energia cortada por razão, recurso × geração e aderência à programação;
  - usina em conjunto: a composição e a geração do conjunto por trecho de composição;
  - hidrelétrica sem EVT, com hidrologia: afluência, vertimento e nível.
- **usina em conjunto sem série própria** (como a PCH Bandeirante): o relatório tem duas partes, "A usina no conjunto", com o que o ONS publica da usina isolada e o peso dela na potência do conjunto, e "Operação do conjunto", antes da conclusão.

A conclusão é gerada por um catálogo de regras declaradas (C1 a C19, com limiares gerais), só com dados do nível da usina, em quatro listas: pontos de atenção, possíveis problemas, a confirmar com o agente e a verificar em campo. Ela fala em indícios, sem afirmar causa nem dar parecer de desempenho. Cada figura e tabela traz, logo abaixo, a fonte dos dados com o identificador, a data de obtenção e as conferências.

O **relatório de carteira** reúne as usinas de um estado ou de um tipo só a partir dos resultados já gravados: o quadro das usinas, os indicadores comparáveis do último ano completo, a ordenação pelos itens da conclusão, as usinas sem resultado (com o motivo) e, na carteira de um estado, o panorama dos agregados por modalidade e mês. Ele não atribui nota nem parecer.

---

## Perfil da usina

O perfil (`usinas/<slug>/perfil.toml`, em UTF-8) reúne tudo o que é próprio da usina, com comentários `#` para a origem de cada valor. As regras gerais, iguais para todas as usinas, ficam em `src/comum/regras.py`: limiar de usina parada, tolerâncias, metas e limiares da conclusão.

| Seção | Campos |
|---|---|
| `[usina]` | `slug` (igual ao nome da pasta), `nome`, `nome_curto`, `estado`, `inicio_operacao_comercial`, `tipo` (prefixo do CEG), `modalidade`, `subsistema`, `situacao` (`rascunho` ou `conferido`) e, no rascunho, `pendentes` |
| `[identificacao]` | `ceg`, `id_ons`, `codigos_programacao` e, conforme o tipo: `cod_usina`, `nome_ons` e `id_reservatorio` (hidrelétricas com EVT ou hidrologia), `id_conjunto` (usina em conjunto), `[[identificacao.planejamento]]` (térmicas: códigos com início e fim) e `[[identificacao.membros]]` |
| `[cobertura]` | o nível de cada conjunto do ONS para a usina (`proprio`, `conjunto`, `agregado` ou `ausente`), copiado do catálogo |
| `[parametros]` | `potencia_instalada_mw`, `unidades_geradoras`, `potencia_unitaria_mw` (ou `potencias_unidades_mw`) e, conforme o tipo: os hidráulicos, `garantia_fisica_mwmed`, `ip_referencia`, `teif_referencia` e `combustivel` (térmicas) |
| `[parametros.fontes]` | a fonte de cada grupo de parâmetros |
| `[analises]` | só nas hidrelétricas com EVT: `vertimento_minimo_m3s`, `faixas_geracao_mw` e textos opcionais |
| `[textos]` | trechos opcionais próprios da usina |

O que é obrigatório, opcional ou recusado em cada tipo está no contrato do perfil da spec da Coleta. Um campo opcional ausente tira do relatório o trecho ou a regra correspondente, com o motivo nas notas.

O perfil é conferido antes de qualquer etapa: campos faltantes, tipos, faixas e coerência, como potência unitária × número de unidades = potência instalada. Um perfil inválido ou em rascunho termina com código 4 e a lista de todos os problemas.

### Como incluir uma usina

1. **Encontre a usina no catálogo**: `python -m src usinas --estado <UF> [--tipo <tipo>]`. A listagem mostra, para cada conjunto do ONS, se a usina tem série própria (`P`), só do conjunto (`C`), só agregada (`A`) ou nenhuma (`-`), e a coluna `PERFIL` com o slug das que já têm perfil. Usina só agregada não tem relatório próprio: ela aparece no panorama da carteira do estado.
2. **Gere o rascunho do perfil**: `python -m src perfil --ceg <CEG> --slug <slug>`. Ele vem com os identificadores, a cobertura, a composição do conjunto e os códigos de programação e de planejamento do catálogo, com `situacao = "rascunho"` e a lista `pendentes`.
3. **Complete o perfil**: cada pendente com o valor e a fonte em comentário (potência e unidades: atos de outorga da ANEEL; garantia física: portaria vigente do MME; IP e TEIF de referência: cálculo da garantia física; parâmetros hidráulicos: projeto da usina). Confira os identificadores e troque para `situacao = "conferido"`.
4. **Execute o fluxo**: `python -m src completo --usina <slug>`. Os arquivos do ONS já baixados em `data/raw/` para outras usinas são reaproveitados.
5. **Confira a auditoria** em `data/usinas/<slug>/coleta/`: os arquivos `auditoria_*.csv` contam, por arquivo, as linhas da usina e as que conferem só pelo identificador ou só pela conferência (contagens altas indicam identificador errado ou mudança de cadastro no ONS); `cadastro_ficha.csv` traz a ficha da usina, e as divergências com o perfil aparecem na Conferência e no relatório.
6. **Aprove e registre**: depois de revisar o relatório, registre-o com `python -m src referencia --usina <slug> --data-geracao "<data do relatório>" --aprovado-em "<data>"` e faça o commit. A partir daí, `python -m src comparar --todas --coleta` confere que nenhuma mudança no código alterou o relatório aprovado.

---

## Cópias de segurança e versões

- **Cópias do projeto**: `python -m src copia-seguranca --motivo <texto>` cria `_backup_<AAAA-MM-DD>_<motivo>/`.
  - Conteúdo: código, testes, specs, relatórios, referências aprovadas, Spec Kit, perfis, README e `requirements.txt`, com `copia.json` (SHA-256 de cada arquivo), `LEIA-ME.txt` e um `conftest.py` que impede a coleta pelo pytest.
  - A nova cópia é conferida, e só então as mais antigas são excluídas, até ficarem **no máximo duas**.
  - Dados brutos, dados das etapas e documentos de referência ficam fora.
- **Relatórios aprovados**: ficam em `relatorios_referencia/<slug>/`, com a Coleta e o perfil congelados. Uma referência não commitada não pode ser substituída.
- **Versões anteriores dos arquivos do ONS**: quando o ONS republica um arquivo com conteúdo diferente, a versão anterior vai para `_versoes_anteriores/`, na pasta do conjunto.
  - Ficam **no máximo duas por arquivo**, as mais recentes.
  - As excluídas são registradas no manifesto (`_manifesto_ons.json`, `versoes_excluidas`).
  - O mesmo vale para os dicionários de dados.
- **Cópia `.bak`**: só nos arquivos de dados da Coleta e do Tratamento (`data/usinas/<slug>/coleta/` e `tratamento/`), com a versão imediatamente anterior.
  - Conteúdo idêntico não é regravado.
  - A gravação é conferida no disco e, em falha, o arquivo volta ao que era.
  - Catálogo, Conferência, Análises, relatórios, carteiras e referências não têm `.bak`: são gravados numa pasta temporária, conferidos e só então trocados.

---

## Testes

```powershell
python -m pytest tests
```

Os testes não acessam a rede. Eles cobrem:

- cada etapa, o catálogo, o rascunho do perfil, a carteira e as referências;
- o perfil e o pré-requisito entre etapas;
- a persistência, as cópias e as versões;
- a conformidade com a constituição: figuras em seaborn, nível de log único, ponto de entrada único, dependências;
- a ausência de valores de usina no código;
- o fluxo completo de uma usina fictícia de cada tipo (`tests/fixtures/usinas_ficticias/`), sobre arquivos brutos sintéticos, sem nenhum identificador de outra usina nas saídas;
- os invariantes do relatório das hidrelétricas com EVT.

Depois de um ajuste no código, `python -m src comparar --todas --coleta` confere que os relatórios aprovados não mudaram.

---

## Metodologia resumida

- **Atualização**: um arquivo local só é reaproveitado se corresponder à versão publicada, pela data de publicação e pelo tamanho registrados no manifesto.
- **Tipo e nível**: o tipo da usina vem do prefixo do CEG; o nível de cada série (usina, conjunto ou agregado) vem do catálogo e fica no perfil.
- **Série de referência**: a série horária que define o período da usina; nas usinas sem série própria, a do conjunto, a partir da entrada da usina nele. Os trechos de nível e de composição dentro do período são listados.
- **Validação**: as regras são aplicadas no Tratamento; os registros sinalizados são mantidos nos totais e excluídos só no campo afetado. As regras conferem a consistência interna das grandezas do ONS e a plausibilidade física frente aos parâmetros do perfil.
- **Horários**: cada conjunto é levado à hora de início; os dados hidrológicos e a restrição com detalhe têm convenções próprias, descritas na spec do Tratamento. Ausências são listadas e nunca interpoladas.
- **Indicadores oficiais**: o DISPF da usina é a média das unidades, ponderada pela potência e pelas horas; nas hidrelétricas, TEIFa = Σ(HDF + HEDF) ÷ Σ(HP − HDP − HEDP) e TEIP = Σ(HDP + HEDP) ÷ ΣHP, em janela de 60 meses, recalculadas e conferidas com as publicadas.
- **Usina parada**: geração ≤ 1 MW. Nas hidrelétricas com EVT, as horas paradas são classificadas pela EVT, pela programação diária e pela sincronização das unidades.
- **Conclusão**: regras comuns e regras do tipo, com limiares gerais e período mínimo; uma regra sem base no nível da usina não gera item e fica nas notas, com o motivo.
- **Limitações**:
  - os dados abertos do ONS não informam a causa do vertimento, das reduções de geração ou dos desligamentos, nem os eventos individuais de desligamento;
  - os dados hidrológicos são informados pelos agentes e não são consistidos pelo ONS;
  - para a usina em conjunto sem série própria, o ONS publica só os números do conjunto;
  - os valores das usinas Tipo III no panorama são previsão do ONS.
