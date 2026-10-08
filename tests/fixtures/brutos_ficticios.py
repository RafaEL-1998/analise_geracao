"""Arquivos brutos sintéticos da usina fictícia (tests/fixtures/usina_ficticia/perfil.toml), no formato do ONS.

Gera, numa pasta ``data/raw`` temporária, jan e fev/2024 de: Energia Vertida Turbinável, os quatro conjuntos de
indicadores e taxas, Disponibilidade por usina, Dados hidrológicos horários (convenção de fim de hora), Geração por usina
e Modalidade das usinas, mais o dicionário de dados da EVT. Cada conjunto traz uma linha de homônimo em que só o
identificador confere. Não há Programação diária: a seção correspondente sai do relatório.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

CEG = "UHE.PH.GO.000001-0.01"
ID_ONS = "GOUHFI"
COD_USINA = 999
NOME = "USINA FICTICIA"
ID_RESERVATORIO = "PNUHFI"
PRODUTIVIDADE = 0.52
COLUNAS_EVT = [
    "id_subsistema", "nom_subsistema", "nom_bacia", "nom_rio", "nom_agente", "nom_reservatorio", "cod_usina",
    "din_instante", "val_geracao", "val_disponibilidade", "val_vazaoturbinada", "val_vazaovertida",
    "val_vazaovertidanaoturbinavel", "val_produtividade", "val_folgadegeracao", "val_energiavertida",
    "val_vazaovertidaturbinavel", "val_energiavertidaturbinavel",
]


def serie_operacao() -> pd.DataFrame:
    """Operação horária coerente (identidades do ONS respeitadas): paradas com EVT, cheia e indisponibilidade total."""
    linhas: List[Dict] = []
    for t in pd.date_range("2024-01-01 00:00", "2024-02-29 23:00", freq="h"):
        disp = 90.0
        if pd.Timestamp("2024-01-10 00:00") <= t <= pd.Timestamp("2024-01-11 05:00"):
            disp = 0.0  # 30 h de indisponibilidade total
        elif pd.Timestamp("2024-02-01") <= t < pd.Timestamp("2024-02-06"):
            disp = 60.0  # uma unidade fora
        ger = 0.0 if disp == 0 else (50.0 if disp == 60 else 70.0)
        vertida = 5.0
        if t.normalize() == pd.Timestamp("2024-01-20"):
            vertida = 200.0  # cheia: afluência acima do engolimento máximo (180 m³/s)
        if pd.Timestamp("2024-02-10 09:00") <= t <= pd.Timestamp("2024-02-10 13:00"):
            ger, vertida = 0.0, 150.0  # usina parada com EVT; afluência entre uma e três unidades
        if pd.Timestamp("2024-02-15 10:00") <= t <= pd.Timestamp("2024-02-15 12:00"):
            ger, vertida = 0.0, 40.0  # usina parada com EVT; afluência que cabia numa unidade
        folga = max(0.0, disp - ger)
        nao_turbinavel = vertida if disp == 0 else 0.0
        turbinavel = min(vertida - nao_turbinavel, folga / PRODUTIVIDADE)
        nao_turbinavel = vertida - turbinavel if disp != 0 and turbinavel < vertida else nao_turbinavel
        linhas.append({
            "id_subsistema": "SE", "nom_subsistema": "SUDESTE", "nom_bacia": "PARANAIBA", "nom_rio": "RIO FICTICIO",
            "nom_agente": "AGENTE FICTICIO", "nom_reservatorio": NOME, "cod_usina": COD_USINA, "din_instante": t,
            "val_geracao": ger, "val_disponibilidade": disp, "val_vazaoturbinada": ger / PRODUTIVIDADE,
            "val_vazaovertida": vertida, "val_vazaovertidanaoturbinavel": nao_turbinavel,
            "val_produtividade": PRODUTIVIDADE, "val_folgadegeracao": folga, "val_energiavertida": vertida * PRODUTIVIDADE,
            "val_vazaovertidaturbinavel": turbinavel, "val_energiavertidaturbinavel": turbinavel * PRODUTIVIDADE,
        })
    return pd.DataFrame(linhas)


def _csv(tabela: pd.DataFrame, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_csv(caminho, sep=";", index=False, date_format="%Y-%m-%d %H:%M:%S")


def _parquet(tabela: pd.DataFrame, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_parquet(caminho, index=False)


def _por_mes(tabela: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    return {f"{mes.year}_{mes.month:02d}": g for mes, g in tabela.groupby(tabela["din_instante"].dt.to_period("M"))}


def gerar_brutos(raw: Path) -> pd.DataFrame:
    """Grava os arquivos brutos em ``raw`` e devolve a operação horária usada."""
    raw = Path(raw)
    op = serie_operacao()

    # Energia Vertida Turbinável: um arquivo por mês, com homônimo (só cod_usina) e outra usina
    for sufixo, g in _por_mes(op).items():
        extra = g.head(1).copy()
        homonimo = extra.assign(nom_reservatorio="OUTRA USINA")
        outra = extra.assign(cod_usina=111, nom_reservatorio="BALBINA", nom_agente="OUTRO AGENTE")
        _csv(pd.concat([g, homonimo, outra])[COLUNAS_EVT], raw / f"ENERGIA_VERTIDA_TURBINAVEL_{sufixo}.csv")
    dicionario = {"dicionario_simplificado": [
        *({"codigo": c, "descricao": f"descrição de {c}"} for c in COLUNAS_EVT),
        {"codigo": "06-06-2024", "descricao": "Versão de teste"},
    ]}
    (raw / "_dicionarios").mkdir(parents=True, exist_ok=True)
    (raw / "_dicionarios" / "DicionarioDados_EnergiaVertidaTurbinavel.json").write_text(
        json.dumps(dicionario, ensure_ascii=False), encoding="utf-8")

    # Disponibilidade por usina (CSV mensal): sincronizada = unidades em operação × 30 MW
    unidades = np.ceil(op["val_geracao"] / 30.0)
    disp = pd.DataFrame({
        "id_subsistema": "SE", "id_estado": "GO", "nom_usina": "UHE FICTICIA", "id_ons": ID_ONS, "ceg": CEG,
        "din_instante": op["din_instante"], "val_potenciainstalada": 90.0, "val_dispoperacional": op["val_disponibilidade"],
        "val_dispsincronizada": np.where(op["val_geracao"] > 1, unidades * 30.0, 0.0),
    })
    for sufixo, g in _por_mes(disp).items():
        homonimo = g.head(1).assign(id_estado="MT")  # só o identificador confere
        _csv(pd.concat([g, homonimo]), raw / "disponibilidade_usina" / f"DISPONIBILIDADE_USINA_{sufixo}.csv")

    # Dados hidrológicos horários (Parquet mensal), na convenção de fim de hora (a última hora do dia às 23:59)
    publicado = op["din_instante"].where(op["din_instante"].dt.hour != 23,
                                         op["din_instante"].dt.normalize() + pd.Timedelta(minutes=23 * 60 + 59))
    publicado = publicado.where(op["din_instante"].dt.hour == 23, op["din_instante"] + pd.Timedelta(hours=1))
    afluente = op["val_vazaoturbinada"] + op["val_vazaovertida"]
    hid = pd.DataFrame({
        "id_reservatorio": ID_RESERVATORIO, "nom_reservatorio": NOME, "cod_usina": float(COD_USINA),
        "din_instante": publicado, "val_nivelmontante": 400.0, "val_niveljusante": 340.0, "val_volumeutil": 50.0,
        "val_vazaoafluente": afluente, "val_vazaodefluente": afluente, "val_vazaoturbinada": op["val_vazaoturbinada"],
        "val_vazaovertida": op["val_vazaovertida"], "val_vazaooutrasestruturas": np.nan,
        "val_vazaovertidanaoturbinavel": op["val_vazaovertidanaoturbinavel"],
    })
    hid["_mes"] = op["din_instante"].dt.to_period("M")
    for mes, g in hid.groupby("_mes"):
        homonimo = g.head(1).assign(id_reservatorio="XXXX")  # só o identificador confere
        _parquet(pd.concat([g, homonimo]).drop(columns="_mes"),
                 raw / "dados_hidrologicos_ho" / f"DADOS_HIDROLOGICOS_HO_{mes.year}_{mes.month:02d}.parquet")

    # Geração por usina (Parquet mensal)
    ger = pd.DataFrame({"id_subsistema": "SE", "id_estado": "GO", "nom_usina": "UHE FICTICIA", "id_ons": ID_ONS, "ceg": CEG,
                        "din_instante": op["din_instante"], "val_geracao": op["val_geracao"]})
    for sufixo, g in _por_mes(ger).items():
        homonimo = g.head(1).assign(ceg="UHE.PH.MT.000002-0.01")  # só o identificador confere
        _parquet(pd.concat([g, homonimo]), raw / "geracao_usina_2" / f"GERACAO_USINA-2_{sufixo}.parquet")

    _indicadores(raw / "indicadores_ons")

    # Modalidade das usinas: a usina, um homônimo (outro CEG) e outra usina
    linhas = [
        f"{NOME};{CEG};TIPO II-B;90.000;COSR-NCO;SE FICTICIA 230 KV;GO;GOIAS;A;{ID_ONS}",
        f"{NOME} II;UHE.PH.GO.000003-0.01;TIPO III;10.000;COSR-NCO;;GO;GOIAS;A;GOFIC2",
        "UHE OUTRA;UHE.PH.SP.000004-0.01;TIPO I;100.000;COSR-SE;SE X;SP;SAO PAULO;A;SPOUTR",
    ]
    cabecalho = ("nom_usina;ceg;nom_modalidadeoperacao;val_potenciaautorizada;sgl_centrooperacao;nom_pontoconexao;"
                 "id_estado;nom_estado;sts_aneel;id_ons")
    (raw / "modalidade_usina").mkdir(parents=True, exist_ok=True)
    (raw / "modalidade_usina" / "MODALIDADE_USINA.csv").write_text("\n".join([cabecalho, *linhas]) + "\n",
                                                                    encoding="utf-8")
    return op


def _indicadores(raiz: Path) -> None:
    meses = [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")]
    comuns = {"ceg": CEG, "id_usina": ID_ONS, "nom_agenteproprietario": "AGENTE FICTICIO",
              "nom_modalidadeoperacao": "TIPO II-B", "val_potencia": "30.0"}
    mensal, anual, parametros = [], [], []
    for ug in (1, 2, 3):
        cod = f"GOUHFI-UG{ug}"
        for mes in meses:
            hp = mes.days_in_month * 24.0
            hdp = 96.0 if (ug == 3 and mes.month == 2) else 0.0  # UG3 fora de 01 a 05/02 (programado)
            hdf = 2.0 * ug
            mensal.append({**comuns, "num_unidadegeradora": str(ug), "cod_equipamento": cod,
                           "dat_mesreferencia": mes.strftime("%Y-%m-%d"), "val_dispf": f"{100 - (hdp + hdf) / hp * 100:.6f}",
                           "val_indisppf": f"{hdp / hp * 100:.6f}", "val_indispff": f"{hdf / hp * 100:.6f}",
                           "val_dmdff": "0.0", "val_fdff": "0.0", "val_tdff": "0.0"})
            nome_ug = f"UG   30 MW {NOME}              {ug} GO"
            horas = {"HP": hp, "HS": hp - hdp - hdf - 10.0, "HRD": 10.0, "HDP": hdp, "HDF": hdf, "HDCE": 0.0,
                     "HEDP": 0.0, "HEDF": 0.0}
            for insumo, valor in horas.items():
                parametros.append({"nom_usina": NOME, "id_tipousina": "Hidroelétrica", "nom_unidadegeradora": nome_ug,
                                   "cod_ceg": CEG, "dat_periodo": mes.strftime("%m/%Y"),
                                   "din_parametro": mes.strftime("%Y-%m-%d"), "nom_tpinsumo": insumo,
                                   "val_parametro": f"{valor:.2f}", "num_versao": "1.0"})
        anual.append({**comuns, "num_unidadegeradora": str(ug), "cod_equipamento": cod, "din_ano": "2024",
                      "val_dispf": "99.0", "val_indisppf": "0.5", "val_indispff": "0.5", "val_dmdff": "0.0",
                      "val_fdff": "0.0", "val_tdff": "0.0"})
    homonimo = {**mensal[0], "id_usina": "GOOUTR"}  # só o CEG confere
    _csv(pd.DataFrame([*mensal, homonimo]),
         raiz / "ind_disponibilidade_fgeracao_uge_mensal" / "IND_DISPONIBILIDADE_FCGERACAO_UGE_MENSAL_2024.csv")
    _csv(pd.DataFrame(anual), raiz / "ind_disponibilidade_fgeracao_uge_anual" / "IND_DISPONIBILIDADE_FCGERACAO_UGE_ANUAL.csv")
    _csv(pd.DataFrame(parametros), raiz / "taxa_teif_teip_parametro" / "TAXA_TEIF_TEIP_PARAM_2024.csv")
    taxas = [{"cod_ceg": CEG, "din_mes": mes.strftime("%Y-%m-%d"), "nom_taxa": taxa, "val_taxa": valor,
              "num_versao": "1.0", "din_calculo": "2024-03-10 10:00:00"}
             for mes in meses for taxa, valor in (("TEIFa", "0.01"), ("TEIP", "0.02"))]
    _csv(pd.DataFrame(taxas), raiz / "taxa_teif_teip" / "TAXA_TEIF_TEIP.csv")
