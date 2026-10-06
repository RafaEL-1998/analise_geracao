# Data Model: Bases Complementares do ONS, Dicionários de Dados e Cópia de Segurança

**Feature**: [spec.md](spec.md) · **Pesquisa**: [research.md](research.md)

Convenções gerais:
- Os CSV usam `;`, ponto decimal, UTF-8 e datas `AAAA-MM-DD HH:MM:SS`.
- `din_instante` é sempre a **hora de início** (convenção da base EVT).
- Os identificadores da usina seguem o princípio IV da constituição 1.2.0.

---

## 1. Persistência (US1)

### ResultadoGravacao (enumeração)

| Valor | Quando |
|---|---|
| `NOVO` | o destino não existia; gravado e conferido |
| `ALTERADO` | o conteúdo mudou; a versão anterior foi para `<nome>.bak` e a nova foi gravada e conferida |
| `INALTERADO` | o conteúdo é idêntico ao atual; nada é gravado e o `.bak` fica como estava |

Em falha, levanta-se `ErroPersistencia` (subclasse de `ONSError`) e o destino volta ao estado anterior.

### Cópia de segurança

- **Arquivo**: `<nome do arquivo>.bak`, na mesma pasta do destino (ex.: `uhe_sao_domingos_ons_programacao_horaria.csv.bak`).
- **Invariante**: guarda a versão imediatamente anterior à última alteração de conteúdo.
- **Regras**:
  - criada ou substituída só no resultado `ALTERADO`;
  - nunca lida como dado;
  - vale só para `data/processed/`.

### Assinatura dos dados (planilhas)

- Propriedade personalizada `assinatura_dados` do xlsx.
- Valor: SHA-256 de `Σ (nome da aba + "\n" + CSV da aba sem índice)`, nas abas em ordem.
- É usada só para decidir `INALTERADO`.

---

## 2. Dicionário de dados (US2)

### Entrada do manifesto `<pasta bruta>/_dicionarios/_manifesto_ons.json`

Os campos atuais do manifesto (spec 005) continuam: `url`, `ultima_modificacao`, `tamanho_publicado_bytes`, `tamanho_bytes`, `registrado_em_utc`, `origem_registro` e `versoes_anteriores[]`. Campos novos:

| Campo | Tipo | Regra |
|---|---|---|
| `conjunto` | texto | id do catálogo (ex.: `dados_hidrologicos_ho`) |
| `formato` | `PDF` \| `JSON` | formato do recurso |
| `resultado_ultima_obtencao` | `NOVO` \| `INALTERADO` \| `ALTERADO` \| `FALHA` | resultado da última tentativa |
| `obtido_em_utc` | data e hora | data da última tentativa |
| `sha256` | texto (64) | hash da cópia corrente |

**Transições de estado**:
- (sem cópia) → `NOVO` → `INALTERADO` | `ALTERADO` (versão anterior preservada).
- Qualquer estado → `FALHA`: a cópia válida anterior é mantida; na próxima obtenção bem-sucedida, o estado volta a `INALTERADO` ou `ALTERADO`.
- `NAO_PUBLICADO` não é estado do manifesto: aparece só no registro, quando o catálogo não traz o formato.
- `NAO_OBTIDO` também aparece só no registro: o catálogo ainda não foi consultado para os dicionários do conjunto (nenhuma coleta dele desde a spec 006). Distingue-se de `FALHA` (consulta tentada sem sucesso) e de `NAO_PUBLICADO` (consulta feita, formato ausente no catálogo).

### Registro `data/processed/relatorio_dicionarios_ons.csv`

Montado a partir de todos os manifestos, com uma linha por conjunto e formato (20 linhas esperadas). Colunas:
- `conjunto`, `pasta`, `formato`, `arquivo`, `url`;
- `resultado_ultima_obtencao`, `obtido_em_utc`, `sha256`, `tamanho_bytes`;
- `versoes_anteriores`, `ultima_versao_anterior`.

---

## 3. Motor dos conjuntos horários (US3 a US5)

### DescricaoConjunto (declarativa, imutável)

| Campo | Disponibilidade | Hidrologia | Geração |
|---|---|---|---|
| `pacote` | `disponibilidade_usina` | `dados_hidrologicos_ho` | `geracao-usina-2` |
| `pasta_raw` | `data/raw/disponibilidade_usina` | `data/raw/dados_hidrologicos_ho` | `data/raw/geracao_usina_2` |
| `formatos_preferidos` | Parquet, CSV | Parquet, CSV | Parquet, CSV |
| `identificador` | `id_ons` = `MSUHSD` | `cod_usina` = 153 | `id_ons` = `MSUHSD` |
| `conferencia` | `ceg` = CEG; `id_estado` = `MS` | `nom_reservatorio` contém "SAO DOMINGOS"; `id_reservatorio` = `PNUHSD` | `ceg` = CEG; `id_estado` = `MS` |
| `convencao_hora` | início | **fim** (23:59 = última hora) | início |
| `colunas_valor` | `val_potenciainstalada`, `val_dispoperacional`, `val_dispsincronizada` | 9 grandezas (seção 5) | `val_geracao` |

### RecursoSelecionado

- `chave_periodo`: `(ano, mes)`, ou `(ano, None)` nos arquivos anuais.
- `formato` e `recurso`: o escolhido para a chave.
- `duplicados_catalogo`: lista dos recursos descartados com o mesmo nome.

**Regras**:
- A chave deve se sobrepor ao período da base EVT.
- Usa-se o primeiro formato preferido publicado para a chave.
- Entre duplicados, fica o recurso com `last_modified` preenchido e, em empate, o de maior tamanho.

### Auditoria por arquivo: `relatorio_auditoria_<conjunto>_ons.csv`

| Coluna | Descrição |
|---|---|
| `arquivo`, `formato`, `periodo` | origem (`periodo` = `AAAA` ou `AAAA-MM`) |
| `linhas_lidas` | total de linhas de dados do arquivo |
| `linhas_formato_irregular` | linhas não vazias com nº de campos diferente do cabeçalho (CSV), não extraídas e avisadas no log com o número das primeiras (princípio IV; mesmo critério da EVT, spec 005); zero no Parquet |
| `linhas_usina` | linhas com identificador **e** conferência |
| `linhas_so_identificador`, `linhas_so_conferencia` | identificação parcial (contadas, não extraídas) |
| `horas_usina` | instantes distintos da usina no arquivo |
| `valores_invalidos` | células não conversíveis em número nas colunas de valor |
| `duplicatas_conflitantes` | horas repetidas com valores diferentes |
| `recursos_duplicados_catalogo` | quantos recursos do catálogo tinham o mesmo nome |
| `status` | `PROCESSADO` \| `SEM_REGISTROS` \| `FALHA` |
| `mensagem` | detalhe da falha, se houver |

### Ausências: `uhe_sao_domingos_ons_<conjunto>_ausencias.csv`

- Colunas: `tipo` (`MES_SEM_ARQUIVO` \| `MES_SEM_USINA` \| `HORAS`), `inicio`, `fim`, `horas`.
- Meses e intervalos contínuos de horas ausentes no período da base EVT.
- Nunca interpolados.

---

## 4. Disponibilidade (US3)

### DisponibilidadeHoraria: `uhe_sao_domingos_ons_disponibilidade_horaria.csv`

| Coluna | Unidade | Regra |
|---|---|---|
| `din_instante` | — | único; dentro do período da base EVT |
| `val_potenciainstalada` | MW | numérico ou vazio |
| `val_dispoperacional` | MW | numérico ou vazio |
| `val_dispsincronizada` | MW | numérico ou vazio |
| `qualidade` | — | `OK` ou as regras violadas, separadas por vírgula |
| `arquivo_origem` | — | arquivo de onde veio a hora |

Regras de qualidade:
- `D1`: sincronizada > operacional + 0,01 MW;
- `D2`: operacional > instalada + 0,01 MW;
- `D3`: algum valor negativo;
- `D4`: algum valor não numérico.

As horas com qualidade diferente de `OK` ficam fora das análises.

### HoraParadaClassificada (análise; aba `DISP_HORAS_PARADAS`)

- `din_instante`, `val_geracao`, `val_dispoperacional`, `val_dispsincronizada`, `val_energiavertidaturbinavel`.
- `sincronizacao`: `SINCRONIZADA` se a sincronizada > 1 MW; senão, `NAO_SINCRONIZADA`.
- `evt`: `COM_EVT` se a EVT > 0; senão, `SEM_EVT`.
- `classe_programacao`: classe da spec 004 nas horas cobertas pela programação; `SEM_PROGRAMACAO` fora delas.

**Validação**: só entram as horas com geração ≤ 1 MW e qualidade `OK`. A soma das classes deve ser igual ao total de horas paradas comuns (SC-005).

### ConferenciaDisponibilidade (aba `DISP_CONFERENCIA` e `DISP_DIVERGENCIAS`)

- **Resumo**: `horas_comuns`, `coincidentes` (|operacional − declarada| ≤ 0,01 MW), `divergentes`, `so_ons_disponibilidade`, `so_base_evt`.
- **Divergências** agrupadas em períodos contínuos: `inicio`, `fim`, `horas`, `diferenca_media_mw`, `diferenca_maxima_mw`.

### ResumoDisponibilidade (abas `DISP_MENSAL` e `DISP_ANUAL`)

- `periodo`, `horas_comuns`;
- `disp_operacional_media_mw`, `disp_declarada_media_mw`, `disp_sincronizada_media_mw`, `geracao_media_mw`;
- `capacidade_nao_sincronizada_media_mw`, `capacidade_nao_sincronizada_mwh`;
- `reserva_desligada_teif_mwh` = Σ(HRD × potência da unidade), da spec 004;
- `diferenca_mwh`;
- `horas_paradas`, `horas_paradas_sem_sincronizacao`, `horas_paradas_sincronizadas`.

---

## 5. Hidrologia (US4)

### HidrologiaHoraria: `uhe_sao_domingos_ons_hidrologia_horaria.csv`

| Coluna | Unidade | Regra |
|---|---|---|
| `din_instante` | — | hora de início = (instante publicado arredondado para cima até a hora cheia) − 1 h |
| `din_instante_publicado` | — | valor original (hora de fim; 23:59 na última hora do dia) |
| `val_vazaoafluente`, `val_vazaodefluente`, `val_vazaoturbinada`, `val_vazaovertida`, `val_vazaovertidanaoturbinavel`, `val_vazaooutrasestruturas` | m³/s | negativo → `H1`; vazio permanece vazio |
| `val_nivelmontante`, `val_niveljusante` | m | vazio permanece vazio |
| `val_volumeutil` | % | fora de 0–100 → `H2` |
| `qualidade` | — | `OK` ou as regras `H1`, `H2`, `H3` (não numérico), `H4` (nível de montante ou de jusante a mais de `DESVIO_MAXIMO_NIVEL_M` = 10 m da mediana da série) |
| `arquivo_origem` | — | arquivo de onde veio a hora |

### AlinhamentoHidrologia: `uhe_sao_domingos_ons_hidrologia_alinhamento.csv` (1 linha)

- Contagens: `horas_comuns`, `coincidentes_turbinada`, `coincidentes_vertida`, `coincidentes_ambas`.
- `pct_coincidencia`: `coincidentes_ambas` ÷ `horas_comuns` × 100.
- Parâmetros: `meta_pct` = 99; `tolerancia_m3s` = 0,5; `deslocamento_aplicado_h` = −1.
- `confirmado`: verdadeiro se `pct_coincidencia` ≥ 99. Se for falso, a análise não publica os cruzamentos (FR-022).

### FaixaAfluencia (enumeração; abas `HID_FAIXAS_AFLUENCIA`, por mês, e `HID_FAIXAS_ANUAL`, por ano)

| Valor | Regra (afluência na hora com EVT) |
|---|---|
| `ACIMA_ENGOLIMENTO_USINA` | > 163 m³/s |
| `ENTRE_UMA_E_DUAS_UNIDADES` | > 81,5 e ≤ 163 m³/s |
| `ATE_UMA_UNIDADE` | ≤ 81,5 m³/s |
| `SEM_DADO_HIDROLOGICO` | afluência vazia, inválida ou hora ausente |

**Saída**: horas e EVT (MWh) por faixa, por mês e por ano. A soma das faixas deve ser igual ao total de horas com EVT do período comum. No relatório, as tabelas anuais de horas e de EVT (MWh) por faixa têm a mesma estrutura.

### ResumoHidrologicoMensal (aba `HID_MENSAL`)

- `mes`, `horas`;
- `afluencia_media_m3s`, `afluencia_maxima_m3s`;
- `turbinada_media_m3s`, `vertida_media_m3s`, `vertida_nao_turbinavel_media_m3s`;
- `nivel_montante_min_m`, `nivel_montante_medio_m`, `nivel_montante_max_m`, `nivel_jusante_medio_m`;
- `volume_util_medio_pct`;
- `horas_afluencia_acima_engolimento`.

### PerfilHorarioHidrologico (aba `HID_PERFIL_HORA_DO_DIA`)

- `grupo_dias`: `COM_PARADA_EVT` ou `DEMAIS`;
- `hora` (0 a 23), `dias`;
- `nivel_montante_medio_m`, `afluencia_media_m3s`, `turbinada_media_m3s`, `vertida_media_m3s`.

---

## 6. Geração oficial (US5)

### GeracaoHorariaOficial: `uhe_sao_domingos_ons_geracao_horaria.csv`

Colunas: `din_instante`, `val_geracao` (MW), `qualidade` (`OK` ou `G1` = não numérico) e `arquivo_origem`.

### ConferenciaGeracao (abas `GER_CONFERENCIA`, `GER_MENSAL` e `GER_DIVERGENCIAS`)

- **Resumo**: como na conferência da disponibilidade, com tolerância de 0,01 MW.
- **Mensal**: `mes`, `energia_base_evt_mwh`, `energia_ons_geracao_mwh`, `diferenca_mwh`, `horas_so_base_evt`, `horas_so_ons_geracao`.

---

## 7. Cadastro (US6)

### FichaCadastral: `uhe_sao_domingos_ons_cadastro.csv` (1 linha)

- **Dados da usina**: `nom_usina`, `ceg`, `id_ons`, `nom_modalidadeoperacao`, `sgl_centrooperacao`, `nom_pontoconexao`, `val_potenciaautorizada` (MW), `id_estado`, `sts_aneel`.
- **Rastreabilidade**: `data_consulta_utc` (data de obtenção do arquivo, pelo manifesto) e `arquivo_origem`.
- `homonimos`: linhas com "SAO DOMINGOS" no nome, sem acento, e CEG diferente.
- `divergencias`: vazio, ou o texto das divergências (potência ≠ 48 MW; estado ≠ MS).

### AuditoriaCadastro: `relatorio_auditoria_cadastro_ons.csv` (1 linha; aba `CAD_AUDITORIA`)

- Colunas da auditoria dos conjuntos horários que se aplicam ao cadastro: `arquivo`, `formato`, `linhas_lidas`, `linhas_formato_irregular`, `linhas_usina` (linhas com o CEG do projeto), `linhas_so_identificador`, `linhas_so_conferencia`, `status` e `mensagem` (FR-005).
- `status`: `PROCESSADO`; `SEM_REGISTROS` (CEG ausente; a etapa retorna 2); `FALHA` (arquivo ilegível ou sem as colunas `nom_usina`, `ceg`, `id_ons` e `id_estado`; a etapa retorna 2 e a ficha anterior não é regravada).
- Uma linha irregular de outra usina não interrompe a etapa: fica fora da leitura, contada e avisada no log.

---

## 8. Resultados da análise (`src/analyzer.py`)

Campos novos de `ResultadosAnalise`, todos dicionários vazios quando a etapa correspondente não rodou:

| Campo | Conteúdo |
|---|---|
| `disponibilidade` | `conferencia`, `divergencias`, `horas_paradas`, `classes`, `mensal`, `anual`, `auditoria`, `ausencias`, `periodo`, `obtido_em` |
| `hidrologia` | `alinhamento`, `faixas_mensal`, `faixas_anual`, `mensal`, `perfil`, `auditoria`, `ausencias`, `periodo`, `obtido_em` |
| `geracao_oficial` | `conferencia`, `mensal`, `divergencias`, `auditoria`, `ausencias`, `periodo`, `obtido_em` |
| `cadastro` | `ficha`, `divergencias`, `obtido_em`, `auditoria` |
| `dicionarios` | registro dos dicionários (aba `DICIONARIOS`) |

---

## 9. Arquivos em `data/processed/` gravados pela persistência (FR-012)

| Etapa | Arquivos |
|---|---|
| Consolidação (spec 001) | `uhe_sao_domingos_energia_vertida_consolidado.csv`, `relatorio_auditoria_varredura.csv` |
| Tratamento e validação (spec 002) | `uhe_sao_domingos_energia_vertida_tratado.{csv,parquet,xlsx}`, `relatorio_validacao_fisica.{csv,md}` |
| Indicadores (spec 004) | 5 CSV `uhe_sao_domingos_ons_*` (indicadores mensal e anual, horas por estado, taxas, divergências), `relatorio_auditoria_indicadores_ons.csv` e `uhe_sao_domingos_indicadores_ons.xlsx` |
| Programação (spec 004) | `uhe_sao_domingos_ons_programacao_horaria.csv`, `uhe_sao_domingos_ons_programacao_dias_ausentes.csv`, `relatorio_auditoria_programacao_ons.csv` |
| Dicionários (US2) | `relatorio_dicionarios_ons.csv` |
| Disponibilidade (US3) | `uhe_sao_domingos_ons_disponibilidade_horaria.csv`, `uhe_sao_domingos_ons_disponibilidade_ausencias.csv`, `relatorio_auditoria_disponibilidade_ons.csv` |
| Hidrologia (US4) | `uhe_sao_domingos_ons_hidrologia_horaria.csv`, `uhe_sao_domingos_ons_hidrologia_ausencias.csv`, `uhe_sao_domingos_ons_hidrologia_alinhamento.csv`, `relatorio_auditoria_hidrologia_ons.csv` |
| Geração (US5) | `uhe_sao_domingos_ons_geracao_horaria.csv`, `uhe_sao_domingos_ons_geracao_ausencias.csv`, `relatorio_auditoria_geracao_ons.csv` |
| Cadastro (US6) | `uhe_sao_domingos_ons_cadastro.csv`, `relatorio_auditoria_cadastro_ons.csv` |

---

## 10. Ajustes feitos na implementação (05/10/2026)

- **Hidrologia, exclusão campo a campo (FR-026)**:
  - um valor sinalizado (H1, H2, H4) sai só das médias do próprio campo; a hora continua nas demais análises;
  - motivo: o volume útil negativo de 2019 coincide com a parada total, com o reservatório rebaixado até cerca de 342 m, e as vazões dessas horas são válidas;
  - na disponibilidade (D1 a D4) a hora inteira continua fora, porque as regras envolvem os três campos.
- **Regra H4**: criada depois de encontrar leituras trocadas de nível (montante de 308,67 m; jusante de 3,09, 395,9 e 730,9 m); uma única leitura dessas distorcia o perfil horário.
- **Abas a mais na planilha**:
  - `DISP_CLASSES_PARADA` e `DISP_AUSENCIAS`;
  - `HID_HORAS_EVT`, `HID_ANUAL` e `HID_AUSENCIAS`;
  - `GER_ANUAL`, `GER_AUSENCIAS` e `GER_AUDITORIA`.
- **Ficha cadastral**:
  - colunas a mais `linhas_so_identificador` e `linhas_so_conferencia`;
  - a ficha é localizada pelo CEG; id ONS ou estado divergente aparece em `divergencias` (FR-030), e não como ausência.
- **Convergência (05/10/2026, T054 a T061)**:
  - **linhas irregulares (T054)**: os CSV das bases novas (motor comum e cadastro) passaram a contar as linhas com nº de campos diferente do cabeçalho em `linhas_formato_irregular`. Essas linhas ficam fora da leitura e são avisadas no log. Antes, a linha curta entrava com campos vazios, o excedente da linha longa era descartado sem aviso e, no cadastro, uma linha longa interrompia a etapa;
  - **EVT por faixa e ano (T055)**: tabela anual de EVT (MWh) por faixa, com a mesma estrutura da tabela de horas, no Markdown e no PDF, e aba `HID_FAIXAS_ANUAL`;
  - **auditoria do cadastro (T059)**: `relatorio_auditoria_cadastro_ons.csv` e aba `CAD_AUDITORIA` (seção 7);
  - **disponibilidade no PDF (T060)**: a seção traz a tabela anual, a figura 06 (médias mensais) e as horas paradas por classe; o detalhe mensal fica na aba `DISP_MENSAL`. A tabela mensal prevista na T028 não entrou no PDF, para não acrescentar cerca de 98 linhas a uma informação já mostrada na figura.
- **Segunda convergência (05/10/2026, T062)**: a constatação de afluência traz a ressalva de que os dados hidrológicos não informam o motivo das paradas (FR-031).
