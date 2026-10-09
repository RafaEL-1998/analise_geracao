# Proposta de escopo: relatórios de desempenho para todos os tipos de geração com dados do ONS

**Situação**: proposta para decisão do usuário (ainda não é spec) · **Data**: 08/10/2026

## 1. Objetivo

Transformar o projeto, hoje restrito a usinas hidrelétricas, numa ferramenta que:

- baixa os dados abertos do ONS;
- gera, para qualquer usina que esses dados cubram, um relatório estatístico de desempenho no padrão do relatório da UHE São Domingos: térmicas, nucleares, hidrelétricas (UHE, PCH, CGH), eólicas e solares;
- mostra também os limites da geração distribuída.

O relatório da São Domingos fica como está e serve de garantia: cada fase só termina quando o `comparar` com a referência der "Nenhuma diferença".

## 2. O que os dados do ONS permitem, por tipo de usina

O ONS publica dados por usina individual só para quem tem relacionamento direto com ele:

- **Tipo I, II-A e II-B**: dados por usina individual.
- **Tipo II-C** (conjunto de usinas): a maior parte das séries vem por conjunto.
- **Tipo III e geração distribuída**: o ONS publica só agregados.

Contagens: cadastro do ONS (Modalidade das usinas) e geração de setembro de 2026.

| Tipo | Usinas no cadastro (Brasil / MS) | Dados por usina no ONS | Conjuntos próprios do tipo | O que o relatório pode responder |
|---|---|---|---|---|
| **UHE** | 210 / 5 | completos (Tipo I, II-A, II-B; cerca de 160 usinas) | Energia Vertida Turbinável, Dados hidrológicos horários | o que já fazemos: EVT, usina parada, afluência, indisponibilidade por unidade |
| **UTE e UTN** (térmica e nuclear) | 617 + 3 / 33 | bons: geração, disponibilidade, DISPF e TEIFa/TEIP (cerca de 90 UTE), programação | Geração térmica por motivo de despacho (`geracao-termica-despacho-2`), CVU das térmicas (`cvu-usitermica`) | atendimento ao despacho, geração por motivo (mérito, inflexibilidade, restrição elétrica…), indisponibilidade forçada por unidade, CVU contra CMO, disponível sem despacho |
| **EOL** (eólica) | 1.489 / 0 | por usina dentro do conjunto, desde 2021; geração e fator de capacidade por conjunto | Restrição por constrained-off com detalhe por usina (`restricao_coff_eolica_detail`: geração verificada e estimada, vento), Fator de capacidade (`fator-capacidade-2`), Programação × previsão | fator de capacidade, energia cortada (curtailment) e motivo, vento, aderência à programação |
| **UFV** (solar) | 2.701 / 86 (+22 conjuntos) | idem eólica; restrição por usina desde 2023 | Restrição por constrained-off fotovoltaica com detalhe por usina, Fator de capacidade | idem eólica, com irradiância no lugar do vento |
| **PCH** | 561 / 16 | poucas: só as que estão em conjunto (Tipo II-C); a maioria é Tipo III | — | só no nível do conjunto; para a usina isolada faltam dados no ONS |
| **CGH** | 366 / 9 | nenhuma: todas Tipo III | — | não há dado por usina no ONS |
| **GD** (micro e minigeração distribuída) | — | nenhuma: só o total "Pequenas Usinas (MMGD)" por subsistema (6,7 TWh em set/2026) | — | só o panorama agregado; a usina individual está nos dados da ANEEL, não do ONS |

**Indicadores oficiais por unidade (DISPF, TEIFa/TEIP)**: existem para UHE (156 usinas), UTE (87 a 95) e UTN (2). Não existem para eólica, solar, PCH e CGH Tipo III.

**Exemplo (UTE William Arjona, Campo Grande)**: aparece em 8 dos 10 conjuntos que o projeto já baixa. Os identificadores são CEG `UTE.GN.MS.027075-0.01`, id ONS `MSUTWI`, Tipo I, 177 MW, a gás. É a candidata natural a usina piloto das térmicas.

## 3. O que muda no projeto

**Fica como está (núcleo já pronto)**:
- as cinco etapas;
- coleta com catálogo, versões e dicionários;
- gravação segura e cópias de segurança;
- perfil da usina;
- conferências entre fontes e `comparar`;
- testes sem rede.

**Muda**:

1. **Perfil com o tipo da usina**: os campos próprios de cada tipo passam a valer conforme o tipo (engolimento e queda só para hidrelétrica; combustível e CVU para térmica; e assim por diante).
2. **Catálogo de usinas e perfil automático**:
   - `python -m src usinas --estado MS --tipo UTE` lista as usinas e diz quais conjuntos do ONS cobrem cada uma;
   - `python -m src perfil --ceg <CEG>` monta o rascunho do perfil a partir do cadastro.
   - O fiscal só confere e completa os parâmetros com a fonte.
3. **Base do período pela geração**: hoje a EVT define o período e a coleta para se a usina não está nela. Passa a valer a série de geração, ou a série própria do tipo.
4. **Conjuntos novos na coleta**, declarados num registro único (identificador de extração e conferência de cada um, como hoje):
   - geração térmica por motivo de despacho, CVU, CMO semanal;
   - fator de capacidade;
   - restrições por constrained-off (eólica e solar, com detalhe por usina);
   - composição dos conjuntos de usinas (`usina_conjunto`);
   - capacidade de geração.
5. **Análises e relatório em duas camadas**:
   - **seções comuns a todos os tipos**: identificação e cadastro, geração, disponibilidade, indicadores oficiais quando houver, programação, conferências, qualidade dos dados, conclusão;
   - **seções próprias de cada tipo**: EVT e hidrologia (UHE); despacho e custo (UTE); vento ou irradiância e curtailment (EOL, UFV).
   - A conclusão segue regras declaradas por tipo, como as C1 a C11.
6. **Relatório de carteira** (fase final): ranking e quadro comparativo das usinas de um estado ou tipo. É útil para escolher onde fiscalizar.

## 4. Fases sugeridas

| Fase | Entrega | Usina de validação |
|---|---|---|
| A. Fundação multitipo | correções P1 a P5 da Coleta; perfil com tipo; catálogo de usinas e perfil automático; período pela geração; seções comuns parametrizadas | São Domingos sem nenhuma diferença; uma térmica com as seções comuns |
| B. Térmicas e nucleares | despacho por motivo, inflexibilidade, CVU contra CMO, indisponibilidade forçada por unidade, conclusão de térmica | UTE William Arjona (MS) |
| C. Eólicas e solares | fator de capacidade, curtailment e motivo, vento ou irradiância, aderência à programação, conclusão própria | uma UFV de conjunto em MS e uma eólica do Nordeste |
| D. PCH e CGH | relatório no nível do conjunto (Tipo II-C) e aviso claro dos limites do Tipo III | uma PCH de conjunto em MS |
| E. Carteira | relatório por estado ou tipo, com ranking de indícios | MS completo |
| F. Fora do ONS (avaliar) | GD e PCH/CGH Tipo III com dados da ANEEL | a decidir |

Cada fase segue o Spec Kit: spec da etapa afetada, plano, tarefas, implementação, convergência e cópia de segurança antes.

## 5. Governança

- **Constituição 3.0.0** (MAJOR): o escopo muda de "usina hidrelétrica" para "usina de qualquer tipo coberta pelos dados abertos do ONS". O princípio III (uma usina por execução, definida pelo perfil) fica; o relatório de carteira entraria como regra nova na fase E.
- **Specs**: não nasce spec nova por tipo. As cinco specs por etapa ganham requisitos por tipo, porque a constituição só admite spec nova para uma etapa nova. Os catálogos de conjuntos e de seções passam a ter uma coluna "tipos de usina".
- **Proteção do que já está pronto**: antes de cada fase, cópia de segurança. Ao fim de cada fase, `comparar` da São Domingos com `_backup_2026-10-08_antes_ampliacao_tipos_de_geracao/linha_de_base` sem diferença.

## 6. Riscos e limites

- **Granularidade**: eólicas e solares quase sempre estão em conjuntos. Parte dos números será do conjunto, não da usina, e o relatório precisa dizer isso.
- **Volume de dados**:
  - os conjuntos de restrição são semi-horários, por usina, desde 2021;
  - a coleta precisa baixar só o período da usina, como já faz com os demais conjuntos.
- **Causas**: como hoje, os dados abertos não trazem a causa de paradas e restrições; o relatório aponta indícios.
- **GD e Tipo III**: fora do alcance do ONS. Prometer relatório por usina para esses casos exigiria outra fonte (ANEEL), com outras regras de coleta.

## 7. Decisões que preciso do usuário para começar

1. **Fases**: a ordem A → B → C → D → E está boa? A fase F (fontes da ANEEL) entra no escopo ou fica de fora?
2. **Usinas piloto**: William Arjona para as térmicas; qual UFV e qual PCH de MS para as fases C e D?
3. **Quando começar**: recomendo a fase A depois da fiscalização de 14 a 16/10, para não mexer no fluxo durante a preparação. A proposta da constituição 3.0.0 e a spec da fase A podem ser escritas antes, sem tocar no código.
