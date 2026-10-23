"""Catálogo e resultados gravados fictícios para os testes da carteira (spec 006, fase E; tarefas T131 e T132).

- ``gravar_catalogo``: ``data/catalogo/`` com as linhas dadas de ``usinas.csv`` e de ``agregados.csv`` (as demais
  tabelas só com o cabeçalho), no formato que ``ler_catalogo`` aceita;
- ``gravar_analises``: ``resultados.pkl`` e ``etapa.json`` das Análises de uma usina, com o ``indicadores_carteira``
  dado e o estado e o formato do manifesto escolhidos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.analises.resultados import ResultadosAnalise, salvar_resultados
from src.coleta.catalogo_usinas import (
    COLUNAS_AGREGADOS,
    COLUNAS_COBERTURA,
    COLUNAS_CONJUNTOS,
    COLUNAS_PLANEJAMENTO,
    COLUNAS_PROGRAMACAO,
    COLUNAS_USINAS,
    VERSAO_FORMATO_CATALOGO,
)
from src.comum.caminhos import ARQUIVOS_CATALOGO

MONTADO_EM = "2026-10-22 12:00:00"
MESES = [f"2025-{m:02d}" for m in range(10, 13)] + [f"2026-{m:02d}" for m in range(1, 10)]


def linha_usina(ceg: str, nome: str, tipo: str, estado: str, cobertura: str, modalidade: str = "TIPO I") -> Dict[str, str]:
    linha = {c: "" for c in COLUNAS_USINAS}
    linha.update({"ceg": ceg, "nom_usina": nome, "tipo": tipo, "id_estado": estado, "cobertura_resumo": cobertura,
                  "modalidade": modalidade})
    return linha


def linha_agregado(estado: str, mes: str, modalidade: str, tipo_ons: str, grupo: str, energia: float, horas: int,
                   previsao: bool, ausentes: int = 0) -> Dict[str, Any]:
    return {"id_estado": estado, "mes": mes, "modalidade": modalidade, "tipo_ons": tipo_ons, "grupo": grupo,
            "energia_mwh": energia, "horas": horas, "horas_ausentes": ausentes, "previsao": previsao,
            "arquivo": f"GERACAO_USINA-2_{mes.replace('-', '_')}.parquet"}


def gravar_catalogo(raiz: Path, usinas: List[Dict[str, str]], agregados: List[Dict[str, Any]]) -> Path:
    pasta = Path(raiz) / "data" / "catalogo"
    pasta.mkdir(parents=True, exist_ok=True)
    tabelas = {
        "usinas": pd.DataFrame(usinas, columns=COLUNAS_USINAS),
        "conjuntos": pd.DataFrame(columns=COLUNAS_CONJUNTOS),
        "cobertura": pd.DataFrame(columns=COLUNAS_COBERTURA),
        "planejamento": pd.DataFrame(columns=COLUNAS_PLANEJAMENTO),
        "programacao": pd.DataFrame(columns=COLUNAS_PROGRAMACAO),
        "agregados": pd.DataFrame(agregados, columns=COLUNAS_AGREGADOS),
    }
    for chave, tabela in tabelas.items():
        tabela.to_csv(pasta / ARQUIVOS_CATALOGO[chave], sep=";", index=False)
    info = {"versao_formato": VERSAO_FORMATO_CATALOGO, "montado_em_utc": MONTADO_EM, "sem_portal": True,
            "cadastro": {"modalidade-usina": {"arquivo": "MODALIDADE_USINA.csv", "publicacao": "2026-10-20T22:04:57"}},
            "agregados": {"meses": MESES, "meses_sem_arquivo": [], "arquivos": []}}
    (pasta / ARQUIVOS_CATALOGO["catalogo"]).write_text(json.dumps(info), encoding="utf-8")
    return pasta


def indicadores(tipo: str, ano: Optional[int] = 2025, parcial: bool = False,
                contagens: Optional[Dict[str, int]] = None, avaliadas: int = 4, nao_avaliadas: int = 0,
                **valores: Optional[float]) -> Dict[str, Any]:
    """``indicadores_carteira`` com os valores dados (em %, do nível da usina); os demais indicadores vazios."""
    chaves = ("fator_capacidade", "disponibilidade", "teifa", "energia_cortada", "atendimento_despacho")
    saida: Dict[str, Any] = {"tipo": tipo, "periodo": {"inicio": pd.Timestamp("2021-01-01"),
                                                       "fim": pd.Timestamp("2026-09-30 23:00")},
                             "ano": ano, "ano_parcial": parcial}
    for chave in chaves:
        v = valores.get(chave)
        saida[chave] = None if v is None else {"valor": float(v), "nivel": "usina", "unidade": "%"}
    if saida["atendimento_despacho"] is not None:
        saida["atendimento_despacho"].update(horas_dentro=2, horas_programadas=32)
    if saida["teifa"] is not None:
        saida["teifa"]["mes"] = pd.Timestamp(f"{ano}-12-01")
    listas = ("pontos_atencao", "possiveis_problemas", "confirmar_agente", "verificar_campo")
    c = contagens or {}
    saida["conclusao"] = {**{k: (int(c.get(k, 0)) if avaliadas else None) for k in listas},
                          "regras_avaliadas": avaliadas, "regras_nao_avaliadas": nao_avaliadas}
    return saida


def resultados_vazios() -> ResultadosAnalise:
    vazio = pd.DataFrame()
    return ResultadosAnalise(cobertura={}, globais={}, indicadores_anuais=vazio, evt_mensal=vazio,
                             distribuicao_mes_do_ano=vazio, evt_por_faixa_geracao=vazio, perfil_horario_geracao=vazio,
                             perfil_horario_evt=vazio, eventos_parada_com_evt=vazio,
                             eventos_indisponibilidade_total=vazio, mudanca_classificacao={}, anomalias=vazio,
                             resumo_anomalias=vazio, extremos=vazio, perfil_estatistico=vazio)


def gravar_analises(raiz: Path, slug: str, indicadores_carteira: Dict[str, Any], status: str = "concluida",
                    versao_formato: int = 3, nivel_geracao: str = "usina") -> Path:
    pasta = Path(raiz) / "data" / "usinas" / slug / "analises"
    pasta.mkdir(parents=True, exist_ok=True)
    res = resultados_vazios()
    res.tipo = indicadores_carteira.get("tipo", "")
    res.niveis = {"geracao": {"nivel": nivel_geracao,
                              "identificador_conjunto": "CJU_GOCJFI" if nivel_geracao == "conjunto" else ""}}
    res.indicadores_carteira = indicadores_carteira
    salvar_resultados(res, pasta / "resultados.pkl")
    manifesto = {"etapa": "analises", "usina": slug, "versao_formato": versao_formato,
                 "concluida_em": "2026-10-22T12:00:00Z", "status": status, "codigo_saida": 0}
    (pasta / "etapa.json").write_text(json.dumps(manifesto), encoding="utf-8")
    return pasta
