# Contract: Perfil da usina

**Spec**: [spec.md](../spec.md) (FR-006 a FR-009 e FR-056) · **Objetos, valores derivados e regras de leitura**: [data-model.md](../data-model.md) (seções 3.1 e 5.1) · **Rascunho**: [cli-perfil.md](cli-perfil.md)

Um único contrato do perfil, para os sete tipos de usina: UHE, PCH, CGH, UTE, UTN, EOL e UFV. Na UHE, os campos e as regras são os da primeira versão do perfil, mais `tipo` e `modalidade`.

## Local e formato

- **Arquivo**: `usinas/<slug>/perfil.toml`, em UTF-8, no formato TOML (lido com `tomllib`, da biblioteca padrão).
- **Slug**: nome da pasta em `usinas/`, igual a `usina.slug`; `carteiras` é reservado (é a pasta das carteiras em `reports/`).
- **Comentários**: começam com `#` e registram a origem de cada valor.
- **Pasta da usina**: guarda também `documentos/` (fora do git), que o fluxo não lê.
- **Quando é lido**: no início de todo comando com `--usina` (as cinco etapas, `completo`, `referencia` e `comparar` com `--referencia`), antes de qualquer outra ação, inclusive da consulta ao portal. A `carteira` valida o perfil de cada usina do recorte, achado pelo CEG, e lista as que têm perfil inválido ou em rascunho entre as sem resultado; o `comparar --todas` valida o perfil congelado de cada referência; `usinas`, `perfil` e `copia-seguranca` não o validam. Durante cada etapa, o perfil validado fica ativo (`perfil_ativo()`).
- **Como nasce**: escrito pelo fiscal ou gerado em rascunho pelo comando `perfil`, a partir do catálogo de usinas (seção "Rascunho"), e conferido pelo fiscal antes do primeiro uso.
- **O perfil traz só valores próprios da usina**. Os valores derivados (engolimento máximo, disponibilidade de referência, produtividade nominal, plena carga, limites físicos, potência de cada unidade, códigos de planejamento vigentes) são calculados a partir dele ([data-model](../data-model.md), seção 3.1). As regras gerais (limiares, tolerâncias e metas) ficam em `src/comum/regras.py` e não podem ser alteradas pelo perfil; os únicos limiares próprios da usina são os da seção `[analises]`.

## Seções e campos

"Real" aceita número inteiro ou real do TOML; "inteiro" aceita só inteiro; booleano nunca vale como número. Texto obrigatório e texto opcional presente não podem ser vazios. Campos não previstos são ignorados.

Exigência por tipo, nas colunas de cada tabela: `O` = obrigatório; `C` = obrigatório quando um conjunto do ONS que usa o campo tem a cobertura indicada (`proprio` ou `conjunto`, salvo indicação); `opcional`; `—` = não se aplica, e a presença é recusada. O tipo usado nas regras é o do prefixo do CEG.

### `[usina]`

| Campo | Tipo | Exigência | Validação | Uso |
|---|---|---|---|---|
| `slug` | texto | O | letras minúsculas, algarismos e `_`; igual ao nome da pasta; diferente de `carteiras` | pastas da usina em `data/usinas/` e `reports/` |
| `nome` | texto | O | não vazio | título e textos do relatório |
| `nome_curto` | texto | O | não vazio | nome sem o tipo, nas frases sobre homônimos do cadastro; nos tipos sem `nome_ons`, também a contagem de homônimos |
| `estado` | texto | O | 2 letras maiúsculas | conferência na coleta; conferência do cadastro; textos do relatório |
| `inicio_operacao_comercial` | inteiro | O | de 1900 até o ano atual | tabela de parâmetros e constatações |
| `tipo` | texto | O | `UHE`, `PCH`, `CGH`, `UTE`, `UTN`, `EOL` ou `UFV`; igual ao prefixo do CEG | conjuntos coletados, seções e regras do tipo |
| `modalidade` | texto | O | `TIPO I`, `TIPO II-A`, `TIPO II-B` ou `TIPO II-C`. Tipo III (`TIPO III`, `TIPO III (EM DIT)`) é recusado: o ONS só publica o agregado | identificação e capa |
| `situacao` | texto | opcional | `rascunho` ou `conferido`; ausente vale `conferido`; `rascunho` é sempre recusado | — |
| `pendentes` | lista de texto | opcional | vazia ou ausente quando `conferido` | lista do rascunho |
| `subsistema` | texto | UHE, PCH, CGH, EOL e UFV: opcional; UTE e UTN: C com `cvu` | `SE`, `S`, `NE` ou `N` | identificador do CMO e conferência do CVU |

### `[identificacao]`

| Campo | Tipo | UHE | PCH e CGH | UTE e UTN | EOL e UFV | Validação | Uso |
|---|---|---|---|---|---|---|---|
| `ceg` | texto | O | O | O | O | `<UHE\|PCH\|CGH\|UTE\|UTN\|EOL\|UFV>.<2 letras>.<UF>.<6 algarismos>-<1 algarismo>.<2 algarismos>` | identificador nos indicadores, nas taxas, no cadastro, no despacho e na Capacidade de geração; conferência na disponibilidade, na geração, no fator de capacidade e nas restrições da usina |
| `id_ons` | texto | O | C: `proprio` na geração ou na disponibilidade | O | C: `proprio` na geração, no fator de capacidade ou nas restrições | não vazio | identificador na disponibilidade, na geração, no fator de capacidade e nas restrições da usina; conferência nos indicadores por UG e no cadastro |
| `cod_usina` | inteiro | O | C: EVT ou hidrologia | — | — | > 0 | identificador na EVT e nos Dados hidrológicos horários |
| `nome_ons` | texto | O | C: EVT ou hidrologia | — | — | maiúsculas sem acento: letras, algarismos, espaço, `.`, `-` e `/` | conferência ("contém") na EVT, na hidrologia e na programação; homônimos no cadastro |
| `id_reservatorio` | texto | O | C: hidrologia | — | — | não vazio | conferência nos Dados hidrológicos horários |
| `cod_programacao` ou `codigos_programacao` | texto ou lista de texto | O | O | O | O | um dos dois, nunca os dois; a lista não vazia | identificador na Programação diária (código de exibição); a lista quando a usina ou o conjunto é programado em mais de um código, um por barra |
| `id_conjunto` | texto | — | C: `conjunto` na geração, no fator de capacidade ou na razão da restrição | idem | idem | não vazio | identificador da série do conjunto na geração, no fator de capacidade e na razão da restrição; composição do conjunto |

#### `[[identificacao.planejamento]]` (UTE e UTN)

Uma entrada por código de planejamento, com o período em que vale. Exigida, com pelo menos uma entrada, quando a `[cobertura]` traz `despacho` ou `cvu`; nos demais tipos, não se aplica.

| Campo | Tipo | Validação |
|---|---|---|
| `codigo` | inteiro | > 0; comparado como número no despacho e no CVU |
| `inicio` | texto | `AAAA-MM` |
| `fim` | texto | `AAAA-MM`, ≥ `inicio`; vazio = vigente |

Dois códigos diferentes podem valer ao mesmo tempo, como uma unidade por combustível. O mesmo código não pode ter períodos sobrepostos.

#### `[[identificacao.membros]]` (opcional; PCH, CGH, EOL e UFV em conjunto)

Uma entrada por usina do conjunto, com `id_ons` (não vazio), `ceg` (no padrão), `inicio` e `fim` (`AAAA-MM-DD`; `fim` vazio = vigente), vinda da Composição dos conjuntos e conferida pelo fiscal. Só serve à conferência da soma das usinas com a geração do conjunto (a Coleta extrai a restrição com detalhe de cada membro). Sem ela, essa conferência fica não aplicável, com o motivo. Nos demais tipos, não se aplica.

### `[cobertura]`

Uma chave por conjunto de série do registro que serve ao tipo ([data-model](../data-model.md), seção 6): `evt`, `indicadores`, `programacao`, `disponibilidade`, `hidrologia`, `geracao`, `despacho`, `cvu`, `fator_capacidade`, `restricao_detalhe` e `restricao_razao`. Obrigatória fora da UHE.

| Valor | Efeito |
|---|---|
| `"proprio"` | a Coleta obtém o conjunto pelo identificador da usina |
| `"conjunto"` | a Coleta obtém o conjunto pelo `id_conjunto`, e os números ficam no nível do conjunto |
| `["proprio", "conjunto"]` | a usina mudou de nível no período: a Coleta obtém as duas séries, e os trechos dizem qual vale em cada hora |
| `"agregado"` ou `"ausente"` | o conjunto não é obtido; conferências e seções dele ficam não aplicáveis, com o motivo |

- Chave desconhecida, ou de conjunto que não serve ao tipo, é recusada (por exemplo, `despacho` numa UFV).
- `indicadores` cobre os quatro conjuntos de indicadores e taxas. Um deles sem linhas da usina vira conferência não aplicável, com o motivo.
- Os conjuntos cadastrais (Modalidade das usinas, Composição dos conjuntos e Capacidade de geração) e o CMO não entram na tabela: são obtidos sempre que servem ao tipo (a Composição, na usina com `id_conjunto`; o CMO, com `usina.subsistema`).
- Sem a tabela, só numa UHE: os dez conjuntos da UHE, com `proprio`, e mais nenhum.

### `[parametros]`

| Campo | Tipo | UHE | PCH e CGH | UTE e UTN | EOL e UFV | Validação | Uso |
|---|---|---|---|---|---|---|---|
| `potencia_instalada_mw` | real | O | O | O | O | > 0; em EOL e UFV, é a capacidade instalada | análises, relatório, limites físicos e conferência do cadastro |
| `unidades_geradoras` | inteiro | O | O | O | O | ≥ 1 | engolimento máximo, faixas de afluência, relatório |
| `potencia_unitaria_mw` ou `potencias_unidades_mw` | real ou lista de reais | O (só a unitária) | O | O | O | um dos dois, nunca os dois; a lista com um valor > 0 por unidade; a soma das unidades igual à potência instalada, com tolerância de 0,1 MW | indicadores por UG e relatório |
| `tipo_turbina` | texto | O | C: EVT ou hidrologia | — | — | não vazio | tabela de parâmetros e textos do relatório |
| `engolimento_nominal_ug_m3s` | real | O | C: EVT ou hidrologia | — | — | > 0 | engolimento máximo e faixas de afluência |
| `garantia_fisica_mwmed` | real | O | opcional | opcional | opcional | > 0 e ≤ `potencia_instalada_mw` | análises, conclusão e relatório |
| `ip_referencia` | real | O | opcional | opcional | — | ≥ 0 e < 1 | disponibilidade de referência; análises e relatório |
| `teif_referencia` | real | O | opcional | opcional | — | ≥ 0 e < 1 | disponibilidade de referência; análises e relatório |
| `queda_bruta_m` | real | O | C: EVT ou hidrologia | — | — | > 0 | produtividade nominal (validação física) e tabela de parâmetros |
| `perda_hidraulica_m` | real | O | C: EVT ou hidrologia | — | — | ≥ 0 e < `queda_bruta_m` | idem |
| `rendimento_turbina_gerador` | real | O | C: EVT ou hidrologia | — | — | > 0 e ≤ 1 | idem |
| `vazao_remanescente_m3s` | real | O | C: EVT ou hidrologia | — | — | ≥ 0 | tabela de parâmetros e notas |
| `combustivel` | texto | — | — | O | — | não vazio | tabela de parâmetros e seções de térmica |

### `[parametros.fontes]`

| Campo | Tipo | Exigência | Validação | Uso |
|---|---|---|---|---|
| `geral` | texto | O, em todos os tipos | não vazio | fonte e data dos parâmetros, na tabela de parâmetros |
| `garantia_fisica` | texto | O quando há garantia física; senão, opcional | não vazio | fonte e data da garantia física |
| `inicio_operacao_comercial` | texto | opcional | se presente, não vazio | origem do ano de início da operação comercial, na tabela de parâmetros |
| `ip_teif` | texto | opcional | se presente, não vazio | nota "O IP e o TEIF de referência são os do <texto>; …" |

### `[analises]`

Exigida na UHE e, na PCH e na CGH, com a EVT na `[cobertura]`; não se aplica a UTE, UTN, EOL e UFV.

| Campo | Tipo | Obrigatório | Validação | Uso |
|---|---|---|---|---|
| `vertimento_minimo_m3s` | real | sim | ≥ 0 (0 = usina sem vertimento contínuo) | limiar do vertimento mínimo |
| `faixas_geracao_mw` | lista de números | sim | não vazia; estritamente crescente; cada valor acima de 1 MW (usina parada) e abaixo de 90 % da potência instalada (plena carga) | faixas intermediárias da análise de EVT por nível de geração |
| `descricao_vertimento_minimo` | texto | não | se presente, não vazio | nota de definições do vertimento mínimo |

### `[analises.fontes]`

| Campo | Tipo | Obrigatório | Validação | Uso |
|---|---|---|---|---|
| `vertimento_minimo` | texto | não | se presente, não vazio | origem do limiar de vertimento mínimo, na tabela de parâmetros |

### `[textos]`

Opcional em todos os tipos.

| Campo | Tipo | Obrigatório | Validação | Uso |
|---|---|---|---|---|
| `ressalva_volume_util` | texto | não | se presente, não vazio | ressalva própria da usina, nas notas da hidrologia |

Sem um texto opcional, o relatório omite o trecho correspondente ([Geração do relatório](../../005-geracao-relatorio/spec.md)).

## Recusa do perfil

Um perfil ausente, ilegível, com campo obrigatório faltante, com texto opcional vazio, com tipo ou faixa errados, com incoerência, com campo que não se aplica ao tipo, com chave de `[cobertura]` inválida, com modalidade Tipo III ou em rascunho é recusado com o código 4, sem gravar nada. A mensagem sai na saída de erro, com todos os problemas de uma vez, um por linha:

```text
Perfil da usina '<slug>' inválido (usinas/<slug>/perfil.toml):
- <problema>
- <problema>
```

As faixas e as coerências só são conferidas quando os campos envolvidos têm o tipo certo. Os números das mensagens saem no formato do Python, com ponto decimal, salvo na soma das unidades, com vírgula.

| Problema | Mensagem |
|---|---|
| arquivo ausente | `arquivo do perfil não encontrado: usinas/<slug>/perfil.toml` |
| TOML inválido ou fora do UTF-8 | `arquivo ilegível: <erro do leitor>` |
| campo obrigatório ausente | `<campo>: campo obrigatório ausente` |
| campo exigido pela cobertura | `<campo>: obrigatório para <tipo> com a cobertura "<nível>" em <conjuntos>` |
| campo que não se aplica ao tipo | `<campo>: não se aplica a <tipo>` |
| texto de outro tipo | `<campo>: deve ser texto` |
| texto obrigatório vazio | `<campo>: não pode ser vazio` |
| texto opcional presente e vazio | `<campo>: não pode ser vazio (campo opcional presente)` |
| inteiro de outro tipo | `<campo>: deve ser número inteiro` |
| real de outro tipo | `<campo>: deve ser número` |
| lista de números inválida | `<campo>: deve ser lista não vazia de números` |
| lista de textos inválida | `<campo>: deve ser lista de textos não vazios` |
| tabela repetida inválida | `<campo>: deve ser uma lista de tabelas [[<campo>]]` |
| `usina.slug` fora do padrão | `usina.slug: só letras minúsculas, algarismos e _` |
| `usina.slug` diferente da pasta | `usina.slug: '<slug>' diferente do nome da pasta '<pasta>'` |
| `usina.slug` reservado | `usina.slug: "carteiras" é o nome da pasta das carteiras em reports/; escolha outro` |
| `usina.estado` | `usina.estado: deve ter 2 letras maiúsculas` |
| `usina.inicio_operacao_comercial` | `usina.inicio_operacao_comercial: deve estar entre 1900 e o ano atual` |
| `usina.tipo` fora da lista | `usina.tipo: use UHE, PCH, CGH, UTE, UTN, EOL ou UFV` |
| tipo × CEG | `usina.tipo: "<tipo>" diferente do prefixo do CEG ("<prefixo>")` |
| `usina.modalidade` Tipo III | `usina.modalidade: Tipo III não tem relatório por usina; o ONS só publica o agregado (ver a carteira do estado)` |
| `usina.modalidade` fora da lista | `usina.modalidade: use TIPO I, TIPO II-A, TIPO II-B ou TIPO II-C` |
| `usina.situacao` fora da lista | `usina.situacao: use rascunho ou conferido` |
| perfil em rascunho | `usina.situacao: perfil em rascunho; complete os pendentes com a fonte e troque para "conferido"`, seguida de `pendente: <campo>` para cada pendente |
| pendentes num perfil conferido | `usina.pendentes: deve estar vazia quando a situação é "conferido"` |
| `usina.subsistema` | `usina.subsistema: use SE, S, NE, N` |
| `identificacao.ceg` | `identificacao.ceg: fora do padrão TIPO.XX.UF.NNNNNN-D.DD (TIPO: UHE, PCH, CGH, UTE, UTN, EOL ou UFV)` |
| códigos de programação | `identificacao: use cod_programacao ou codigos_programacao, não os dois`; `identificacao.codigos_programacao: lista vazia` |
| `identificacao.cod_usina` | `identificacao.cod_usina: deve ser maior que zero` |
| `identificacao.nome_ons` | `identificacao.nome_ons: em maiúsculas e sem acento, como nos conjuntos do ONS` |
| planejamento | `identificacao.planejamento <n>: codigo deve ser inteiro maior que zero`; `… <n>: inicio no formato AAAA-MM`; `… <n>: fim no formato AAAA-MM ou vazio (vigente)`; `… <n>: fim antes do início`; `identificacao.planejamento: código <c> com períodos sobrepostos` |
| membros | `identificacao.membros <n>: id_ons, ceg no padrão, inicio AAAA-MM-DD e fim AAAA-MM-DD ou vazio` |
| `[cobertura]` | `cobertura: tabela obrigatória para <tipo>`; `cobertura: deve ser uma tabela [cobertura]`; `cobertura.<chave>: conjunto do ONS desconhecido ou que não serve a <tipo>`; `cobertura.<chave>: use proprio, conjunto, agregado, ausente ou a lista ["proprio", "conjunto"]` |
| potência instalada ou unitária, engolimento, garantia física ou queda bruta ≤ 0 | `parametros.<campo>: deve ser maior que zero` |
| `parametros.unidades_geradoras` | `parametros.unidades_geradoras: deve ser pelo menos 1` |
| potência unitária × unidades | `parametros.potencia_unitaria_mw × unidades_geradoras (<produto> MW) diferente da potência instalada (<instalada> MW) em mais de 0.1 MW` |
| lista de potências | `parametros.potencias_unidades_mw: não se aplica a UHE`; `parametros: use potencia_unitaria_mw ou potencias_unidades_mw, não os dois`; `parametros.potencias_unidades_mw: cada valor deve ser maior que zero`; `parametros.potencias_unidades_mw: <n> valores para <m> unidades`; `parametros: soma das unidades (<x> MW) diferente da potência instalada (<y> MW) em mais de 0,1 MW` |
| garantia física | `parametros.garantia_fisica_mwmed: maior que a potência instalada` |
| IP ou TEIF | `parametros.<campo>: deve estar entre 0 (inclusive) e 1 (exclusive)` |
| rendimento | `parametros.rendimento_turbina_gerador: deve estar entre 0 (exclusive) e 1 (inclusive)` |
| perda hidráulica | `parametros.perda_hidraulica_m: não pode ser negativa` ou `parametros.perda_hidraulica_m: deve ser menor que a queda bruta` |
| vazão remanescente | `parametros.vazao_remanescente_m3s: não pode ser negativa` |
| vertimento mínimo | `analises.vertimento_minimo_m3s: não pode ser negativo` |
| faixas de geração | `analises.faixas_geracao_mw: deve ser crescente` ou `analises.faixas_geracao_mw: cada valor deve ficar acima de 1 MW (usina parada) e abaixo da plena carga (<0,90 × potência instalada> MW)` |

Exemplo (perfil da São Domingos com cinco problemas introduzidos):

```text
Perfil da usina 'sao_domingos' inválido (usinas/sao_domingos/perfil.toml):
- usina.estado: deve ter 2 letras maiúsculas
- parametros.garantia_fisica_mwmed: campo obrigatório ausente
- parametros.potencia_unitaria_mw × unidades_geradoras (40 MW) diferente da potência instalada (48 MW) em mais de 0.1 MW
- analises.faixas_geracao_mw: cada valor deve ficar acima de 1 MW (usina parada) e abaixo da plena carga (43.2 MW)
- textos.ressalva_volume_util: não pode ser vazio (campo opcional presente)
```

## Uso de cada identificador

A regra de qual coluna de cada conjunto recebe cada valor é geral e fica no registro dos conjuntos; o perfil só informa os valores. A comparação de cada conjunto está no [data-model](../data-model.md), seção 5.2.

| Conjunto do ONS | Identificador de extração | Conferência |
|---|---|---|
| Energia Vertida Turbinável | `cod_usina` | `nome_ons` contido em `nom_reservatorio` |
| Indicadores por unidade geradora (mensal e anual) | `ceg` | `id_ons` (coluna `id_usina`) |
| Taxas TEIFa e TEIP; Parâmetros das taxas | `ceg` (coluna `cod_ceg`) | não há |
| Programação diária | `cod_programacao` ou `codigos_programacao` (coluna `cod_exibicaousina`) | `estado` e, nas hidrelétricas, `nome_ons` contido em `nom_usina` |
| Disponibilidade por usina | `id_ons` | `ceg` e `estado` |
| Dados hidrológicos horários | `cod_usina` | `nome_ons` contido em `nom_reservatorio`, e `id_reservatorio` |
| Geração por usina, da usina | `id_ons` | `ceg` e `estado` |
| Geração por usina, do conjunto | `id_conjunto` (coluna `id_ons`) | `estado` |
| Geração térmica por motivo de despacho | `ceg` | `[[identificacao.planejamento]]`: código no período dele (coluna `cod_usinaplanejamento`) |
| CVU das usinas térmicas | `[[identificacao.planejamento]]`: os códigos (coluna `cod_usinaplanejamento`) | `subsistema` (coluna `id_subsistema`) |
| CMO semanal | `subsistema` (coluna `id_subsistema`) | não há: contexto do subsistema |
| Fator de capacidade; restrição com a razão | `id_ons` (usina) ou `id_conjunto` (conjunto) | `ceg` (usina) ou `estado` (conjunto) |
| Restrição com detalhe | `id_ons` (e o de cada membro) | `ceg` (e o de cada membro) |
| Modalidade das usinas (cadastro) | `ceg` | `id_ons` e `estado`, só contados |
| Composição dos conjuntos | `id_conjunto` (coluna `id_ons_conjunto`) | `estado` (coluna `estad_id`) |
| Capacidade de geração | `ceg` | `estado`; nas usinas do conjunto, o subsistema da linha delas na composição |

Nomes nunca identificam nem conferem nos conjuntos dos demais tipos: o ONS os grafa de mais de um jeito ("Willian" e "William"; "230kV" e "230 kV").

## Perfil da São Domingos (exemplo)

```toml
# Perfil da UHE São Domingos (MS). Valores de identificação conferidos nos conjuntos do ONS;
# parâmetros técnicos do RF 0009/2017-AGEPAN-SFG, exceto a garantia física (ANEEL).
# Homônimos excluídos pelos identificadores: PCH São Domingos I e II (GO), CGH São Domingos (SC),
# CGH São Domingos do Prata (RS), UTE São Domingos (SP), eólicas e solares São Domingos (RN, BA).

[usina]
slug = "sao_domingos"
nome = "UHE São Domingos"
nome_curto = "São Domingos"                # frases sobre homônimos no cadastro
estado = "MS"
inicio_operacao_comercial = 2013
tipo = "UHE"                               # prefixo do CEG
modalidade = "TIPO II-A"                   # modalidade de operação no cadastro do ONS

[identificacao]
cod_usina = 153                      # Energia Vertida Turbinável e Dados hidrológicos horários
nome_ons = "SAO DOMINGOS"            # nome da usina e do reservatório nos conjuntos (conferência)
ceg = "UHE.PH.MS.028761-0.01"        # indicadores, TEIFa/TEIP, geração, disponibilidade e cadastro
id_ons = "MSUHSD"                    # geração, disponibilidade e cadastro
cod_programacao = "PRUHSD"           # Programação diária (código de exibição)
id_reservatorio = "PNUHSD"           # Dados hidrológicos horários (conferência)

[parametros]
potencia_instalada_mw = 48.0
unidades_geradoras = 2
potencia_unitaria_mw = 24.0
tipo_turbina = "Kaplan de eixo vertical"
engolimento_nominal_ug_m3s = 81.5
garantia_fisica_mwmed = 36.4
ip_referencia = 0.06861
teif_referencia = 0.02333
queda_bruta_m = 35.24
perda_hidraulica_m = 0.747
rendimento_turbina_gerador = 0.9053
vazao_remanescente_m3s = 4.78

[parametros.fontes]
geral = "RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3"
garantia_fisica = "ANEEL, valor vigente consultado em 02/10/2026"
inicio_operacao_comercial = "Despachos ANEEL nº 377/2013 e nº 2.692/2013, citados no RF 0009/2017-AGEPAN-SFG"
ip_teif = "cálculo de garantia física registrado no RF 0009/2017-AGEPAN-SFG, quando a garantia física era de 36,9 MWmed"

[analises]
vertimento_minimo_m3s = 6.0                       # patamar contínuo de vertimento da série (0 se não houver)
faixas_geracao_mw = [10.0, 20.0, 30.0, 40.0]      # faixas intermediárias da análise de EVT por nível de geração
descricao_vertimento_minimo = "patamar contínuo da série, da ordem da vazão remanescente"

[analises.fontes]
vertimento_minimo = "patamar de 5 a 6 m³/s observado na série"

[textos]
ressalva_volume_util = "O volume útil é apresentado como informado; ele varia entre os anos sem variação correspondente do nível de montante, por isso o comportamento do reservatório é descrito pelo nível."
```

Sem `[cobertura]` e sem `situacao`: valem os dez conjuntos da UHE, e o perfil conta como conferido. O perfil da usina fictícia dos testes (`tests/fixtures/usina_ficticia/perfil.toml`, três unidades geradoras) é um exemplo sem os textos opcionais; os das sete usinas fictícias, um por tipo, ficam em `tests/fixtures/usinas_ficticias/<tipo>/perfil.toml`.

## Rascunho

O comando `perfil` ([cli-perfil.md](cli-perfil.md)) grava o rascunho assim:
- um cabeçalho em comentário, com a data de montagem do catálogo e o lembrete de conferir, completar e trocar a situação;
- `situacao = "rascunho"` e a lista `pendentes`;
- um comentário em cada valor, com a origem: o conjunto do ONS e a data de publicação do arquivo usado no catálogo, e "a conferir" onde o valor pede conferência (o nome curto e o início da operação comercial);
- os campos pendentes como linhas comentadas, cada uma com o campo da fonte; os parâmetros opcionais do tipo também, marcados "opcional";
- nos códigos de programação, os períodos de cada código na Programação diária, num comentário; sem código ligado, a lista dos códigos do estado;
- as divergências achadas no catálogo, como comentário, por exemplo a potência autorizada do cadastro diferente da soma das unidades.

Cada exemplo abaixo mostra o rascunho com os conjuntos do registro; num perfil gravado antes de um conjunto entrar no registro, a chave nova da `[cobertura]` aparece como diferença no `perfil` (código 6), e o fiscal a acrescenta.

### UTE William Arjona: rascunho, Tipo I

```toml
# Rascunho gerado por "python -m src perfil" a partir do catálogo de usinas (data/catalogo/, montado em 2026-10-20 ... UTC).
# Confira cada valor com a fonte, complete os pendentes e troque situacao para "conferido".
# Identificação só pelos códigos (CEG, id ONS, id do conjunto e códigos de programação), nunca pelo nome.

[usina]
slug = "william_arjona"
nome = "UTE WILLIAM ARJONA (UTWI)"   # Modalidade das usinas, publicado em 18/10/2026; ajuste para o nome do relatório
nome_curto = "UTE WILLIAM ARJONA (UTWI)"  # a conferir
estado = "MS"                         # Modalidade das usinas
tipo = "UTE"                          # prefixo do CEG
modalidade = "TIPO I"                 # Modalidade das usinas
subsistema = "SE"                     # Capacidade de geração ou Composição dos conjuntos
inicio_operacao_comercial = 2021      # Capacidade de geração: primeira unidade ativa em 10/07/2021; a conferir
situacao = "rascunho"
pendentes = ["parametros.fontes.geral", "parametros.garantia_fisica_mwmed (opcional)", "parametros.ip_referencia (opcional)", "parametros.teif_referencia (opcional)"]

[identificacao]
ceg = "UTE.GN.MS.027075-0.01"         # Modalidade das usinas
id_ons = "MSUTWI"                     # Modalidade das usinas
codigos_programacao = ["MSUTWI"]      # Programação diária, publicado em 18/10/2026

[[identificacao.planejamento]]        # Geração térmica por motivo de despacho; publicado como Willian Arjona
codigo = 34
inicio = "2013-01"
fim = "2018-08"                       # vazio = vigente

[[identificacao.planejamento]]        # Geração térmica por motivo de despacho; publicado como William Arjona; William Arjona Gás
codigo = 334
inicio = "2021-07"
fim = ""                              # vazio = vigente

[[identificacao.planejamento]]        # Geração térmica por motivo de despacho; publicado como William Arjona Óleo
codigo = 434
inicio = "2021-08"
fim = "2026-01"                       # vazio = vigente

[cobertura]                           # catálogo de usinas; a conferir
indicadores = "proprio"
programacao = "proprio"
disponibilidade = "proprio"
geracao = "proprio"
despacho = "proprio"
cvu = "proprio"

[parametros]
potencia_instalada_mw = 177.116       # Capacidade de geração: 5 unidades ativas
unidades_geradoras = 5
potencias_unidades_mw = [39.16, 39.16, 33.0, 33.1, 32.696]
combustivel = "GÁS"                   # Capacidade de geração
# garantia_fisica_mwmed =             # pendente: opcional; valor e fonte
# ip_referencia =                     # pendente: opcional; valor e fonte
# teif_referencia =                   # pendente: opcional; valor e fonte

[parametros.fontes]
# geral =                             # pendente: documento e data dos parâmetros
```

### PCH Bandeirante: rascunho, em conjunto (Tipo II-C)

```toml
[usina]
slug = "bandeirante"
nome = "PCH BANDEIRANTE (CONEXÃO DEFINITIVA)"  # Modalidade das usinas; ajuste para o nome do relatório
nome_curto = "PCH BANDEIRANTE (CONEXÃO DEFINITIVA)"  # a conferir
estado = "MS"
tipo = "PCH"
modalidade = "TIPO II-C"
subsistema = "SE"
inicio_operacao_comercial = 2019      # Capacidade de geração: primeira unidade ativa em 12/10/2019; a conferir
situacao = "rascunho"

[identificacao]
ceg = "PCH.PH.MS.032163-0.01"         # Modalidade das usinas
id_ons = "MSBDT"                      # Modalidade das usinas
id_conjunto = "CJU_MSCAO"             # Composição dos conjuntos: Conj. Chapadão
codigos_programacao = ["MSCAO-9761", "MSCAO-9762", "MSCAO-9763", "MSCAO-9766", "MSCAO-10205", "MSCAO-9764", "MSCAO-9765", "MSCAO-9784"] # Programação diária, publicado em 20/10/2026
#   períodos na Programação diária: MSCAO-9761 de 01/10/2024 a 02/07/2025; ...; MSCAO-9784 desde 05/07/2025

[[identificacao.membros]]             # Composição dos conjuntos
id_ons = "MSBDT"
ceg = "PCH.PH.MS.032163-0.01"
inicio = "2019-08-22"
fim = ""                              # vazio = vigente
# ... as outras três PCH do conjunto vigente, no mesmo formato ...

[cobertura]                           # catálogo de usinas; a conferir
evt = "ausente"
indicadores = "ausente"
programacao = "conjunto"
disponibilidade = "ausente"
hidrologia = "ausente"
geracao = "conjunto"

[parametros]
potencia_instalada_mw = 27.9999       # Capacidade de geração: 3 unidades ativas
unidades_geradoras = 3
potencia_unitaria_mw = 9.3333
```

Os oito códigos de programação são os dois grupos de quatro do Conj. Chapadão: `MSCAO-9761`, `-9762`, `-9763` e `-9766` até 02/07/2025, e `MSCAO-9764`, `-9765`, `-9784` e `-10205` desde 05/07/2025.

### UFV Seriemas 1: rascunho, em conjunto com série própria na restrição

```toml
[usina]
slug = "seriemas_1"
nome = "UFV SERIEMAS 1 (SAE)"
estado = "MS"
tipo = "UFV"
modalidade = "TIPO II-C"
inicio_operacao_comercial = 2026      # Capacidade de geração: primeira unidade ativa em 22/08/2026; a conferir
situacao = "rascunho"

[identificacao]
ceg = "UFV.RS.MS.052257-0.01"         # Modalidade das usinas
id_ons = "MSSRI1"                     # Modalidade das usinas
id_conjunto = "CJU_MS4FINO"           # Composição dos conjuntos: Conj. Inocência 230 kV
codigos_programacao = ["MS4FINO"]     # Programação diária, publicado em 20/10/2026

[[identificacao.membros]]             # Composição dos conjuntos
id_ons = "MSSRI1"
ceg = "UFV.RS.MS.052257-0.01"
inicio = "2026-04-13"
fim = ""                              # vazio = vigente
# ... as outras sete usinas do conjunto (Seriemas 2 a 8), no mesmo formato ...

[cobertura]                           # catálogo de usinas; a conferir
programacao = "conjunto"
geracao = "conjunto"
fator_capacidade = "conjunto"
restricao_detalhe = "proprio"
restricao_razao = "conjunto"

[parametros]
potencia_instalada_mw = 50.0          # Capacidade de geração: 2 unidades ativas
unidades_geradoras = 2
potencias_unidades_mw = [21.43, 28.57]
# Divergência: potência autorizada no cadastro do ONS = 2,507 MW. Confira com a fonte.
```

### EOL Praia Formosa: identificação e cobertura, Tipo I

```toml
[identificacao]
ceg = "EOL.CV.CE.028631-1.01"
id_ons = "CEUFM"                      # o cadastro publica "CEUFM ", com espaço no fim
codigos_programacao = ["CEUFM"]

[cobertura]
geracao = "proprio"
programacao = "proprio"
fator_capacidade = "proprio"          # desde 07/2009
restricao_detalhe = "proprio"         # desde 10/2021
restricao_razao = "proprio"
```

## Como preencher o perfil de outra usina

1. Montar o catálogo e achar a usina: `python -m src usinas --estado <UF>`. A coluna `PERFIL` mostra se ela já tem perfil; as colunas de cobertura, o que o ONS publica dela.
2. Gerar o rascunho: `python -m src perfil --ceg <CEG> [--slug <slug>]`. Usina Tipo III ou só com agregado não recebe perfil.
3. Conferir no rascunho o tipo, a modalidade, os identificadores, os códigos de programação (e os períodos deles) e a `[cobertura]`, com o catálogo e, se preciso, com os conjuntos do ONS:

   | Campo | Onde conferir |
   |---|---|
   | `cod_usina` | Reservatórios (`cod_resplanejamento`) ou Energia Vertida Turbinável, coluna `cod_usina` (a mesma dos Dados hidrológicos horários) |
   | `nome_ons` | nome do reservatório nos conjuntos do ONS (`nom_reservatorio`), em maiúsculas e sem acento |
   | `ceg` | ANEEL (SIGA); aparece também nos indicadores e no cadastro do ONS |
   | `id_ons` | Geração por usina, Disponibilidade por usina ou Modalidade das usinas, coluna `id_ons` |
   | `id_conjunto` | Composição dos conjuntos, coluna `id_ons_conjunto` |
   | `cod_programacao` ou `codigos_programacao` | Programação diária, coluna `cod_exibicaousina` |
   | `id_reservatorio` | Reservatórios (`res_id`) ou Dados hidrológicos horários, coluna `id_reservatorio` |
   | `[[identificacao.planejamento]]` | Geração térmica por motivo de despacho, coluna `cod_usinaplanejamento` |

4. Completar os parâmetros técnicos pendentes com a fonte e a data em `[parametros.fontes]`: garantia física da ANEEL ou da EPE; potência, unidades, combustível, turbina, engolimento, quedas, rendimento, IP e TEIF de referência dos documentos do agente ou de relatório de fiscalização. Completar `[analises]` onde há EVT e, se houver, os textos opcionais.
5. Esvaziar `pendentes` e trocar `situacao` para `"conferido"`.
6. Executar `python -m src coleta --usina <slug>`. O perfil é validado antes de tudo; os arquivos brutos já baixados para outra usina são reaproveitados.
7. Conferir nas auditorias da coleta as linhas que conferem só em parte (`linhas_so_identificador` e `linhas_so_conferencia`; na EVT, `registros_codigo_sem_nome` e `registros_nome_sem_codigo`; na programação, `linhas_codigo_sem_conferencia`) e, em `cadastro_ficha.csv`, `linhas_ceg` e os homônimos. Elas indicam identificador errado no perfil ou mudança de cadastro no ONS.
