# Quickstart: Validação da Ampliação para Todos os Tipos de Usina

**Spec**: [spec.md](spec.md) · **Plano**: [plan.md](plan.md) · **Contratos**: [contracts/](contracts/)

Roteiro para conferir, fase a fase, que a mudança funciona e que os relatórios aprovados não mudaram. Os comandos são de PowerShell, na raiz do projeto, com o `venv` ativo. A implementação começa com a versão de fiscalização da São Domingos congelada e conferida em `C:\Users\rlazaro\Desktop\UHE_SAO_DOMINGOS_versao_fiscalizacao\` (FR-028); o LEIA-ME dela explica o uso.

## Pré-requisitos

- Dados brutos locais em `data/raw/`. A partir da fase B, a primeira execução de cada usina piloto baixa os conjuntos novos.
- Duas cópias de segurança no máximo (RT5).
- Suíte sem rede:

```powershell
$env:HTTP_PROXY = "http://127.0.0.1:9"; $env:HTTPS_PROXY = "http://127.0.0.1:9"; $env:PYTHONIOENCODING = "utf-8"
python -m pytest tests -q -p no:cacheprovider
```

## 1. Guarda dos relatórios aprovados (fim de toda fase; na fase A, depois de cada item)

Depois do item 1 da fase A, a guarda é um comando só ([cli-referencias.md](contracts/cli-referencias.md)). Ele refaz cada referência num espaço isolado, a partir da Coleta e do perfil congelados, e refaz também a Coleta para conferir o código dela:

```powershell
python -m src comparar --todas --coleta
$LASTEXITCODE
```

**Esperado**:
- código 0 e `Referências comparadas: <N>; com diferença: 0.` (SC-001);
- `data/usinas/`, `reports/` e `data/raw/` sem nenhuma mudança;
- com qualquer diferença (código 6), a fase não termina até o usuário aprovar a diferença ou o código ser corrigido. Uma diferença da Coleta causada por arquivo republicado pelo ONS aparece com o arquivo e a data, para o usuário decidir.

## 2. Início de cada fase

```powershell
python -m src copia-seguranca --motivo antes_fase_B
```

**Esperado**:
- a nova cópia tem `relatorios_referencia/`, conferida, e ficam duas cópias;
- os rascunhos das specs das etapas da fase (`ajustes-specs/`) estão aprovados pelo usuário antes de qualquer código (R26).

## 3. Fase A — fundação (US1)

### 3.1 Antes de tudo: a referência da São Domingos (R22)

Até o item 2 da fase A, nenhuma coleta com o portal no projeto principal. Na fiscalização de 14 a 16/10, usar a versão congelada, que tem os próprios dados.

```powershell
python -m src copia-seguranca --motivo antes_fase_A     # ainda com o código de hoje
python -m src comparar --usina sao_domingos --referencia _backup_2026-10-08_antes_ampliacao_tipos_de_geracao/linha_de_base
```

**Esperado**: código 0. O relatório atual é a referência aprovada.

Item 1 da fase A: `referencia`, `comparar --todas [--coleta]`, a Coleta no formato 2 (datas de obtenção e dicionário da EVT gravados pela Coleta) e os testes dos invariantes. A suíte inclui o teste que roda as etapas 2 a 5 com `data/raw/` vazio.

Item 2, a migração:

```powershell
python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"
python -m src comparar --usina sao_domingos --referencia _backup_2026-10-08_antes_ampliacao_tipos_de_geracao/linha_de_base
python -m src referencia --usina sao_domingos --data-geracao "07/10/2026 08:53" --aprovado-em "08/10/2026"
python -m src comparar --todas --coleta
```

**Esperado**:
- os dois `comparar` com código 0;
- `relatorios_referencia/sao_domingos/` com o relatório, o perfil congelado, a Coleta congelada (`coleta/`, com `datas_obtencao.csv` e `dicionario_evt.json`, sem `.bak`) e o `referencia.json`;
- `linha_de_base/` continua na cópia de 08/10/2026.

A partir daqui, até o congelamento do item 4, nenhum comando baixa dados: nem `usinas` nem a coleta de outra usina.

### 3.2 Correções P1 a P5, registro e perfil por tipo (item 3)

A cada correção:

```powershell
python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"
python -m src comparar --todas --coleta
```

**Esperado**:
- código 0 a cada correção;
- o perfil da São Domingos com só duas linhas novas (`tipo`, `modalidade`);
- a aba DICIONARIOS com os dez conjuntos de hoje.

Item 4: se o formato de algum arquivo da Coleta mudou, a referência é registrada de novo com o mesmo `referencia`, depois do `comparar` com código 0 e do commit da referência anterior pelo usuário. Só então os downloads ficam liberados.

### 3.3 Catálogo de MS e do Brasil ([cli-usinas.md](contracts/cli-usinas.md))

```powershell
python -m src usinas --estado MS
```

**Esperado**:
- 171 usinas no filtro: UHE 5, PCH 16, CGH 9, UTE 33, UFV 86 e 22 linhas de conjunto (contagem do cadastro de 09/10/2026; o ONS pode mudá-la);
- uma coluna de cobertura por conjunto de série do tipo (FR-003, SC-002);
- `data/catalogo/usinas.csv` com todas as linhas do cadastro do Brasil (6.017 em 09/10/2026), e `catalogo.json` com as datas e os arquivos usados (FR-004);
- com `--sem-portal`, o mesmo resultado, sem acesso à rede;
- `python -m src comparar --todas --coleta` com código 0: os downloads do catálogo não mexem na referência. Um arquivo republicado dentro do período da São Domingos aparece como diferença da Coleta, com a data de publicação, para o usuário decidir.

### 3.4 Rascunho do perfil ([cli-perfil.md](contracts/cli-perfil.md))

```powershell
Measure-Command { python -m src perfil --ceg UTE.GN.MS.027075-0.01 --slug william_arjona }
python -m src perfil --ceg UTE.GN.MS.027075-0.01 --slug william_arjona; $LASTEXITCODE
```

**Esperado**:
- **Primeira execução**: código 0 em menos de 1 minuto (SC-003). `usinas/william_arjona/perfil.toml` traz:
  - `situacao = "rascunho"`, `tipo = "UTE"`, `modalidade = "TIPO I"` e o id ONS `MSUTWI`;
  - a `[cobertura]` do catálogo, as cinco unidades ativas e o combustível, com a fonte;
  - os pendentes listados.
  - Os códigos de planejamento (34, 334 e 434) só entram a partir da fase B, com o despacho.
- **Segunda execução**: código 0, ou 6 com as diferenças listadas. O arquivo fica igual, byte a byte (FR-007).

### 3.5 Recusas

```powershell
python -m src coleta --usina william_arjona; $LASTEXITCODE       # ainda em rascunho
python -m src usinas --estado MS --tipo CGH                      # escolher uma CGH Tipo III
python -m src perfil --ceg <CEG da CGH>; $LASTEXITCODE
```

**Esperado**:
- **Rascunho**: código 4, com a lista dos pendentes, e nada gravado em `data/usinas/william_arjona/` (FR-008).
- **CGH Tipo III**: código 2, com a mensagem de que o ONS só publica o agregado e com o comando da carteira. Nenhuma pasta criada em `usinas/` (FR-009).

### 3.6 Relatório com as seções comuns

Depois de o fiscal conferir e completar o perfil da William Arjona (`situacao = "conferido"`):

```powershell
python -m src completo --usina william_arjona
```

**Esperado**:
- código 0;
- o `etapa.json` da Coleta mostra a série de referência "geracao" desde 10/07/2021;
- o relatório tem só as seções comuns (R14), sem energia vertida turbinável nem hidrologia (US1-4);
- as legendas citam o identificador da usina, e as notas listam o que não se aplica;
- `python -m src comparar --todas --coleta` com código 0.

## 4. Fase B — térmicas (US2)

```powershell
python -m src perfil --ceg UTE.GN.MS.027075-0.01 --slug william_arjona   # código 6: chaves despacho e cvu e os códigos de planejamento
python -m src completo --usina william_arjona --data-geracao "<data>"
```

**Esperado**:
- **Seções próprias de térmica**:
  - geração por motivo, por mês e por ano, com as parcelas, e a inflexibilidade programada e verificada;
  - atendimento ao despacho, com horas e energia abaixo e acima e os maiores desvios;
  - horas disponíveis sem despacho;
  - CVU × CMO por semana, por unidade de planejamento (gás e óleo, de 08/2021 a 02/2026), sem julgamento (US2-1 a US2-3).
- **Conferências**:
  - G3 e G4 registradas;
  - DISPF × horas refeito;
  - TEIFa e TEIP como não aplicáveis, se a usina continuar fora das taxas, com o motivo (US2-4, FR-019).
- **Usina fictícia de térmica sem geração**: constatação de usina disponível e não despachada, sem divisão por zero (US2-5).
- **Tempo** da execução com os dados locais, pelo `etapa.json`: até 15 minutos (SC-006).
- **Relatório piloto** (SC-004, SC-007): seção 8.
- **Aprovação**: depois da aprovação do usuário, `python -m src referencia --usina william_arjona --data-geracao "<data>" --aprovado-em "<data>"` (FR-029). Seção 1 com código 0.

## 5. Fase C — eólicas e solares (US3)

```powershell
python -m src completo --usina seriemas_1 --data-geracao "<data>"
python -m src completo --usina praia_formosa --data-geracao "<data>"
```

**Esperado**:
- **Seriemas 1**:
  - série de referência da usina desde 22/08/2026, com menos de 12 meses;
  - sazonalidade omitida, com o motivo nas notas (R17);
  - geração e fator de capacidade identificados como do Conj. Inocência 230 kV, com a composição, nunca divididos (US3-2);
  - energia cortada da usina por razão do conjunto;
  - conclusão sem as regras que pedem dado próprio que a usina não tem (C18, C19).
- **Praia Formosa**:
  - fator de capacidade desde 07/2009;
  - energia cortada só nas semi-horas restritas: da ordem de 181 GWh de 10/2021 a 10/2026, contra cerca de 350 GWh da diferença bruta (R12);
  - semi-horas com vento inválido fora da relação vento × geração e contadas (US3-3);
  - desvio médio e maiores desvios da programação (US3-4); G1 e G5 registradas.
- **Relatórios piloto**: seção 8.
- **Aprovação** das duas e `referencia` de cada uma. Seção 1, com `--coleta`, com código 0.

## 6. Fase D — PCH e CGH (US4)

```powershell
python -m src completo --usina bandeirante --data-geracao "<data>"
```

**Esperado**:
- geração do Conj. Chapadão por trecho de composição: com as cinco térmicas até 01/07/2025 e só as PCH depois, com os tipos de cada trecho;
- notas dizendo que o ONS não publica a geração da usina isolada (US4-1);
- disponibilidade e indicadores oficiais omitidos, com o motivo nas notas (US4-2);
- as linhas próprias sem valor contadas na qualidade dos dados;
- conclusão sem itens, com a frase de que não há base no nível da usina (R16);
- relatório piloto conferido como na seção 8; aprovação e `referencia`; seção 1 com código 0.

## 7. Fase E — carteira (US5) ([cli-carteira.md](contracts/cli-carteira.md))

```powershell
Measure-Command { python -m src carteira --estado MS --data-geracao "<data>" }
Select-String -Path reports\carteiras\ms\relatorio_carteira.md -Pattern "satisfat|cumpre"   # pega também "insatisfatório" e "descumpre"
python -m src carteira --tipo UTE
```

**Esperado**:
- `reports/carteiras/ms/`, com PDF, Markdown, planilha e figuras, em até 5 minutos (SC-006);
- **com resultado**: as quatro pilotos de MS (São Domingos, William Arjona, Seriemas 1 e Bandeirante). As demais usinas de MS vão para "sem resultado", cada uma com o motivo; as linhas de conjunto não contam como usina;
- ordenação por todos os itens de "possíveis problemas", depois de "pontos de atenção" (FR-027);
- panorama dos agregados de MS por tipo e por mês, identificado como agregado, com as horas ausentes e os valores Tipo III marcados como previsão (US5-2);
- nenhuma ocorrência na busca de termos de parecer (SC-007);
- `reports/carteiras/brasil_ute/` gerada pela carteira por tipo;
- nenhuma etapa executada: os `etapa.json` das usinas ficam iguais.

## 8. Conferência de cada relatório piloto (SC-004, SC-007)

Para cada usina piloto nova, antes da aprovação:

```powershell
$md = "reports\william_arjona\relatorio_analise_estatistica.md"
Select-String -Path $md -Pattern "satisfat|cumpre"                       # termos de parecer
Select-String -Path $md -Pattern "MSUHSD|CEUFM|MSSRI1|MSBDT|PRUHSD"      # identificadores das outras pilotos
```

**Esperado**:
- nenhuma ocorrência nas duas buscas. Na segunda, a lista traz os identificadores das outras pilotos, menos os da própria usina;
- todo número de conjunto ou de agregado identificado como tal nas legendas.

## 9. Fechamento (FR-030, SC-008)

```powershell
Get-ChildItem specs -Directory | Select-Object Name
Get-ChildItem README.md, specs, src, tests, usinas, .specify -Recurse -Include *.md, *.py, *.toml |
    Select-String -Pattern "006-ampliacao|spec 006|specs/006" -List
```

**Esperado**:
- `specs/` só com `001-coleta-dados` a `005-geracao-relatorio`, que já trazem as tabelas de aplicabilidade por tipo;
- nenhum arquivo do projeto cita a spec de mudança. As citações no código e nos testes foram trocadas pelas FR das specs das etapas. As cópias de segurança (`_backup_*`) guardam a spec 006 até a poda, e a SC-008 não vale para elas;
- o README descreve todos os tipos;
- `/speckit-converge` sem pendência;
- seção 1, com `--coleta`, com código 0 para as cinco referências.
