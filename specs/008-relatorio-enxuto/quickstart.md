# Quickstart: validação da feature 008

**Feature**: [spec.md](spec.md) · **Contrato**: [estrutura-relatorio-contract.md](contracts/estrutura-relatorio-contract.md) · **Dados**: [data-model.md](data-model.md)

## Pré-requisitos

- venv ativo, PowerShell, na raiz do projeto.
- Bases já processadas em `data/processed/`; nada é baixado.
- Cópia de referência do relatório anterior (cópia datada da implementação).

## 1. Testes (sem rede)

```powershell
python -m pytest tests -q
```

**Esperado**: suíte aprovada, incluindo `tests/test_estrutura_relatorio.py`:
- todos os títulos de constatação mapeados;
- cada constatação uma vez no Markdown e no PDF;
- PDF e Markdown com as mesmas seções, na mesma ordem;
- sumário do PDF com as páginas certas;
- rodapé só com a numeração.

## 2. Relatório

```powershell
python -m src.analyzer
```

**Esperado**:
- **Capa** (página 1 do PDF): identificação, parâmetros, indicadores, "Gerado em …" e sumário, sem texto de constatação.
- **Seções**: cada uma começa com as suas constatações (título em negrito), seguidas das tabelas e figuras com as legendas.
- **Rodapé**: só "Página X de Y".
- **Markdown**: mesma ordem e mesmos títulos do PDF, figuras no corpo, sem "**Fontes**:" e sem a seção "Figuras".
- **PDF**: com menos páginas que as 31 do relatório anterior.

## 3. Não regressão (SC-005)

Contra a cópia de referência, conteúdo a conteúdo (research R8):
- toda tabela, constatação e nota do relatório anterior presente no novo, exceto a parte de fonte das notas da FR-013;
- planilha idêntica (57 abas);
- figuras com o mesmo SHA-256.

## 4. Prazo (SC-007)

Relatório regenerado até 13/10/2026.
