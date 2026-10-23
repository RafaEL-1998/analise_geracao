# Melhorias futuras: CCEE e pendências do fechamento da ampliação

**Situação**: lista para decisão do usuário (ainda não é spec) · **Data**: 23/10/2026

Itens anotados pelo usuário em 23/10/2026, no fechamento da ampliação para todos os tipos de usina. As specs das etapas descrevem o código como ele está hoje; cada item abaixo, quando for feito, começa por uma spec (ou pela revisão da spec da etapa) aprovada antes do código, como manda a constituição.

## 1. Avaliação da CCEE como fonte nova

- **Decisão do usuário (22/10/2026)**: avaliar depois do fechamento da ampliação, pelo `/speckit-assess-intake`. Usar a CCEE pede uma emenda do princípio IV da constituição, que hoje limita a coleta aos dados abertos do ONS.
- **Para que serve**: a geração medida da usina isolada onde o ONS só publica o conjunto ou o agregado. O maior ganho é para PCH e CGH em conjunto (a PCH Bandeirante, piloto proposta), usinas Tipo III e UFV sem série própria no ONS.
- **Conjuntos úteis do catálogo aberto da CCEE** (`dadosabertos.ccee.org.br`, lido pela API do CKAN):
  - `geracao_horaria_usina`: geração horária por parcela de usina, desde 03/2024, sem o CEG;
  - `parcela_usina_montante_mensal`: mensal por usina, desde 2024, com o CEG, a geração, a garantia física e o MRE;
  - garantia física definida, por fonte;
  - CVU, sem o CEG.
  - Não há conjunto de restrição de operação (constrained-off).
- **Ponto de partida**: o usuário baixa um mês dos dois primeiros conjuntos (a CCEE bloqueia o download por script) para avaliar a ligação das parcelas com o CEG e com a usina do ONS.

## 2. Seção "Conferência da geração entre fontes" nas usinas sem EVT

- **Hoje**: a seção estava prevista no relatório das usinas sem EVT, mas nunca foi gerada. Ela aparece na tabela das seções omitidas com o motivo "seção ainda não gerada pelo pipeline", e os resultados das conferências G1 a G5 ficam só nas legendas das tabelas e figuras e nas abas `CONF_*` da planilha.
- **O que fazer**: decidir se a seção é gerada (com as conferências da geração por fonte, como a seção equivalente das hidrelétricas com EVT) ou se sai da lista de seções.
- **Efeito**: muda os relatórios aprovados da William Arjona, da Seriemas 1, da Praia Formosa e da Bandeirante, que precisam ser aprovados e registrados de novo.

## 3. Ausências e auditoria da restrição por razão

- **Hoje**: o Tratamento grava a série semi-horária da restrição com a razão, mas não grava as ausências nem a auditoria que o rascunho aprovado previa. A chave `auditoria_restricao_razao` existe em `src/comum/caminhos.py`, mas o arquivo nunca é gravado. Repetições da mesma semi-hora são resolvidas sem contagem.
- **O que fazer**: gravar as ausências e a auditoria da restrição por razão como as dos outros conjuntos (contagens e mensagem), nas eólicas e solares.
- **Efeito**: arquivos novos no Tratamento; o relatório não deve mudar, salvo se a qualidade dos dados passar a citar essas ausências.

## 4. Ligação dos códigos de programação no catálogo

- **Hoje**: o catálogo só liga à usina o código de programação igual ao id ONS ou com o prefixo do conjunto. Ficam de fora o da São Domingos (`PRUHSD`, id ONS `MSUHSD`) e dois da William Arjona (`MSUTWI - 334` e `MSUTWI - 434`, até 11/02/2026). O catálogo mostra a programação dessas usinas como "ausente".
- **Efeito hoje**: os relatórios não são afetados, porque o perfil traz os códigos certos. O `perfil` da São Domingos devolve o código 6 (perfil diferente do catálogo em `cobertura.programacao`), e o rascunho de uma usina nova com código assim vem sem o código e com a programação "ausente".
- **O que fazer**: ampliar a regra de ligação (por exemplo, pelo nome publicado e pelo estado, ou pelo código com sufixo) e conferir as usinas de MS antes de mudar.
