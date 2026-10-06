# Data Model: Conformidade com a Constituição 1.1.0

**Feature**: `005-conformidade-constituicao` | **Date**: 2026-10-05

## VersaoPreservada (manifesto `_manifesto_ons.json`, entrada de cada arquivo)

```json
"ENERGIA_VERTIDA_TURBINAVEL_2026_08.csv": {
  "url": "...", "ultima_modificacao": "2026-09-30T15:06:00", "tamanho_bytes": 16867890, "...": "...",
  "versoes_anteriores": [
    {
      "arquivo_preservado": "_versoes_anteriores/ENERGIA_VERTIDA_TURBINAVEL_2026_08__pub_20260901T120000.csv",
      "ultima_modificacao": "2026-09-01T12:00:00",
      "tamanho_bytes": 16850112,
      "sha256": "…",
      "arquivado_em_utc": "2026-10-05 15:00:00"
    }
  ]
}
```

Regras:
- Criada só quando a cópia local e o arquivo baixado têm SHA-256 diferentes.
- A lista só cresce; reescritas da entrada mantêm as versões já registradas.
- O arquivo preservado nunca é lido pela extração (subpasta não percorrida).

## AuditoriaArquivo (`relatorio_auditoria_varredura.csv`)

Campo novo, ao final: `registros_formato_irregular` (inteiro ≥ 0) — linhas não vazias com número de campos diferente do cabeçalho; não extraídas.

## LOGGERS_PIPELINE (`src/logger.py`)

`main`, `collector`, `filter`, `consolidator`, `indicadores_ons`, `programacao_ons`, `processor`, `validator`, `analyzer`, `uhe_sao_domingos.pdf_generator`. `configurar_nivel_log(nivel)` aplica o nível a todos.

## Figuras (inalteradas no nome)

`NOMES_FIGURAS` em `src/analyzer.py`: `01_serie_temporal_disponibilidade_geracao_evt.png`, `02_evt_mensal.png`, `03_perfil_horario_geracao_evt.png`, `04_disponibilidade_geracao_anual.png`, `05_vazoes_defluentes_anuais.png` — 300 DPI, produzidas com seaborn.
