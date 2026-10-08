"""Conferência do cadastro: ficha da usina em Modalidade das usinas × perfil da usina (spec da Conferência, FR-017)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from src.comum.formatacao import fmt_num
from src.comum.regras import TOLERANCIA_POTENCIA_CADASTRO_MW as TOLERANCIA_POTENCIA_MW
from src.conferencia.resultado import ResultadoConferencia, diferenca_absoluta, nao_aplicavel

BASES = ("Modalidade das usinas (ficha da usina)", "perfil da usina")


def divergencias_cadastro(ficha: Dict[str, Any], perfil: Any) -> pd.DataFrame:
    """Campos conferidos da ficha: valor do cadastro, valor do perfil, situação e texto da divergência."""
    potencia = pd.to_numeric(pd.Series([ficha.get("val_potenciaautorizada", "")]), errors="coerce").iloc[0]
    esperada = perfil.potencia_autorizada_esperada_mw
    estado, id_ons = perfil.usina.estado, perfil.identificacao.id_ons
    linhas_ceg = int(pd.to_numeric(pd.Series([ficha.get("linhas_ceg", 1)]), errors="coerce").fillna(1).iloc[0])
    estado_ficha = str(ficha.get("id_estado", "") or "")
    id_ficha = str(ficha.get("id_ons", "") or "")
    campos: List[Dict[str, Any]] = [
        {"campo": "potência autorizada (MW)", "valor_cadastro": potencia, "valor_perfil": esperada,
         "diverge": bool(pd.isna(potencia) or diferenca_absoluta(potencia - esperada) > TOLERANCIA_POTENCIA_MW),
         "texto": f"potência autorizada de {fmt_num(potencia, 1)} MW (projeto: {fmt_num(esperada, 0 if float(esperada).is_integer() else 1)} MW)"},
        {"campo": "estado", "valor_cadastro": estado_ficha, "valor_perfil": estado,
         "diverge": estado_ficha.upper() != estado,
         "texto": f"estado {estado_ficha or 'não informado'} (projeto: {estado})"},
        {"campo": "id ONS", "valor_cadastro": id_ficha, "valor_perfil": id_ons,
         "diverge": id_ficha.upper() != id_ons,
         "texto": f"id ONS {id_ficha or 'não informado'} (projeto: {id_ons})"},
        {"campo": "linhas com o CEG", "valor_cadastro": linhas_ceg, "valor_perfil": 1,
         "diverge": linhas_ceg > 1,
         "texto": f"{linhas_ceg} linhas com o CEG do projeto (usada a primeira)"},
    ]
    tabela = pd.DataFrame(campos)
    tabela.insert(3, "situacao", tabela["diverge"].map({True: "DIVERGE", False: "CONFERE"}))
    return tabela


def conferencia_cadastro(ficha: Optional[pd.DataFrame], perfil: Any) -> ResultadoConferencia:
    """Resultado da conferência do cadastro; o texto das divergências é o que a ficha do relatório mostra."""
    if ficha is None or ficha.empty:
        return nao_aplicavel("cadastro", BASES, "campos", "a usina não tem ficha no cadastro do ONS",
                             tolerancia=TOLERANCIA_POTENCIA_MW)
    tabela = divergencias_cadastro(ficha.iloc[0].to_dict(), perfil)
    divergentes = tabela[tabela["diverge"]]
    return ResultadoConferencia(
        id="cadastro", bases=BASES, unidade="campos", comparados=len(tabela),
        coincidentes=len(tabela) - len(divergentes), divergentes=len(divergentes),
        tolerancia=TOLERANCIA_POTENCIA_MW,
        tabelas={"campos": tabela.drop(columns=["diverge"]), "divergencias": "; ".join(divergentes["texto"])},
    )
