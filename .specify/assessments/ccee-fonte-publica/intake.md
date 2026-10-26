# Idea Intake: CCEE como fonte pública nova do pipeline

- **Slug**: ccee-fonte-publica
- **Created**: 2026-10-23
- **Source**: repo path `propostas/2026-10-23-melhorias-futuras.md` (item 2) e texto da sessão de 23/10/2026
- **Type**: new-capability

## Idea (as captured)

> Avaliação da CCEE como fonte pública nova do pipeline (item 2 de `propostas/2026-10-23-melhorias-futuras.md`; decisão do usuário de 22/10/2026 de avaliar pelo `/speckit-assess-intake` depois do fechamento da ampliação, confirmada em 23/10/2026 com "4. ok").
>
> Princípio do projeto dito pelo usuário em 23/10/2026: "esse projeto busca usar tudo e qualquer dado disponível pelos meios públicos".
>
> Para que serve: a geração medida da usina isolada onde o ONS só publica o conjunto ou o agregado; o maior ganho é para PCH e CGH em conjunto (piloto proposta: PCH Bandeirante), usinas Tipo III e UFV sem série própria no ONS.
>
> Conjuntos úteis já vistos no catálogo aberto da CCEE (`dadosabertos.ccee.org.br`, API do CKAN):
> - `geracao_horaria_usina`: geração horária por parcela de usina, desde 03/2024, sem o CEG;
> - `parcela_usina_montante_mensal`: mensal por usina, desde 2024, com o CEG, a geração, a garantia física e o MRE;
> - garantia física definida, por fonte;
> - CVU, sem o CEG;
> - não há conjunto de restrição de operação (constrained-off).
>
> Obstáculo conhecido: a CCEE bloqueia o download por script; ponto de partida é o usuário baixar um mês dos dois primeiros conjuntos para avaliar a ligação das parcelas com o CEG e com a usina do ONS.
>
> Depende da emenda 3.2.0 da constituição (princípio IV ampliado para fontes públicas, proposta em `propostas/2026-10-23-emenda-constituicao-3.2.0.md`, aguardando aprovação).

URLs citadas, não abertas nesta etapa: `https://dadosabertos.ccee.org.br` (host: dadosabertos.ccee.org.br, policy: não aberto na intake; host fora da lista segura, a abertura na pesquisa depende de confirmação do usuário).

## Restated

Usar os dados abertos da CCEE como segunda fonte pública da Coleta, principalmente a geração medida por usina, para analisar usinas que o ONS só publica em conjunto ou em agregado (PCH e CGH em conjunto, Tipo III, UFV sem série própria) e completar as demais com garantia física, MRE e CVU.

## Origin & Context

- **Raised by**: o usuário (inspetor da AGEMS responsável pelo projeto), em 22/10/2026, no fechamento da ampliação para todos os tipos de usina; confirmado em 23/10/2026.
- **Trigger**: a fase D (PCH e CGH em conjunto) mostrou que o ONS não publica a geração da usina isolada nessas modalidades; o relatório da PCH Bandeirante só pode mostrar o conjunto. Em 23/10/2026 o usuário declarou o princípio de usar todo dado disponível por meios públicos.

## First-Glance Unknowns

- [NEEDS CLARIFICATION: a ligação entre a parcela de usina da CCEE, o CEG da ANEEL e a usina ou o conjunto do ONS — `geracao_horaria_usina` não traz o CEG]
- [NEEDS CLARIFICATION: se o bloqueio de download por script é permanente, se a API do CKAN (datastore) permite a leitura por script e se os termos de uso da CCEE permitem a coleta automatizada]
- [NEEDS CLARIFICATION: a cobertura das usinas de MS — PCH e CGH em conjunto, Tipo III, UFV e as térmicas — e o período (a geração horária só desde 03/2024)]
- [NEEDS CLARIFICATION: o que a geração da CCEE mede (medição no ponto de conexão, por parcela, com perdas) e como ela se compara com a geração verificada do ONS nas usinas que as duas fontes cobrem, para a conferência entre fontes (princípio VI)]
- [NEEDS CLARIFICATION: as versões e as republicações dos conjuntos da CCEE (recontabilizações) e como a Coleta as guardaria (princípio IV)]
- [NEEDS CLARIFICATION: o nível do dado (parcela, usina, agente) frente ao princípio VIII]
- [NEEDS CLARIFICATION: a aprovação da emenda 3.2.0 da constituição, de que a entrada da CCEE no fluxo depende]
