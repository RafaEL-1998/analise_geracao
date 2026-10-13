# Contrato: resumo executivo da usina

**Spec**: [../spec.md](../spec.md) · **Data model**: [../data-model.md](../data-model.md)

Este contrato fixa o que o fiscal e o diretor recebem. Os testes da decisão R11 conferem cada item.

## 1. Como é gerado

Não há comando novo. O resumo sai sempre junto com o relatório completo.

| Comando (PowerShell) | Efeito no resumo |
|---|---|
| `python -m src completo --usina <slug>` | gera o relatório completo e o resumo |
| `python -m src relatorio --usina <slug>` | refaz só a etapa 5, a partir dos resultados gravados: relatório completo e resumo |
| `python -m src relatorio --usina <slug> --data-geracao "07/10/2026 08:53"` | mesma data no relatório e no resumo; PDFs iguais byte a byte entre execuções |
| `python -m src comparar --usina <slug> --referencia <pasta>` e `comparar --todas` | comparam também os dois arquivos do resumo |

| Código de saída da etapa 5 | Quando |
|---|---|
| 0 | relatório e resumo gerados e conferidos no disco |
| 1 | erro em qualquer saída, inclusive resumo com mais de duas páginas mesmo sem a evolução anual; as saídas anteriores ficam como estavam |
| 5 | Análises ausentes, com falha ou em formato antigo; nada é gravado, e a mensagem indica a etapa a executar |

## 2. Arquivos

| Arquivo | Formato |
|---|---|
| `reports/<slug>/resumo_executivo.pdf` | A4 retrato, no máximo duas páginas, sem imagem |
| `reports/<slug>/resumo_executivo.md` | Markdown com o mesmo conteúdo, na mesma ordem |

## 3. Documento

Blocos em ordem fixa. Um bloco sem base para a usina é omitido.

### 3.1 Cabeçalho

```text
# <Nome> — resumo executivo
<período> (<n> registros horários) · Gerado em <dd/mm/aaaa HH:MM>
<tipo> · <UF> · <modalidade> · <potência> MW
Agente(s): <o mesmo texto da linha "Agente" da capa do relatório completo>
Resume o relatório completo "<título da capa do relatório completo>", de <n> páginas, gerado na mesma data.
**Termos.** <sigla>: <explicação>; <sigla>: <explicação>; …
```

### 3.2 Indicadores-chave

```text
## Indicadores-chave
| Indicador | Valor | Detalhe |   ← linhas iguais às dos indicadores principais da capa
Seção de origem: capa do relatório completo.
```

### 3.3 Evolução anual

```text
## Evolução anual
| <até seis colunas da tabela anual do relatório, com os mesmos valores> |
* Ano parcial. Colunas e definições na seção <n> do relatório completo.
```

- Omitida quando o resumo passa de duas páginas. No lugar, uma linha: "A evolução anual está na seção <n> do relatório completo."

### 3.4 Sobre os dados

```text
## Sobre os dados
<Dados: cobertura, anos parciais, registros sinalizados.>
<Conferências: uma frase curta por conferência. Limites: o que os dados abertos não informam.>
<Fontes: conjuntos do ONS por identificador da usina e data de obtenção.>
```

- No máximo 250 palavras (FR-013 com o ajuste A2).
- Substitui a legenda de fonte das tabelas (constituição 3.1.0, VII).

### 3.5 Conclusão (último bloco; revisão 1)

```text
## Conclusão
As seções e as notas metodológicas citadas são as do relatório completo.
<frase de abertura do relatório>
### Pontos de atenção
- <item igual ao do relatório>
### Possíveis problemas
- …
### A confirmar com o agente
- …
### A verificar em campo
- …
```

- As listas, os itens, a ordem e o texto são os da seção de conclusão do relatório completo da mesma execução, caractere por caractere.
- Lista sem itens não aparece. Sem nenhum item, o bloco traz só o aviso e a frase do relatório para esse caso.

## 4. Regras do texto

| Regra | Requisito |
|---|---|
| Todo número aparece igual no relatório completo, salvo o número de páginas do relatório no cabeçalho | FR-014 |
| Números no padrão do relatório: milhar com ponto, decimal com vírgula, "dd/mm/aaaa HHh", "mmm/aaaa" e "–" | FR-018 |
| Nenhum termo de parecer fora da conclusão, que é copiada igual | constituição II |
| Texto em 10 pt e tabelas em 9 pt, no PDF | FR-004 |
| No máximo duas tabelas e 1.000 palavras fora delas | FR-005, SC-004 |
