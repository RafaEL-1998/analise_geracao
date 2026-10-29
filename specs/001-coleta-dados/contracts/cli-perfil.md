# Contract: Linha de comando — rascunho do perfil (`perfil`)

**Spec**: [spec.md](../spec.md) (FR-053; perfil nas FR-006 a FR-009 e FR-056) · **Data model**: [seções 2.5 e 2.6](../data-model.md) · **Perfil**: [perfil-usina.md](perfil-usina.md) · **Plano**: decisões técnicas D23 e D33

Os códigos de saída, o `--log-level` e o formato do log são os do [contrato da Coleta](cli-coleta.md).

## Sintaxe

```text
python -m src perfil --ceg <CEG> [--slug <slug>] [--log-level <nível>]
```

- Lê só `data/catalogo/`. Não acessa o portal, não lê os brutos e não executa nenhuma etapa.
- Nunca sobrescreve um perfil.

| Opção | Efeito |
|---|---|
| `--ceg <CEG>` | obrigatório; CEG da usina, como no catálogo (comparado sem acento, sem espaços nas pontas e sem diferença entre maiúsculas e minúsculas) |
| `--slug <slug>` | nome da pasta em `usinas/`; sem ele, vem do nome da usina no cadastro, sem acento, em minúsculas e com `_` no lugar do que não é letra ou algarismo. Letras minúsculas, algarismos e `_`; `carteiras` é reservado |

## O que faz, na ordem

1. Slug informado fora do padrão, ou `carteiras`: código 2.
2. Catálogo ausente ou em formato antigo (`catalogo.json` sem o `versao_formato` atual): código 5, sem gravar nada.
3. CEG fora do catálogo: código 2.
4. Tipo pelo CEG fora dos sete (`conjunto` ou `outro`): código 2.
5. Usina Tipo III, ou só com cobertura agregada ou ausente em todos os conjuntos de série: código 2, sem gravar nada, com a mensagem da tabela abaixo. Também a usina sem a série de referência da Coleta (spec, FR-054) pela cobertura do catálogo, com a mesma regra que a Coleta aplica ao perfil: nem a EVT, nem a Geração por usina própria ou do conjunto, nem, na EOL e na UFV, a restrição com detalhe da usina (como a usina que o ONS só programa).
6. Slug derivado do nome fora do padrão: código 2, pedindo `--slug`.
7. Perfil existente (`usinas/<slug>/perfil.toml`, ou outro perfil com o mesmo CEG): nada é gravado. Mostra as diferenças entre o perfil e o catálogo, uma por linha:
   - sempre, `usina.tipo`, `usina.modalidade`, `usina.estado` e `identificacao.ceg`;
   - os identificadores que o perfil traz (`id_ons`, `id_conjunto`, `cod_usina`, `nome_ons`, `id_reservatorio`);
   - os códigos de programação (os do catálogo que faltam no perfil aparecem como diferença);
   - nas térmicas, `usina.subsistema` e os códigos de planejamento;
   - a `[cobertura]` em cada conjunto do catálogo, inclusive as chaves que o perfil não tem; numa UHE sem a tabela, valem os conjuntos da UHE (`CHAVES_SEM_COBERTURA`) com `proprio`.

   Sai com 6, ou com 0 sem diferença; perfil existente ilegível, código 1.
8. Grava `usinas/<slug>/perfil.toml` com `situacao = "rascunho"` ([perfil-usina.md](perfil-usina.md), seção "Rascunho"), com:
   - os identificadores (CEG, id ONS quando há e id do conjunto), o subsistema e a `[cobertura]` do catálogo, só com os conjuntos de série do registro; nas hidrelétricas com linha nos Reservatórios, também `cod_usina`, `nome_ons` e `id_reservatorio`;
   - `codigos_programacao`: todos os códigos de `programacao.csv` ligados à usina (o código igual ao id ONS) ou ao conjunto (os que começam pelo id dele sem `CJU_`), de todo o período, com o primeiro e o último dia de cada um num comentário. Sem nenhum ligado, o campo fica pendente, com a lista dos códigos do estado para o fiscal escolher;
   - nas térmicas, os códigos de planejamento de `planejamento.csv`, em `[[identificacao.planejamento]]`;
   - os membros do conjunto vigente, em `[[identificacao.membros]]`;
   - as unidades ativas da Capacidade de geração (potência instalada, unidades, potência unitária ou a lista e, nas térmicas, o combustível) e o ano de início pela primeira unidade ativa.

   Confere a gravação no disco e que o arquivo é TOML válido, e sai com 0.

## Códigos de saída

| Código | Situação |
|---|---|
| 0 | rascunho gravado, ou perfil existente igual ao catálogo |
| 1 | erro de gravação, perfil existente ilegível, interrupção pelo usuário ou erro inesperado |
| 2 | opção inválida, inclusive o slug; CEG fora do catálogo; tipo fora dos sete; usina Tipo III ou só com agregado ou sem dados no ONS; usina sem série de referência |
| 5 | catálogo ainda não montado ou em formato antigo |
| 6 | perfil existente com diferenças em relação ao catálogo (nada gravado) |

## Mensagens obrigatórias

| Situação | Onde | Mensagem |
|---|---|---|
| Rascunho gravado | log, `INFO` | `Rascunho do perfil gravado em usinas/<slug>/perfil.toml: <N> campos preenchidos com dados do ONS e <P> pendentes. Confira, complete com a fonte e troque situacao para "conferido".` |
| Catálogo ausente (5) | log, `ERROR` | `O catálogo de usinas não foi montado. Execute antes: python -m src usinas` |
| CEG fora do catálogo (2) | log, `ERROR` | `CEG <CEG> fora do catálogo de usinas (data/catalogo/usinas.csv).` |
| Tipo fora dos sete (2) | log, `ERROR` | `A usina <nome> (<CEG>) tem o tipo "<tipo>" pelo CEG, fora dos tipos atendidos (UHE, PCH, CGH, UTE, UTN, EOL, UFV).` |
| Só agregado (2) | log, `ERROR` | `O ONS publica a usina <nome> (<CEG>) só em agregado (<modalidade>), sem dados próprios nem de conjunto. Ela aparece no panorama da carteira: python -m src carteira --estado <UF>` |
| Sem série de referência (2) | log, `ERROR` | `O ONS não publica a série de referência da usina <nome> (<CEG>): nem a Energia Vertida Turbinável nem a Geração por usina, da usina ou do conjunto[, nem a restrição com detalhe da usina]. Dos conjuntos de série, o catálogo encontra só: <chave> = "<nível>"; …. Sem a série de referência, a usina não tem relatório individual.` (o trecho entre colchetes só na EOL e na UFV) |
| Slug inválido (2) | log, `ERROR` | `Slug inválido: '<slug>' (letras minúsculas, algarismos e _; "carteiras" é reservado).` ou `Slug derivado do nome inválido: '<slug>'; informe --slug.` |
| Perfil existente com diferenças (6) | saída padrão | `O perfil usinas/<slug>/perfil.toml já existe e não foi alterado. Diferenças em relação ao catálogo:`, seguido de uma linha `- <campo>: perfil <valor>; catálogo <valor>` por diferença (`(ausente)` quando o valor falta) |
| Perfil existente sem diferença (0) | saída padrão | `O perfil usinas/<slug>/perfil.toml já existe e não foi alterado; sem diferença em relação ao catálogo.` |

## Depois do rascunho

- Enquanto `situacao = "rascunho"`, toda etapa recusa o perfil com o código 4 e lista os `pendentes` e os demais problemas.
- O fiscal confere os identificadores e a `[cobertura]`, completa os pendentes com a fonte, esvazia `pendentes` e troca `situacao` para `"conferido"`.
- Quando um conjunto novo entra no registro, o `perfil` de novo mostra as chaves novas da `[cobertura]` como diferença (código 6), e o fiscal as acrescenta.

## Exemplos

```powershell
# Rascunho da UTE William Arjona
python -m src perfil --ceg UTE.GN.MS.027075-0.01 --slug william_arjona

# De novo: o perfil não muda; só as diferenças aparecem
python -m src perfil --ceg UTE.GN.MS.027075-0.01 --slug william_arjona
$LASTEXITCODE   # 0 sem diferença; 6 com diferença
```
