"""Arquivos brutos sintéticos da usina fictícia (tests/fixtures/usina_ficticia/perfil.toml), no formato do ONS.

Gera, numa pasta ``data/raw`` temporária, jan e fev/2024 de: Energia Vertida Turbinável, os quatro conjuntos de
indicadores e taxas, Disponibilidade por usina, Dados hidrológicos horários (convenção de fim de hora), Geração por usina
e Modalidade das usinas, mais o dicionário de dados da EVT. Cada conjunto traz uma linha de homônimo em que só o
identificador confere. Não há Programação diária: a seção correspondente sai do relatório.

``gerar_brutos_tipos`` acrescenta, nos mesmos arquivos, as usinas fictícias dos outros tipos (plano da Coleta de dados,
D30; ``tests/fixtures/usinas_ficticias/``): PCH em conjunto, com linhas próprias sem valor e um membro que entra em
02/2024; CGH, UTE e UTN com geração própria (as térmicas com disponibilidade; a UTN com os indicadores do ONS); EOL;
UFV com série curta; a Programação diária de três dias (o conjunto por dois códigos e a UTE); a Composição dos
conjuntos e a Capacidade de geração. Nenhum valor de usina real.

Térmicas: o despacho, o CVU (com revisões) e o CMO da UTE e da UTN. A UTE tem 2023
inteiro sem geração, disponível, com o código de planejamento 901, trocado em 01/2024 pelas unidades 902 (gás) e 903
(óleo); o arquivo anual de 2024 repete os mensais, como o ONS publica.

PCH e CGH: a PCH entra no conjunto em 10/01/2024, depois do início da
série do conjunto (o período é recortado pela composição); uma térmica sai do conjunto em 15/02/2024; o ONS publica o
conjunto como "TÉRMICA" também depois da saída dela (tipo publicado divergente da composição). A CGH, com geração
própria e sem EVT, tem os Dados hidrológicos na convenção de fim de hora, com a vazão turbinada proporcional à geração.

Eólicas e solares: o Fator de capacidade e as duas restrições. A EOL tem tudo próprio,
com a restrição desde 15/01/2024 (adaptação da série longa ao período sintético), vento inválido de 20 a
25/01 e semi-horas restritas de 01 a 10/02 com a razão REL, CNF e ENE; a programação de três dias. A UFV fica num
conjunto com um membro: a geração, o fator de capacidade, a razão e a programação só do conjunto; a restrição com
detalhe da usina desde 25/01/2024 (série de referência curta), com o arquivo de janeiro no esquema antigo, sem as cinco
colunas e com a marca de irradiância booleana.
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
# Usinas fictícias dos outros tipos (plano da Coleta de dados, D30; tests/fixtures/usinas_ficticias/)
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
# A entrada da PCH no conjunto (depois do início da série dele) e a térmica que sai no meio do período
ENTRADA_PCH = "2024-01-10"
MEMBRO_UTE = {"ceg": "UTE.BI.GO.000109-0.01", "id_ons": "GOUTMB", "nome": "UTE MEMBRO", "entrada": "2016-03-01",
              "saida": "2024-02-15", "unidades": (15.0, 15.0)}
GERACAO_UTE_MEMBRO_MW = 10.0
# A CGH com os Dados hidrológicos, sem EVT; um dia de cheia acima do engolimento máximo (2 × 10 m³/s)
COD_USINA_CGH = 998
ID_RESERVATORIO_CGH = "PNCGFI"
PRODUTIVIDADE_CGH = 0.2  # turbinada de 15 m³/s de dia e 10 à noite: só a cheia passa do engolimento
CHEIA_CGH = pd.Timestamp("2024-02-20")
CODIGOS_PROGRAMACAO = {"GOCJFI-1": 6.0, "GOCJFI-2": 6.0, "GOUTFI": 100.0, "GOEOFI": 16.0, "GOCJUF-1": 12.0}
DIAS_PROGRAMACAO = pd.date_range("2024-02-01", "2024-02-03", freq="D")
# série curta (plano das Análises, D19): a restrição com detalhe da UFV começa aqui
INICIO_UFV = pd.Timestamp("2024-01-25")
DISP_REDUZIDA_UTE = (pd.Timestamp("2024-01-15 00:00"), pd.Timestamp("2024-01-24 23:00"))  # 80 MW: regra R7
PARADA_UTE = (pd.Timestamp("2024-02-05 00:00"), pd.Timestamp("2024-02-07 23:00"))  # indisponibilidade total
PARADA_UTN = (pd.Timestamp("2024-02-10 00:00"), pd.Timestamp("2024-02-12 23:00"))
SEM_PROGRAMACAO_UTE = (pd.Timestamp("2024-01-02"), pd.Timestamp("2024-01-14"))  # 22h e 23h: 50 MW sem programação
INFLEX_PARCIAL_UTE = pd.Timestamp("2024-02-20")  # inflexibilidade verificada de 20 MW contra 30 programados
CODIGOS_UTE = {"antigo": 901, "gas": 902, "oleo": 903}
CODIGO_UTN = 950
CVU_UTE = {901: (150.0, 160.0), 902: (200.0, 210.0), 903: (900.0, 900.0)}  # (revisão 0, revisão 1)
CMO_SE = {2023: 300.0, 2024: 100.0}
# Eólicas e solares
CONJUNTO_UFV = {"id_ons": "CJU_GOCJUF", "nome": "CONJ. SOLAR FICTICIO"}
MEMBRO_UFV = {"ceg": "UFV.RS.GO.000108-0.01", "id_ons": "GOUFMB", "nome": "UFV MEMBRO", "entrada": "2023-01-01"}
INICIO_RESTRICAO_EOL = pd.Timestamp("2024-01-15")
VENTO_INVALIDO_EOL = (pd.Timestamp("2024-01-20 00:00"), pd.Timestamp("2024-01-25 23:30"))  # C17
VENTO_IMPLAUSIVEL_EOL = (pd.Timestamp("2024-02-20 00:00"), pd.Timestamp("2024-02-20 01:30"))  # 120 m/s sem a marca
RESTRICAO_EOL = (pd.Timestamp("2024-02-01"), pd.Timestamp("2024-02-10"), 10, 17)  # dias e horas restritas (C16)
CORTE_EOL_MW = 25.0
RAZOES_EOL = {"REL": ("2024-02-01", "2024-02-03"), "CNF": ("2024-02-04", "2024-02-06"),
              "ENE": ("2024-02-07", "2024-02-10")}
RESTRICAO_UFV = (pd.Timestamp("2024-02-12"), pd.Timestamp("2024-02-14"), 10, 14)
CORTE_UFV_MW = 5.0
# Estimada 0 com a UFV gerando (estimativa ausente): duas semi-horas restritas e quatro fora da restrição
ESTIMADA_AUSENTE_UFV = pd.DatetimeIndex(["2024-02-14 14:00", "2024-02-14 14:30", "2024-02-20 10:00", "2024-02-20 10:30",
                                         "2024-02-20 11:00", "2024-02-20 11:30"])
CAPACIDADE_CONJUNTO_UFV = 35.0


def _horas_periodo() -> pd.DatetimeIndex:
    return pd.date_range("2024-01-01 00:00", "2024-02-29 23:00", freq="h")


def _entre(horas: pd.DatetimeIndex, intervalo) -> np.ndarray:
    return np.asarray((horas >= intervalo[0]) & (horas <= intervalo[1]))


def _linhas_geracao(chave: str, horas: pd.DatetimeIndex, valores) -> pd.DataFrame:
    u = FICTICIAS[chave]
    return pd.DataFrame({"din_instante": horas, "id_subsistema": "SE", "id_estado": "GO", "nom_usina": u["nome"],
                         "id_ons": u["id_ons"], "ceg": u["ceg"], "val_geracao": valores,
                         "cod_modalidadeoperacao": u["modalidade"], "nom_tipousina": u["tipo_ons"]})


def geracao_eol(h: pd.DatetimeIndex) -> np.ndarray:
    return 10.0 + (np.asarray(h.hour) % 6) * 4.0


def solar(h: pd.DatetimeIndex, pico: float) -> np.ndarray:
    return np.clip(pico * np.sin(np.pi * (np.asarray(h.hour) - 6) / 12.0), 0.0, None)


def geracao_ufv(h: pd.DatetimeIndex) -> np.ndarray:
    """A UFV, só desde o início da série dela (antes, o conjunto é só o membro)."""
    return np.where(np.asarray(h >= INICIO_UFV), solar(h, 20.0), 0.0)


def geracao_conjunto_ufv(h: pd.DatetimeIndex) -> np.ndarray:
    return geracao_ufv(h) + solar(h, 8.0)


def geracao_ficticias() -> pd.DataFrame:
    """Geração por usina das usinas sem EVT e dos conjuntos, com as colunas do arquivo publicado (a UFV só pelo
    conjunto dela, como a Seriemas 1)."""
    h = _horas_periodo()
    partes = [
        _linhas_geracao("pch", h, np.full(len(h), np.nan)),  # linhas próprias sem valor (plano da Coleta de dados, D21)
        _linhas_geracao("cgh", h, geracao_cgh(h)),
        _linhas_geracao("ute", h, geracao_ute(h)),
        _linhas_geracao("utn", h, np.where(_entre(h, PARADA_UTN), 0.0, 600.0)),
        _linhas_geracao("eol", h, geracao_eol(h)),
        pd.DataFrame({"din_instante": h, "id_subsistema": "SE", "id_estado": "GO", "nom_usina": CONJUNTO["nome"],
                      "id_ons": CONJUNTO["id_ons"], "ceg": "-", "val_geracao": geracao_conjunto(h),
                      # como o Conj. Chapadão: publicado como térmico mesmo depois da saída da térmica
                      "cod_modalidadeoperacao": "Conjunto de Usinas", "nom_tipousina": "TÉRMICA",
                      "nom_tipocombustivel": "Biomassa"}),
        pd.DataFrame({"din_instante": h, "id_subsistema": "SE", "id_estado": "GO", "nom_usina": CONJUNTO_UFV["nome"],
                      "id_ons": CONJUNTO_UFV["id_ons"], "ceg": "-", "val_geracao": geracao_conjunto_ufv(h),
                      "cod_modalidadeoperacao": "Conjunto de Usinas", "nom_tipousina": "FOTOVOLTAICA"}),
    ]
    return pd.concat(partes, ignore_index=True)


def geracao_conjunto(h: pd.DatetimeIndex) -> np.ndarray:
    """O conjunto da PCH: 12 MW em janeiro e 15 MW em fevereiro, mais a térmica enquanto ela está no conjunto."""
    base = np.where(np.asarray(h.month) == 1, 12.0, 15.0)
    return base + np.where(np.asarray(h < pd.Timestamp(MEMBRO_UTE["saida"])), GERACAO_UTE_MEMBRO_MW, 0.0)


def geracao_cgh(h: pd.DatetimeIndex) -> np.ndarray:
    hora = np.asarray(h.hour)
    return np.where((hora >= 6) & (hora <= 18), 3.0, 2.0)


def geracao_ute(h: pd.DatetimeIndex) -> np.ndarray:
    """Geração da UTE em 2024: 100 MW das 8h às 21h, salvo a parada; 50 MW às 22h e 23h sem programação (C15)."""
    hora, dia = np.asarray(h.hour), np.asarray(h.normalize())
    base = np.where((hora >= 8) & (hora <= 21) & ~_entre(h, PARADA_UTE), 100.0, 0.0)
    sem_programa = (hora >= 22) & (dia >= SEM_PROGRAMACAO_UTE[0]) & (dia <= SEM_PROGRAMACAO_UTE[1])
    return np.where(sem_programa, 50.0, base)


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


def _membro_conjunto(ceg: str, id_ons: str, nome: str, inicio: str, conjunto: Dict[str, str] = CONJUNTO,
                     tipo: tuple = ("UHE", "Hidroelétrica ", 7), fim: str = "9999-12-31") -> Dict[str, object]:
    return {"id_subsistema": "SE", "nom_subsistema": "Sudeste/Centro-Oeste", "estad_id": "GO", "nom_estado": "GOIAS",
            "id_tipousina": tipo[0], "nom_tipousina": tipo[1], "id_conjuntousina": tipo[2],
            "id_ons_conjunto": conjunto["id_ons"], "id_ons_usina": id_ons, "nom_conjunto": conjunto["nome"],
            "nom_usina": nome, "ceg": ceg, "dat_iniciorelacionamento": inicio, "dat_fimrelacionamento": fim}


def _cadastrais_ficticias(raw: Path) -> None:
    """Modalidade das usinas (com as usinas da UHE fictícia), Composição dos conjuntos e Capacidade de geração."""
    cadastro = raw / "modalidade_usina" / "MODALIDADE_USINA.csv"
    linhas = [";".join([u["nome"], u["ceg"], u["modalidade"], u["potencia"], "COSR-NCO", "SE " + u["nome"] + " 138 KV",
                        "GO", "GOIAS", "A", u["id_ons"]]) for u in FICTICIAS.values()]
    linhas.append(";".join([CONJUNTO["nome"], "", "TIPO II-C", "30.000", "COSR-NCO", "SE CONJUNTO 138 KV", "GO", "GOIAS",
                            "A", ""]))
    linhas.append(";".join([CONJUNTO_UFV["nome"], "", "TIPO II-C", "35.000", "COSR-NCO", "SE CONJUNTO SOLAR 138 KV", "GO",
                            "GOIAS", "A", ""]))
    cadastro.write_text(cadastro.read_text(encoding="utf-8") + "\n".join(linhas) + "\n", encoding="utf-8")

    pch, ufv = FICTICIAS["pch"], FICTICIAS["ufv"]
    solar_ = ("UFV", "Fotovoltaica", 8)
    _parquet(pd.DataFrame([_membro_conjunto(pch["ceg"], pch["id_ons"], pch["nome"], ENTRADA_PCH),
                           _membro_conjunto(MEMBRO["ceg"], MEMBRO["id_ons"], MEMBRO["nome"], MEMBRO["entrada"]),
                           _membro_conjunto(MEMBRO_UTE["ceg"], MEMBRO_UTE["id_ons"], MEMBRO_UTE["nome"],
                                            MEMBRO_UTE["entrada"], tipo=("UTE", "Termelétrica", 1),
                                            fim=MEMBRO_UTE["saida"]),
                           _membro_conjunto(ufv["ceg"], ufv["id_ons"], ufv["nome"], INICIO_UFV.strftime("%Y-%m-%d"),
                                            CONJUNTO_UFV, solar_),
                           _membro_conjunto(MEMBRO_UFV["ceg"], MEMBRO_UFV["id_ons"], MEMBRO_UFV["nome"],
                                            MEMBRO_UFV["entrada"], CONJUNTO_UFV, solar_)]),
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
    # a térmica que saiu do conjunto; a CGH membro fica sem unidade cadastrada (potência "—")
    linhas_ug += [{**linhas_ug[0], "nom_modalidadeoperacao": "TIPO II-B", "nom_tipousina": "TÉRMICA",
                   "nom_usina": MEMBRO_UTE["nome"], "ceg": MEMBRO_UTE["ceg"], "nom_unidadegeradora": f"UG{n}",
                   "cod_equipamento": f"{MEMBRO_UTE['ceg']}-UG{n}", "num_unidadegeradora": str(n),
                   "nom_combustivel": "BIOMASSA", "val_potenciaefetiva": p}
                  for n, p in enumerate(MEMBRO_UTE["unidades"], start=1)]
    _parquet(pd.DataFrame(linhas_ug), raw / "capacidade_geracao" / "CAPACIDADE_GERACAO.parquet")


# ---------------------------------------------------------------------------
# Térmicas: 2023 da UTE, despacho, CVU e CMO
# ---------------------------------------------------------------------------


def _ute_2023(raw: Path) -> None:
    """2023 inteiro da UTE: geração nula e disponibilidade de 120 MW (a térmica disponível e não despachada)."""
    h = pd.date_range("2023-01-01 00:00", "2023-12-31 23:00", freq="h")
    u = FICTICIAS["ute"]
    geracao = _linhas_geracao("ute", h, np.zeros(len(h)))
    for sufixo, g in _por_mes(geracao).items():
        _acrescentar(g, raw / "geracao_usina_2" / f"GERACAO_USINA-2_{sufixo}.parquet")
    disp = pd.DataFrame({"id_subsistema": "SE", "id_estado": "GO", "nom_usina": u["nome"], "id_ons": u["id_ons"],
                         "ceg": u["ceg"], "din_instante": h, "val_potenciainstalada": 120.0,
                         "val_dispoperacional": 120.0, "val_dispsincronizada": 0.0})
    for sufixo, g in _por_mes(disp).items():
        _acrescentar(g, raw / "disponibilidade_usina" / f"DISPONIBILIDADE_USINA_{sufixo}.csv")


def _linhas_despacho(chave: str, codigo: float, h: pd.DatetimeIndex, merito, inflex, verificado,
                     inflex_verificada) -> pd.DataFrame:
    from src.coleta.registro import COLUNAS_DESPACHO_PROGRAMADO, COLUNAS_DESPACHO_VERIFICADO

    u = FICTICIAS[chave]
    t = pd.DataFrame({"din_instante": h, "nom_tipopatamar": "MÉDIA", "id_subsistema": "SE", "nom_subsistema": "SUDESTE",
                      "nom_usina": u["nome"], "cod_usinaplanejamento": float(codigo), "ceg": u["ceg"]})
    for coluna in COLUNAS_DESPACHO_PROGRAMADO + COLUNAS_DESPACHO_VERIFICADO:
        t[coluna] = "0.0"
    merito, inflex = np.broadcast_to(merito, len(h)), np.broadcast_to(inflex, len(h))
    verificado, inflex_verificada = np.broadcast_to(verificado, len(h)), np.broadcast_to(inflex_verificada, len(h))
    t["val_proggeracao"] = [f"{v:.1f}" for v in merito + inflex]  # publicados como texto, como no ONS
    t["val_progordemmerito"] = [f"{v:.1f}" for v in merito]
    t["val_proginflexibilidade"] = [f"{v:.1f}" for v in inflex]
    t["val_proginflexpura"] = t["val_proginflexibilidade"]
    t["val_verifgeracao"] = [f"{v:.1f}" for v in verificado]
    t["val_verifinflexibilidade"] = [f"{v:.1f}" for v in inflex_verificada]
    t["val_verifinflexpura"] = t["val_verifinflexibilidade"]
    t["val_verifordemmerito"] = [f"{v:.1f}" for v in verificado - inflex_verificada]
    t["tip_restricaoeletrica"] = 0.0
    return t


def despacho_ficticio() -> Dict[str, pd.DataFrame]:
    """Despacho por arquivo: o anual de 2023 (código 901, sem geração), os mensais de 2024 (902 e 903 na UTE, 950 na
    UTN, com uma linha de outra usina) e o anual de 2024, que repete os mensais."""
    h23 = pd.date_range("2023-01-01 00:00", "2023-12-31 23:00", freq="h")
    h = _horas_periodo()
    hora = np.asarray(h.hour)
    programada = (hora >= 8) & (hora <= 21)
    gerada = geracao_ute(h)
    inflex_verificada = np.where(gerada >= 100.0, 30.0, 0.0)
    inflex_verificada[np.asarray(h.normalize() == INFLEX_PARCIAL_UTE) & programada] = 20.0
    utn = np.where(_entre(h, PARADA_UTN), 0.0, 600.0)
    outra = pd.DataFrame({"din_instante": h[:2], "nom_usina": "UTE OUTRA", "cod_usinaplanejamento": 999.0,
                          "ceg": "UTE.GN.GO.000999-0.01", "val_proggeracao": "5.0", "val_verifgeracao": "5.0"})
    anos_2024 = pd.concat([
        _linhas_despacho("ute", CODIGOS_UTE["gas"], h, np.where(programada, 70.0, 0.0), np.where(programada, 30.0, 0.0),
                         gerada, inflex_verificada),
        _linhas_despacho("ute", CODIGOS_UTE["oleo"], h, 0.0, 0.0, 0.0, 0.0),
        _linhas_despacho("utn", CODIGO_UTN, h, 0.0, utn, utn, utn),
        outra,
    ], ignore_index=True)
    arquivos = {"GERACAO_TERMICA_DESPACHO_2023.parquet":
                _linhas_despacho("ute", CODIGOS_UTE["antigo"], h23, 0.0, 0.0, 0.0, 0.0),
                "GERACAO_TERMICA_DESPACHO_2024.parquet": anos_2024}
    for sufixo, g in _por_mes(anos_2024).items():
        arquivos[f"GERACAO_TERMICA_DESPACHO-2_{sufixo}.parquet"] = g
    return arquivos


def _semanas(inicio: str, fim: str) -> pd.DatetimeIndex:
    return pd.date_range(inicio, fim, freq="7D")  # sábados, início da semana operativa


def cvu_ficticio() -> Dict[str, pd.DataFrame]:
    """CVU por ano: duas revisões por semana (vale a mais recente), um CVU negativo da 903 e linhas de outras usinas."""
    def linhas(semanas, codigos, subsistema="SE"):
        saida = []
        for s in semanas:
            for codigo in codigos:
                for revisao, valor in enumerate(CVU_UTE.get(codigo, (20.0, 20.0))):
                    saida.append({"dat_iniciosemana": s, "dat_fimsemana": s + pd.Timedelta(days=6),
                                  "ano_referencia": s.year, "mes_referencia": s.month, "num_revisao": revisao,
                                  "nom_semanaoperativa": f"S {s:%d/%m/%Y}", "cod_usinaplanejamento": codigo,
                                  "id_subsistema": subsistema, "nom_subsistema": "SUDESTE", "nom_usina": f"U{codigo}",
                                  "val_cvu": valor})
        return saida
    s23 = _semanas("2022-12-31", "2023-12-23")
    s24 = _semanas("2023-12-30", "2024-02-24")
    l24 = linhas(s24, [CODIGOS_UTE["gas"], CODIGOS_UTE["oleo"], CODIGO_UTN]) + linhas(s24[:1], [999])
    l24 += [{**l24[0], "id_subsistema": "NE", "val_cvu": 1.0}]  # o código da UTE no subsistema errado
    negativo = next(i for i, x in enumerate(l24) if x["cod_usinaplanejamento"] == CODIGOS_UTE["oleo"]
                    and x["num_revisao"] == 1 and x["dat_iniciosemana"] == s24[2])
    l24[negativo]["val_cvu"] = -1.0
    return {"CVU_USINA_TERMICA_2023.parquet": pd.DataFrame(linhas(s23, [CODIGOS_UTE["antigo"]])),
            "CVU_USINA_TERMICA_2024.parquet": pd.DataFrame(l24)}


def cmo_ficticio() -> Dict[str, pd.DataFrame]:
    """CMO semanal (sexta-feira de cada semana), com o NE e uma semana republicada com outro valor em 2024."""
    def linhas(semanas, ano):
        return [{"id_subsistema": sub, "nom_subsistema": nome, "din_instante": s + pd.Timedelta(days=6),
                 **{c: f"{(CMO_SE[ano] if sub == 'SE' else 10.0):.2f}"
                    for c in ("val_cmomediasemanal", "val_cmoleve", "val_cmomedia", "val_cmopesada")}}
                for s in semanas for sub, nome in (("SE", "SUDESTE"), ("NE", "NORDESTE"))]
    l24 = linhas(_semanas("2023-12-30", "2024-02-24"), 2024)
    l24.append({**l24[2], "val_cmomediasemanal": "105.00"})  # republicada: vale a publicada por último
    return {"CMO_SEMANAL_2023.parquet": pd.DataFrame(linhas(_semanas("2022-12-31", "2023-12-23"), 2023)),
            "CMO_SEMANAL_2024.parquet": pd.DataFrame(l24)}


def _termicas(raw: Path) -> None:
    _ute_2023(raw)
    for nome, t in despacho_ficticio().items():
        _parquet(t, raw / "geracao_termica_despacho_2" / nome)
    for nome, t in cvu_ficticio().items():
        _parquet(t, raw / "cvu_usitermica" / nome)
    for nome, t in cmo_ficticio().items():
        _parquet(t, raw / "cmo_semanal" / nome)


# ---------------------------------------------------------------------------
# Eólicas e solares: fator de capacidade e restrições
# ---------------------------------------------------------------------------


def _semi_horas(inicio: pd.Timestamp) -> pd.DatetimeIndex:
    return pd.date_range(inicio, "2024-02-29 23:30", freq="30min")


def _restrita(semi: pd.DatetimeIndex, janela) -> np.ndarray:
    dias, horas = np.asarray(semi.normalize()), np.asarray(semi.hour)
    return (dias >= janela[0]) & (dias <= janela[1]) & (horas >= janela[2]) & (horas <= janela[3])


def _cabecalho(chave_ou_conjunto, semi: pd.DatetimeIndex, modalidade: str) -> Dict[str, object]:
    if isinstance(chave_ou_conjunto, str):
        u = FICTICIAS[chave_ou_conjunto]
        return {"id_subsistema": "SE", "id_estado": "GO", "nom_modalidadeoperacao": modalidade,
                "nom_usina": u["nome"], "id_ons": u["id_ons"], "ceg": u["ceg"], "din_instante": semi}
    c = chave_ou_conjunto
    return {"id_subsistema": "SE", "id_estado": "GO", "nom_modalidadeoperacao": modalidade, "nom_usina": c["nome"],
            "id_ons": c["id_ons"], "ceg": c.get("ceg", "-"), "din_instante": semi}


def fator_capacidade_ficticio() -> pd.DataFrame:
    """Fator de capacidade horário da EOL (própria) e do conjunto da UFV (CEG "-")."""
    h = _horas_periodo()
    eol, conjunto = geracao_eol(h), geracao_conjunto_ufv(h)
    return pd.concat([
        pd.DataFrame({**_cabecalho("eol", h, "TIPO I"), "val_geracaoprogramada": 16.0, "val_geracaoverificada": eol,
                      "val_capacidadeinstalada": 40.0, "val_fatorcapacidade": eol / 40.0}),
        pd.DataFrame({**_cabecalho(CONJUNTO_UFV, h, "Conjunto de Usinas"), "val_geracaoprogramada": 12.0,
                      "val_geracaoverificada": conjunto, "val_capacidadeinstalada": CAPACIDADE_CONJUNTO_UFV,
                      "val_fatorcapacidade": conjunto / CAPACIDADE_CONJUNTO_UFV}),
    ], ignore_index=True)


def restricao_eol() -> Dict[str, pd.DataFrame]:
    """A restrição com detalhe e a com a razão da EOL, desde 15/01/2024: vento inválido de 20 a 25/01; semi-horas
    restritas de 01 a 10/02, das 10h às 17h, com 25 MW de corte; às 3h, um erro da estimativa fora da restrição."""
    semi = _semi_horas(INICIO_RESTRICAO_EOL)
    verificada = geracao_eol(semi)
    restrita = _restrita(semi, RESTRICAO_EOL)
    estimada = verificada + np.where(restrita, CORTE_EOL_MW, 0.0) + np.where(np.asarray(semi.hour) == 3, 1.0, 0.0)
    invalido = ((semi >= VENTO_INVALIDO_EOL[0]) & (semi <= VENTO_INVALIDO_EOL[1])).astype(int)
    implausivel = (semi >= VENTO_IMPLAUSIVEL_EOL[0]) & (semi <= VENTO_IMPLAUSIVEL_EOL[1])
    vento = np.where(invalido == 1, 0.0, np.where(implausivel, 120.0, 8.0))
    detalhe = pd.DataFrame({**_cabecalho("eol", semi, "TIPO I"), "nom_conjuntousina": "",
                            "val_ventoverificado": vento, "flg_dadoventoinvalido": invalido,
                            "val_geracaoestimada": estimada, "val_geracaoverificada": verificada,
                            "id_ons_conjuntousina": "", "flg_geracaorestrita": restrita.astype(int),
                            "val_geracaoreferenciafinal": np.nan})
    dias = np.asarray(semi.normalize())
    codigo = np.full(len(semi), None, dtype=object)
    for razao, (inicio, fim) in RAZOES_EOL.items():
        codigo[restrita & (dias >= pd.Timestamp(inicio)) & (dias <= pd.Timestamp(fim))] = razao
    razao = pd.DataFrame({**_cabecalho("eol", semi, "TIPO I"), "val_geracao": verificada,
                          "val_geracaolimitada": np.where(restrita, verificada, np.nan),
                          "val_disponibilidade": estimada, "val_geracaoreferencia": estimada,
                          "cod_razaorestricao": codigo,
                          **{f"num_minutos_{r.lower()}": np.where(codigo == r, 30, 0) for r in RAZOES_EOL}})
    return {"detalhe": detalhe, "razao": razao}


def restricao_ufv() -> Dict[str, pd.DataFrame]:
    """A restrição com detalhe da UFV (desde 25/01/2024) e do membro, e a com a razão do conjunto; o arquivo de
    janeiro da detalhada no esquema antigo (sem as cinco colunas, marca de irradiância booleana)."""
    partes = []
    for chave, inicio, pico in (("ufv", INICIO_UFV, 20.0), (MEMBRO_UFV, pd.Timestamp("2024-01-01"), 8.0)):
        semi = _semi_horas(inicio)
        verificada = solar(semi, pico)
        restrita = _restrita(semi, RESTRICAO_UFV) if chave == "ufv" else np.zeros(len(semi), dtype=bool)
        estimada = verificada + np.where(restrita, CORTE_UFV_MW, 0.0)
        if chave == "ufv":
            estimada = np.where(semi.isin(ESTIMADA_AUSENTE_UFV), 0.0, estimada)
        cabecalho = _cabecalho(chave, semi, "TIPO II-C")
        partes.append(pd.DataFrame({**cabecalho, "nom_conjuntousina": CONJUNTO_UFV["nome"],
                                    "val_irradianciaverificado": solar(semi, 800.0),
                                    "flg_dadoirradianciainvalido": 0,
                                    "val_geracaoestimada": estimada,
                                    "val_geracaoverificada": verificada, "id_ons_conjuntousina": CONJUNTO_UFV["id_ons"],
                                    "flg_geracaorestrita": restrita.astype(int), "val_geracaoreferenciafinal": np.nan,
                                    "nom_origemirradiancia": "Supervisão", "flg_dadoirradianciasupervisaoinvalido": 0}))
    detalhe = pd.concat(partes, ignore_index=True)
    semi = _semi_horas(pd.Timestamp("2024-01-01"))
    restrita = _restrita(semi, RESTRICAO_UFV)
    conjunto = geracao_conjunto_ufv(semi)
    razao = pd.DataFrame({**_cabecalho(CONJUNTO_UFV, semi, "Conjunto de Usinas"), "val_geracao": conjunto,
                          "val_geracaolimitada": np.where(restrita, conjunto, np.nan),
                          "val_disponibilidade": conjunto + np.where(restrita, CORTE_UFV_MW, 0.0),
                          "val_geracaoreferencia": conjunto + np.where(restrita, CORTE_UFV_MW, 0.0),
                          "cod_razaorestricao": np.where(restrita, "REL", None),
                          "num_minutos_rel": np.where(restrita, 30, 0), "num_minutos_cnf": 0, "num_minutos_ene": 0})
    return {"detalhe": detalhe, "razao": razao}


ESQUEMA_ANTIGO = ["id_ons_conjuntousina", "nom_origemirradiancia", "flg_dadoirradianciasupervisaoinvalido",
                  "val_geracaoreferenciafinal", "flg_geracaorestrita"]


def _renovaveis(raw: Path) -> None:
    for sufixo, t in _por_mes(fator_capacidade_ficticio()).items():
        _parquet(t, raw / "fator_capacidade_2" / f"FATOR_CAPACIDADE-2_{sufixo}.parquet")
    eol, ufv = restricao_eol(), restricao_ufv()
    for sufixo, t in _por_mes(eol["detalhe"]).items():
        _parquet(t, raw / "restricao_coff_eolica_detail" / f"RESTRICAO_COFF_EOLICA_DETAIL_{sufixo}.parquet")
    for sufixo, t in _por_mes(eol["razao"]).items():
        _parquet(t, raw / "restricao_coff_eolica_usi" / f"RESTRICAO_COFF_EOLICA_{sufixo}.parquet")
    for sufixo, t in _por_mes(ufv["detalhe"]).items():
        if sufixo == "2024_01":  # esquema antigo
            t = t.drop(columns=ESQUEMA_ANTIGO).assign(flg_dadoirradianciainvalido=False)
        _parquet(t, raw / "restricao_coff_fotovoltaica_detail" / f"RESTRICAO_COFF_FOTOVOLTAICA_DETAIL_{sufixo}.parquet")
    for sufixo, t in _por_mes(ufv["razao"]).items():
        _parquet(t, raw / "restricao_coff_fotovoltaica" / f"RESTRICAO_COFF_FOTOVOLTAICA_{sufixo}.parquet")


def _hidrologia_cgh(raw: Path) -> None:
    """Dados hidrológicos da CGH, acrescentados aos arquivos da UHE fictícia, na convenção de fim de
    hora (a última hora do dia às 23:59), com a vazão turbinada proporcional à geração e um dia de cheia."""
    h = _horas_periodo()
    turbinada = geracao_cgh(h) / PRODUTIVIDADE_CGH
    vertida = np.where(np.asarray(h.normalize() == CHEIA_CGH), 30.0, 1.0)
    instantes = pd.Series(h)
    publicado = instantes.where(instantes.dt.hour != 23, instantes.dt.normalize() + pd.Timedelta(minutes=23 * 60 + 59))
    publicado = publicado.where(instantes.dt.hour == 23, instantes + pd.Timedelta(hours=1))
    hid = pd.DataFrame({
        "id_reservatorio": ID_RESERVATORIO_CGH, "nom_reservatorio": FICTICIAS["cgh"]["nome"], "cod_usina": float(COD_USINA_CGH),
        "din_instante": publicado, "val_nivelmontante": 520.0, "val_niveljusante": 500.0, "val_volumeutil": 80.0,
        "val_vazaoafluente": turbinada + vertida, "val_vazaodefluente": turbinada + vertida,
        "val_vazaoturbinada": turbinada, "val_vazaovertida": vertida, "val_vazaooutrasestruturas": np.nan,
        "val_vazaovertidanaoturbinavel": 0.0,
    })
    for mes, g in hid.groupby(h.to_period("M")):
        _acrescentar(g, raw / "dados_hidrologicos_ho" / f"DADOS_HIDROLOGICOS_HO_{mes.year}_{mes.month:02d}.parquet")


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
    _termicas(raw)
    _renovaveis(raw)
    _hidrologia_cgh(raw)
