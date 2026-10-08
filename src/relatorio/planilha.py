"""Planilha e CSV do relatório: uma aba por tabela."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd

from src.analises.resultados import ResultadosAnalise
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


def exportar_tabelas(
    res: ResultadosAnalise,
    caminho_xlsx: Path,
    caminho_csv: Path,
) -> Tuple[Path, Path]:
    """Exporta todas as tabelas calculadas para Excel e os indicadores anuais para CSV."""
    dest_xlsx, dest_csv = Path(caminho_xlsx), Path(caminho_csv)
    dest_xlsx.parent.mkdir(parents=True, exist_ok=True)

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
    logger.info("Exportando tabelas analíticas para Excel: %s", dest_xlsx)
    with pd.ExcelWriter(dest_xlsx, engine="openpyxl") as writer:
        for nome, tabela in abas.items():
            tabela.to_excel(writer, sheet_name=nome, index=False)
            planilha = writer.sheets[nome]
            for idx, coluna in enumerate(tabela.columns, start=1):
                letra = planilha.cell(row=1, column=idx).column_letter
                planilha.column_dimensions[letra].width = min(max(len(str(coluna)), 12) + 3, 60)
            planilha.freeze_panes = "A2"

    logger.info("Exportando indicadores anuais para CSV: %s", dest_csv)
    res.indicadores_anuais.to_csv(dest_csv, sep=";", index=False, encoding="utf-8")
    return dest_xlsx, dest_csv
