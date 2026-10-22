"""Afluência, vertimento e nível na hidrelétrica sem EVT (spec 006, fase D; rascunho 004, FR-061; tarefa T150).

A hora da hidrologia vem conferida pela geração da usina (FR-026 da Conferência). Confirmada, a seção traz a tabela
anual e as médias mensais, sem os cruzamentos com a EVT; sem a confirmação, só a cobertura e o resultado da
conferência, como a FR-034 faz hoje. A integração com a CGH fictícia está em ``tests/integracao/test_usinas_ficticias.py``.
"""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from src.analises.constatacoes import _achado_afluencia_comum
from src.analises.hidrologia import analisar_hidrologia_sem_evt
from src.conferencia.vazoes import conferencia_alinhamento_hidrologia
from src.tratamento.series import SerieConjunto

HORAS = pd.date_range("2024-01-01", periods=96, freq="h")
GERACAO = pd.Series([10.0 + (i * 7) % 23 for i in range(96)])


def _hidrologia(desvio_h: int = 0) -> SerieConjunto:
    turbinada = GERACAO * 3.0
    return SerieConjunto(horaria=pd.DataFrame({
        "din_instante": HORAS + pd.Timedelta(hours=desvio_h), "val_vazaoafluente": turbinada + 5.0,
        "val_vazaodefluente": turbinada + 5.0, "val_vazaoturbinada": turbinada, "val_vazaovertida": 5.0,
        "val_vazaovertidanaoturbinavel": 0.0, "val_nivelmontante": 344.3, "val_niveljusante": 330.0,
        "val_volumeutil": 50.0, "qualidade": "OK"}))


def _base() -> pd.DataFrame:
    return pd.DataFrame({"din_instante": HORAS, "geracao_mw": GERACAO, "nivel": "usina"})


COBERTURA = {"anos_parciais": [2024]}


def test_com_a_hora_confirmada_pela_geracao() -> None:
    serie = _hidrologia()
    h = analisar_hidrologia_sem_evt(serie, conferencia_alinhamento_hidrologia(serie, _base()), COBERTURA, "2026-10-22")
    assert h["publicado"] and h["sem_evt"] and not h["motivo_alinhamento"]
    assert list(h["anual"]["periodo"]) == ["2024"] and bool(h["anual"]["ano_parcial"].iloc[0])
    assert len(h["mensal"]) == 1
    # sem os cruzamentos com a EVT: nem faixas de afluência nem dias com parada com EVT
    assert not {"faixas", "faixas_anual", "perfil"} & set(h)
    r = h["resumo"]
    assert r["horas"] == 96 and r["vertida_media_m3s"] == 5.0
    # afluência acima do engolimento máximo da São Domingos (perfil ativo dos testes: 2 × 81,5 m³/s)
    assert r["horas_afluencia_acima_engolimento"] == int(((GERACAO * 3.0 + 5.0) > 163.0).sum())
    titulo, texto = _achado_afluencia_comum(SimpleNamespace(hidrologia=h))
    assert titulo == "Afluência e vertimento"
    assert "a hora foi conferida pela geração da usina (correlação entre a vazão turbinada e a geração de 1,000" in texto
    assert "EVT" not in texto


def test_sem_a_hora_confirmada_so_a_cobertura() -> None:
    serie = _hidrologia(desvio_h=1)  # a convenção errada: a maior correlação é com −1 h
    h = analisar_hidrologia_sem_evt(serie, conferencia_alinhamento_hidrologia(serie, _base()), COBERTURA)
    assert not h["publicado"] and "anual" not in h and "mensal" not in h
    texto = _achado_afluencia_comum(SimpleNamespace(hidrologia=h))[1]
    assert "a hora não foi confirmada pela geração da usina" in texto and "só a cobertura é mostrada" in texto


def test_sem_a_geracao_da_usina_a_hora_nao_e_conferida() -> None:
    serie = _hidrologia()
    conferencia = conferencia_alinhamento_hidrologia(serie, _base().assign(nivel="conjunto"))
    h = analisar_hidrologia_sem_evt(serie, conferencia, COBERTURA)
    assert not h["publicado"] and "nível da usina" in h["motivo_alinhamento"]
    texto = _achado_afluencia_comum(SimpleNamespace(hidrologia=h))[1]
    assert "a hora não pôde ser conferida pela geração da usina (sem a geração no nível da usina" in texto


def test_sem_a_serie_o_resultado_fica_vazio() -> None:
    assert analisar_hidrologia_sem_evt(None, None, COBERTURA) == {}
    assert _achado_afluencia_comum(SimpleNamespace(hidrologia={})) is None
    # o resultado do caminho da EVT não gera a constatação das usinas sem EVT
    assert _achado_afluencia_comum(SimpleNamespace(hidrologia={"publicado": True})) is None
