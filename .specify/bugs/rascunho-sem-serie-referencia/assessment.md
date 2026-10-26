# Bug Assessment: rascunho do perfil aceito para usina sem série de referência

- **Slug**: rascunho-sem-serie-referencia
- **Created**: 2026-10-26
- **Source**: pasted text (achado 4 de `propostas/2026-10-26-homologacao-lote-1.md`)
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

> Nove usinas (UTE Amandina II, Costa Rica, Fibria MS, Fibria MS-II, Iaco Agrícola, Suzano RRP1, Bracell; PCH São Lourenço-MT e Cabeça de Boi) tiveram o rascunho gravado pelo comando `perfil` e a Coleta recusada: "Coleta recusada: a usina '…' não tem série de referência: nem a Energia Vertida Turbinável nem a Geração por usina (da usina ou do conjunto) na [cobertura]".

## Symptom

O comando `perfil` recusa (código 2) a usina só em agregado ou ausente, mas grava o rascunho da usina que só tem dados próprios ou de conjunto na Programação diária (ou noutro conjunto que não é série de referência); o fiscal só descobre na Coleta que não há relatório possível. O esperado é a recusa no rascunho, com a explicação.

## Reproduction

1. `python -m src perfil --ceg UTE.FL.MS.049647-2.01 --slug ute_suzano_rrp1`: código 0, rascunho gravado; a `[cobertura]` traz `programacao = "proprio"` e `geracao = "ausente"`.
2. Aceitar o rascunho e rodar `python -m src completo --usina ute_suzano_rrp1`: Coleta recusada (código 1), sem série de referência.

## Suspected Code Paths

- `src/coleta/perfil_rascunho.py:178-194` (`_resolver_usina`) — recusa só quando `cobertura_resumo` é `agregado`, `ausente` ou vazio.
- `src/coleta/catalogo_usinas.py:728-733` — `cobertura_resumo` é o melhor nível entre todos os conjuntos do tipo, inclusive a Programação diária, os indicadores, o despacho e o CVU.
- `src/coleta/serie_referencia.py:63-77` (`escolher`) — a regra da série de referência da Coleta: EVT própria, ou Geração por usina própria ou do conjunto, ou, na eólica e na solar, a restrição com detalhe da usina.

## Root Cause Hypothesis

O rascunho usa o resumo da cobertura (qualquer conjunto) como sinal de "há relatório individual", enquanto a Coleta exige a série de referência. Os dois critérios divergem nas usinas que o ONS programa mas não publica na Geração por usina (várias UTE a biomassa e a cavaco de MS, Tipo II-B e II-C). Confiança: alta.

## Proposed Remediation

**Preferred**: em `_resolver_usina`, conferir a série de referência pela tabela `cobertura` do catálogo, com a mesma regra de `serie_referencia.escolher` (EVT `proprio`; ou Geração por usina `proprio` ou `conjunto`; ou, na EOL e na UFV, restrição com detalhe `proprio`), e recusar com o código 2 e uma mensagem que diga o que o ONS publica da usina (por exemplo, "só a Programação diária") e que ela não tem relatório individual. A regra fica numa função única, usada pelo rascunho e pela Coleta, para não divergir de novo.

**Alternatives**:
- Mudar o `cobertura_resumo` para considerar só as séries de referência: corrige também os números do catálogo e os motivos da carteira, mas muda o significado de uma coluna que a carteira já mostra (motivo "sem resultado"); pode ser uma coluna nova (`serie_referencia`) em vez de mudar a atual.

**Files likely to change**:
- `src/coleta/perfil_rascunho.py`, `src/coleta/serie_referencia.py` (função compartilhada)
- opcional: `src/coleta/catalogo_usinas.py` (coluna nova) e `src/relatorio/carteira.py` (motivo)
- `specs/001-coleta-dados/spec.md` e `contracts/cli-perfil.md` (código 2 também sem série de referência)
- `tests/coleta/test_perfil_rascunho.py`

**Tests to add or update**:
- Usina do catálogo fictício só com a programação: código 2, sem rascunho, com a mensagem.
- Usina com Geração por usina do conjunto e sem série própria: rascunho gravado (como a Bandeirante).
- EOL/UFV em conjunto com a restrição com detalhe própria: rascunho gravado (como a Seriemas 1).

## Risks & Considerations

- A carteira de MS hoje conta essas usinas como "sem perfil"; com a coluna nova, passariam a "sem série de referência". Mudança de texto na carteira, que não é referência protegida.
- Os números de cobertura citados ao usuário (1.911 usinas "próprias" no Brasil) incluem usinas sem série de referência; recontar depois da correção.

## Open Questions

- Respondida pelo usuário em 26/10/2026 ("yes, I'll go with your recommendation"): só a recusa no rascunho agora; a coluna `serie_referencia` no catálogo fica para a melhoria 5.
