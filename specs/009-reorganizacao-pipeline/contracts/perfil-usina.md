# Contract: Perfil da Usina

**Feature**: `009-reorganizacao-pipeline` | **Date**: 2026-10-07 | Campos e validação: [data-model.md](../data-model.md) (seção 2) · Decisões: [research.md](../research.md) (R5 e R6)

## Local e formato

- **Arquivo**: `usinas/<slug>/perfil.toml`, em UTF-8, no formato TOML.
- **Pasta da usina**: guarda o perfil e os documentos de referência da usina (`usinas/<slug>/documentos/`, fora do git).
- **Comentários**: começam com `#` e servem para registrar de onde veio cada valor.

## Perfil da São Domingos (referência)

```toml
# Perfil da UHE São Domingos (MS). Valores de identificação conferidos nos conjuntos do ONS;
# parâmetros técnicos do RF 0009/2017-AGEPAN-SFG, exceto a garantia física (ANEEL).
# Homônimos excluídos pelos identificadores: PCH São Domingos I e II (GO), CGH São Domingos (SC),
# CGH São Domingos do Prata (RS), UTE São Domingos (SP), eólicas e solares São Domingos (RN, BA).

[usina]
slug = "sao_domingos"
nome = "UHE São Domingos"
estado = "MS"
inicio_operacao_comercial = 2013

[identificacao]
cod_usina = 153                      # Energia Vertida Turbinável e Dados hidrológicos horários
nome_ons = "SAO DOMINGOS"            # nome da usina e do reservatório nos conjuntos (conferência)
ceg = "UHE.PH.MS.028761-0.01"        # indicadores, TEIFa/TEIP, geração, disponibilidade e cadastro
id_ons = "MSUHSD"                    # geração, disponibilidade e cadastro
cod_programacao = "PRUHSD"           # Programação diária (código de exibição)
id_reservatorio = "PNUHSD"           # Dados hidrológicos horários (conferência)

[parametros]
potencia_instalada_mw = 48.0
unidades_geradoras = 2
potencia_unitaria_mw = 24.0
tipo_turbina = "Kaplan de eixo vertical"
engolimento_nominal_ug_m3s = 81.5
garantia_fisica_mwmed = 36.4
ip_referencia = 0.06861
teif_referencia = 0.02333
queda_bruta_m = 35.24
perda_hidraulica_m = 0.747
rendimento_turbina_gerador = 0.9053
vazao_remanescente_m3s = 4.78

[parametros.fontes]
geral = "RF 0009/2017-AGEPAN-SFG, Tabelas 1 a 3"
garantia_fisica = "ANEEL, valor vigente consultado em 02/10/2026"

[analises]
vertimento_minimo_m3s = 6.0          # patamar contínuo de vertimento da série (0 se não houver)
faixas_geracao_mw = [10.0, 20.0, 30.0, 40.0]   # faixas intermediárias da análise de EVT por nível de geração
```

## Uso de cada identificador

A regra de qual coluna de cada conjunto recebe cada valor é geral e fica no código da coleta. O perfil só informa os valores.

| Conjunto do ONS | Identificador de extração | Conferência |
|---|---|---|
| Energia Vertida Turbinável | `cod_usina` | `nome_ons` contido no nome do reservatório |
| Indicadores por unidade geradora; Taxas TEIFa e TEIP (e parâmetros) | `ceg` | `id_ons` |
| Programação diária | `cod_programacao` | `nome_ons` e `estado` |
| Geração por usina | `id_ons` | `ceg` e `estado` |
| Disponibilidade por usina | `id_ons` | `ceg` e `estado` |
| Dados hidrológicos horários | `cod_usina` | `nome_ons` e `id_reservatorio` |
| Modalidade das usinas (cadastro) | `ceg` | `id_ons` e `estado` |

## Validação

O perfil é validado ao iniciar qualquer comando com `--usina`. Um perfil com problema é recusado com código 4 e a lista completa dos problemas. As regras de cada campo estão no data-model (seção 2). As principais:

- todos os campos acima são obrigatórios;
- unidades ≥ 1, e a potência unitária × unidades é igual à potência instalada (± 0,1 MW);
- IP e TEIF entre 0 e 1;
- o estado tem 2 letras;
- o CEG segue o padrão da ANEEL;
- as faixas de geração são crescentes e ficam entre o limiar de parada e a plena carga;
- o slug é igual ao nome da pasta.

## Como preencher o perfil de outra usina

1. Copiar a pasta `usinas/sao_domingos/` para `usinas/<novo_slug>/`, sem `documentos/`, e trocar todos os valores.
2. Preencher os identificadores:

   | Campo | Onde obter |
   |---|---|
   | `cod_usina` | conjunto Energia Vertida Turbinável, coluna `cod_usina` |
   | `ceg` | ANEEL (SIGA) |
   | `id_ons` | conjuntos Geração por usina e Disponibilidade por usina |
   | `cod_programacao` | conjunto Programação diária, coluna `cod_exibicaousina` |
   | `id_reservatorio` | conjunto Dados hidrológicos horários |

3. Preencher os parâmetros técnicos com a fonte: garantia física da ANEEL; potência, unidades, turbina, engolimento, IP e TEIF de referência dos documentos do agente ou de relatório de fiscalização.
4. Executar `python -m src coleta --usina <novo_slug>`.
5. Conferir na auditoria de extração as linhas em que só o identificador ou só a conferência batem. Elas indicam homônimos ou identificador errado.
