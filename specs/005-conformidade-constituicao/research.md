# Research: Conformidade com a Constituição 1.1.0

**Feature**: `005-conformidade-constituicao` | **Date**: 2026-10-05

## R1. Onde e quando preservar a versão anterior (US1)
- **Decision**: em `download_resource` (`src/collector.py`), depois que a nova versão foi baixada com sucesso para o arquivo temporário e antes de substituir a cópia local: se a cópia local existe e sua soma de verificação (SHA-256) difere da do arquivo baixado, ela é movida para `<pasta>/_versoes_anteriores/<nome>__pub_<data de publicação anterior><extensão>`; se as somas forem iguais, nada é preservado.
- **Rationale**: é o único ponto em que o coletor sobrescreve arquivos (linha `temp_path.replace(local_path)`), comum aos três conjuntos (EVT, indicadores e programação usam a mesma função). Mover só depois do download bem-sucedido garante que uma falha de rede não deixe a pasta sem versão corrente. A comparação por conteúdo evita cópias quando o ONS só republica metadados (caso visto em 30/09/2026, mesmo tamanho).
- **Alternatives considered**: comparar só tamanho (insuficiente: republicação com mesmo tamanho); guardar todas as versões sempre (duplicaria arquivos idênticos); pasta única global de versões (misturaria conjuntos com nomes iguais de dicionário de dados).

## R2. Nome das versões preservadas
- **Decision**: `<stem>__pub_<AAAAMMDDTHHMMSS><sufixo>` a partir do `ultima_modificacao` registrado no manifesto; sem registro, `__arq_<data de arquivamento UTC>`; se o nome já existir, acrescenta-se `_2`, `_3`…
- **Rationale**: ordenação cronológica natural, sem colisão, legível no Windows (sem `:`).

## R3. Leitores ignoram as versões preservadas
- **Decision**: subpasta `_versoes_anteriores/` dentro de cada pasta bruta.
- **Rationale**: todos os leitores usam busca não recursiva (`raw_dir.glob("*.csv")` no filtro de EVT; `<conjunto>/*.csv` nos indicadores; `*.parquet` na programação); a subpasta não é percorrida. Um teste confirma.

## R4. Registro no manifesto
- **Decision**: a entrada de cada arquivo ganha a lista `versoes_anteriores` com `arquivo_preservado`, `ultima_modificacao`, `tamanho_bytes`, `sha256` e `arquivado_em_utc`; `_register_version` passa a manter essa lista ao reescrever a entrada.
- **Rationale**: o manifesto já é o registro de versões (spec 001); atende ao princípio IV (data de publicação e de ingestão registradas).

## R5. Nível de log único (US3)
- **Decision**: `configurar_nivel_log(nivel)` em `src/logger.py` aplica o nível a uma lista única `LOGGERS_PIPELINE` (`main`, `collector`, `filter`, `consolidator`, `indicadores_ons`, `programacao_ons`, `processor`, `validator`, `analyzer`, `uhe_sao_domingos.pdf_generator`); cada ponto de entrada (`src.main`, `src.processor`, `src.analyzer`, `src.indicadores_ons`, `src.programacao_ons`, `src.pdf_generator`) chama a função com o valor de `--log-level`.
- **Rationale**: hoje os loggers nascem de três formas (`setup_logger`, `logging.getLogger` com handler próprio e logger sem handler) e cada `main` só ajusta o seu. Ajustar o nível dos loggers nomeados resolve sem mudar formatação nem handlers.
- **Alternatives considered**: logger raiz único (mudaria a formatação e duplicaria mensagens dos módulos que já têm handler).

## R6. Linhas com formato irregular (US4)
- **Decision**: no `_scan_file` do filtro, linha não vazia com número de campos diferente do cabeçalho é contada em `registros_formato_irregular`, não extraída e avisada no log (arquivo, quantidade e números das 5 primeiras linhas). Linhas vazias continuam ignoradas.
- **Rationale**: princípio IV (inconsistência de separadores ou campos insuficientes registrada em log). Varredura de 05/10/2026: 0 linhas irregulares em 42 arquivos e 14.993.512 linhas — a base extraída não muda. A contagem fica na auditoria (CSV), sem entrar no texto do relatório (FR-007).
- **Alternatives considered**: extrair linhas longas truncando campos (risco de valores deslocados).

## R7. Figuras com seaborn (US2)
- **Decision**: manter as 5 funções e nomes de arquivo; as marcas de dados passam a ser produzidas por seaborn: `lineplot` (série temporal), `histplot` com `weights` e `multiple="stack"` (EVT mensal e vazões anuais empilhadas), `heatmap` (perfil horário) e `barplot` com `hue` (disponibilidade e geração anuais). Faixas de indisponibilidade, linhas e rótulos de referência continuam sobre os mesmos eixos (seaborn é construído sobre matplotlib). Tema central: `_estilo_graficos()` aplicado com `sns.axes_style`/`plt.rc_context`, paleta atual passada ao seaborn.
- **Rationale**: Requisito Técnico 5; preserva conteúdo, paleta validada e legibilidade. `barplot` do seaborn não empilha; `histplot` ponderado é o recurso nativo de empilhamento.
- **Alternatives considered**: `sns.objects` (API ainda experimental na 0.13); manter matplotlib (viola a constituição).

## R8. Dependências (US5)
- **Decision**: `requirements.txt` = pandas, numpy, pyarrow, openpyxl, matplotlib, seaborn, reportlab, pytest, com as versões mínimas atuais (numpy ≥ 1.26); retirar `requests`. Teste automático compara os pacotes de terceiros importados em `src/` e `tests/` (análise sintática) com a lista.
- **Rationale**: SC-004 verificável a cada execução da suíte.
