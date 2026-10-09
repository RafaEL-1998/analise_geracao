# Ajustes à spec da Coleta de dados — spec 006, fase A

**Situação**: rascunho para aprovação do usuário (tarefa T009) · **Destino**: `specs/001-coleta-dados/`, na incorporação (fase F)

Redação final. Os requisitos novos seguem a numeração da spec da Coleta (a partir da FR-049). Os alterados citam a FR de hoje. Detalhes de formato estão no [data-model](../data-model.md) e nos [contratos](../contracts/), que passam a ser contratos da Coleta na incorporação.

## Objetivo (acréscimo)

A Coleta passa a atender qualquer usina que os dados abertos do ONS cobrem: UHE, PCH, CGH, UTE, UTN, EOL e UFV. O tipo e a cobertura declarados no perfil definem os conjuntos obtidos e a série que define o período. A Coleta também monta o catálogo de usinas e o rascunho do perfil.

## Requisitos alterados

- **FR-002** (linha de comando): entram os comandos:
  - `usinas`, que monta o catálogo;
  - `perfil --ceg <CEG> [--slug <slug>]`, que monta o rascunho do perfil;
  - `referencia` e o modo `comparar --todas [--coleta]`, descritos na spec da Geração do relatório.
  - `usinas` e `perfil` não usam `--usina`.
- **FR-005** (códigos de saída): o 4 vale também para o perfil em rascunho; o 5, para o `perfil` com o catálogo ausente ou em formato antigo; o 6, para o `perfil` com um perfil existente diferente do catálogo.
- **FR-006 a FR-009** (perfil): o perfil passa a declarar:
  - `tipo` e `modalidade` (Tipo III recusado);
  - `situacao` (`rascunho` é recusado com o código 4 e a lista `pendentes`; ausente vale `conferido`);
  - a tabela `[cobertura]`, obrigatória fora da UHE;
  - os campos de cada tipo, pela tabela de [perfil-multitipo.md](../contracts/perfil-multitipo.md);
  - o CEG com os sete prefixos;
  - a potência das unidades como `potencia_unitaria_mw` ou `potencias_unidades_mw`, com a soma igual à potência instalada (tolerância de 0,1 MW);
  - o slug `carteiras`, que é reservado e não pode ser usado.
  - O perfil da São Domingos ganha só `tipo = "UHE"` e `modalidade = "TIPO II-A"`.
- **FR-010** (pastas): entram `data/catalogo/` (catálogo), `reports/carteiras/<nome>/` (carteiras) e `relatorios_referencia/<slug>/` (relatórios aprovados).
- **FR-014 e FR-015** (`copia-seguranca`):
  - a cópia passa a incluir `relatorios_referencia/` inteira, conferida pelos SHA-256 dos `referencia.json` antes da poda;
  - o `LEIA-ME.txt` lista as referências levadas.
- **FR-016** (conjuntos): os conjuntos vêm do registro (FR-049), filtrados pelo tipo e pela `[cobertura]` da usina. Na UHE sem `[cobertura]`, os dez de hoje, na mesma ordem, e mais nenhum.
- **FR-017** (período): o período passa a vir da série de referência do tipo (FR-054). Na hidrelétrica com EVT, continua o da EVT, como hoje.
- **FR-019** (recursos repetidos): a escolha do recurso repetido vale para todos os conjuntos, inclusive a EVT, os indicadores e a programação. O arquivo temporário do download leva o id do recurso (correção P1).
- **FR-031** (dicionários): a coleta obtém os dicionários dos conjuntos da usina. O registro `dicionarios.csv` lista só esses conjuntos. Na UHE sem `[cobertura]`, os dez de hoje, na mesma ordem.
- **FR-035** (comparação de textos): a mesma normalização (sem acento, sem espaços nas pontas, maiúsculas) vale na extração e nos pré-filtros. O filtro do Parquet usa o valor publicado e o normalizado (correção P3).
- **FR-036** (extração): num conjunto com conferência declarada, a coluna de conferência ausente torna o arquivo `FALHA`, com o motivo (correção P4).
- **FR-039** (valores numéricos): a vírgula decimal é aceita em todos os conjuntos, inclusive nos horários e na potência da ficha (correção P2).
- **FR-046** (auditoria): o CSV vazio da EVT fica `FALHA` com o motivo "arquivo vazio" (correção P5).
- **FR-047 e FR-048** (resultados e resumo):
  - a Coleta passa ao formato 2 (FR-050);
  - o `resumo` ganha `tipo`, `modalidade`, `serie_referencia`, `trechos`, `conjuntos_nao_aplicaveis` e `linhas_usina_sem_valor`.

## Requisitos novos

- **FR-049** (registro dos conjuntos): um registro único (`src/coleta/registro.py`) DEVE declarar, para cada conjunto do ONS:
  - pacote e pasta;
  - tipos de usina;
  - nível (usina, conjunto ou agregado);
  - resolução;
  - formatos preferidos;
  - identificador e conferências, montados do perfil;
  - colunas de valor e convenção de hora;
  - se pode ser série de referência.
  - A lista dos conjuntos do pipeline, usada pelos dicionários e pelas fontes, DEVE ser derivada dele.
- **FR-050** (formato 2): a Coleta DEVE gravar:
  - `datas_obtencao.csv`: por conjunto, `arquivos_registrados`, `publicacao_mais_recente` e `obtencao_mais_recente`, só com os arquivos do escopo da usina;
  - nas usinas com EVT, `dicionario_evt.json`, cópia do dicionário da EVT.
  - As etapas seguintes DEVEM ler esses arquivos, e nunca `data/raw/`. A etapa seguinte recusa a Coleta no formato 1 com o código 5.
- **FR-051** (catálogo de usinas): `python -m src usinas [--estado] [--tipo] [--modalidade] [--sem-portal] [--forcar-download]` DEVE:
  - sincronizar, sem `--sem-portal`:
    - a Modalidade das usinas, a Composição dos conjuntos e a Capacidade de geração;
    - o arquivo mais recente de cada conjunto de série;
    - a geração dos últimos 12 meses completos;
    - os dicionários desses conjuntos;
  - gravar `data/catalogo/` por inteiro, sem `.bak`: `usinas.csv`, `conjuntos.csv`, `cobertura.csv`, `planejamento.csv`, `programacao.csv`, `agregados.csv` e `catalogo.json` (data-model, seção 2);
  - listar as usinas do filtro, com uma coluna de cobertura por conjunto de série do tipo ([cli-usinas.md](../contracts/cli-usinas.md)).
  - O tipo vem do prefixo do CEG. A linha sem CEG é de conjunto.
- **FR-052** (cobertura): para cada usina e conjunto de série, o catálogo DEVE gravar o nível:
  - `proprio`;
  - `conjunto`, inclusive quando a usina tem linhas próprias sem valor;
  - `agregado`;
  - `ausente`.
  - Junto, o identificador usado, as linhas, as linhas sem valor, o arquivo e a data de publicação verificados.
- **FR-053** (rascunho do perfil): `python -m src perfil --ceg <CEG> [--slug <slug>]` DEVE ler só `data/catalogo/` e:
  - recusar, sem gravar: o CEG fora do catálogo (2); a usina Tipo III ou só com agregado (2); o catálogo ausente (5);
  - com perfil existente, só mostrar as diferenças (0 ou 6);
  - gravar o rascunho de [cli-perfil.md](../contracts/cli-perfil.md), com:
    - os identificadores e o subsistema;
    - a `[cobertura]` dos conjuntos implementados;
    - os códigos de programação ligados pelo id ONS ou pelo prefixo do conjunto (os demais ficam pendentes, com a lista do estado);
    - os membros do conjunto;
    - as unidades ativas, com a fonte;
    - os pendentes.
- **FR-054** (série de referência e trechos): a série de referência DEVE ser:
  - a EVT, na hidrelétrica com EVT;
  - a Geração por usina, pelo id ONS, na usina com geração própria;
  - a Geração por usina do conjunto, pelo id do conjunto, na usina em conjunto sem série própria.
  - A série de referência é varrida em todos os arquivos publicados. O período vai da primeira à última hora com valor; com cobertura `["proprio", "conjunto"]`, é a união das duas séries.
  - Fora da hidrelétrica com EVT, DEVEM ser gravados:
    - `trechos.csv`, com mudança de modalidade, de composição ou de código e a marca `mostrar`;
    - `geracao_complemento.parquet`;
    - `composicao_conjunto.csv` e `capacidade_ficha.csv`, quando há cobertura.

## Aplicabilidade por tipo (fase A)

`S` = coletado quando a `[cobertura]` o declara; `—` = não se aplica.

| Conjunto | UHE | PCH | CGH | UTE | UTN | EOL | UFV |
|---|---|---|---|---|---|---|---|
| Energia Vertida Turbinável | S | S | S | — | — | — | — |
| Indicadores e taxas (quatro conjuntos) | S | S | S | S | S | — | — |
| Programação diária | S | S | S | S | S | S | S |
| Disponibilidade por usina | S | S | S | S | S | — | — |
| Dados hidrológicos horários | S | S | S | — | — | — | — |
| Geração por usina (da usina ou do conjunto) | S | S | S | S | S | S | S |
| Modalidade das usinas | sempre | sempre | sempre | sempre | sempre | sempre | sempre |
| Composição dos conjuntos e Capacidade de geração | fora da UHE sem `[cobertura]` | sempre | sempre | sempre | sempre | sempre | sempre |

## Casos de borda (acréscimos)

- Coluna de conferência ausente num arquivo: `FALHA`, com o motivo.
- Código de programação sem ligação com a usina: o rascunho deixa pendente e lista os códigos do estado.
- Nomes e tipos instáveis no ONS: a identificação é só pelos códigos, e o tipo vem do CEG.

## Critérios de sucesso (acréscimos)

- **SC-015**: o catálogo lista 100 % das linhas do cadastro do ONS, com tipo, modalidade e cobertura.
- **SC-016**: o rascunho do perfil de uma usina com dado próprio sai em menos de 1 minuto.
- **SC-017**: com `data/raw/` vazio, as etapas 2 a 5 rodam a partir da Coleta e geram o mesmo relatório.

## Decisões do usuário (acréscimo)

| Data | Decisão |
|---|---|
| 09/10/2026 | Ampliação para todos os tipos de usina (spec 006, aprovada); correções P1 a P5 na fase A; implementação antes da fiscalização, com a versão de fiscalização congelada fora do projeto. |
