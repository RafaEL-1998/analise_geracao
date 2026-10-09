# Contract: Perfil da usina para todos os tipos

**Spec**: [spec.md](../spec.md) (FR-006 a FR-011) · **Data model**: [seção 3](../data-model.md) · **Research**: R4, R5

Este contrato amplia o [contrato atual do perfil](../../001-coleta-dados/contracts/perfil-usina.md). Continuam valendo:
- o local e o formato: `usinas/<slug>/perfil.toml`, em UTF-8, lido com `tomllib`;
- a leitura no início de todo comando com `--usina`;
- a validação de uma vez só, com a lista de todos os problemas (código 4);
- os tipos de valor: "real", "inteiro" e texto não vazio;
- os campos e as regras de hoje na UHE.

Abaixo, só o que muda.

## O que muda

| Parte | Mudança |
|---|---|
| `[usina]` | entram `tipo`, `modalidade`, `situacao`, `pendentes` e, nas térmicas, `subsistema` |
| `[identificacao]` | cada campo passa a ser exigido conforme o tipo e a `[cobertura]`; entram `id_conjunto`, `codigos_programacao`, `[[identificacao.planejamento]]` e `[[identificacao.membros]]`; o CEG aceita os sete prefixos |
| `[cobertura]` | tabela nova: o nível de cada conjunto de série do ONS que cobre a usina |
| `[parametros]` | os campos hidráulicos passam a ser exigidos só onde há EVT ou hidrologia; entram `potencias_unidades_mw` e `combustivel` |
| `[analises]` | exigida só onde há EVT |

## `[usina]`: campos novos

| Campo | Tipo | Obrigatório | Validação |
|---|---|---|---|
| `tipo` | texto | sim | `UHE`, `PCH`, `CGH`, `UTE`, `UTN`, `EOL` ou `UFV`; igual ao prefixo do CEG |
| `modalidade` | texto | sim | `TIPO I`, `TIPO II-A`, `TIPO II-B` ou `TIPO II-C`. Tipo III é recusado: o ONS só publica o agregado (FR-001, FR-009) |
| `situacao` | texto | não | `rascunho` ou `conferido`; ausente vale `conferido`; `rascunho` é sempre recusado |
| `pendentes` | lista de texto | não | precisa estar vazia ou ausente quando `conferido` |
| `subsistema` | texto | em UTE e UTN com `cvu` na cobertura (a partir da fase B) | `SE`, `S`, `NE` ou `N`; o rascunho o traz do catálogo |

O `slug` não pode ser `carteiras`, que é a pasta das carteiras em `reports/`.

## `[identificacao]`

Legenda: `O` = obrigatório; `C` = obrigatório quando um conjunto com cobertura `proprio` ou `conjunto` usa o campo; `—` = não se aplica, e a presença é recusada.

| Campo | Tipo | UHE | PCH e CGH | UTE e UTN | EOL e UFV | Uso |
|---|---|---|---|---|---|---|
| `ceg` | texto | O | O | O | O | padrão `<UHE\|PCH\|CGH\|UTE\|UTN\|EOL\|UFV>.<2 letras>.<UF>.<6 algarismos>-<1>.<2>` |
| `id_ons` | texto | O | C | O | C | geração, disponibilidade, fator de capacidade e restrição, quando `proprio` |
| `cod_usina` | inteiro | O | C | — | — | EVT e hidrologia |
| `nome_ons` | texto | O | C | — | — | conferência na EVT e na hidrologia, como hoje |
| `id_reservatorio` | texto | O | C | — | — | hidrologia |
| `cod_programacao` ou `codigos_programacao` | texto ou lista | O | O | O | O | Programação diária; lista quando a usina ou o conjunto tem mais de um código |
| `id_conjunto` | texto | — | C | C | C | geração, fator de capacidade e razão da restrição, quando `conjunto`; composição |

### `[[identificacao.planejamento]]` (UTE e UTN)

Uma entrada por código de planejamento, com o período em que vale. É exigida pelo menos uma quando a `[cobertura]` traz `despacho` ou `cvu` (a partir da fase B).

| Campo | Tipo | Validação |
|---|---|---|
| `codigo` | inteiro | > 0; comparado como número no despacho e no CVU |
| `inicio` | texto | `AAAA-MM` |
| `fim` | texto | `AAAA-MM`, ≥ `inicio`; vazio = vigente |

Dois códigos diferentes podem valer ao mesmo tempo, como uma unidade por combustível. O mesmo código não pode ter períodos sobrepostos.

### `[[identificacao.membros]]` (opcional; usinas em conjunto)

Uma entrada por usina do conjunto, com `id_ons`, `ceg`, `inicio` e `fim` (`AAAA-MM-DD`; `fim` vazio = vigente), vinda da Composição dos conjuntos e conferida pelo fiscal. Só serve à conferência G2 (soma das usinas × conjunto). Sem ela, a G2 fica não aplicável, com o motivo.

## `[cobertura]`

Uma chave por conjunto de série do [registro](../data-model.md) (seção 4), só dos já implementados: `evt`, `indicadores`, `programacao`, `disponibilidade`, `hidrologia`, `geracao`, `despacho`, `cvu`, `fator_capacidade`, `restricao_detalhe` e `restricao_razao`.

| Valor | Efeito |
|---|---|
| `"proprio"` | a Coleta obtém o conjunto pelo identificador da usina |
| `"conjunto"` | a Coleta obtém o conjunto pelo `id_conjunto`, e os números ficam no nível do conjunto |
| `["proprio", "conjunto"]` | a usina mudou de nível no período: a Coleta obtém as duas séries, e os trechos dizem qual vale em cada hora |
| `"agregado"` ou `"ausente"` | o conjunto não é obtido; conferências e seções dele ficam não aplicáveis, com o motivo |

- Chave desconhecida, ou de conjunto que não serve ao tipo, é recusada (por exemplo, `despacho` numa UFV).
- `indicadores` cobre os quatro conjuntos de indicadores e taxas. Um deles sem linhas da usina vira conferência não aplicável, com o motivo.
- Os conjuntos cadastrais e o CMO não entram na tabela: são sempre obtidos para os tipos que os usam.
- Sem a tabela, só numa UHE: os dez conjuntos de hoje, com `proprio`, e mais nenhum.

## `[parametros]`

| Campo | Tipo | UHE | PCH e CGH | UTE e UTN | EOL e UFV | Validação |
|---|---|---|---|---|---|---|
| `potencia_instalada_mw` | real | O | O | O | O | > 0; em EOL e UFV, é a capacidade instalada |
| `unidades_geradoras` | inteiro | O | O | O | O | ≥ 1 |
| `potencia_unitaria_mw` ou `potencias_unidades_mw` | real ou lista | O (a única) | O | O | O | a soma das unidades dá a potência instalada, com tolerância de 0,1 MW; a lista tem um valor por unidade |
| `garantia_fisica_mwmed` | real | O | opcional | opcional | opcional | > 0 e ≤ potência instalada |
| `ip_referencia`, `teif_referencia` | real | O | opcional | opcional | — | ≥ 0 e < 1 |
| hidráulicos (`tipo_turbina`, `engolimento_nominal_ug_m3s`, `queda_bruta_m`, `perda_hidraulica_m`, `rendimento_turbina_gerador`, `vazao_remanescente_m3s`) | — | O | C (EVT ou hidrologia) | — | — | os de hoje |
| `combustivel` | texto | — | — | O | — | não vazio |

- `[parametros.fontes]`: `geral` é obrigatória; `garantia_fisica` é obrigatória quando há garantia física; as demais fontes são opcionais, como hoje.
- `[analises]` é exigida onde há EVT (UHE, e PCH ou CGH com EVT). `[textos]` é opcional.

## Rascunho

O comando `perfil` ([cli-perfil.md](cli-perfil.md)) grava o rascunho assim:
- `situacao = "rascunho"` e a lista `pendentes`;
- um comentário em cada valor, com a origem: o conjunto do ONS e a data de publicação;
- os campos pendentes como linhas comentadas, cada uma com o campo da fonte;
- as divergências achadas no catálogo, como comentário, por exemplo a potência autorizada do cadastro diferente da soma das unidades.

Mensagens de recusa novas, no formato de hoje (`- <problema>`):

| Situação | Mensagem |
|---|---|
| Rascunho | `usina.situacao: perfil em rascunho; complete os pendentes com a fonte e troque para "conferido"`, seguida de `pendente: <campo>` para cada pendente |
| Tipo III | `usina.modalidade: Tipo III não tem relatório por usina; o ONS só publica o agregado (ver a carteira do estado)` |
| Tipo × CEG | `usina.tipo: "<tipo>" diferente do prefixo do CEG ("<prefixo>")` |
| Campo exigido | `identificacao.<campo>: obrigatório para <tipo> com a cobertura "<nível>" em <conjunto>` |
| Campo que não se aplica | `<seção>.<campo>: não se aplica a <tipo>` |
| Cobertura inválida | `cobertura.<chave>: conjunto do ONS desconhecido ou que não serve a <tipo>`; `cobertura.<chave>: use proprio, conjunto, agregado, ausente ou a lista ["proprio", "conjunto"]` |
| Unidades | `parametros.potencias_unidades_mw: <n> valores para <m> unidades`; `parametros: soma das unidades (<x> MW) diferente da potência instalada (<y> MW) em mais de 0,1 MW` |
| Planejamento | `identificacao.planejamento: código <c> com períodos sobrepostos` |

## Exemplos

Cada exemplo mostra o rascunho a partir da fase indicada. Antes dela, as chaves de `[cobertura]` dos conjuntos ainda não implementados não aparecem, e o fiscal as acrescenta quando o `perfil` mostrar as diferenças (código 6).

### UHE São Domingos: só duas linhas novas (FR-011; fase A)

```toml
[usina]
slug = "sao_domingos"
# ... campos de hoje, sem mudança ...
tipo = "UHE"
modalidade = "TIPO II-A"
```

Sem `[cobertura]` e sem `situacao`: valem os dez conjuntos de hoje, e o perfil conta como conferido.

### UTE William Arjona: rascunho (a partir da fase B, com o despacho e o CVU)

```toml
# Rascunho gerado por "python -m src perfil" a partir do catálogo de usinas.
# Confira cada valor com a fonte, complete os pendentes e troque situacao para "conferido".
# Identificação só pelos códigos: o ONS grafa "William Arjona", "Willian Arjona" e "UT WILL. ARJONA".

[usina]
slug = "william_arjona"
nome = "UTE WILLIAM ARJONA (UTWI)"   # Modalidade das usinas; ajuste para o nome do relatório
nome_curto = "William Arjona"        # a conferir
estado = "MS"
tipo = "UTE"                         # prefixo do CEG
modalidade = "TIPO I"                # Modalidade das usinas
subsistema = "SE"                    # Capacidade de geração
inicio_operacao_comercial = 2021     # Capacidade de geração: unidades ativas desde 10/07/2021; a conferir
situacao = "rascunho"
pendentes = ["parametros.fontes.geral", "parametros.garantia_fisica_mwmed (opcional)", "parametros.ip_referencia (opcional)"]

[identificacao]
ceg = "UTE.GN.MS.027075-0.01"
id_ons = "MSUTWI"
codigos_programacao = ["MSUTWI"]     # Programação diária

[[identificacao.planejamento]]       # Geração térmica por motivo de despacho
codigo = 34
inicio = "2013-01"
fim = "2018-08"

[[identificacao.planejamento]]       # desde 07/2021; de 08/2021 a 02/2026, a parte a gás
codigo = 334
inicio = "2021-07"
fim = ""

[[identificacao.planejamento]]       # a parte a óleo
codigo = 434
inicio = "2021-08"
fim = "2026-02"

[cobertura]                          # catálogo de usinas; a conferir
geracao = "proprio"
disponibilidade = "proprio"
indicadores = "proprio"
programacao = "proprio"
despacho = "proprio"
cvu = "proprio"

[parametros]
potencia_instalada_mw = 177.116      # Capacidade de geração: cinco unidades ativas
unidades_geradoras = 5
# potencias_unidades_mw: o rascunho traz os cinco valores da Capacidade de geração (de 32,696 a 39,16 MW)
combustivel = "gás"                  # Capacidade de geração

[parametros.fontes]
# geral = ""                         # pendente: documento e data dos parâmetros
```

### UFV Seriemas 1: rascunho, em conjunto (a partir da fase C, com a restrição e o fator de capacidade)

```toml
[usina]
slug = "seriemas_1"
nome = "UFV SERIEMAS 1 (SAE)"
nome_curto = "Seriemas 1"
estado = "MS"
tipo = "UFV"
modalidade = "TIPO II-C"
inicio_operacao_comercial = 2026     # Capacidade de geração: unidades desde 22/08/2026; a conferir
situacao = "rascunho"

[identificacao]
ceg = "UFV.RS.MS.052257-0.01"
id_ons = "MSSRI1"                    # cadastro e restrição com detalhe
id_conjunto = "CJU_MS4FINO"          # Composição dos conjuntos: Conj. Inocência 230 kV, desde 13/04/2026
codigos_programacao = ["MS4FINO"]    # programação do conjunto

[[identificacao.membros]]            # Composição dos conjuntos; oito usinas, Seriemas 1 a 8
id_ons = "MSSRI1"
ceg = "UFV.RS.MS.052257-0.01"
inicio = "2026-04-13"
fim = ""
# ... as outras sete usinas do conjunto, no mesmo formato ...

[cobertura]
restricao_detalhe = "proprio"        # desde 22/08/2026
restricao_razao = "conjunto"
fator_capacidade = "conjunto"
geracao = "conjunto"                 # desde 05/05/2026
programacao = "conjunto"

[parametros]
potencia_instalada_mw = 50.0         # Capacidade de geração: duas unidades
unidades_geradoras = 2
potencias_unidades_mw = [21.43, 28.57]
# Divergência: potência autorizada no cadastro do ONS = 2,507 MW. Confira com a fonte.
```

### PCH Bandeirante: rascunho, em conjunto (a partir da fase A)

```toml
[usina]
slug = "bandeirante"
nome = "PCH BANDEIRANTE (CONEXÃO DEFINITIVA)"
nome_curto = "Bandeirante"
estado = "MS"
tipo = "PCH"
modalidade = "TIPO II-C"
situacao = "rascunho"

[identificacao]
ceg = "PCH.PH.MS.032163-0.01"
id_ons = "MSBDT"                     # linhas próprias na geração, sem valor
id_conjunto = "CJU_MSCAO"            # Conj. Chapadão, desde 22/08/2019; teve térmicas até 01/07/2025
codigos_programacao = ["MSCAO-10205", "MSCAO-9764", "MSCAO-9765", "MSCAO-9784"]  # um por barra; a conferir

[cobertura]
geracao = "conjunto"
programacao = "conjunto"
evt = "ausente"
hidrologia = "ausente"
disponibilidade = "ausente"
indicadores = "ausente"

[parametros]
potencia_instalada_mw = 28.0         # Capacidade de geração: três unidades
unidades_geradoras = 3
potencia_unitaria_mw = 9.3333
```

### EOL Praia Formosa: identificação e cobertura, Tipo I (a partir da fase C)

```toml
[identificacao]
ceg = "EOL.CV.CE.028631-1.01"
id_ons = "CEUFM"
codigos_programacao = ["CEUFM"]

[cobertura]
geracao = "proprio"
programacao = "proprio"
fator_capacidade = "proprio"         # desde 07/2009
restricao_detalhe = "proprio"        # desde 10/2021
restricao_razao = "proprio"
```
