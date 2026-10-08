"""Testes da sinalização de qualidade das séries horárias (D1 a D4, H1 a H4, G1)."""

from __future__ import annotations

import pandas as pd

from src.tratamento.disponibilidade import qualidade as qualidade_disponibilidade
from src.tratamento.geracao import qualidade as qualidade_geracao
from src.tratamento.hidrologia import limpos as _limpos, qualidade


def test_regras_de_qualidade_da_disponibilidade() -> None:
    horaria = pd.DataFrame({
        "val_potenciainstalada": [48.0, 48.0, 48.0, 48.0, 48.0, 48.0],
        "val_dispoperacional": [44.0, 44.0, 48.5, -1.0, 44.0, 44.005],
        "val_dispsincronizada": [24.0, 44.02, 24.0, -1.0, None, 44.01],
        "_nao_numerico": [False, False, False, False, True, False],
    })
    assert qualidade_disponibilidade(horaria).tolist() == ["OK", "D1", "D2", "D3", "D4", "OK"]


def test_regras_de_qualidade_da_hidrologia() -> None:
    h = pd.DataFrame({
        "val_vazaoafluente": [100.0, -1.0, 100.0, 100.0, 100.0],
        "val_vazaodefluente": [100.0] * 5, "val_vazaoturbinada": [80.0] * 5, "val_vazaovertida": [20.0] * 5,
        "val_vazaovertidanaoturbinavel": [0.0, 0.0, 0.0, None, 0.0], "val_vazaooutrasestruturas": [None] * 5,
        "val_nivelmontante": [344.5] * 5, "val_niveljusante": [None] * 5,
        "val_volumeutil": [50.0, 50.0, 101.0, 50.0, 50.0],
        "_nao_numerico": [False, False, False, False, True],
    })
    assert qualidade(h).tolist() == ["OK", "H1", "H2", "OK", "H3"]  # vazio não é erro nem zero


def test_nivel_implausivel_sai_so_do_campo_afetado() -> None:
    """H4: nível a mais de 10 m da mediana (leitura trocada) é sinalizado e excluído só no próprio campo."""
    h = pd.DataFrame({
        "din_instante": pd.date_range("2025-01-01", periods=6, freq="h"),
        "val_vazaoafluente": [100.0] * 6, "val_vazaoturbinada": [80.0] * 6, "val_vazaovertida": [20.0] * 6,
        "val_nivelmontante": [344.3, 344.2, 308.67, 342.1, 344.4, 344.3],   # 342,1 m: rebaixamento real (fica)
        "val_niveljusante": [309.9, 309.8, 309.9, 730.9, 309.7, 3.09],
        "val_volumeutil": [50.0] * 6, "_nao_numerico": [False] * 6,
    })
    assert qualidade(h).tolist() == ["OK", "OK", "H4", "H4", "OK", "H4"]
    limpos = _limpos(h)
    assert limpos["val_nivelmontante"].isna().tolist() == [False, False, True, False, False, False]
    assert limpos["val_niveljusante"].isna().tolist() == [False, False, False, True, False, True]
    assert limpos["val_vazaoturbinada"].notna().all()  # a hora continua nas demais análises


def test_geracao_nao_numerica_e_g1() -> None:
    horaria = pd.DataFrame({"val_geracao": [10.0, None], "_nao_numerico": [False, True]})
    assert qualidade_geracao(horaria).tolist() == ["OK", "G1"]
