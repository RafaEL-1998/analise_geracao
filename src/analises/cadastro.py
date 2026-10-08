"""Ficha cadastral da usina no ONS, com as divergências apontadas pela Conferência."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd


def analisar_cadastro(ficha: pd.DataFrame, auditoria: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """Ficha cadastral da usina no ONS (FR-040), com a auditoria da leitura do cadastro feita pela Coleta, se houver."""
    linha = ficha.iloc[0].to_dict()
    divergencias = str(linha.get("divergencias") or "").strip()
    return {"ficha": linha, "divergencias": divergencias, "obtido_em": str(linha.get("data_consulta_utc") or ""),
            "auditoria": auditoria if auditoria is not None else pd.DataFrame()}
