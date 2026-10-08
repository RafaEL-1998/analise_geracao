# Quickstart: validação da reorganização (feature 009)

**Feature**: [spec.md](spec.md) · **Linha de comando**: [contracts/cli-etapas.md](contracts/cli-etapas.md) · **Perfil**: [contracts/perfil-usina.md](contracts/perfil-usina.md) · **Artefatos**: [data-model.md](data-model.md) (seções 3 e 4)

## Pré-requisitos

- PowerShell na raiz do projeto, com o `venv` ativo.
- Dados brutos em `data/raw/`. Nada precisa ser baixado: os cenários usam `--sem-portal`.
- Cópia `_backup_2026-10-07_antes_reorganizacao/`, com a linha de base do relatório em `linha_de_base/` (research R2). É gerada ao fim da fase 1, com a conclusão já aprovada e a data fixa `07/10/2026 08:53`.

## 1. Testes sem rede (SC-007)

```powershell
$env:HTTP_PROXY = "http://127.0.0.1:9"; $env:HTTPS_PROXY = "http://127.0.0.1:9"
python -m pytest tests -q
```

**Esperado**:
- a suíte é aprovada;
- existem testes de cada etapa, do perfil, do pré-requisito entre etapas, da poda das cópias e das versões, da varredura de literais e do fluxo completo da usina fictícia;
- nenhum arquivo de `data/`, `reports/` ou `usinas/` é alterado pelos testes.

## 2. Conclusão do relatório (SC-009), na fase 1, antes da reorganização

```powershell
python -m src.analyzer        # fluxo atual, ainda antes da reorganização
```

**Esperado**:
- **Lugar**: a seção "Conclusão" fica antes de "Notas metodológicas e limitações", no PDF, no Markdown e no sumário. No PDF, ela cabe em uma página.
- **Listas**: quatro, na ordem "Pontos de atenção", "Possíveis problemas", "A confirmar com o agente" e "A verificar em campo". Cada uma tem até cinco itens de uma frase, terminando com a seção de origem.
- **Unidade geradora**: a UG2 aparece em "Possíveis problemas", com os meses de limitação forçada de potência e a participação na TEIFa, e também nas listas de confirmação e de verificação.
- **Texto**: nenhum termo de avaliação de desempenho e nenhum texto de constatação repetido.
- **Planilha**: a aba `CONCLUSAO` traz todos os itens, e a aba `FONTES` a cobre.
- **Aprovação**: o usuário aprova o texto. Só então a linha de base é gerada.

## 3. Relatório da São Domingos igual ao de referência (SC-001)

```powershell
python -m src completo --usina sao_domingos --sem-portal --data-geracao "07/10/2026 08:53"
python -m src comparar --usina sao_domingos --referencia _backup_2026-10-07_antes_reorganizacao\linha_de_base
```

**Esperado**:
- todas as etapas terminam com 0;
- o `comparar` termina com 0: PDF, Markdown, CSV e as 8 figuras idênticos byte a byte; planilha (57 abas) idêntica célula a célula;
- os dados tratados em `data/usinas/sao_domingos/tratamento/` têm o mesmo conteúdo dos arquivos correspondentes de `data/processed/` (FR-011).

## 4. Etapas isoladas e pré-requisito (SC-002)

```powershell
python -m src relatorio --usina sao_domingos             # só o relatório, a partir das análises gravadas
python -m src tratamento --usina ficticia_sem_coleta     # perfil válido, sem coleta
echo $LASTEXITCODE
```

**Esperado**:
- **Relatório**: regerado sem refazer as etapas anteriores.
- **Tratamento sem coleta**:
  - sai com código 5 e uma mensagem que manda executar a coleta;
  - nada é gravado.
- **Reexecução de uma etapa**: as etapas seguintes ficam `desatualizada` no `etapa.json` e recusam as que dependem delas até serem refeitas.

## 5. Perfil (SC-005)

**Esperado**:
- um perfil sem `garantia_fisica_mwmed`, ou com potência unitária × unidades diferente da instalada, é recusado com código 4 e a lista dos problemas, antes da coleta;
- o teste de integração da usina fictícia (três unidades, Francis, identificadores próprios, dados sintéticos) gera um relatório completo sem nenhuma menção à São Domingos, e as faixas de afluência dizem "entre uma e três unidades".

## 6. Cópias de segurança (SC-006)

```powershell
python -m src copia-seguranca --motivo teste_quickstart
Get-ChildItem -Directory _backup_*
```

**Esperado**:
- no máximo duas pastas `_backup_*`, as mais recentes;
- a nova traz `copia.json`, conferido, `LEIA-ME.txt` e `conftest.py`;
- nenhuma cópia de 06/10/2026 ou antes.

## 7. Specs e constituição (SC-003 e SC-004)

```powershell
Get-ChildItem specs -Directory                                     # 001 a 005, uma por etapa
Select-String -Path .specify\memory\constitution.md -Pattern "SYNC IMPACT|Emenda|153|MSUHSD|São Domingos"
Select-String -Path specs\*\spec.md -Pattern "revisto pela spec|revisão de"
```

**Esperado**:
- cinco pastas de spec;
- nenhuma ocorrência na constituição;
- nenhuma remissão a revisões nas specs;
- `mapeamento-specs.md`, aprovado antes da remoção das specs antigas, com destino para 100 % dos itens em vigor.

## 8. Pasta do projeto (SC-008)

**Esperado**:
- cada exclusão ou movimentação feita consta do `inventario-limpeza.md` aprovado;
- os documentos de referência estão em `usinas/sao_domingos/documentos/` e `referencias/`;
- `data/raw/` está intacto;
- não há `.bak` soltos fora das pastas de dados das etapas.
