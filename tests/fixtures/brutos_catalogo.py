"""Brutos sintéticos para o catálogo de usinas (spec 006, decisões R1 a R3, R21 e R31), no formato do ONS.

Um pequeno "Brasil" fictício, em GO e MT, que exercita os casos do catálogo:
- UHE com EVT e dados hidrológicos, ligada pelos Reservatórios (R31);
- PCH em conjunto de usinas, com linhas próprias sem valor na geração e um conjunto que teve uma térmica até 07/2025;
- UTE Tipo I com duas unidades ativas e duas desativadas;
- UFV em conjunto, sem id ONS no cadastro, com potência autorizada divergente da soma das unidades (vírgula decimal);
- CGH Tipo III (só agregado), uma linha de conjunto sem CEG, um CEG de prefixo desconhecido;
- EOL com o tipo publicado pelo ONS diferente do tipo do CEG; UHE sem nenhum dado;
- agregados de MMGD e de Tipo III na geração, com uma hora repetida e horas ausentes.

Nenhum valor de usina real. ``HOJE`` fixa a data do catálogo: os 12 meses completos vão de 10/2025 a 09/2026.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

HOJE = date(2026, 10, 19)
MESES_GERACAO = pd.period_range("2025-09", "2026-09", freq="M")  # 2025-09 fica fora dos 12 meses completos

UHE = {"ceg": "UHE.PH.GO.000001-0.01", "id_ons": "GOUHFI", "cod_usina": 999, "res_id": "PNUHFI",
       "reservatorio": "FICTICIO"}
PCH = {"ceg": "PCH.PH.GO.000010-0.01", "id_ons": "GOPCHA", "conjunto": "CJU_GOCJA"}
UTE = {"ceg": "UTE.GN.GO.000020-0.01", "id_ons": "GOUTEB"}
UFV = {"ceg": "UFV.RS.GO.000030-0.01", "id_ons_composicao": "GOUFVG", "conjunto": "CJU_GOCJB"}
CGH = {"ceg": "CGH.PH.GO.000040-0.01", "id_ons": "GOCGHD"}
OUTRO = {"ceg": "UTX.XX.GO.000050-0.01", "id_ons": "GOUTXE"}
EOL = {"ceg": "EOL.CV.MT.000060-0.01", "id_ons": "MTEOLZ"}
SEM_DADOS = {"ceg": "UHE.PH.MT.000070-0.01", "id_ons": "MTUHSD", "cod_usina": 888, "res_id": "PNUHSE"}
UTE_ANTIGA = {"ceg": "UTE.BI.GO.000011-0.01", "id_ons": "GOUTEA"}

CABECALHO_CADASTRO = ("nom_usina;ceg;nom_modalidadeoperacao;val_potenciaautorizada;sgl_centrooperacao;nom_pontoconexao;"
                      "id_estado;nom_estado;sts_aneel;id_ons")
LINHAS_CADASTRO = [
    f"UHE FICTICIA;{UHE['ceg']};TIPO II-B;90.000;COSR-NCO       ;SE FICTICIA 230 KV;GO;GOIAS   ;A;{UHE['id_ons']}",
    f"PCH ALFA;{PCH['ceg']};TIPO II-C;28.000;COSR-NCO       ;SE ALFA 138 KV;GO;GOIAS   ;A;{PCH['id_ons']}",
    f"UTE BETA;{UTE['ceg']};TIPO I;150.000;COSR-NCO       ;SE BETA 230 KV;GO;GOIAS   ;A;{UTE['id_ons']}",
    f"UFV GAMA;{UFV['ceg']};TIPO II-C;2,507;COSR-NCO       ;SE GAMA 230 KV;GO;GOIAS   ;A;",
    f"CGH DELTA;{CGH['ceg']};TIPO III;1.000;COSR-NCO       ;Rede de Distribuição 13,8 kV;GO;GOIAS   ;A;{CGH['id_ons']}",
    "CONJUNTO ALFA;;TIPO II-C;50.000;COSR-NCO       ;SE ALFA 138 KV;GO;GOIAS   ;A;",
    f"USINA EPSILON;{OUTRO['ceg']};TIPO I;10.000;COSR-NCO       ;SE EPSILON;GO;GOIAS   ;A;{OUTRO['id_ons']}",
    f"EOL ZETA;{EOL['ceg']};TIPO I;30.000;COSR-NCO       ;SE ZETA 230 KV;MT;MATO GROSSO   ;A;{EOL['id_ons']}",
    f"UHE SEM DADOS;{SEM_DADOS['ceg']};TIPO I;200.000;COSR-NCO       ;SE OMEGA 500 KV;MT;MATO GROSSO   ;A;{SEM_DADOS['id_ons']}",
]


def _parquet(tabela: pd.DataFrame, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_parquet(caminho, index=False)


def _csv(tabela: pd.DataFrame, caminho: Path) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_csv(caminho, sep=";", index=False, date_format="%Y-%m-%d %H:%M:%S")


def _horas(mes: pd.Period) -> pd.DatetimeIndex:
    return pd.date_range(mes.start_time, mes.end_time.floor("h"), freq="h")


def gravar_cadastrais(raw: Path) -> None:
    """Modalidade das usinas (CSV), Composição dos conjuntos, Capacidade de geração e Reservatórios (Parquet)."""
    (raw / "modalidade_usina").mkdir(parents=True, exist_ok=True)
    (raw / "modalidade_usina" / "MODALIDADE_USINA.csv").write_text(
        "\n".join([CABECALHO_CADASTRO, *LINHAS_CADASTRO]) + "\n", encoding="utf-8")

    def membro(conjunto, nome_conjunto, ceg, id_ons, nome, tipo_ons, inicio, fim):
        return {"id_subsistema": "SE", "nom_subsistema": "Sudeste/Centro-Oeste", "estad_id": "GO", "nom_estado": "GOIAS",
                "id_tipousina": tipo_ons, "nom_tipousina": "Hidroelétrica ", "id_conjuntousina": 3,
                "id_ons_conjunto": conjunto, "id_ons_usina": id_ons, "nom_conjunto": nome_conjunto, "nom_usina": nome,
                "ceg": ceg, "dat_iniciorelacionamento": inicio, "dat_fimrelacionamento": fim}
    _parquet(pd.DataFrame([
        membro(PCH["conjunto"], "CONJ. HIDRAULICO ALFA", PCH["ceg"], PCH["id_ons"], "PCH ALFA", "UHE", "2019-08-22",
               "9999-12-31"),
        membro(PCH["conjunto"], "CONJ. HIDRAULICO ALFA", UTE_ANTIGA["ceg"], UTE_ANTIGA["id_ons"], "UTE ANTIGA", "UTE",
               "2019-08-22", "2025-07-01"),
        membro(UFV["conjunto"], "CONJ. FOTOVOLTAICO BETA", UFV["ceg"], UFV["id_ons_composicao"], "UFV GAMA", "UFV",
               "13/04/2026", ""),
    ]), raw / "usina_conjunto" / "USINA_CONJUNTO.parquet")

    def ug(nome, ceg, tipo_ons, estado, n, potencia, combustivel, entrada, desativacao="9999-12-31"):
        return {"id_subsistema": "SE", "nom_subsistema": "SUDESTE ", "id_estado": estado, "nom_estado": estado,
                "nom_modalidadeoperacao": "TIPO I", "nom_agenteproprietario": "AGENTE", "nom_agenteoperador": "AGENTE",
                "nom_tipousina": tipo_ons, "nom_usina": nome, "ceg": ceg, "nom_unidadegeradora": f"UG{n}",
                "cod_equipamento": f"{ceg}-UG{n}", "num_unidadegeradora": str(n), "nom_combustivel": combustivel,
                "dat_entradateste": "0001-01-01", "dat_entradaoperacao": entrada, "dat_desativacao": desativacao,
                "val_potenciaefetiva": potencia}
    unidades = [ug("UHE FICTICIA", UHE["ceg"], "HIDROELÉTRICA", "GO", n, 30.0, "HIDRÁULICA", "2013-05-01")
                for n in (1, 2, 3)]
    unidades += [ug("PCH ALFA", PCH["ceg"], "HIDROELÉTRICA", "GO", n, 9.3333, "HIDRÁULICA", "2019-08-22")
                 for n in (1, 2, 3)]
    unidades += [ug("UTE BETA", UTE["ceg"], "TÉRMICA", "GO", n, 75.0, "GÁS", "2021-07-10") for n in (1, 2)]
    unidades += [ug("UTE BETA", UTE["ceg"], "TÉRMICA", "GO", n, 50.0, "GÁS", "2013-01-01", "2018-05-01")
                 for n in (3, 4)]
    unidades += [ug("UFV GAMA", UFV["ceg"], "FOTOVOLTAICA", "GO", 1, 21.43, "FOTOVOLTAICA", "2026-08-22", ""),
                 ug("UFV GAMA", UFV["ceg"], "FOTOVOLTAICA", "GO", 2, 28.57, "FOTOVOLTAICA", "2026-08-22", "")]
    unidades += [ug("EOL ZETA", EOL["ceg"], "FOTOVOLTAICA", "MT", 1, 30.0, "EÓLICA", "2015-01-01")]
    _parquet(pd.DataFrame(unidades), raw / "capacidade_geracao" / "CAPACIDADE_GERACAO.parquet")

    _parquet(pd.DataFrame([
        {"nom_reservatorio": UHE["reservatorio"], "tip_reservatorio": "FIO DAGUA", "cod_resplanejamento": UHE["cod_usina"],
         "nom_usina": "FICTÍCIA", "ceg": UHE["ceg"], "res_id": UHE["res_id"]},
        {"nom_reservatorio": "OMEGA", "tip_reservatorio": "FIO DAGUA", "cod_resplanejamento": SEM_DADOS["cod_usina"],
         "nom_usina": "SEM DADOS", "ceg": SEM_DADOS["ceg"], "res_id": SEM_DADOS["res_id"]},
    ]), raw / "reservatorio" / "RESERVATORIO.parquet")


def gravar_series(raw: Path) -> None:
    """O arquivo mais recente (e um anterior) de cada conjunto de série, e a geração de 09/2025 a 09/2026."""
    setembro, agosto = pd.Period("2026-09", "M"), pd.Period("2026-08", "M")
    # EVT: só o arquivo mais recente vale; o anterior traria a UHE sem dados, que fica "ausente"
    for mes, cod in ((setembro, UHE["cod_usina"]), (agosto, SEM_DADOS["cod_usina"])):
        horas = _horas(mes)[:24]
        evt = pd.DataFrame({"id_subsistema": "SE", "nom_reservatorio": "X", "cod_usina": cod, "din_instante": horas,
                            "val_geracao": 70.0, "val_disponibilidade": 90.0})
        outra = evt.head(2).assign(cod_usina=111)
        _csv(pd.concat([evt, outra]), raw / f"ENERGIA_VERTIDA_TURBINAVEL_{mes.year}_{mes.month:02d}.csv")
    horas = _horas(setembro)[:24]
    _parquet(pd.DataFrame({"id_reservatorio": UHE["res_id"], "nom_reservatorio": "X", "cod_usina": float(UHE["cod_usina"]),
                           "din_instante": horas, "val_vazaoturbinada": 100.0, "val_vazaovertida": 5.0}),
             raw / "dados_hidrologicos_ho" / "DADOS_HIDROLOGICOS_HO_2026_09.parquet")
    disp = pd.concat([pd.DataFrame({"id_estado": "GO", "id_ons": i, "ceg": c, "din_instante": horas,
                                    "val_dispoperacional": 50.0, "val_dispsincronizada": 40.0})
                      for i, c in ((UHE["id_ons"], UHE["ceg"]), (UTE["id_ons"], UTE["ceg"]))])
    _parquet(disp, raw / "disponibilidade_usina" / "DISPONIBILIDADE_USINA_2026_09.parquet")
    _csv(pd.DataFrame({"ceg": [UHE["ceg"], UTE["ceg"]], "id_usina": [UHE["id_ons"], UTE["id_ons"]],
                       "dat_mesreferencia": "2026-08-01", "val_dispf": "99.0"}),
         raw / "indicadores_ons" / "ind_disponibilidade_fgeracao_uge_mensal"
         / "IND_DISPONIBILIDADE_FCGERACAO_UGE_MENSAL_2026.csv")

    def programacao(codigos: List[str], dia: str) -> pd.DataFrame:
        linhas = [{"din_programacaodia": dia, "num_patamar": p, "cod_exibicaousina": c, "nom_usina": f"USINA {c}",
                   "nom_modalidadeoperacao": "TIPO I", "id_estado": "MT" if c.startswith("MT") else "GO",
                   "val_geracaoprogramada": np.nan if (c == "GOCJA-102" and p > 24) else 10.0}
                  for c in codigos for p in range(1, 49)]
        return pd.DataFrame(linhas)
    codigos = [UHE["id_ons"], UTE["id_ons"], "GOCJA-101", "GOCJA-102", "GOCJB", "GOOUTRO", EOL["id_ons"]]
    _parquet(programacao(codigos, "2026-10-18"), raw / "programacao_diaria" / "PROGRAMACAO_DIARIA_2026_10_18.parquet")
    _parquet(programacao(["GOVELHO"], "2026-10-17"), raw / "programacao_diaria" / "PROGRAMACAO_DIARIA_2026_10_17.parquet")

    for mes in MESES_GERACAO:
        _parquet(geracao_do_mes(mes), raw / "geracao_usina_2" / f"GERACAO_USINA-2_{mes.year}_{mes.month:02d}.parquet")
    gravar_termicas(raw)


# Fase B (spec 006): códigos de planejamento da UTE no despacho; o 71 sai em 09/2026, o 70 é vigente
PLANEJAMENTO_UTE = {7: ("2018-01", "2018-08"), 70: ("2026-09", "2026-10"), 71: ("2026-09", "2026-09")}


def _despacho(ceg: str, codigo: float, horas: pd.DatetimeIndex, nome: str) -> pd.DataFrame:
    return pd.DataFrame({"din_instante": horas, "nom_tipopatamar": "LEVE", "id_subsistema": "SE",
                         "nom_subsistema": "SUDESTE", "nom_usina": nome, "cod_usinaplanejamento": codigo, "ceg": ceg,
                         "val_proggeracao": "10.0", "val_verifgeracao": "9.5"})


def gravar_termicas(raw: Path) -> None:
    """Despacho (um arquivo anual antigo e dois mensais) e CVU: os códigos de planejamento do catálogo."""
    pasta = raw / "geracao_termica_despacho_2"
    _parquet(pd.concat([_despacho(UTE["ceg"], 7.0, pd.DatetimeIndex(["2018-01-01 00:00", "2018-08-10 23:00"]),
                                  "UTE BETA"),
                        _despacho(UTE_ANTIGA["ceg"], 8.0, pd.DatetimeIndex(["2018-03-01 00:00"]), "UTE ALFA")]),
             pasta / "GERACAO_TERMICA_DESPACHO_2018.parquet")
    _parquet(pd.concat([_despacho(UTE["ceg"], 70.0, _horas(pd.Period("2026-09", "M"))[:2], "UT BETA"),
                        _despacho(UTE["ceg"], 71.0, _horas(pd.Period("2026-09", "M"))[:2], "UT BETA")]),
             pasta / "GERACAO_TERMICA_DESPACHO-2_2026_09.parquet")
    _parquet(_despacho(UTE["ceg"], 70.0, _horas(pd.Period("2026-10", "M"))[:2], "UTE BETA"),
             pasta / "GERACAO_TERMICA_DESPACHO-2_2026_10.parquet")
    semanas = pd.date_range("2026-09-26", periods=2, freq="7D")
    _parquet(pd.DataFrame([{"dat_iniciosemana": s, "dat_fimsemana": s + pd.Timedelta(days=6), "num_revisao": 0,
                            "cod_usinaplanejamento": c, "id_subsistema": "SE", "nom_usina": "W", "val_cvu": v}
                           for s in semanas for c, v in ((70, 300.0), (71, 0.0), (999, 50.0))]),
             raw / "cvu_usitermica" / "CVU_USINA_TERMICA_2026.parquet")


def geracao_do_mes(mes: pd.Period) -> pd.DataFrame:
    """Geração por usina de um mês: usinas, conjuntos e os grupos agregados do estado."""
    horas = _horas(mes)
    series: Dict[tuple, float] = {
        ("TIPO II-B", "HIDROELÉTRICA", "UHE FICTICIA", UHE["id_ons"], UHE["ceg"], "GO"): 70.0,
        ("TIPO I", "TÉRMICA", "UTE BETA", UTE["id_ons"], UTE["ceg"], "GO"): 100.0,
        ("TIPO II-C", "HIDROELÉTRICA", "PCH ALFA", PCH["id_ons"], PCH["ceg"], "GO"): np.nan,  # linhas próprias sem valor
        ("Conjunto de Usinas", "HIDROELÉTRICA", "CONJ. HIDRAULICO ALFA", PCH["conjunto"], "-", "GO"): 20.0,
        ("Conjunto de Usinas", "FOTOVOLTAICA", "CONJ. FOTOVOLTAICO BETA", UFV["conjunto"], "-", "GO"): 15.0,
        ("TIPO I", "EOLIELÉTRICA", "EOL ZETA", EOL["id_ons"], EOL["ceg"], "MT"): 12.0,
        ("TIPO III", "HIDROELÉTRICA", "CGH DELTA", CGH["id_ons"], CGH["ceg"], "GO"): 0.5,
        ("Pequenas Usinas (MMGD)", "FOTOVOLTAICA", "PQU GOGO MMGD", None, "-", "GO"): 30.0,
        ("Pequenas Usinas (Tipo III)", "HIDROELÉTRICA", "PQU GOGO TIPO III", None, "-", "GO"): 4.0,
    }
    partes = []
    for (modalidade, tipo, nome, id_ons, ceg, estado), valor in series.items():
        t = pd.DataFrame({"din_instante": horas, "id_subsistema": "SE", "nom_subsistema": "SUDESTE", "id_estado": estado,
                          "nom_estado": estado, "cod_modalidadeoperacao": modalidade, "nom_tipousina": tipo,
                          "nom_tipocombustivel": tipo, "nom_usina": nome, "id_ons": id_ons, "ceg": ceg,
                          "val_geracao": valor})
        if modalidade == "Pequenas Usinas (Tipo III)" and mes == pd.Period("2026-08", "M"):
            t = t.iloc[10:]  # 10 horas ausentes
        if modalidade == "Pequenas Usinas (MMGD)" and mes == pd.Period("2026-09", "M"):
            t = pd.concat([t, t.head(1)])  # uma hora repetida
        partes.append(t)
    return pd.concat(partes, ignore_index=True)


def gerar_brutos_catalogo(raw: Path) -> None:
    """Grava os cadastrais e as séries em ``raw`` (uma pasta ``data/raw`` temporária)."""
    raw = Path(raw)
    gravar_cadastrais(raw)
    gravar_series(raw)
