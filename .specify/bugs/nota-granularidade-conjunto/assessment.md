# Bug Assessment: nota de granularidade errada na usina de conjunto com série própria

- **Slug**: nota-granularidade-conjunto
- **Created**: 2026-10-26
- **Source**: pasted text (achado 5 de `propostas/2026-10-26-homologacao-lote-1.md`)
- **Verdict**: valid
- **Severity**: medium

## Report (verbatim or summarized)

> Nos relatórios da PCH Eng. E. J. Dreher, PCH Eng. Henrique Kotzian, UTE Eldorado e UTE Santa Luzia I, as notas dizem "Granularidade: o ONS publica a geração do conjunto Conj. Boca do Monte (), e não a da usina isolada", com o identificador vazio, enquanto a série de referência do mesmo relatório é a Geração por usina da própria usina (por exemplo, id ONS RSUHED).

## Symptom

Quando só outro conjunto (a Programação diária) está no nível do conjunto e a geração é da usina, o relatório afirma que a geração é publicada só para o conjunto, com o identificador vazio. É uma afirmação falsa num documento de fiscalização; nenhum número muda.

## Reproduction

1. Perfil de uma usina membro de um conjunto, com Geração por usina própria e a Programação diária do conjunto (por exemplo, `ute_eldorado`: geração MSELDR, programação MSCRBR-9561 e MSCRBR-9582).
2. `python -m src completo --usina ute_eldorado`.
3. Nas notas metodológicas, o item "Granularidade: o ONS publica a geração do conjunto … (), e não a da usina isolada".

## Suspected Code Paths

- `src/relatorio/comum.py:111-113` (`com_conjunto`) — verdadeiro quando a base ou qualquer conjunto (`res.niveis`) está no nível do conjunto.
- `src/relatorio/comum.py` (`notas`, ramo `elif com_conjunto(res)`) — escreve que "o ONS publica a geração do conjunto" e usa `_g(res).get("identificador_conjunto", "")`, que é vazio quando a geração é da usina.

## Root Cause Hypothesis

A nota foi escrita para a usina em conjunto sem série própria (PCH Bandeirante), em que a geração é do conjunto; o teste `com_conjunto` é mais largo (qualquer conjunto no nível do conjunto) e passou a valer também para a usina com geração própria e programação do conjunto, que nenhuma referência tinha. Confiança: alta.

## Proposed Remediation

**Preferred**: separar os dois casos na nota de granularidade:
- geração (base) no nível do conjunto: o texto de hoje, com o identificador do conjunto da geração;
- geração da usina e algum outro conjunto no nível do conjunto: "o ONS publica <a Programação diária> do conjunto <nome> (<identificador do conjunto naquele conjunto>), e não a da usina; esses números são identificados como do conjunto e não são divididos entre as usinas", com os nomes e identificadores tirados de `res.niveis`.

**Files likely to change**:
- `src/relatorio/comum.py`
- `specs/005-geracao-relatorio/spec.md` (texto da nota de granularidade, se estiver fixado)
- `tests/relatorio/` e uma usina fictícia nesse caso (UTE ou PCH com geração própria e programação do conjunto)

**Tests to add or update**:
- Usina com geração própria e programação do conjunto: a nota cita a Programação diária e o identificador do conjunto; não diz que a geração é do conjunto; não tem "()".
- PCH em conjunto sem série própria: a nota de hoje (a referência da Bandeirante não muda).

## Risks & Considerations

- Princípio IX: Bandeirante (geração do conjunto) e Seriemas 1 (outro ramo da nota) não mudam; conferir com `comparar --todas`.
- Conferir também o bloco "Sobre os dados" do resumo executivo, se repetir a granularidade.

## Open Questions

- Nenhuma.
