# Quickstart: validação da feature 007

**Feature**: [spec.md](spec.md) · **Contrato**: [relatorio-fontes-contract.md](contracts/relatorio-fontes-contract.md) · **Dados**: [data-model.md](data-model.md)

## Pré-requisitos

- venv ativo, PowerShell, na raiz do projeto.
- Bases já processadas em `data/processed/` (specs 001 a 006); nada é baixado.
- Cópia de referência do relatório anterior à feature (cópia datada da implementação), para a não regressão.

## 1. Testes (sem rede)

```powershell
python -m pytest tests -q
```

**Esperado**: suíte aprovada, incluindo `tests/test_fontes_relatorio.py`:
- cobertura do mapa;
- textos gerados dos resultados;
- conferência não feita quando a base falta;
- rodapé com N;
- toda tabela e figura com legenda no Markdown e no PDF.

## 2. Relatório

```powershell
python -m src.analyzer
```

**Esperado**:
- **PDF e Markdown**: cada figura e tabela seguida de "Fonte dos dados: …". O rodapé do PDF e o cabeçalho do Markdown citam "10 conjuntos".
- **Exemplos de conferência**:
  - figura 01 e indicadores anuais: geração e disponibilidade declarada conferidas, com "70.895 de 70.895 horas coincidentes (100,0%)";
  - figura 02 (EVT mensal): "Sem outra fonte para conferir: EVT";
  - decomposição TEIFa/TEIP: meses reproduzidos;
  - tabela DISPF × horas: 4 divergências na aba `ONS_DIVERGENCIAS`.
- **Planilha**: aba `FONTES` com uma linha para cada uma das outras 56 abas.

## 3. Não regressão (SC-004)

Comparar com a cópia de referência, ignorando as linhas "Fonte dos dados:" e "**Fontes**:":
- Markdown: seções e constatações idênticas;
- planilha: as 56 abas idênticas célula a célula; `FONTES` nova.

## 4. Conteúdo das legendas (SC-002 e SC-003)

- Conferir, figura a figura e tabela a tabela, se os conjuntos citados são os que alimentam cada uma (mapa da seção 3 do data-model contra o código).
- Conferir se os resultados citados batem com as abas `GER_CONFERENCIA`, `DISP_CONFERENCIA`, `HID_ALINHAMENTO` e `ONS_DIVERGENCIAS`.

## 5. Prazo (SC-006)

Relatório regenerado até 13/10/2026.
