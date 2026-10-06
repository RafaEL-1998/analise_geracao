# Research: Bases Complementares do ONS, Dicionários de Dados e Cópia de Segurança

**Feature**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Data**: 2026-10-05

Todas as sondagens foram feitas em 05/10/2026 em pasta temporária, sem alterar arquivos do projeto. Elas cruzaram a base EVT local com o catálogo e os arquivos do ONS. Não restou nenhum ponto "NEEDS CLARIFICATION" no contexto técnico.

---

## R1. Cópia de segurança dos dados processados (US1)

**Decisão**: um módulo novo, `src/persistencia.py`, concentra toda gravação em `data/processed/`. Cada gravação segue esta sequência:

1. **Gravação em arquivo temporário**: `<nome>.tmp`, na mesma pasta do destino.
2. **Conferência física do temporário**:
   - o arquivo existe e pode ser lido;
   - o número de registros e o de colunas são os pretendidos.
3. **Comparação com o arquivo atual**: se o conteúdo for idêntico, o temporário é apagado e o resultado é `INALTERADO`. Nem o arquivo nem o `.bak` são tocados (FR-009).
4. **Cópia de segurança**: o arquivo atual é copiado para `<nome>.bak`, substituindo a cópia anterior (FR-008).
5. **Troca atômica**: o temporário substitui o destino (`Path.replace`, mesma unidade de disco).
6. **Verificação final**: o SHA-256 do destino deve ser igual ao do temporário.
7. **Em falha a partir do passo 4**:
   - o destino volta à versão do `.bak`;
   - se o arquivo era novo, o destino inválido é apagado;
   - o temporário é removido;
   - é levantado `ErroPersistencia`, com o nome do arquivo, o que faz a etapa encerrar com código 1 (FR-010).

Resultados possíveis: `NOVO`, `ALTERADO`, `INALTERADO`, sempre registrados no log.

**Comparação por formato** (medida em 05/10/2026):

| Formato | Determinístico? | Comparação "conteúdo idêntico" | Conferência física |
|---|---|---|---|
| CSV (pandas ou módulo `csv`) | sim | bytes iguais | releitura: linhas e colunas |
| Markdown / texto | sim | bytes iguais | releitura do texto |
| Parquet (pyarrow) | **sim** (mesmo DataFrame gravado duas vezes = bytes iguais) | bytes iguais | metadados do arquivo: `num_rows`, `num_columns` |
| Planilha xlsx (openpyxl) | **não** (datas internas do pacote mudam a cada gravação) | **assinatura dos dados** gravada como propriedade personalizada `assinatura_dados` (SHA-256 da serialização CSV de cada aba, na ordem) e lida de `docProps/custom.xml` sem abrir as abas | abas na ordem esperada; dimensões de cada aba (linhas = registros + cabeçalho) em modo somente leitura |

**Justificativa**:
- Ler a planilha tratada (70.895 × 25) custa 18,4 s e gravá-la, 33,7 s. Comparar ou conferir relendo os dados dobraria esse custo; a assinatura é lida em milissegundos. Teste feito: assinatura gravada e lida de volta, com dimensões corretas inclusive em aba vazia.
- O temporário na mesma pasta garante troca atômica no Windows.
- Os leitores usam nomes explícitos ou `glob("*.csv")` e `glob("*.parquet")` sem recursão, então `*.csv.bak`, `*.parquet.bak` e `*.tmp` nunca são lidos (FR-011).

**Alternativas consideradas**:
- Copiar para `.bak` sempre, sem comparar: execuções repetidas apagariam a versão anterior (viola FR-009).
- Comparar planilhas relendo as abas: custo extra de cerca de 20 s por planilha grande.
- Registro externo de assinaturas (`_assinaturas.json`): mais um arquivo de controle sujeito a ficar defasado.
- `.bak` datados acumulados: rejeitado pelo usuário (uma cópia por arquivo basta para recuperar o estado anterior).

**Escopo** (constituição 1.2.0, Requisito Técnico 3):
- Arquivos cobertos: todos os gravados em `data/processed/` pelo pipeline. São eles:
  - consolidação e auditoria da varredura (`src/consolidator.py`);
  - base tratada em CSV, Parquet e xlsx (`src/processor.py`);
  - relatório de validação física em CSV e Markdown (`src/validator.py`);
  - indicadores (`src/indicadores_ons.py`);
  - programação (`src/programacao_ons.py`);
  - todas as saídas novas desta feature.
- Fora da regra: `reports/`, manifestos, dicionários e arquivos de controle.

---

## R2. Dicionários de dados (US2)

**Constatação**:
- Cada um dos 10 conjuntos do pipeline publica dois recursos de dicionário no catálogo: "Dicionário de Dados" (PDF) e "Dicionário de Dados Json" (JSON).
- O catálogo não informa tamanho nem data de modificação desses recursos (`size` e `last_modified` nulos).
- Em 05/10/2026 nenhum dicionário estava salvo localmente.

| Conjunto (id no catálogo) | Arquivos |
|---|---|
| energia-vertida-turbinavel | `DicionarioDados_EnergiaVertidaTurbinavel.{pdf,json}` |
| programacao_diaria | `DicionarioDados_Valores_Programacao_Diaria.{pdf,json}` |
| taxa_teif_teip | `DicionarioDados_Taxa_Teifa_Teip.{pdf,json}` |
| taxa_teif_teip_parametro | `DicionarioDados_Taxa_Teifa_Teip_Parametro.{pdf,json}` |
| ind_disponibilidade_fgeracao_uge_mensal | `DicionarioDados_Ind_Disponibilidade_FuncaoGeracao_UGE_Mensal.{pdf,json}` |
| ind_disponibilidade_fgeracao_uge_anual | `DicionarioDados_Ind_Disponibilidade_FuncaoGeracao_UGE_Anual.{pdf,json}` |
| disponibilidade_usina | `DicionarioDados_Disponibilidade_Usinas.{pdf,json}` |
| dados_hidrologicos_ho | `DicionarioDados_DadosHidrologicosHorarios.{pdf,json}` |
| geracao-usina-2 | `DicionarioDados_GeracaoPorUsina.{pdf,json}` |
| modalidade-usina | `DicionarioDados_Modalidade_Operacao_Usina.{pdf,json}` |

**Decisão**: novo módulo `src/dicionarios_ons.py`.

- **Seleção**: recursos de formato PDF ou JSON cujo nome, sem acentos, contém "dicionario".
- **Obtenção**: sempre baixados (`download_resource(..., force=True)`), porque sem data e tamanho não há como saber se mudaram.
- **Classificação do resultado**: o SHA-256 da cópia local é comparado antes e depois.
  - `NOVO`: não havia cópia;
  - `INALTERADO`: hash igual;
  - `ALTERADO`: hash diferente; a versão anterior vai para `_versoes_anteriores/` pelo mecanismo da spec 005;
  - `FALHA`: erro de rede ou HTTP;
  - `NAO_PUBLICADO`: o conjunto não tem dicionário num dos formatos.
- **Local**: `<pasta bruta do conjunto>/_dicionarios/`, com manifesto próprio (`_manifesto_ons.json`) e `_versoes_anteriores/`. A EVT fica em `data/raw/_dicionarios/`. O prefixo `_` e a leitura sem recursão das pastas brutas impedem que um dicionário seja lido como dado.
- **Registro**: o resultado e a data da última obtenção ficam na entrada do manifesto (`resultado_ultima_obtencao`, `obtido_em_utc`). O consolidado `data/processed/relatorio_dicionarios_ons.csv` é montado a partir de todos os manifestos, de modo que execuções parciais não apagam o registro dos outros conjuntos.
- **Quando executa**: a cada coleta, dentro de cada etapa que baixa dados (`baixar=True`), só para os conjuntos dessa etapa.
  - A etapa 1 obtém só o dicionário da EVT, depois do `discover_and_download_all`, sem tocar os CSV de dados (FR-015).
  - O modo `--dicionarios-only` obtém os 10 conjuntos.
- **Falhas**: registradas, sem interromper as demais etapas (FR-015).

**Alternativas consideradas**:
- Baixar só quando o arquivo local não existe: não detecta mudanças, contrariando o "SEMPRE" do usuário e a constituição 1.2.0.
- Guardar os dicionários em `data/raw/dicionarios/` centralizado: afasta o dicionário dos dados que ele descreve.
- Interromper o pipeline em caso de falha: o dicionário é documentação; a análise não depende dele.

---

## R3. Motor comum dos conjuntos horários (US3, US4, US5)

**Decisão**: novo módulo `src/conjuntos_ons.py`, com uma descrição declarativa por conjunto (`DescricaoConjunto`) e as funções comuns:

- **Período do arquivo pelo nome**: `_(\d{4})(?:_(\d{2}))?\.` resolve tanto os anuais (geração até 2021) quanto os mensais.
- **Seleção por período**: entram os arquivos que se sobrepõem a [início, fim] da base EVT.
- **Formato por período**: para cada chave (ano ou ano-mês), o formato preferido publicado; se ele não existir, o seguinte (Parquet → CSV). Isso atende ao FR-003: cada mês é obtido num formato que o contém.
- **Recursos duplicados no catálogo**: mesmo nome de arquivo (ex.: hidrologia 2026_10, com 278.680 e 14.698 bytes). Fica o recurso com `last_modified` preenchido e, em empate, o maior; a duplicidade vai para a auditoria.
- **Download**: `download_resource` com manifesto da pasta, cache por versão publicada e preservação de versões (spec 005), em 8 downloads simultâneos, como na programação.
- **Leitura**:
  - Parquet: projeção das colunas;
  - CSV: `;` e UTF-8, com releitura em Latin-1 se necessário.
  - Os campos de identificação são lidos de todas as linhas para contar a identificação parcial; os valores, só das linhas da usina.
  - Conversão numérica com contagem de valores não conversíveis.
- **Auditoria por arquivo**, conforme o FR-005.
- **Duplicatas**: uma hora por instante, a do arquivo mais recente (FR-006).
- **Recorte e ausências**: recorte no período e lista de meses e intervalos de horas ausentes, sem interpolação.

**Justificativa**: três conjuntos com o mesmo fluxo (catálogo → período → formato → download → filtro → auditoria → série horária). Um motor único evita triplicar código e testes, segue o padrão de `indicadores_ons.py` e `programacao_ons.py` e mantém cada módulo de conjunto pequeno (descrição, regras próprias e análises).

**Verificações**:
- **Disponibilidade, 2023-01**: Parquet e CSV têm as mesmas 744 h e os mesmos valores nos 3 campos. Os valores numéricos vêm como texto no Parquet.
- **Leitura de um CSV mensal completo** de disponibilidade (cerca de 25 MB, 169 mil linhas) com filtro: 0,42 s.

**Alternativas consideradas**:
- Um módulo independente por conjunto, sem motor: mais código repetido para o mesmo prazo.
- Consultas remotas pelo servidor MCP: o pipeline precisa de cópias locais auditáveis (princípio V), e o servidor lê só o formato compacto, que na disponibilidade é incompleto (R4).

---

## R4. Disponibilidade por usina (US3)

**Constatações**:
- **Catálogo**:
  - CSV com 143 arquivos mensais, de 2015-01 a 2026-10, cerca de 25 MB cada;
  - Parquet com 48 arquivos, **só 2015-01/02 e 2023-01 em diante**;
  - XLSX com 142 arquivos.
- **Presença da usina**: 720 h em 09/2018 e em 06/2021 (CSV) e todas as horas de 2023 a 04/10/2026, sem duplicatas, sem valores não numéricos e sem sincronizada acima da operacional.
  - A afirmação anterior "a usina aparece desde 01/2023" resultava de consultas que leem só o formato compacto.
- **Identificação**: id ONS `MSUHSD`, CEG `UHE.PH.MS.028761-0.01`, estado `MS`, nome "São Domingos", tipo UHE. Os mesmos valores aparecem em 2018, 2021 e 2023–2026.
- **Hora**: início da hora (00:00 a 23:00), como a base EVT.
- **Amostra de jan/2025**: operacional = disponibilidade declarada da EVT em 744/744 h; sincronizada média de 45,96 MW contra operacional de 46,21 MW.
- **Médias anuais da sincronizada** (2023–2026): 37,7, 35,9, 31,7 e 27,6 MW; a operacional ficou estável, perto de 43,5 MW.

**Decisões**:
- **Formatos**: CSV para 08/2018–12/2022 (53 arquivos, cerca de 1,3 GB) e Parquet de 2023-01 em diante (cerca de 10 MB).
- **Qualidade por hora**: a coluna `qualidade` recebe `OK` ou as regras violadas, e as horas sinalizadas ficam fora das análises (FR-018). As regras são:
  - D1: sincronizada > operacional + 0,01 MW;
  - D2: operacional > instalada + 0,01 MW;
  - D3: algum valor negativo;
  - D4: algum valor não numérico.
- **Coincidência operacional × declarada**: tolerância de 0,01 MW (os valores são publicados com 2 casas e iguais na amostra). As divergências são agrupadas em períodos contínuos.
- **Classificação das horas paradas** (geração ≤ 1 MW, FR-019):
  - sincronização: `SINCRONIZADA` se a sincronizada for maior que 1 MW; senão, `NAO_SINCRONIZADA`;
  - EVT: `COM_EVT` ou `SEM_EVT`;
  - programação, onde houver: a classe da spec 004 (`PARADA_EVT_PROGRAMACAO_ZERO` etc.); fora do período da programação, `SEM_PROGRAMACAO`.
- **Comparação com a reserva desligada** (FR-020): por mês, compara-se Σ(operacional − sincronizada) em MWh com Σ(HRD × potência da unidade) dos parâmetros TEIFa/TEIP (spec 004). A diferença é publicada sem meta, porque são apurações diferentes.

**Alternativas consideradas**:
- Usar só o Parquet: perderia 08/2018–12/2022.
- Usar só o CSV: cerca de 1 GB a mais de download sem ganho, já que os dois formatos são iguais em 2023-01.

---

## R5. Dados hidrológicos horários (US4)

**Constatações**:
- **Catálogo**: Parquet mensal de 2010-01 a 2026-10 (203 recursos, 2026_10 duplicado); cerca de 127 MB desde 2018.
- **Identificação estável**: `cod_usina` 153, `id_reservatorio` `PNUHSD`, `nom_reservatorio` "SAO DOMINGOS", tipo "Fio dagua", bacia Paraná, subsistema SE. Os mesmos valores aparecem em 2018, 2021 e 2025, e nenhum outro reservatório tem "DOMINGOS" no nome.
- **Convenção de fim de hora**:
  - a primeira hora do dia aparece à 01:00 e a última às 23:59 (uma por dia: 361 em 2018, 364 em 2021, 365 em 2025);
  - **conversão**: hora de início = (instante arredondado para cima até a hora cheia) − 1 h;
  - **validação em jan/2025**: com a conversão, turbinada e vertida coincidem com a EVT em 744/744 h; sem a conversão, a turbinada coincide em só 374/744.
- **Horas ausentes**: 2018 começa em 04/01 15h (antes do período da EVT); 7 h ausentes em 2021 e 4 em 2025.
- **Faixas observadas em jan/2025**:
  - nível de montante entre 344,17 e 344,88 m;
  - volume útil entre 16,7% e 87,8%;
  - nível de jusante sem nulos;
  - afluência média de 112,4 m³/s;
  - das 709 h com EVT, 695 com afluência ≤ 163 m³/s e 69 com ≤ 81,5 m³/s.

**Decisões**:
- **Extração**: `cod_usina` = 153, conferida por "SAO DOMINGOS" e `PNUHSD` (constituição 1.2.0, princípio IV).
- **Alinhamento**:
  - coincidência de turbinada e vertida com a EVT dentro de 0,5 m³/s, nas horas em que as duas existem;
  - meta de 99% (FR-022 e SC-003);
  - resultado gravado em `uhe_sao_domingos_ons_hidrologia_alinhamento.csv`;
  - abaixo da meta, a etapa retorna o código 3 e a análise não publica os cruzamentos hidrológicos.
- **Qualidade por hora**:
  - H1: vazão negativa;
  - H2: volume útil fora de 0 a 100%;
  - H3: valor não numérico;
  - vazio continua vazio (FR-026).
- **Faixas de afluência para horas com EVT** (FR-023):
  - `ACIMA_ENGOLIMENTO_USINA`: afluência > 163 m³/s;
  - `ENTRE_UMA_E_DUAS_UNIDADES`: 81,5 < afluência ≤ 163 m³/s;
  - `ATE_UMA_UNIDADE`: afluência ≤ 81,5 m³/s;
  - `SEM_DADO_HIDROLOGICO`.
- **Perfil por hora do dia** (FR-024): médias de nível de montante, afluente, turbinada e vertida, para dias com ao menos 1 h de parada com EVT e para os demais dias.

**Alternativas consideradas**:
- Desfasar 1 h sem tratar o 23:59: a última hora de cada dia ficaria fora de lugar.
- Faixas pela disponibilidade horária em vez do engolimento nominal: mais fiel, mas mistura duas fontes numa classe só. O engolimento nominal é parâmetro do projeto, e a disponibilidade já é tratada na US3.

---

## R6. Geração por usina (US5)

**Constatações**:
- **Catálogo**: Parquet completo, 80 recursos (anuais de 2000 a 2021, mensais de 2022-01 em diante); cerca de 407 MB desde 2018.
- **Identificação**: id ONS `MSUHSD`, CEG e estado MS.
- **Série**: começa em 18/06/2015 (consulta de 02/10/2026). Foi igual à EVT hora a hora de 2018 a 2026 naquela consulta, e de novo em jan/2025 (744/744 h; 23,054 GWh nas duas).
- **Hora ausente**: 1 h em 2018, a mesma de 04/11/2018 ausente na EVT (horário de verão).

**Decisões**:
- Coincidência dentro de 0,01 MW; as horas presentes em só uma das fontes são listadas.
- A energia mensal (MWh) de cada fonte é comparada com a diferença.
- Constatação só se houver divergência (FR-031).
- A história é P2: não altera nenhuma conclusão e reforça a reprodutibilidade.

**Alternativas consideradas**: estender a série para antes de 28/08/2018. Fica fora do escopo (decisão do usuário: recorte no período da base EVT).

---

## R7. Modalidade das usinas (US6)

**Constatações**:
- Arquivo único, cadastro sem série histórica.
- **Ficha da usina**: UHE SÃO DOMINGOS, CEG `UHE.PH.MS.028761-0.01`, `MSUHSD`, TIPO II-A, 48,000 MW, COSR-S, SE ÁGUA CLARA 138 KV, MS, situação "A".
- **Homônimos**: mais de 20 "São Domingos" (CGH em SC e no RS, PCH São Domingos I e II em GO, 6 eólicas no RN, 9 solares).

**Decisões**:
- Extração pelo CEG, conferida pelo id ONS e pelo estado; os homônimos são contados.
- **Data da consulta**: a data de obtenção do arquivo (manifesto).
- **Histórico**: preservado pelas versões anteriores do arquivo bruto (spec 005).
- **Divergências sinalizadas**: potência ≠ 48 MW; estado ≠ MS.
- **Formato**: CSV (menos de 1 MB). A estrutura é igual à do Parquet; o CSV é escolhido porque é legível sem ferramenta.

---

## R8. Integração no pipeline e linha de comando

**Decisão**: novas etapas em `src/main.py`, depois das etapas 3 e 4:
- etapa 5: disponibilidade;
- etapa 6: hidrologia;
- etapa 7: geração;
- etapa 8: cadastro.

Cada etapa:
- tem modo `--X-only`;
- tem opção `--sem-X`;
- recebe `pasta_raw` e `pasta_saida` como parâmetros;
- usa o período da base consolidada.

Modos de conveniência:
- `--complementares-only`: executa as etapas 5 a 8 e seus dicionários, sem tocar a base EVT. É o comando recomendado, porque a base EVT não é baixada de novo.
- `--dicionarios-only`: obtém só os dicionários dos 10 conjuntos.

Os códigos de saída estão no [cli-contract.md](contracts/cli-contract.md). Cada módulo novo também tem `main()` próprio com `--no-download`, `--force-download` e `--log-level`.

**Justificativa**: mantém o padrão das etapas 3 e 4 e o teste de integração por simulação, e respeita a decisão do usuário de não baixar de novo a base EVT.

---

## R9. Relatório

**Decisões**:
- **Resultados**: `ResultadosAnalise` ganha os dicionários `disponibilidade`, `hidrologia`, `geracao_oficial` e `cadastro` (vazios se a etapa não rodou). `analisar()` recebe os conjuntos opcionais.
- **Seções novas** (numeração automática), depois da seção da programação: "Disponibilidade sincronizada" e "Afluência, vertimento e nível do reservatório". Depois da cobertura: "Identificação da usina no cadastro do ONS". Junto à qualidade dos dados: "Conferência da geração com a série oficial".
- **Constatações**: disponibilidade sincronizada e afluência sempre que houver dados; geração e cadastro só com divergência.
- **Abas**: `DISP_*`, `HID_*`, `GER_*`, `CAD_*` e `DICIONARIOS`.
- **Parâmetros e fontes**: linhas com conjunto, período, identificador, data de obtenção e limiares novos.
- **Figuras** (seaborn, tema e paleta centrais, skill dataviz carregada antes do código):
  - `06_disponibilidade_operacional_sincronizada_mensal.png`: linhas mensais de operacional, sincronizada e geração (MW, eixo único);
  - `07_evt_por_faixa_de_afluencia.png`: barras anuais empilhadas de horas com EVT por faixa;
  - `08_perfil_horario_nivel_vazoes.png`: dois painéis (vazões e nível), sem eixo duplo, com os dois grupos de dias.
- **Não regressão** (SC-008):
  - textos e tabelas das seções existentes comparados com a cópia de referência, ignorando a numeração;
  - abas existentes comparadas célula a célula.

---

## R10. Volume, desempenho e prazo

| Item | Estimativa |
|---|---|
| Download inicial | cerca de 1,9 GB (disponibilidade ~1,3 GB; geração ~410 MB; hidrologia ~130 MB; cadastro e dicionários < 5 MB) |
| Processamento sem rede | disponibilidade: 53 CSV × 0,4 s + Parquet; hidrologia: ~100 Parquet pequenos; geração: ~60 Parquet. Meta de menos de 10 min (SC-009) |
| Custo da US1 nas etapas existentes | 1 leitura de assinatura por planilha, 1 hash por arquivo e as releituras de CSV/Parquet para conferência (alguns segundos) |

**Ordem de entrega**: US1 → US2 → US3 → US4 → relatório (P1, até 13/10/2026) → US5 → US6.

---

## R11. Governança

- A constituição foi emendada para a 1.2.0 em 05/10/2026, antes do plano:
  - identificadores de disponibilidade, hidrologia e modalidade;
  - dicionários obrigatórios a cada coleta;
  - escopo do `.bak`.
- Antes da implementação: cópia datada do conjunto afetado (`_backup_AAAA-MM-DD_antes_spec006/`: src, tests, specs, reports, README, requirements, `.specify`), conforme o Requisito Técnico 3(b).
- Nenhuma dependência nova: `hashlib`, `zipfile`, `shutil`, `concurrent.futures` e `urllib` são da biblioteca padrão, e openpyxl 3.1 já oferece propriedades personalizadas.

---

## R12. Constatações da implementação (05/10/2026)

- **Disponibilidade** (98 arquivos: 53 CSV e 45 Parquet):
  - 70.895 horas, com a operacional igual à declarada da EVT em 100% das horas;
  - a capacidade não sincronizada coincide com a reserva desligada TEIFa/TEIP em 2020–2023 e diverge de 2024 em diante (resultado publicado, sem meta).
- **Hidrologia** (98 arquivos):
  - 07/2024 veio do CSV (o Parquet não está no catálogo) e 2024_05 está duplicado no catálogo;
  - o alinhamento ficou em 100% de 70.731 horas comuns;
  - a exclusão por hora inteira foi trocada por exclusão campo a campo (data-model, seção 10), e entrou a regra H4.
- **Geração** (61 arquivos): igual à base de EVT em 100% das horas; a energia do período difere em 0,019 MWh (arredondamento).
- **Cadastro**: TIPO II-A, COSR-S, SE ÁGUA CLARA 138 KV, 48 MW, situação "A", 20 homônimos.
- **Defeito corrigido**: `filecmp.cmp` guarda em cache o resultado por caminho, tamanho e data, o que levava a `INALTERADO` falso; a comparação passou a ser byte a byte, sem cache.
- **Cores das figuras** (validadas pelo script da skill dataviz):
  - sincronizada em amarelo (posição 4) e vazão afluente em violeta (posição 7);
  - o magenta (posição 5) reprovou o piso de visão normal contra o laranja da vertida em todos os pares (ΔE 12,9);
  - faixas de afluência em rampa ordinal de laranja (#ef8a5d, #c24f1f, #8c3612; passo claro com 2,48:1).
