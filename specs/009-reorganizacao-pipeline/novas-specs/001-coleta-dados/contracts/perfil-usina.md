# Contract: Perfil da usina

**Spec**: [spec.md](../spec.md) · **Objetos, valores derivados e regras de leitura**: [data-model.md](../data-model.md) (seções 3.1 e 5.1)

## Local e formato

- **Arquivo**: `usinas/<slug>/perfil.toml`, em UTF-8, no formato TOML (lido com `tomllib`, da biblioteca padrão).
- **Slug**: nome da pasta em `usinas/`, igual a `usina.slug`.
- **Comentários**: começam com `#` e registram a origem de cada valor.
- **Pasta da usina**: guarda também `documentos/` (fora do git), que o fluxo não lê.
- **Quando é lido**: no início de todo comando com `--usina` (as cinco etapas, `completo` e `comparar`), antes de qualquer outra ação, inclusive da consulta ao portal; a `copia-seguranca` não lê perfil. Durante cada etapa, o perfil validado fica ativo (`perfil_ativo()`).
- **O perfil traz só valores próprios da usina**. Os valores derivados (engolimento máximo, disponibilidade de referência, produtividade nominal, plena carga, limites físicos) são calculados a partir dele ([data-model](../data-model.md), seção 3.1). As regras gerais (limiares, tolerâncias e metas) ficam em `src/comum/regras.py` e não podem ser alteradas pelo perfil; os únicos limiares próprios da usina são os da seção `[analises]`.

## Seções e campos

"Real" aceita número inteiro ou real do TOML; "inteiro" aceita só inteiro; booleano nunca vale como número. Texto obrigatório e texto opcional presente não podem ser vazios. Campos não previstos são ignorados.

### `[usina]`

| Campo | Tipo | Obrigatório | Validação | Uso |
|---|---|---|---|---|
| `slug` | texto | sim | letras minúsculas, algarismos e `_`; igual ao nome da pasta | pastas da usina em `data/usinas/` e `reports/` |
| `nome` | texto | sim | não vazio | título e textos do relatório |
| `nome_curto` | texto | sim | não vazio | nome sem o tipo, nas frases sobre homônimos do cadastro |
| `estado` | texto | sim | 2 letras maiúsculas | conferência na coleta; conferência do cadastro; textos do relatório |
| `inicio_operacao_comercial` | inteiro | sim | de 1900 até o ano atual | tabela de parâmetros e constatações |

### `[identificacao]`

| Campo | Tipo | Obrigatório | Validação | Uso |
|---|---|---|---|---|
| `cod_usina` | inteiro | sim | > 0 | identificador na EVT e nos Dados hidrológicos horários |
| `nome_ons` | texto | sim | maiúsculas sem acento: letras, algarismos, espaço, `.`, `-` e `/` | conferência ("contém") na EVT, na hidrologia e na programação; homônimos no cadastro |
| `ceg` | texto | sim | padrão da ANEEL para UHE: `UHE.PH.<UF>.<6 algarismos>-<1 algarismo>.<2 algarismos>` | identificador nos indicadores, nas taxas e no cadastro; conferência na disponibilidade e na geração |
| `id_ons` | texto | sim | não vazio | identificador na disponibilidade e na geração; conferência nos indicadores por UG e no cadastro |
| `cod_programacao` | texto | sim | não vazio | identificador na Programação diária (código de exibição) |
| `id_reservatorio` | texto | sim | não vazio | conferência nos Dados hidrológicos horários |

### `[parametros]`

| Campo | Tipo | Obrigatório | Validação | Uso |
|---|---|---|---|---|
| `potencia_instalada_mw` | real | sim | > 0 | análises, relatório, limites físicos e conferência do cadastro |
| `unidades_geradoras` | inteiro | sim | ≥ 1 | engolimento máximo, faixas de afluência, relatório |
| `potencia_unitaria_mw` | real | sim | > 0; vezes `unidades_geradoras`, igual a `potencia_instalada_mw` com tolerância de 0,1 MW | indicadores por UG e relatório |
| `tipo_turbina` | texto | sim | não vazio | tabela de parâmetros e textos do relatório |
| `engolimento_nominal_ug_m3s` | real | sim | > 0 | engolimento máximo e faixas de afluência |
| `garantia_fisica_mwmed` | real | sim | > 0 e ≤ `potencia_instalada_mw` | análises, conclusão e relatório |
| `ip_referencia` | real | sim | ≥ 0 e < 1 | disponibilidade de referência; análises e relatório |
| `teif_referencia` | real | sim | ≥ 0 e < 1 | disponibilidade de referência; análises e relatório |
| `queda_bruta_m` | real | sim | > 0 | produtividade nominal (validação física) e tabela de parâmetros |
| `perda_hidraulica_m` | real | sim | ≥ 0 e < `queda_bruta_m` | idem |
| `rendimento_turbina_gerador` | real | sim | > 0 e ≤ 1 | idem |
| `vazao_remanescente_m3s` | real | sim | ≥ 0 | tabela de parâmetros e notas |

### `[parametros.fontes]`

| Campo | Tipo | Obrigatório | Validação | Uso |
|---|---|---|---|---|
| `geral` | texto | sim | não vazio | fonte e data dos parâmetros, na tabela de parâmetros |
| `garantia_fisica` | texto | sim | não vazio | fonte e data da garantia física |
| `inicio_operacao_comercial` | texto | não | se presente, não vazio | origem do ano de início da operação comercial, na tabela de parâmetros |
| `ip_teif` | texto | não | se presente, não vazio | nota "O IP e o TEIF de referência são os do <texto>; …" |

### `[analises]`

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

| Campo | Tipo | Obrigatório | Validação | Uso |
|---|---|---|---|---|
| `ressalva_volume_util` | texto | não | se presente, não vazio | ressalva própria da usina, nas notas da hidrologia |

Sem um texto opcional, o relatório omite o trecho correspondente ([Geração do relatório](../../005-geracao-relatorio/spec.md)).

## Recusa do perfil

Um perfil ausente, ilegível, com campo obrigatório faltante, com texto opcional vazio, com tipo ou faixa errados ou com incoerência é recusado com o código 4, sem gravar nada. A mensagem sai na saída de erro, com todos os problemas de uma vez, um por linha:

```text
Perfil da usina '<slug>' inválido (usinas/<slug>/perfil.toml):
- <problema>
- <problema>
```

As faixas e as coerências só são conferidas quando os campos envolvidos têm o tipo certo. Os números das mensagens saem no formato do Python, com ponto decimal.

| Problema | Mensagem |
|---|---|
| arquivo ausente | `arquivo do perfil não encontrado: usinas/<slug>/perfil.toml` |
| TOML inválido ou fora do UTF-8 | `arquivo ilegível: <erro do leitor>` |
| campo obrigatório ausente | `<campo>: campo obrigatório ausente` |
| texto de outro tipo | `<campo>: deve ser texto` |
| texto obrigatório vazio | `<campo>: não pode ser vazio` |
| texto opcional presente e vazio | `<campo>: não pode ser vazio (campo opcional presente)` |
| inteiro de outro tipo | `<campo>: deve ser número inteiro` |
| real de outro tipo | `<campo>: deve ser número` |
| lista de faixas inválida | `analises.faixas_geracao_mw: deve ser lista não vazia de números` |
| `usina.slug` fora do padrão | `usina.slug: só letras minúsculas, algarismos e _` |
| `usina.slug` diferente da pasta | `usina.slug: '<slug>' diferente do nome da pasta '<pasta>'` |
| `usina.estado` | `usina.estado: deve ter 2 letras maiúsculas` |
| `usina.inicio_operacao_comercial` | `usina.inicio_operacao_comercial: deve estar entre 1900 e o ano atual` |
| `identificacao.cod_usina` | `identificacao.cod_usina: deve ser maior que zero` |
| `identificacao.nome_ons` | `identificacao.nome_ons: em maiúsculas e sem acento, como nos conjuntos do ONS` |
| `identificacao.ceg` | `identificacao.ceg: fora do padrão UHE.PH.UF.NNNNNN-D.DD` |
| potência instalada ou unitária, engolimento, garantia física ou queda bruta ≤ 0 | `parametros.<campo>: deve ser maior que zero` |
| `parametros.unidades_geradoras` | `parametros.unidades_geradoras: deve ser pelo menos 1` |
| potência unitária × unidades | `parametros.potencia_unitaria_mw × unidades_geradoras (<produto> MW) diferente da potência instalada (<instalada> MW) em mais de 0.1 MW` |
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

A regra de qual coluna de cada conjunto recebe cada valor é geral e fica no código da coleta; o perfil só informa os valores. A comparação de cada conjunto está no [data-model](../data-model.md), seção 5.2.

| Conjunto do ONS | Identificador de extração | Conferência |
|---|---|---|
| Energia Vertida Turbinável | `cod_usina` | `nome_ons` contido em `nom_reservatorio` |
| Indicadores por unidade geradora (mensal e anual) | `ceg` | `id_ons` (coluna `id_usina`) |
| Taxas TEIFa e TEIP; Parâmetros das taxas | `ceg` (coluna `cod_ceg`) | não há |
| Programação diária | `cod_programacao` (coluna `cod_exibicaousina`) | `nome_ons` contido em `nom_usina`, e `estado` |
| Disponibilidade por usina | `id_ons` | `ceg` e `estado` |
| Dados hidrológicos horários | `cod_usina` | `nome_ons` contido em `nom_reservatorio`, e `id_reservatorio` |
| Geração por usina | `id_ons` | `ceg` e `estado` |
| Modalidade das usinas (cadastro) | `ceg` | `id_ons` e `estado`, só contados |

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

O perfil da usina fictícia dos testes (`tests/fixtures/usina_ficticia/perfil.toml`, três unidades geradoras) é um exemplo sem os textos opcionais.

## Como preencher o perfil de outra usina

1. Criar `usinas/<novo_slug>/perfil.toml` a partir de um perfil existente, sem copiar `documentos/`, e trocar todos os valores.
2. Preencher a identificação:

   | Campo | Onde obter |
   |---|---|
   | `cod_usina` | Energia Vertida Turbinável, coluna `cod_usina` (a mesma dos Dados hidrológicos horários) |
   | `nome_ons` | nome do reservatório nos conjuntos do ONS (`nom_reservatorio`), em maiúsculas e sem acento |
   | `ceg` | ANEEL (SIGA); aparece também nos indicadores e no cadastro do ONS |
   | `id_ons` | Geração por usina, Disponibilidade por usina ou Modalidade das usinas, coluna `id_ons` |
   | `cod_programacao` | Programação diária, coluna `cod_exibicaousina` |
   | `id_reservatorio` | Dados hidrológicos horários, coluna `id_reservatorio` |

3. Preencher os parâmetros técnicos com a fonte e a data em `[parametros.fontes]`: garantia física da ANEEL; potência, unidades, turbina, engolimento, quedas, rendimento, IP e TEIF de referência dos documentos do agente ou de relatório de fiscalização.
4. Preencher `[analises]` e, se houver, os textos opcionais.
5. Executar `python -m src coleta --usina <novo_slug>`. O perfil é validado antes de tudo; os arquivos brutos já baixados para outra usina são reaproveitados.
6. Conferir nas auditorias da coleta as linhas que conferem só em parte (`linhas_so_identificador` e `linhas_so_conferencia`; na EVT, `registros_codigo_sem_nome` e `registros_nome_sem_codigo`; na programação, `linhas_codigo_sem_conferencia`) e, em `cadastro_ficha.csv`, `linhas_ceg` e os homônimos. Elas indicam identificador errado no perfil ou mudança de cadastro no ONS.
