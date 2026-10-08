# Análise de Usinas Hidrelétricas com Dados Abertos do ONS

Pipeline em Python para uma usina hidrelétrica. Ele:

- coleta dez conjuntos do [Portal de Dados Abertos do ONS](https://dados.ons.org.br);
- trata e confere os dados;
- analisa a energia vertida turbinável (EVT), a disponibilidade, a operação programada e verificada e a hidrologia;
- gera um relatório de apoio à fiscalização, com PDF, Markdown, planilha e figuras.

Cada usina é descrita por um **perfil** (`usinas/<slug>/perfil.toml`). A primeira é a UHE São Domingos (MS), `usinas/sao_domingos/`.

O projeto segue o Spec-Driven Development (Spec Kit):

- a constituição fica em `.specify/memory/constitution.md`;
- cada etapa do fluxo tem uma spec em `specs/`.

Os resultados não são repetidos aqui, para não ficarem desatualizados. Veja `reports/<slug>/relatorio_analise_estatistica.pdf`, gerado a partir dos dados a cada execução.

---

## Fluxo de cinco etapas

**Coleta de dados → Tratamento de dados → Conferência → Análises → Geração do relatório**

| Etapa | Comando | O que faz | Grava em | Spec |
|---|---|---|---|---|
| 1. Coleta de dados | `coleta` | Consulta o catálogo do ONS e baixa só o que é novo ou mudou, guardando as versões anteriores e os dicionários de dados. Extrai a usina dos dez conjuntos pelos identificadores do perfil e audita cada arquivo lido. | `data/raw/` (compartilhado) e `data/usinas/<slug>/coleta/` | `specs/001-coleta-dados/` |
| 2. Tratamento de dados | `tratamento` | Padroniza tipos e horários e valida as regras R1 a R9: sinaliza os registros, sem descartar nenhum. Lista as ausências e monta as séries horárias e os indicadores. | `data/usinas/<slug>/tratamento/` | `specs/002-tratamento-dados/` |
| 3. Conferência | `conferencia` | Confere as fontes entre si: geração, disponibilidade, vazões com a hidrologia, DISPF com as horas por estado operativo, TEIFa e TEIP recalculadas, e cadastro. | `data/usinas/<slug>/conferencia/` | `specs/003-conferencia/` |
| 4. Análises | `analises` | Calcula indicadores, eventos de usina parada com EVT, perfis horários e faixas de afluência, e monta as constatações e a conclusão. | `data/usinas/<slug>/analises/` | `specs/004-analises/` |
| 5. Geração do relatório | `relatorio` | Gera as figuras (seaborn), o PDF, o Markdown e a planilha. | `reports/<slug>/` | `specs/005-geracao-relatorio/` |

Cada etapa:

- grava um `etapa.json` na sua pasta, com a situação, o código de saída, os arquivos gravados (com SHA-256) e o resumo da execução;
- só roda se a anterior estiver `concluida` para a mesma usina; refazer uma etapa marca as seguintes como `desatualizada`.

Só a Coleta acessa o portal do ONS.

### Conjuntos do ONS e identificação da usina

A usina é extraída de cada conjunto por um identificador e conferida por um segundo campo, ambos com os valores do perfil. As linhas em que só um dos dois confere (por exemplo, de usinas homônimas) não são extraídas; elas são contadas na auditoria da Coleta.

| Conjunto do ONS | Identificador de extração | Conferência |
|---|---|---|
| [Energia Vertida Turbinável](https://dados.ons.org.br/dataset/energia-vertida-turbinavel) | `cod_usina` | `nom_reservatorio` contém `nome_ons` |
| Indicadores de disponibilidade por unidade geradora, bases [mensal](https://dados.ons.org.br/dataset/ind_disponibilidade_fgeracao_uge_mensal) e [anual](https://dados.ons.org.br/dataset/ind_disponibilidade_fgeracao_uge_anual) | `ceg` | `id_usina` = `id_ons` |
| [Taxas TEIFa e TEIP](https://dados.ons.org.br/dataset/taxa_teif_teip) e [parâmetros das taxas](https://dados.ons.org.br/dataset/taxa_teif_teip_parametro) | `cod_ceg` = `ceg` | não há (os conjuntos não publicam o id ONS) |
| [Programação diária](https://dados.ons.org.br/dataset/programacao_diaria) | `cod_exibicaousina` = `cod_programacao` | `nom_usina` contém `nome_ons`, e estado |
| [Disponibilidade por usina](https://dados.ons.org.br/dataset/disponibilidade_usina) | `id_ons` | `ceg` e estado |
| [Dados hidrológicos horários](https://dados.ons.org.br/dataset/dados_hidrologicos_ho) | `cod_usina` | `nom_reservatorio` contém `nome_ons`, e `id_reservatorio` |
| [Geração por usina](https://dados.ons.org.br/dataset/geracao-usina-2) | `id_ons` | `ceg` e estado |
| [Modalidade das usinas](https://dados.ons.org.br/dataset/modalidade-usina) (cadastro) | `ceg` | `id_ons` e estado (divergência vai para a Conferência) |

Os dicionários de dados (PDF e JSON) dos dez conjuntos são obtidos a cada coleta e guardados em `_dicionarios/`, junto aos dados brutos.

---

## Instalação

Ambiente: Windows 10/11 com PowerShell e Python 3.11 ou mais recente. O projeto usa o 3.14.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Como executar

```powershell
# Fluxo completo, com consulta ao portal do ONS
python -m src completo --usina sao_domingos

# Fluxo completo sem internet, só com os arquivos já baixados
python -m src completo --usina sao_domingos --sem-portal

# Uma etapa de cada vez
python -m src coleta      --usina sao_domingos
python -m src tratamento  --usina sao_domingos
python -m src conferencia --usina sao_domingos
python -m src analises    --usina sao_domingos
python -m src relatorio   --usina sao_domingos
```

`completo` executa as cinco etapas na ordem e para na primeira que não terminar com código 0.

**Opções**

| Opção | Comandos | Efeito |
|---|---|---|
| `--usina <slug>` | etapas, `completo` e `comparar` | usina a analisar: nome da pasta em `usinas/` (obrigatório) |
| `--sem-portal` | `coleta` e `completo` | não consulta o portal; extrai só dos arquivos locais |
| `--forcar-download` | `coleta` e `completo` | baixa de novo todos os arquivos de dados |
| `--data-geracao "DD/MM/AAAA HH:MM"` | `relatorio` e `completo` | fixa a data de geração e torna o PDF reproduzível byte a byte |
| `--log-level {DEBUG,INFO,WARNING,ERROR}` | todos | nível de log de todos os módulos (padrão `INFO`); o log sai só na tela |

**Ferramentas**

```powershell
# Cópia de segurança do projeto (no máximo duas; a mais antiga sai depois de a nova ser conferida)
python -m src copia-seguranca --motivo antes_ajuste_x

# Compara o relatório atual da usina com o de outra pasta.
# PDF, Markdown, CSV e figuras são comparados byte a byte; a planilha, célula a célula.
python -m src comparar --usina sao_domingos --referencia <pasta>
```

**Códigos de saída**

| Código | Significado |
|---|---|
| 0 | sucesso (no `comparar`, nenhuma diferença) |
| 1 | erro: catálogo do ONS inacessível, dado que impede a etapa, falha de gravação (com o arquivo restaurado), erro inesperado ou interrupção |
| 2 | arquivo de dados não obtido ou não lido, ou usina sem registro na EVT ou no cadastro (Coleta); também opção inválida na linha de comando |
| 3 | conferência das vazões com a hidrologia abaixo da meta de 99 % (Conferência). A etapa fica `concluida`, mas o `completo` para |
| 4 | perfil da usina inválido; a mensagem lista os problemas |
| 5 | etapa anterior sem resultado concluído (ausente, com falha ou desatualizada); nada é gravado |
| 6 | o `comparar` encontrou diferenças |

Uma falha ao obter um dicionário de dados não muda o código de saída. Com `--sem-portal`, o fluxo completo da São Domingos leva cerca de 5 minutos.

---

## Estrutura de pastas

```text
.
├── src/                        código; ponto de entrada único: python -m src
│   ├── __main__.py             linha de comando
│   ├── pipeline.py             execução das etapas, etapa.json e pré-requisitos
│   ├── comum/                  perfil, caminhos, regras gerais, persistência, log, comparação e cópia de segurança
│   ├── coleta/                 1. Coleta de dados
│   ├── tratamento/             2. Tratamento de dados
│   ├── conferencia/            3. Conferência
│   ├── analises/               4. Análises
│   └── relatorio/              5. Geração do relatório
├── tests/                      testes sem rede: uma pasta por etapa, mais comum/, integracao/ e fixtures/
├── usinas/<slug>/
│   ├── perfil.toml             perfil da usina
│   └── documentos/             documentos da usina (fora do git)
├── data/                       dados (fora do git)
│   ├── raw/                    arquivos do ONS, compartilhados por todas as usinas, com manifestos,
│   │                           _versoes_anteriores/ e _dicionarios/
│   └── usinas/<slug>/          coleta/, tratamento/, conferencia/ e analises/, cada uma com o seu etapa.json
├── reports/<slug>/             relatorio_analise_estatistica.pdf e .md, perfil_estatistico_anual.xlsx e .csv,
│                               figures/ (8 figuras, 300 DPI) e etapa.json
├── specs/                      uma spec por etapa (001-coleta-dados a 005-geracao-relatorio)
├── .specify/                   constituição e modelos do Spec Kit
├── referencias/                documentos gerais de consulta (fora do git)
├── _backup_<data>_<motivo>/    cópias de segurança (no máximo duas; fora do git)
├── requirements.txt
└── README.md
```

---

## Perfil da usina

O perfil (`usinas/<slug>/perfil.toml`, em UTF-8) reúne tudo o que é próprio da usina. Use comentários `#` para registrar a origem de cada valor. As regras gerais, iguais para todas as usinas, ficam no código, em `src/comum/regras.py`: limiar de usina parada, tolerâncias, metas e limiares da conclusão.

| Seção | Campos |
|---|---|
| `[usina]` | `slug` (igual ao nome da pasta), `nome`, `nome_curto`, `estado` (UF), `inicio_operacao_comercial` (ano) |
| `[identificacao]` | `cod_usina`, `nome_ons` (em maiúsculas e sem acento, como nos conjuntos), `ceg`, `id_ons`, `cod_programacao`, `id_reservatorio` |
| `[parametros]` | `potencia_instalada_mw`, `unidades_geradoras`, `potencia_unitaria_mw`, `tipo_turbina`, `engolimento_nominal_ug_m3s`, `garantia_fisica_mwmed`, `ip_referencia`, `teif_referencia`, `queda_bruta_m`, `perda_hidraulica_m`, `rendimento_turbina_gerador`, `vazao_remanescente_m3s` |
| `[parametros.fontes]` | `geral` e `garantia_fisica` (obrigatórios); `inicio_operacao_comercial` e `ip_teif` (opcionais) |
| `[analises]` | `vertimento_minimo_m3s` (0 se não houver patamar contínuo), `faixas_geracao_mw` (crescentes, entre a usina parada e a plena carga); `descricao_vertimento_minimo` (opcional) |
| `[analises.fontes]` | `vertimento_minimo` (opcional) |
| `[textos]` | `ressalva_volume_util` (opcional) |

Um campo opcional ausente tira do relatório o trecho correspondente.

O perfil é conferido antes de qualquer etapa: campos faltantes, tipos, faixas e coerência, como potência unitária × número de unidades = potência instalada. Um perfil inválido termina com código 4 e a lista de todos os problemas.

### Como incluir uma usina

1. **Crie o perfil.** Crie `usinas/<slug>/` (slug com letras minúsculas, algarismos e `_`) e copie `usinas/sao_domingos/perfil.toml` como modelo.
2. **Preencha os identificadores.** Procure a usina nos arquivos do ONS:

   | Campo | Onde obter |
   |---|---|
   | `ceg`, `id_ons`, `estado` | conjunto Modalidade das usinas (`MODALIDADE_USINA.csv`), colunas `ceg`, `id_ons` e `id_estado`. Procure pelo nome e confira o tipo (UHE) e o estado: há usinas homônimas |
   | `cod_usina`, `nome_ons` | conjunto Energia Vertida Turbinável, colunas `cod_usina` e `nom_reservatorio` |
   | `id_reservatorio` | conjunto Dados hidrológicos horários, coluna `id_reservatorio`, na linha do mesmo `cod_usina` |
   | `cod_programacao` | conjunto Programação diária, coluna `cod_exibicaousina`, na linha da usina (`nom_usina` e `id_estado`) |

3. **Preencha os parâmetros técnicos**, cada um com a fonte em `[parametros.fontes]`:
   - potência, unidades, turbina e engolimento nominal: atos de outorga da ANEEL e relatórios de fiscalização;
   - garantia física: valor vigente na ANEEL ou em portaria do MME;
   - IP e TEIF de referência: cálculo da garantia física;
   - queda, perda hidráulica e rendimento: projeto ou relatórios da usina;
   - vazão remanescente: outorga ou licença ambiental.
4. **Execute o fluxo**: `python -m src completo --usina <slug>`. Os arquivos do ONS já baixados em `data/raw/` para outra usina são reaproveitados.
5. **Confira a auditoria de identificação** em `data/usinas/<slug>/coleta/`:
   - `auditoria_*.csv`: por arquivo, as linhas da usina e as que conferem só pelo identificador ou só pela conferência (`linhas_so_identificador` e `linhas_so_conferencia`; na EVT, `registros_codigo_sem_nome` e `registros_nome_sem_codigo`). Contagens altas indicam identificador errado no perfil ou mudança de cadastro no ONS;
   - `cadastro_ficha.csv`: a ficha da usina no cadastro do ONS, com os homônimos contados;
   - divergências entre a ficha e o perfil (id ONS, estado, potência) aparecem na Conferência e no relatório.

---

## Cópias de segurança e versões

- **Cópias do projeto**: `python -m src copia-seguranca --motivo <texto>` cria `_backup_<AAAA-MM-DD>_<motivo>/`.
  - Conteúdo: código, testes, specs, relatórios, Spec Kit, perfis, README e `requirements.txt`, com `copia.json` (SHA-256 de cada arquivo), `LEIA-ME.txt` e um `conftest.py` que impede a coleta pelo pytest.
  - A nova cópia é conferida, e só então as mais antigas são excluídas, até ficarem **no máximo duas**.
  - Dados brutos, dados das etapas e documentos de referência ficam fora.
- **Versões anteriores dos arquivos do ONS**: quando o ONS republica um arquivo com conteúdo diferente, a versão anterior vai para `_versoes_anteriores/`, na pasta do conjunto.
  - Ficam **no máximo duas por arquivo**, as mais recentes.
  - As excluídas são registradas no manifesto (`_manifesto_ons.json`, `versoes_excluidas`).
  - O mesmo vale para os dicionários de dados.
- **Cópia `.bak`**: só nos arquivos de dados da Coleta e do Tratamento (`data/usinas/<slug>/coleta/` e `tratamento/`), com a versão imediatamente anterior.
  - Conteúdo idêntico não é regravado.
  - A gravação é conferida no disco e, em falha, o arquivo volta ao que era.
  - Conferência, Análises e relatórios não têm `.bak`: são refeitos a partir dos dados.

---

## Testes

```powershell
python -m pytest tests
```

Os testes não acessam a rede. Eles cobrem:

- cada etapa;
- o perfil e o pré-requisito entre etapas;
- a persistência, as cópias e as versões;
- a conformidade com a constituição: figuras em seaborn, nível de log único, ponto de entrada único, dependências;
- a ausência de valores de usina no código;
- o fluxo completo de uma usina fictícia de três unidades (`tests/fixtures/usina_ficticia/`).

Para conferir que o relatório não mudou depois de um ajuste no código, gere-o com `--data-geracao` igual ao da referência e use `python -m src comparar`.

---

## Metodologia resumida

- **Atualização**: um arquivo local só é reaproveitado se corresponder à versão publicada, pela data de publicação e pelo tamanho registrados no manifesto.
- **Validação**: as regras são aplicadas no Tratamento; os registros sinalizados são mantidos nos totais.
  - R1 a R5 conferem a consistência interna das grandezas do ONS: não negatividade e identidades de cálculo.
  - R6 a R9 conferem a plausibilidade física frente aos parâmetros do perfil: limites de potência e vazão, geração acima da disponibilidade, faixa de produtividade e geração sem vazão turbinada.
- **Horários**: a EVT usa a hora de início. Nos dados hidrológicos, a hora de fim é convertida para a de início; a última hora do dia vem às 23:59. Ausências são listadas e nunca interpoladas.
- **Indicadores oficiais**:
  - o DISPF da usina é a média das unidades, ponderada pela potência e pelas horas;
  - as horas por estado operativo são conferidas pela identidade HP = HS + HRD + HDP + HDF + HDCE + HEDP + HEDF;
  - TEIFa = Σ(HDF + HEDF) ÷ Σ(HP − HDP − HEDP) e TEIP = Σ(HDP + HEDP) ÷ ΣHP, em janela de 60 meses. Assim recalculadas, reproduzem as taxas publicadas e podem ser decompostas por unidade e por parcela.
- **Usina parada**: geração ≤ 1 MW. As horas paradas são classificadas:
  - pela EVT;
  - pela programação diária do ONS (programação ≤ 1 MW ou > 1 MW; desvio quando a usina está parada com programação > 5 MW);
  - pela sincronização das unidades.
- **Hidrologia**:
  - as horas com EVT são classificadas pela afluência em relação ao engolimento de uma unidade e ao da usina;
  - o perfil por hora do dia compara os dias com parada com EVT e os demais;
  - um valor sinalizado (H1 a H4) é excluído só no campo afetado.
- **Conclusão**: as regras C1 a C11, com limiares gerais, montam quatro listas: pontos de atenção, possíveis problemas, a confirmar com o agente e a verificar em campo. Elas falam em indícios, sem afirmar causa nem dar parecer de desempenho.
- **Limitações**:
  - a disponibilidade declarada e o fator de capacidade são aproximações a partir do conjunto de EVT;
  - os dados hidrológicos são informados pelos agentes e não são consistidos pelo ONS;
  - nenhum conjunto aberto do ONS informa a causa do vertimento, das reduções de geração ou dos desligamentos, nem os eventos individuais de desligamento.
