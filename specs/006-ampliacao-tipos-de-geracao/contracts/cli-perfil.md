# Contract: Linha de comando — rascunho do perfil (`perfil`)

**Spec**: [spec.md](../spec.md) (FR-006 a FR-009) · **Data model**: [seções 2.5 e 3](../data-model.md) · **Perfil**: [perfil-multitipo.md](perfil-multitipo.md) · **Research**: R5

## Sintaxe

```text
python -m src perfil --ceg <CEG> [--slug <slug>] [--log-level <nível>]
```

- Lê só `data/catalogo/`. Não acessa o portal, não lê os brutos e não executa nenhuma etapa.
- Nunca sobrescreve um perfil (FR-007).

| Opção | Efeito |
|---|---|
| `--ceg <CEG>` | obrigatório; CEG da usina, como no catálogo |
| `--slug <slug>` | nome da pasta em `usinas/`; sem ele, vem do nome da usina sem acento, em minúsculas e com `_`. Letras minúsculas, algarismos e `_`; `carteiras` é reservado |

## O que faz, na ordem

1. Catálogo ausente ou em formato antigo: código 5, sem gravar nada.
2. CEG fora do catálogo: código 2.
3. Usina Tipo III, ou só com cobertura agregada ou ausente em todos os conjuntos de série (FR-009): código 2, sem gravar nada, com a mensagem da tabela abaixo.
4. Perfil existente (`usinas/<slug>/perfil.toml`, ou outro perfil com o mesmo CEG): nada é gravado. Mostra as diferenças entre o perfil e o catálogo (campo, valor no perfil, valor no catálogo), inclusive as chaves novas de `[cobertura]` de uma fase posterior. Sai com 6, ou com 0 sem diferença.
5. Grava `usinas/<slug>/perfil.toml` com `situacao = "rascunho"` ([perfil-multitipo.md](perfil-multitipo.md), seção "Rascunho"), com:
   - os identificadores, o subsistema e a `[cobertura]` do catálogo, só com os conjuntos já implementados;
   - os códigos de programação de `programacao.csv`: o código igual ao id ONS, ou os que começam pelo id do conjunto sem `CJU_`. Sem nenhum dos dois, o campo fica pendente, com a lista dos códigos do estado para o fiscal escolher;
   - os códigos de planejamento de `planejamento.csv` (a partir da fase B);
   - os membros do conjunto vigente;
   - as unidades ativas da Capacidade de geração.
   Confere a gravação no disco e sai com 0.

## Códigos de saída

| Código | Situação |
|---|---|
| 0 | rascunho gravado, ou perfil existente igual ao catálogo |
| 1 | erro de gravação ou inesperado |
| 2 | opção inválida; CEG fora do catálogo; usina Tipo III ou só com agregado ou sem dados no ONS |
| 5 | catálogo ainda não montado ou em formato antigo |
| 6 | perfil existente com diferenças em relação ao catálogo (nada gravado) |

## Mensagens obrigatórias

| Situação | Onde | Mensagem |
|---|---|---|
| Rascunho gravado | log, `INFO` | `Rascunho do perfil gravado em usinas/<slug>/perfil.toml: <N> campos preenchidos com dados do ONS e <P> pendentes. Confira, complete com a fonte e troque situacao para "conferido".` |
| Catálogo ausente (5) | log, `ERROR` | `O catálogo de usinas não foi montado. Execute antes: python -m src usinas` |
| Só agregado (2) | log, `ERROR` | `O ONS publica a usina <nome> (<CEG>) só em agregado (<modalidade>), sem dados próprios nem de conjunto. Ela aparece no panorama da carteira: python -m src carteira --estado <UF>` |
| Perfil existente (6) | saída padrão | `O perfil usinas/<slug>/perfil.toml já existe e não foi alterado. Diferenças em relação ao catálogo:`, seguido de uma linha `- <campo>: perfil <valor>; catálogo <valor>` por diferença |

## Depois do rascunho

- Enquanto `situacao = "rascunho"`, toda etapa recusa o perfil com o código 4 e lista os `pendentes` e os demais problemas.
- O fiscal confere os identificadores e a `[cobertura]`, completa os pendentes com a fonte, esvazia `pendentes` e troca `situacao` para `"conferido"`.

## Exemplos

```powershell
# Rascunho da UTE William Arjona
python -m src perfil --ceg UTE.GN.MS.027075-0.01 --slug william_arjona

# De novo: o perfil não muda; só as diferenças aparecem
python -m src perfil --ceg UTE.GN.MS.027075-0.01 --slug william_arjona
$LASTEXITCODE   # 0 sem diferença; 6 com diferença
```
