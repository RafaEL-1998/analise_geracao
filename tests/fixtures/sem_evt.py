"""Duas usinas sem EVT sobre os brutos do catálogo (``brutos_catalogo``), para os testes das etapas.

- ``ute_beta``: térmica Tipo I com geração, disponibilidade e programação próprias (sem indicadores);
- ``pch_alfa``: PCH em conjunto de usinas, com a geração e a programação do conjunto (dois códigos).

``projeto_sem_evt`` monta o projeto numa pasta temporária, com os caminhos trocados durante a execução, e roda as
etapas pedidas para cada usina. Nenhum valor de usina real.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

import pytest

from src import pipeline
from src.comum import caminhos
from src.comum import perfil as modulo_perfil
from src.comum.perfil import carregar_perfil
from tests.fixtures import brutos_catalogo as bc

PERFIS = {
    "ute_beta": f'''[usina]
slug = "ute_beta"
nome = "UTE BETA"
nome_curto = "Beta"
estado = "GO"
inicio_operacao_comercial = 2021
tipo = "UTE"
modalidade = "TIPO I"

[identificacao]
ceg = "{bc.UTE["ceg"]}"
id_ons = "{bc.UTE["id_ons"]}"
codigos_programacao = ["{bc.UTE["id_ons"]}"]

[cobertura]
geracao = "proprio"
disponibilidade = "proprio"
indicadores = "ausente"
programacao = "proprio"

[parametros]
potencia_instalada_mw = 150.0
unidades_geradoras = 2
potencia_unitaria_mw = 75.0
combustivel = "GÁS"

[parametros.fontes]
geral = "documento de teste"
''',
    "pch_alfa": f'''[usina]
slug = "pch_alfa"
nome = "PCH ALFA"
nome_curto = "Alfa"
estado = "GO"
inicio_operacao_comercial = 2019
tipo = "PCH"
modalidade = "TIPO II-C"

[identificacao]
ceg = "{bc.PCH["ceg"]}"
id_ons = "{bc.PCH["id_ons"]}"
id_conjunto = "{bc.PCH["conjunto"]}"
codigos_programacao = ["GOCJA-101", "GOCJA-102"]

[cobertura]
evt = "ausente"
indicadores = "ausente"
programacao = "conjunto"
disponibilidade = "ausente"
hidrologia = "ausente"
geracao = "conjunto"

[parametros]
potencia_instalada_mw = 28.0
unidades_geradoras = 3
potencia_unitaria_mw = 9.3333

[parametros.fontes]
geral = "documento de teste"
''',
}


def projeto_sem_evt(raiz: Path, etapas: Iterable[str], slugs: Iterable[str] = tuple(PERFIS),
                    preparar: Any = None) -> Dict[str, Dict[str, Any]]:
    """Grava os brutos e os perfis em ``raiz`` e roda as etapas de cada usina; devolve, por usina, o código e o
    manifesto de cada etapa e a pasta da usina em ``data/usinas/``.

    ``preparar(raw)``, se informado, ajusta os brutos antes das etapas.
    """
    bc.gerar_brutos_catalogo(raiz / "data" / "raw")
    if preparar is not None:
        preparar(raiz / "data" / "raw")
    for slug in slugs:
        (raiz / "usinas" / slug).mkdir(parents=True, exist_ok=True)
        (raiz / "usinas" / slug / "perfil.toml").write_text(PERFIS[slug], encoding="utf-8")
    mp = pytest.MonkeyPatch()
    mp.setattr(caminhos, "DATA_DIR", raiz / "data")
    mp.setattr(caminhos, "RAW_DATA_DIR", raiz / "data" / "raw")
    mp.setattr(caminhos, "REPORTS_DIR", raiz / "reports")
    mp.setattr(modulo_perfil, "RAIZ_PROJETO", raiz)
    resultado: Dict[str, Dict[str, Any]] = {}
    try:
        for slug in slugs:
            perfil = carregar_perfil(slug, raiz)
            usina: Dict[str, Any] = {"pasta": raiz / "data" / "usinas" / slug, "codigos": {}, "manifestos": {}}
            for etapa in etapas:
                opcoes = {"sem_portal": True} if etapa == "coleta" else {}
                usina["codigos"][etapa] = pipeline.executar_etapa(etapa, perfil, **opcoes)
                manifesto = usina["pasta"] / etapa / caminhos.MANIFESTO_ETAPA
                usina["manifestos"][etapa] = (json.loads(manifesto.read_text(encoding="utf-8"))
                                              if manifesto.exists() else {})
                if usina["codigos"][etapa] != 0:
                    break
            resultado[slug] = usina
    finally:
        mp.undo()
    return resultado
