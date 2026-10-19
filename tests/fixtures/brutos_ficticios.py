"""Arquivos brutos sintéticos da usina fictícia (tests/fixtures/usina_ficticia/perfil.toml), no formato do ONS.

Gera, numa pasta ``data/raw`` temporária, jan e fev/2024 de: Energia Vertida Turbinável, os quatro conjuntos de
indicadores e taxas, Disponibilidade por usina, Dados hidrológicos horários (convenção de fim de hora), Geração por usina
e Modalidade das usinas, mais o dicionário de dados da EVT. Cada conjunto traz uma linha de homônimo em que só o
identificador confere. Não há Programação diária: a seção correspondente sai do relatório.

``gerar_brutos_tipos`` acrescenta, nos mesmos arquivos, as usinas fictícias dos outros tipos (spec 006, decisão R23;
``tests/fixtures/usinas_ficticias/``): PCH em conjunto, com linhas próprias sem valor e um membro que entra em
02/2024; CGH, UTE e UTN com geração própria (as térmicas com disponibilidade; a UTN com os indicadores do ONS); EOL;
UFV com série curta; a Programação diária de três dias (o conjunto por dois códigos e a UTE); a Composição dos
conjuntos e a Capacidade de geração. Nenhum valor de usina real.
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


def gravar_dicionario_evt(caminho: Path) -> None:
    """Dicionário de dados da EVT no formato do ONS (todas as colunas da base e a linha da versão)."""
    dicionario = {"dicionario_simplificado": [
        *({"codigo": c, "descricao": f"descrição de {c}"} for c in COLUNAS_EVT),
        {"codigo": "06-06-2024", "descricao": "Versão de teste"},
    ]}
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dicionario, ensure_ascii=False), encoding="utf-8")


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
    gravar_dicionario_evt(raw / "_dicionarios" / "DicionarioDados_EnergiaVertidaTurbinavel.json")

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


# ---------------------------------------------------------------------------
# Usinas fictícias dos outros tipos (spec 006, decisão R23; tests/fixtures/usinas_ficticias/)
# ---------------------------------------------------------------------------

# Identificadores das seis usinas sem EVT e do membro do conjunto; nenhum existe no ONS
FICTICIAS: Dict[str, Dict[str, str]] = {
    "pch": {"ceg": "PCH.PH.GO.000101-0.01", "id_ons": "GOPCFI", "nome": "PCH FICTICIA", "tipo_ons": "HIDROELÉTRICA",
            "modalidade": "TIPO II-C", "potencia": "16.000"},
    "cgh": {"ceg": "CGH.PH.GO.000103-0.01", "id_ons": "GOCGFI", "nome": "CGH FICTICIA", "tipo_ons": "HIDROELÉTRICA",
            "modalidade": "TIPO II-C", "potencia": "4.000"},
    "ute": {"ceg": "UTE.GN.GO.000104-0.01", "id_ons": "GOUTFI", "nome": "UTE FICTICIA", "tipo_ons": "TÉRMICA",
            "modalidade": "TIPO I", "potencia": "120.000"},
    "utn": {"ceg": "UTN.NU.GO.000105-0.01", "id_ons": "GOUNFI", "nome": "UTN FICTICIA", "tipo_ons": "NUCLEAR",
            "modalidade": "TIPO I", "potencia": "640.000"},
    "eol": {"ceg": "EOL.CV.GO.000106-0.01", "id_ons": "GOEOFI", "nome": "EOL FICTICIA", "tipo_ons": "EOLIELÉTRICA",
            "modalidade": "TIPO I", "potencia": "40.000"},
    "ufv": {"ceg": "UFV.RS.GO.000107-0.01", "id_ons": "GOUFFI", "nome": "UFV FICTICIA", "tipo_ons": "FOTOVOLTAICA",
            "modalidade": "TIPO II-C", "potencia": "25.000"},
}
CONJUNTO = {"id_ons": "CJU_GOCJFI", "nome": "CONJ. HIDRAULICO FICTICIO"}
MEMBRO = {"ceg": "CGH.PH.GO.000102-0.01", "id_ons": "GOCGMB", "nome": "CGH MEMBRO", "entrada": "2024-02-01"}
CODIGOS_PROGRAMACAO = {"GOCJFI-1": 6.0, "GOCJFI-2": 6.0, "GOUTFI": 100.0}
DIAS_PROGRAMACAO = pd.date_range("2024-02-01", "2024-02-03", freq="D")
INICIO_UFV = pd.Timestamp("2024-02-10")  # série curta (decisão R17)
DISP_REDUZIDA_UTE = (pd.Timestamp("2024-01-15 00:00"), pd.Timestamp("2024-01-24 23:00"))  # 80 MW: regra R7
PARADA_UTE = (pd.Timestamp("2024-02-05 00:00"), pd.Timestamp("2024-02-07 23:00"))  # indisponibilidade total
PARADA_UTN = (pd.Timestamp("2024-02-10 00:00"), pd.Timestamp("2024-02-12 23:00"))


def _horas_periodo() -> pd.DatetimeIndex:
    return pd.date_range("2024-01-01 00:00", "2024-02-29 23:00", freq="h")


def _entre(horas: pd.DatetimeIndex, intervalo) -> np.ndarray:
    return np.asarray((horas >= intervalo[0]) & (horas <= intervalo[1]))


def _linhas_geracao(chave: str, horas: pd.DatetimeIndex, valores) -> pd.DataFrame:
    u = FICTICIAS[chave]
    return pd.DataFrame({"din_instante": horas, "id_subsistema": "SE", "id_estado": "GO", "nom_usina": u["nome"],
                         "id_ons": u["id_ons"], "ceg": u["ceg"], "val_geracao": valores,
                         "cod_modalidadeoperacao": u["modalidade"], "nom_tipousina": u["tipo_ons"]})


def geracao_ficticias() -> pd.DataFrame:
    """Geração por usina das usinas sem EVT e do conjunto, com as colunas do arquivo publicado."""
    h = _horas_periodo()
    hora = np.asarray(h.hour)
    solar = np.clip(20.0 * np.sin(np.pi * (hora - 6) / 12.0), 0.0, None)
    ufv = np.asarray(h >= INICIO_UFV)
    partes = [
        _linhas_geracao("pch", h, np.full(len(h), np.nan)),  # linhas próprias sem valor (achado A3)
        _linhas_geracao("cgh", h, np.where((hora >= 6) & (hora <= 18), 3.0, 2.0)),
        _linhas_geracao("ute", h, np.where((hora >= 8) & (hora <= 21) & ~_entre(h, PARADA_UTE), 100.0, 0.0)),
        _linhas_geracao("utn", h, np.where(_entre(h, PARADA_UTN), 0.0, 600.0)),
        _linhas_geracao("eol", h, 10.0 + (hora % 6) * 4.0),
        _linhas_geracao("ufv", h[ufv], solar[ufv]),
        pd.DataFrame({"din_instante": h, "id_subsistema": "SE", "id_estado": "GO", "nom_usina": CONJUNTO["nome"],
                      "id_ons": CONJUNTO["id_ons"], "ceg": "-",
                      "val_geracao": np.where(np.asarray(h.month) == 1, 12.0, 15.0),
                      "cod_modalidadeoperacao": "Conjunto de Usinas", "nom_tipousina": "HIDROELÉTRICA"}),
    ]
    return pd.concat(partes, ignore_index=True)


def _disponibilidade_ficticias(geracao: pd.DataFrame) -> pd.DataFrame:
    h = _horas_periodo()
    ute = np.where(_entre(h, PARADA_UTE), 0.0, np.where(_entre(h, DISP_REDUZIDA_UTE), 80.0, 120.0))
    utn = np.where(_entre(h, PARADA_UTN), 0.0, 640.0)
    partes = []
    for chave, operacional, pinst, unidade in (("ute", ute, 120.0, 60.0), ("utn", utn, 640.0, 320.0)):
        u = FICTICIAS[chave]
        ger = geracao.loc[geracao["id_ons"] == u["id_ons"], "val_geracao"].to_numpy()
        partes.append(pd.DataFrame({
            "id_subsistema": "SE", "id_estado": "GO", "nom_usina": u["nome"], "id_ons": u["id_ons"], "ceg": u["ceg"],
            "din_instante": h, "val_potenciainstalada": pinst, "val_dispoperacional": operacional,
            "val_dispsincronizada": np.where(ger > 1, np.minimum(np.ceil(ger / unidade) * unidade, operacional), 0.0)}))
    return pd.concat(partes, ignore_index=True)


def _acrescentar(tabela: pd.DataFrame, caminho: Path) -> None:
    """Acrescenta linhas a um arquivo bruto já gravado (CSV ou Parquet), mantendo as do arquivo."""
    if caminho.suffix == ".parquet":
        anterior = pd.read_parquet(caminho) if caminho.exists() else pd.DataFrame()
        _parquet(pd.concat([anterior, tabela], ignore_index=True), caminho)
    else:
        anterior = pd.read_csv(caminho, sep=";", dtype=str, keep_default_na=False) if caminho.exists() else pd.DataFrame()
        _csv(pd.concat([anterior, tabela], ignore_index=True), caminho)


def _indicadores_utn(raiz: Path) -> None:
    """Indicadores e taxas das duas unidades da UTN fictícia, acrescentados aos arquivos da UHE fictícia."""
    u = FICTICIAS["utn"]
    meses = [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-02-01")]
    comuns = {"ceg": u["ceg"], "id_usina": u["id_ons"], "nom_agenteproprietario": "AGENTE FICTICIO",
              "nom_modalidadeoperacao": "TIPO I", "val_potencia": "320.0"}
    mensal, anual, parametros = [], [], []
    for ug in (1, 2):
        nome_ug = "UG  320 MW " + u["nome"] + "              " + str(ug) + " GO"
        for mes in meses:
            hp = mes.days_in_month * 24.0
            hdf = 72.0 if (ug == 1 and mes.month == 2) else 4.0  # parada da UG1 de 10 a 12/02
            mensal.append({**comuns, "num_unidadegeradora": str(ug), "cod_equipamento": f"GOUNFI-UG{ug}",
                           "dat_mesreferencia": mes.strftime("%Y-%m-%d"), "val_dispf": f"{100 - hdf / hp * 100:.6f}",
                           "val_indisppf": "0.000000", "val_indispff": f"{hdf / hp * 100:.6f}",
                           "val_dmdff": "0.0", "val_fdff": "0.0", "val_tdff": "0.0"})
            horas = {"HP": hp, "HS": hp - hdf, "HRD": 0.0, "HDP": 0.0, "HDF": hdf, "HDCE": 0.0, "HEDP": 0.0, "HEDF": 0.0}
            for insumo, valor in horas.items():
                parametros.append({"nom_usina": u["nome"], "id_tipousina": "Termonuclear", "nom_unidadegeradora": nome_ug,
                                   "cod_ceg": u["ceg"], "dat_periodo": mes.strftime("%m/%Y"),
                                   "din_parametro": mes.strftime("%Y-%m-%d"), "nom_tpinsumo": insumo,
                                   "val_parametro": f"{valor:.2f}", "num_versao": "1.0"})
        anual.append({**comuns, "num_unidadegeradora": str(ug), "cod_equipamento": f"GOUNFI-UG{ug}", "din_ano": "2024",
                      "val_dispf": "97.0", "val_indisppf": "0.0", "val_indispff": "3.0", "val_dmdff": "36.0",
                      "val_fdff": "0.0", "val_tdff": "0.0"})
    _acrescentar(pd.DataFrame(mensal),
                 raiz / "ind_disponibilidade_fgeracao_uge_mensal" / "IND_DISPONIBILIDADE_FCGERACAO_UGE_MENSAL_2024.csv")
    _acrescentar(pd.DataFrame(anual),
                 raiz / "ind_disponibilidade_fgeracao_uge_anual" / "IND_DISPONIBILIDADE_FCGERACAO_UGE_ANUAL.csv")
    _acrescentar(pd.DataFrame(parametros), raiz / "taxa_teif_teip_parametro" / "TAXA_TEIF_TEIP_PARAM_2024.csv")
    taxas = [{"cod_ceg": u["ceg"], "din_mes": mes.strftime("%Y-%m-%d"), "nom_taxa": taxa, "val_taxa": valor,
              "num_versao": "1.0", "din_calculo": "2024-03-10 10:00:00"}
             for mes in meses for taxa, valor in (("TEIFa", "0.03"), ("TEIP", "0.01"))]
    _acrescentar(pd.DataFrame(taxas), raiz / "taxa_teif_teip" / "TAXA_TEIF_TEIP.csv")


def _programacao_ficticias(raw: Path) -> None:
    """Programação diária de três dias: o conjunto por dois códigos e a UTE, em patamares de 30 minutos."""
    for dia in DIAS_PROGRAMACAO:
        linhas = []
        for codigo, valor in CODIGOS_PROGRAMACAO.items():
            for patamar in range(1, 49):
                hora = (patamar - 1) // 2
                programado = valor if codigo != "GOUTFI" or 8 <= hora <= 21 else 0.0
                linhas.append({"din_programacaodia": dia, "num_patamar": patamar, "cod_exibicaousina": codigo,
                               "nom_usina": f"USINA {codigo}", "nom_modalidadeoperacao": "TIPO I", "id_estado": "GO",
                               "val_geracaoprogramada": programado})
        _parquet(pd.DataFrame(linhas),
                 raw / "programacao_diaria" / f"PROGRAMACAO_DIARIA_{dia.year}_{dia.month:02d}_{dia.day:02d}.parquet")


def _membro_conjunto(ceg: str, id_ons: str, nome: str, inicio: str) -> Dict[str, object]:
    return {"id_subsistema": "SE", "nom_subsistema": "Sudeste/Centro-Oeste", "estad_id": "GO", "nom_estado": "GOIAS",
            "id_tipousina": "UHE", "nom_tipousina": "Hidroelétrica ", "id_conjuntousina": 7,
            "id_ons_conjunto": CONJUNTO["id_ons"], "id_ons_usina": id_ons, "nom_conjunto": CONJUNTO["nome"],
            "nom_usina": nome, "ceg": ceg, "dat_iniciorelacionamento": inicio, "dat_fimrelacionamento": "9999-12-31"}


def _cadastrais_ficticias(raw: Path) -> None:
    """Modalidade das usinas (com as usinas da UHE fictícia), Composição dos conjuntos e Capacidade de geração."""
    cadastro = raw / "modalidade_usina" / "MODALIDADE_USINA.csv"
    linhas = [";".join([u["nome"], u["ceg"], u["modalidade"], u["potencia"], "COSR-NCO", "SE " + u["nome"] + " 138 KV",
                        "GO", "GOIAS", "A", u["id_ons"]]) for u in FICTICIAS.values()]
    linhas.append(";".join([CONJUNTO["nome"], "", "TIPO II-C", "30.000", "COSR-NCO", "SE CONJUNTO 138 KV", "GO", "GOIAS",
                            "A", ""]))
    cadastro.write_text(cadastro.read_text(encoding="utf-8") + "\n".join(linhas) + "\n", encoding="utf-8")

    pch = FICTICIAS["pch"]
    _parquet(pd.DataFrame([_membro_conjunto(pch["ceg"], pch["id_ons"], pch["nome"], "2016-03-01"),
                           _membro_conjunto(MEMBRO["ceg"], MEMBRO["id_ons"], MEMBRO["nome"], MEMBRO["entrada"])]),
             raw / "usina_conjunto" / "USINA_CONJUNTO.parquet")

    unidades = {"pch": (8.0, 8.0), "cgh": (2.0, 2.0), "ute": (60.0, 60.0), "utn": (320.0, 320.0),
                "eol": (4.0,) * 10, "ufv": (10.0, 15.0)}
    combustivel = {"pch": "HIDRÁULICA", "cgh": "HIDRÁULICA", "ute": "GÁS NATURAL", "utn": "NUCLEAR", "eol": "EÓLICA",
                   "ufv": "FOTOVOLTAICA"}
    linhas_ug = [{"id_subsistema": "SE", "nom_subsistema": "SUDESTE ", "id_estado": "GO", "nom_estado": "GO",
                  "nom_modalidadeoperacao": u["modalidade"], "nom_agenteproprietario": "AGENTE FICTICIO",
                  "nom_agenteoperador": "AGENTE FICTICIO", "nom_tipousina": u["tipo_ons"], "nom_usina": u["nome"],
                  "ceg": u["ceg"], "nom_unidadegeradora": f"UG{n}", "cod_equipamento": f"{u['ceg']}-UG{n}",
                  "num_unidadegeradora": str(n), "nom_combustivel": combustivel[k], "dat_entradateste": "0001-01-01",
                  "dat_entradaoperacao": "2016-03-01", "dat_desativacao": "9999-12-31", "val_potenciaefetiva": p}
                 for k, u in FICTICIAS.items() for n, p in enumerate(unidades[k], start=1)]
    _parquet(pd.DataFrame(linhas_ug), raw / "capacidade_geracao" / "CAPACIDADE_GERACAO.parquet")


def gerar_brutos_tipos(raw: Path) -> None:
    """Os brutos da UHE fictícia mais os das usinas fictícias dos outros tipos, nos mesmos arquivos do ONS."""
    raw = Path(raw)
    gerar_brutos(raw)
    geracao = geracao_ficticias()
    for sufixo, g in _por_mes(geracao).items():
        _acrescentar(g, raw / "geracao_usina_2" / f"GERACAO_USINA-2_{sufixo}.parquet")
    for sufixo, g in _por_mes(_disponibilidade_ficticias(geracao)).items():
        _acrescentar(g, raw / "disponibilidade_usina" / f"DISPONIBILIDADE_USINA_{sufixo}.csv")
    _indicadores_utn(raw / "indicadores_ons")
    _programacao_ficticias(raw)
    _cadastrais_ficticias(raw)
