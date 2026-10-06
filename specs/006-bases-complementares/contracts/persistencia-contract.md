# Contrato: `src/persistencia.py` (gravação com cópia de segurança)

**Feature**: `006-bases-complementares` (US1) | **Date**: 2026-10-05

Todo arquivo gravado em `data/processed/` DEVE passar por uma destas funções. Os relatórios em `reports/` e os arquivos de controle (manifestos, dicionários) não as usam (constituição 1.2.0, Requisito Técnico 3).

## Funções públicas

| Função | Uso | Comparação "idêntico" | Conferência física |
|---|---|---|---|
| `gravar_csv(df, destino, **opcoes_to_csv) -> ResultadoGravacao` | tabelas pandas (`sep=";"`, UTF-8, datas ISO por padrão) | bytes | releitura: linhas e colunas iguais às do `df` |
| `gravar_linhas_csv(cabecalho, linhas, destino, delimitador=";") -> ResultadoGravacao` | escrita linha a linha (consolidação e auditoria da varredura) | bytes | contagem de linhas = registros + 1 e cabeçalho igual |
| `gravar_parquet(df, destino) -> ResultadoGravacao` | base tratada | bytes (pyarrow é determinístico) | metadados: `num_rows`, `num_columns` |
| `gravar_planilha(abas, destino, formatar=None) -> ResultadoGravacao` | `abas`: dicionário ordenado `{nome: DataFrame}`; `formatar(writer)` opcional (larguras, painéis congelados) | propriedade `assinatura_dados` | abas na ordem; dimensões de cada aba; assinatura gravada |
| `gravar_texto(texto, destino) -> ResultadoGravacao` | Markdown (relatório de validação física) | bytes | releitura igual ao texto |

`ResultadoGravacao` ∈ {`NOVO`, `ALTERADO`, `INALTERADO`}; ver [data-model.md](../data-model.md).

## Garantias

1. **Ordem**: o temporário `<nome>.tmp` é gravado e conferido → comparado com o atual → o atual é copiado para `<nome>.bak` → troca atômica → conferência do SHA-256 do destino.
2. **Conteúdo idêntico**: não regrava o destino nem toca no `.bak`.
3. **Falha antes da troca**: o destino fica intacto e o temporário é removido.
4. **Falha depois da troca**: o destino é restaurado a partir do `.bak` (ou apagado, se era novo).
5. **Sinalização de falhas**: toda falha levanta `ErroPersistencia(destino, motivo)` e gera log de erro com o nome do arquivo.
6. **Registro de sucesso**: todo sucesso gera log INFO com o resultado e o número de registros.
7. **Pastas**: a função cria a pasta do destino, se necessário. Não grava nada fora da pasta do destino.
8. **Leitores**: nenhum leitor do pipeline lê `*.bak` ou `*.tmp` (FR-011). Os leitores usam nomes explícitos ou `glob` sem recursão por extensão exata.

## Testes de contrato (sem rede, em pasta temporária)

1. Gravar sem versão anterior → `NOVO`, sem `.bak`.
2. Gravar com conteúdo diferente → `ALTERADO`; o `.bak` é igual à versão anterior.
3. Gravar o mesmo conteúdo → `INALTERADO`; destino e `.bak` sem alteração (hash e data de modificação).
4. Simular falha na troca e na conferência → destino idêntico ao anterior, temporário removido e `ErroPersistencia` levantado.
5. Planilha regravada com os mesmos dados → `INALTERADO`, apesar de os bytes do pacote mudarem.
6. Leitores (`carregar_*_processada`, `periodo_base_evt`) ignoram `.bak` e `.tmp` na pasta.
