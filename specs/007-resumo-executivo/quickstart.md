# Quickstart: Validação do Resumo Executivo

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Contrato**: [contracts/resumo-executivo.md](contracts/resumo-executivo.md)

Roteiro para conferir que o resumo funciona e que o relatório aprovado da São Domingos não mudou. Os comandos são de PowerShell, na raiz do projeto, com o `venv` ativo.

## Pré-requisitos

- Portão do fim da fase A da 006 aprovado (T074), com `comparar --todas --coleta` em código 0 (decisão R13).
- A referência atual da São Domingos commitada, porque o `referencia` recusa substituir uma referência não commitada (decisão R12).
- Ajustes A1 e A2 da spec aprovados pelo usuário ([plan.md](plan.md), "Ajustes na spec").
- Cópia de segurança antes do código, ficando no máximo duas:

```powershell
python -m src copia-seguranca --motivo antes_resumo_executivo
```

## 1. Suíte sem rede

```powershell
$env:HTTP_PROXY = "http://127.0.0.1:9"; $env:HTTPS_PROXY = "http://127.0.0.1:9"; $env:PYTHONIOENCODING = "utf-8"
python -m pytest tests -q -p no:cacheprovider
```

**Esperado**: suíte aprovada, com os testes novos do resumo (decisão R11) e os invariantes da 006 sem mudança.

## 2. Resumo da São Domingos

```powershell
python -m src relatorio --usina sao_domingos --data-geracao "07/10/2026 08:53"
$LASTEXITCODE
Get-Content reports/sao_domingos/etapa.json -Encoding utf8 | Select-String "resumo_executivo" -Context 0,4
```

**Esperado**:
- código 0;
- `reports/sao_domingos/resumo_executivo.pdf` e `resumo_executivo.md` gravados;
- no `etapa.json`, `resumo_executivo` com `paginas` igual a 2, `evolucao_anual` verdadeiro e `palavras` até 1.000.

## 3. Conclusão igual à do relatório completo

```powershell
$r = Get-Content reports/sao_domingos/relatorio_analise_estatistica.md -Raw -Encoding utf8
$s = Get-Content reports/sao_domingos/resumo_executivo.md -Raw -Encoding utf8
$conclusao = [regex]::Match($r, "(?s)## \d+\. Conclusão\r?\n\r?\n(.*?)\r?\n## ").Groups[1].Value.Trim()
$s.Contains($conclusao)
```

**Esperado**: `True` (SC-002).

## 4. Leitura do resumo

Abrir `reports/sao_domingos/resumo_executivo.pdf` e conferir:
- duas páginas A4 em retrato, sem figura, com no máximo duas tabelas;
- blocos na ordem: cabeçalho com a linha de termos, indicadores-chave, evolução anual, "Sobre os dados" e conclusão;
- cabeçalho com os dois agentes e os seus períodos e o número de páginas do relatório completo;
- evolução anual com 2018* a 2026* e os mesmos valores da seção 2 do relatório completo;
- "Sobre os dados" com as conferências e as fontes, no máximo 250 palavras.

Fazer as cinco perguntas da SC-005 a um leitor que não leu o relatório completo.

## 5. Guarda do relatório aprovado

```powershell
python -m src comparar --todas --coleta
$LASTEXITCODE
```

**Esperado** (decisão R12):
- código 6, com exatamente duas diferenças, ambas "só na pasta atual": `resumo_executivo.pdf` e `resumo_executivo.md`;
- nenhuma diferença no relatório completo, na planilha, no CSV e nas figuras (SC-006).

## 6. Aprovação do resumo como referência

Só com a aprovação do usuário (princípio IX):

```powershell
python -m src referencia --usina sao_domingos --data-geracao "07/10/2026 08:53" --aprovado-em "<data da aprovação>"
python -m src comparar --todas --coleta
$LASTEXITCODE
```

**Esperado**: `referencia.json` com os dois arquivos do resumo; depois, `comparar` com código 0.

## 7. Outros tipos de usina

Depois da 006 de cada tipo, gerar o relatório das usinas fictícias pela suíte (`tests/integracao/test_usinas_ficticias.py`) e conferir no teste:
- resumo com no máximo duas páginas;
- indicadores e colunas anuais do caminho da usina;
- números de conjunto identificados como tais.
