"""Testes da gravação e da leitura dos resultados das Análises (resultados.pkl, com a versão do formato)."""

from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd
import pytest

from src.analises.etapa import analisar
from src.analises.evt import preparar_dados
from src.analises.resultados import VERSAO_FORMATO, carregar_resultados, salvar_resultados


def test_gravacao_e_leitura_preservam_os_resultados(df_sintetico: pd.DataFrame, tmp_path: Path) -> None:
    res = analisar(preparar_dados(df_sintetico), {})
    caminho = tmp_path / "resultados.pkl"
    salvar_resultados(res, caminho)
    lido = carregar_resultados(caminho)
    pd.testing.assert_frame_equal(lido.indicadores_anuais, res.indicadores_anuais)
    assert lido.achados == res.achados and lido.conclusao == res.conclusao
    assert not list(tmp_path.glob("*.bak"))  # refeito a partir dos dados tratados: sem cópia
    salvar_resultados(res, caminho)
    assert not list(tmp_path.glob("*.bak"))


def test_formato_diferente_e_recusado(tmp_path: Path) -> None:
    caminho = tmp_path / "resultados.pkl"
    caminho.write_bytes(pickle.dumps({"versao_formato": VERSAO_FORMATO + 1, "resultados": None}))
    with pytest.raises(ValueError, match="formato diferente"):
        carregar_resultados(caminho)
