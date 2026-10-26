# Homologação, lote 1: 52 usinas rodadas sem conferência humana

**Situação**: resultado para decisão do usuário · **Data**: 26/10/2026 · **Código**: o de hoje, sem mudança

## Como foi feito

- **Usinas**: as 28 de MS com série própria ou em conjunto no catálogo (menos as cinco referências) e 24 do resto do Brasil, a de maior potência de cada tipo e situação: UHE com e sem EVT, UTE, UTN, EOL e UFV próprias e em conjunto, e as únicas três PCH com série própria.
- **Perfil**: o rascunho do comando `perfil`, aceito só com os dados do ONS, sem conferência: os pendentes ficaram vazios e a fonte dos parâmetros recebeu o texto que o usuário usou na UTE William Arjona. Os relatórios não servem para uso na fiscalização.
- **Execução**: `completo` com o portal, uma usina por vez, num espaço isolado (`usinas/`, `data/usinas/` e `reports/` do projeto não foram tocados); os brutos baixados ficaram no `data/raw/` compartilhado.

## Resultado

| Situação | Usinas |
|---|---|
| Relatório completo e resumo executivo gerados | **30** |
| Perfil recusado antes da coleta | 13 |
| Coleta recusada: sem série de referência | 9 |
| Erro inesperado (exceção ou travamento) | **0** |

Toda usina com o perfil válido e com série de referência gerou o relatório (30 de 30), em 1 a 3 minutos cada.

| Grupo | Relatórios / usinas |
|---|---|
| UFV com série própria (MS e Brasil) | 18 / 18 |
| EOL com série própria | 3 / 3 |
| UTE com série de geração | 5 / 7 (Três Lagoas e Portocém I recusadas no perfil) |
| PCH | 5 / 7 (as duas sem série de referência) |
| UHE | 0 / 7 |
| UTN | 0 / 2 |
| EOL e UFV em conjunto | 0 / 2 (cadastro incompleto) |
| UTE sem série de geração | 0 / 7 |

## Achados, em ordem de impacto

1. **UHE sem EVT recusada pelos campos da trilha da EVT** (provável bug; Canastra e Pimental). A conferência do perfil exige de toda UHE os 11 campos da trilha da EVT (engolimento, queda, perdas, rendimento, tipo de turbina, vazão remanescente, garantia física, IP e TEIF de referência, vertimento mínimo e faixas de geração), mas a UHE sem EVT segue a trilha comum, que não usa esses campos; a PCH, na mesma trilha, roda sem eles.
2. **UHE com EVT depende de parâmetros que o ONS não publica** (limite do desenho; Tucuruí, Itaipu, Xingó, Ilha Solteira). Os mesmos 11 campos são exigidos e usados na trilha da EVT. São 157 UHE com EVT no Brasil: é a maior lacuna de cobertura. Caminhos: o fiscal completar com os documentos da ANEEL ou do agente, como na São Domingos, ou a trilha da EVT rodar sem eles, omitindo o que depende deles (princípio II).
3. **Programação exigida mesmo sem cobertura** (provável bug; Três Lagoas, Angra I, Angra II). O perfil exige `identificacao.cod_programacao` mesmo com a programação "ausente" na cobertura. Junto, a ligação dos códigos do catálogo (melhoria 5) não acha os códigos publicados como "MSTLA - 618" (Três Lagoas, id ONS MSUTLG).
4. **Usina só com a programação passa pelo rascunho e é recusada na Coleta** (provável bug; Amandina II, Costa Rica, Fibria MS, Fibria MS-II, Iaco Agrícola, Suzano RRP1, Bracell, PCH São Lourenço-MT, PCH Cabeça de Boi). O catálogo conta a programação para classificar a usina como "própria" ou "em conjunto", e o comando `perfil` grava o rascunho; a Coleta recusa, com mensagem clara, por falta de série de referência. O rascunho deveria recusar já (código 2), como faz com a cobertura ausente. Efeito colateral: os números de cobertura do catálogo (1.911 usinas "próprias") contam usinas sem série de geração.
5. **Nota de granularidade errada** (bug de conteúdo; quatro relatórios: PCH Eng. E. J. Dreher, PCH Eng. Henrique Kotzian, UTE Eldorado, UTE Santa Luzia I). Na usina que pertence a um conjunto e tem série própria, as notas dizem que "o ONS publica a geração do conjunto … (), e não a da usina isolada", com o identificador vazio, o que contradiz a série de referência da própria usina.
6. **Cadastro incompleto no ONS** (dado; Portocém I, nova; UHE Anta; EOL Cajuína C23; UFV Lins 03). Faltam potência, unidades ou início da operação na Capacidade de geração: o fiscal precisa completar.
7. **"-0,0" numa tabela** (cosmético; as três PCH do conjunto de Chapadão e a referência aprovada da PCH Bandeirante, jan/2025 e ago/2025). Zero negativo depois do arredondamento; corrigir muda a referência da Bandeirante.
8. **Ruído no log** (operação): cerca de 730 avisos por execução, um por arquivo diário da programação ("linhas só com a conferência"), que escondem os avisos que importam.
9. **Relatório sem conclusão** (limite; PCH Dreher e Kotzian, UTE Eldorado e Santa Luzia I): sem Disponibilidade por usina nem indicadores do ONS no nível da usina, nenhuma regra da conclusão se aplica; o relatório diz isso, mas fica com 8 seções e 11 páginas.

10. **Unidade com letra no nome** (bug, achado depois da correção do achado 3; UTE Três Lagoas). As unidades a ciclo combinado são publicadas como "1A", "1B", "2A", "2B", "1C" e "2C"; a leitura do número da unidade só aceita algarismos, as 16 linhas ficam sem unidade, as tabelas por unidade juntam as unidades e a regra C10 da conclusão quebra (`int(NaN)`). É o primeiro erro inesperado da homologação.

## Andamento das correções

- 26/10/2026, `programacao-sem-cobertura` (achado 3): aplicada; Angra I e Angra II geram o relatório; Três Lagoas passa do perfil e para no achado 10. Referências sem diferença.

## Próximos passos propostos

- Achados 1, 3, 4, 5 e 7: uma avaliação de bug cada (`/speckit-bug-assess`), com a correção pela spec da etapa e a aprovação do usuário antes do código.
- Achado 2: avaliação de melhoria (rodar a trilha da EVT sem os parâmetros técnicos, ou um caminho para completá-los com fonte pública da ANEEL).
- Achado 8: junto com a correção do achado 3 ou como melhoria de operação.
- Depois das correções: repetir este lote (o mesmo, para comparar) e medir de novo.

Arquivos da execução (fora do projeto): lista, scripts, logs, resultados por usina e os 30 relatórios em `scratchpad/homologacao/` da sessão de 26/10/2026.
