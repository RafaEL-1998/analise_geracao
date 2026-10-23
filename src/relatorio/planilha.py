"""Planilha e CSV do relatório: uma aba por tabela (nas usinas sem EVT, as abas das seções comuns)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

import pandas as pd

from src.analises.conjunto import em_duas_partes
from src.analises.resultados import ResultadosAnalise, sem_evt
from src.comum.logger import setup_logger
from src.relatorio.conteudo import tabela_conclusao
from src.relatorio.fontes import tabela_fontes_abas

logger = setup_logger("relatorio")


def _globais_como_tabela(res: ResultadosAnalise) -> pd.DataFrame:
    linhas = []
    for chave, valor in res.globais.items():
        linhas.append({"indicador": chave, "valor": str(valor) if isinstance(valor, pd.Timestamp) else valor})
    c = res.cobertura
    linhas += [
        {"indicador": "inicio_serie", "valor": str(c["inicio"])},
        {"indicador": "fim_serie", "valor": str(c["fim"])},
        {"indicador": "horas_ausentes", "valor": ", ".join(str(t) for t in c["horas_faltantes"])},
        {"indicador": "anos_parciais", "valor": ", ".join(str(a) for a in c["anos_parciais"])},
        {"indicador": "mes_mudanca_classificacao_vertimento",
         "valor": str(res.mudanca_classificacao.get("mes") or "")},
    ]
    return pd.DataFrame(linhas)


def _abas_sem_evt(res: ResultadosAnalise) -> Dict[str, pd.DataFrame]:
    """Abas das usinas sem EVT: as seções comuns, os indicadores do ONS, a qualidade, os trechos e as omissões."""
    c = res.comum
    abas: Dict[str, Optional[pd.DataFrame]] = {
        "CONSTATACOES": pd.DataFrame(res.achados, columns=["tema", "constatacao"]),
        "CONCLUSAO": tabela_conclusao(res),
        "BASE_ANUAL": c["anuais"],
        "BASE_MENSAL": c["mensal"],
        "BASE_MES_DO_ANO": c["sazonalidade"],
        "BASE_HORA_DO_DIA": c["perfil_horario"],
        "BASE_SINALIZACOES": c["qualidade"]["sinalizacoes"],
        "GER_AUSENCIAS": c["qualidade"]["ausencias"],
        "TRECHOS": res.trechos,
        "OMITIDOS": pd.DataFrame(res.omitidos, columns=["item", "tipo", "motivo"]),
        "CONF_NAO_APLICAVEIS": c.get("conferencias_nao_aplicaveis"),
        "PARAMETROS": res.parametros,
    }
    d = c.get("disponibilidade") or {}
    abas.update({"DISP_MENSAL": d.get("mensal"), "DISP_ANUAL": d.get("anual"),
                 "DISP_EVENTOS_INDISP_TOTAL": d.get("eventos_indisponibilidade_total")})
    p = c.get("programacao") or {}
    abas.update({"PROG_RESUMO_MENSAL": p.get("mensal"), "PROG_EVENTOS_DESVIO": p.get("eventos")})
    t = getattr(res, "termica", None) or {}
    if t:  # seções de térmica: as tabelas completas
        a = t.get("atendimento") or {}
        d = t.get("disponivel_sem_despacho") or {}
        cv = t.get("cvu_cmo") or {}
        abas.update({"TERM_MOTIVOS_ANUAL": t.get("motivos_anual"), "TERM_MOTIVOS_MENSAL": t.get("motivos_mensal"),
                     "TERM_INFLEXIBILIDADE": t.get("inflexibilidade"), "TERM_ATENDIMENTO_ANUAL": a.get("anual"),
                     "TERM_ATENDIMENTO_MENSAL": a.get("mensal"), "TERM_MAIORES_DESVIOS": a.get("maiores_desvios"),
                     "TERM_DISP_SEM_DESPACHO": d.get("anual"), "TERM_CVU_CMO_SEMANAL": cv.get("semanal"),
                     "TERM_CVU_CMO_RESUMO": cv.get("resumo")})
        for sigla, cid in (("G3", "programacao_despacho"), ("G4", "verificada_despacho")):
            conf = (t.get("conferencias") or {}).get(cid) or {}
            abas.update({f"CONF_{sigla}_MENSAL": conf.get("mensal"), f"CONF_{sigla}_DIVERGENCIAS": conf.get("divergencias")})
    r = getattr(res, "renovavel", None) or {}
    if r:  # seções de eólica e solar: as tabelas completas
        fc, corte, rec, prog = (r.get(k) or {} for k in ("fator_capacidade", "restricao", "recurso", "programacao"))
        abas.update({"REN_FC_ANUAL": fc.get("anual"), "REN_FC_MENSAL": fc.get("mensal"),
                     "REN_CORTE_ANUAL": corte.get("anual"), "REN_CORTE_MENSAL": corte.get("mensal"),
                     "REN_CORTE_RAZAO": corte.get("por_razao"), "REN_RECURSO_FAIXAS": rec.get("faixas"),
                     "REN_DESVIOS_PROGRAMACAO": prog.get("maiores_desvios")})
        conferencias = r.get("conferencias") or {}
        abas["CONF_G1_PARES"] = (conferencias.get("geracao_fontes") or {}).get("pares")
        for sigla, cid in (("G1", "geracao_fontes"), ("G2", "soma_conjunto"), ("G5", "programacao_renovaveis")):
            conf = conferencias.get(cid) or {}
            abas.update({f"CONF_{sigla}_MENSAL": conf.get("mensal"), f"CONF_{sigla}_DIVERGENCIAS": conf.get("divergencias")})
    cj = getattr(res, "conjunto", None) or {}
    if cj:  # seção do conjunto: as tabelas completas, com a composição de cada trecho
        abas.update({"CONJ_TRECHOS": cj.get("trechos"), "CONJ_COMPOSICAO": cj.get("composicao"),
                     "CONJ_MENSAL": cj.get("mensal"), "CONJ_TIPO_PUBLICADO": cj.get("tipo_publicado"),
                     "CONJ_PESO_USINA": cj.get("peso_usina") if em_duas_partes(res) else None})
    h = res.hidrologia or {}
    if h:  # afluência da hidrelétrica sem EVT
        abas.update({"HID_ALINHAMENTO": h.get("alinhamento"), "HID_MENSAL": h.get("mensal"), "HID_ANUAL": h.get("anual"),
                     "HID_AUSENCIAS": h.get("ausencias"), "HID_AUDITORIA": h.get("auditoria")})
    return {nome: t for nome, t in abas.items()
            if t is not None and (len(t) or nome in ("CONSTATACOES", "CONCLUSAO", "BASE_ANUAL", "OMITIDOS"))}


def exportar_tabelas(
    res: ResultadosAnalise,
    caminho_xlsx: Path,
    caminho_csv: Path,
) -> Tuple[Path, Path]:
    """Exporta todas as tabelas calculadas para Excel e os indicadores anuais para CSV."""
    dest_xlsx, dest_csv = Path(caminho_xlsx), Path(caminho_csv)
    dest_xlsx.parent.mkdir(parents=True, exist_ok=True)
    if sem_evt(res):
        return _exportar_sem_evt(res, dest_xlsx, dest_csv)

    abas = {
        "CONSTATACOES": pd.DataFrame(res.achados, columns=["tema", "constatacao"]),
        "CONCLUSAO": tabela_conclusao(res),
        "INDICADORES_ANUAIS": res.indicadores_anuais,
        "INDICADORES_GLOBAIS": _globais_como_tabela(res),
        "COBERTURA_POR_ANO": res.cobertura["por_ano"],
        "AGENTES": res.cobertura["agentes"],
        "EVT_MENSAL": res.evt_mensal,
        "EVT_MES_DO_ANO": res.distribuicao_mes_do_ano,
        "EVT_POR_FAIXA_GERACAO": res.evt_por_faixa_geracao,
        "PERFIL_HORARIO_GERACAO": res.perfil_horario_geracao.reset_index(),
        "PERFIL_HORARIO_EVT": res.perfil_horario_evt.reset_index(),
        "EVENTOS_PARADA_COM_EVT": res.eventos_parada_com_evt,
        "HORAS_GERACAO_ZERO_MES": res.horas_geracao_zero,
        "EVENTOS_INDISP_TOTAL": res.eventos_indisponibilidade_total,
        "ANOMALIAS": res.anomalias,
        "RESUMO_ANOMALIAS": res.resumo_anomalias,
        "VALIDACAO_REGRAS": res.validacao,
        "EXTREMOS": res.extremos,
        "PERFIL_ESTATISTICO_ANUAL": res.perfil_estatistico,
        "PARAMETROS": res.parametros,
    }
    o = res.ons
    abas_ons = {
        "ONS_DISP_ANUAL_USINA": o.get("disp_anual"),
        "ONS_UG_ANUAL": o.get("ug_anual"),
        "ONS_HORAS_UG_ANUAL": o.get("horas_anual"),
        "ONS_HORAS_UG_MENSAL": o.get("horas_mensal"),
        "ONS_TEIFA_TEIP": o.get("recalculo_taxas"),
        "ONS_DECOMPOSICAO_TAXAS": o.get("decomposicao"),
        "ONS_DIVERGENCIAS": o.get("divergencias"),
    }
    abas.update({nome: t for nome, t in abas_ons.items() if t is not None and len(t)})
    pr = res.programacao
    abas_programacao = {
        "PROG_RESUMO_MENSAL": pr.get("mensal"),
        "PROG_EVENTOS_DESVIO": pr.get("eventos"),
        "PROG_HORA_DO_DIA": pr.get("perfil"),
        "PROG_DIAS_AUSENTES": pr.get("dias_ausentes"),
        "PROG_AUDITORIA_ARQUIVOS": pr.get("auditoria"),
        "PROG_HORAS_CLASSIFICADAS": pr.get("classificadas"),
    }
    abas.update({nome: t for nome, t in abas_programacao.items() if t is not None and len(t)})
    di = res.disponibilidade
    if di:
        abas_disponibilidade = {
            "DISP_CONFERENCIA": pd.DataFrame([di["conferencia"]]),
            "DISP_DIVERGENCIAS": di["divergencias"],
            "DISP_CLASSES_PARADA": di["classes"],
            "DISP_HORAS_PARADAS": di["horas_paradas"],
            "DISP_MENSAL": di["mensal"],
            "DISP_ANUAL": di["anual"],
            "DISP_AUSENCIAS": di["ausencias"],
            "DISP_AUDITORIA": di["auditoria"],
        }
        abas.update({nome: t for nome, t in abas_disponibilidade.items() if t is not None and len(t)})
    hi = res.hidrologia
    if hi:
        abas_hidrologia = {
            "HID_ALINHAMENTO": hi["alinhamento"],
            "HID_FAIXAS_AFLUENCIA": hi.get("faixas_mensal"),
            "HID_FAIXAS_ANUAL": hi.get("faixas_anual"),
            "HID_HORAS_EVT": hi.get("faixas"),
            "HID_MENSAL": hi.get("mensal"),
            "HID_ANUAL": hi.get("anual"),
            "HID_PERFIL_HORA_DO_DIA": hi.get("perfil"),
            "HID_AUSENCIAS": hi["ausencias"],
            "HID_AUDITORIA": hi["auditoria"],
        }
        abas.update({nome: t for nome, t in abas_hidrologia.items() if t is not None and len(t)})
    ge = res.geracao_oficial
    if ge:
        abas_geracao = {
            "GER_CONFERENCIA": pd.DataFrame([ge["conferencia"]]),
            "GER_MENSAL": ge["mensal"],
            "GER_ANUAL": ge["anual"],
            "GER_DIVERGENCIAS": ge["divergencias"],
            "GER_AUSENCIAS": ge["ausencias"],
            "GER_AUDITORIA": ge["auditoria"],
        }
        abas.update({nome: t for nome, t in abas_geracao.items() if t is not None and len(t)})
    if res.cadastro:
        abas["CAD_FICHA"] = pd.DataFrame([res.cadastro["ficha"]])
        if len(res.cadastro.get("auditoria", [])):
            abas["CAD_AUDITORIA"] = res.cadastro["auditoria"]
    registro_dicionarios = res.dicionarios.get("registro")
    if registro_dicionarios is not None and len(registro_dicionarios):
        abas["DICIONARIOS"] = registro_dicionarios
    # spec da Geração do relatório (FR-028): origem e conferências de cada aba, por último
    abas["FONTES"] = tabela_fontes_abas(res, list(abas))
    _gravar_planilha(abas, dest_xlsx)

    logger.info("Exportando indicadores anuais para CSV: %s", dest_csv)
    res.indicadores_anuais.to_csv(dest_csv, sep=";", index=False, encoding="utf-8")
    return dest_xlsx, dest_csv


def _abas_complementares(res: ResultadosAnalise, abas: Dict[str, pd.DataFrame]) -> None:
    """Indicadores do ONS, cadastro e dicionários, comuns aos dois caminhos."""
    o = res.ons
    abas_ons = {
        "ONS_DISP_ANUAL_USINA": o.get("disp_anual"),
        "ONS_UG_ANUAL": o.get("ug_anual"),
        "ONS_HORAS_UG_ANUAL": o.get("horas_anual"),
        "ONS_HORAS_UG_MENSAL": o.get("horas_mensal"),
        "ONS_TEIFA_TEIP": o.get("recalculo_taxas"),
        "ONS_DECOMPOSICAO_TAXAS": o.get("decomposicao"),
        "ONS_DIVERGENCIAS": o.get("divergencias"),
    }
    abas.update({nome: t for nome, t in abas_ons.items() if t is not None and len(t)})
    if res.cadastro:
        abas["CAD_FICHA"] = pd.DataFrame([res.cadastro["ficha"]])
        if len(res.cadastro.get("auditoria", [])):
            abas["CAD_AUDITORIA"] = res.cadastro["auditoria"]
    registro_dicionarios = res.dicionarios.get("registro")
    if registro_dicionarios is not None and len(registro_dicionarios):
        abas["DICIONARIOS"] = registro_dicionarios


def _exportar_sem_evt(res: ResultadosAnalise, dest_xlsx: Path, dest_csv: Path) -> Tuple[Path, Path]:
    abas = _abas_sem_evt(res)
    _abas_complementares(res, abas)
    abas["FONTES"] = tabela_fontes_abas(res, list(abas))
    _gravar_planilha(abas, dest_xlsx)
    logger.info("Exportando indicadores anuais para CSV: %s", dest_csv)
    res.comum["anuais"].to_csv(dest_csv, sep=";", index=False, encoding="utf-8")
    return dest_xlsx, dest_csv


def _gravar_planilha(abas: Dict[str, pd.DataFrame], dest_xlsx: Path) -> None:
    logger.info("Exportando tabelas analíticas para Excel: %s", dest_xlsx)
    with pd.ExcelWriter(dest_xlsx, engine="openpyxl") as writer:
        for nome, tabela in abas.items():
            tabela.to_excel(writer, sheet_name=nome, index=False)
            planilha = writer.sheets[nome]
            for idx, coluna in enumerate(tabela.columns, start=1):
                letra = planilha.cell(row=1, column=idx).column_letter
                planilha.column_dimensions[letra].width = min(max(len(str(coluna)), 12) + 3, 60)
            planilha.freeze_panes = "A2"
