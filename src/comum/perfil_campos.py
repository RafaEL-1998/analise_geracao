"""Campos do perfil por tipo de usina (spec 006, decisão R4; data-model, seção 3.2; contrato perfil-multitipo.md).

Para cada campo e grupo de tipos, a exigência:

- ``O``: obrigatório;
- ``C``: obrigatório quando um dos conjuntos do ONS que usam o campo tem, na ``[cobertura]``, um dos níveis indicados
  (``proprio`` ou ``conjunto``, salvo indicação);
- ``opcional``;
- ``—``: não se aplica, e a presença é recusada.

Os campos comuns a todos os tipos (data-model 3.1) são conferidos diretamente em ``src.comum.perfil``. Na UHE, os
campos e as regras de hoje continuam iguais.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

OBRIGATORIO = "O"
COM_COBERTURA = "C"
OPCIONAL = "opcional"
NAO_SE_APLICA = "—"

GRUPO_DO_TIPO: Dict[str, str] = {"UHE": "UHE", "PCH": "PCH_CGH", "CGH": "PCH_CGH", "UTE": "UTE_UTN", "UTN": "UTE_UTN",
                                 "EOL": "EOL_UFV", "UFV": "EOL_UFV"}
COBERTURAS_QUE_OBTEM: Tuple[str, ...] = ("proprio", "conjunto")


@dataclass(frozen=True)
class Exigencia:
    """Exigência de um campo para um grupo de tipos."""

    nivel: str
    conjuntos: Tuple[str, ...] = ()  # chaves do registro que tornam o campo obrigatório (nível C)
    coberturas: Tuple[str, ...] = COBERTURAS_QUE_OBTEM  # valores da cobertura que o exigem (nível C)


O = Exigencia(OBRIGATORIO)
OPC = Exigencia(OPCIONAL)
NAO = Exigencia(NAO_SE_APLICA)


def _c(*conjuntos: str, coberturas: Tuple[str, ...] = COBERTURAS_QUE_OBTEM) -> Exigencia:
    return Exigencia(COM_COBERTURA, conjuntos, coberturas)


HIDRAULICOS: Tuple[str, ...] = ("tipo_turbina", "engolimento_nominal_ug_m3s", "queda_bruta_m", "perda_hidraulica_m",
                                "rendimento_turbina_gerador", "vazao_remanescente_m3s")
_EVT_OU_HIDROLOGIA = _c("evt", "hidrologia")
_ID_CONJUNTO = _c("geracao", "fator_capacidade", "restricao_razao", coberturas=("conjunto",))

# Campo -> {grupo de tipos: exigência} (data-model, seção 3.2)
CAMPOS: Dict[str, Dict[str, Exigencia]] = {
    "identificacao.id_ons": {"UHE": O, "PCH_CGH": _c("geracao", "disponibilidade", coberturas=("proprio",)),
                             "UTE_UTN": O,
                             "EOL_UFV": _c("geracao", "fator_capacidade", "restricao_detalhe", "restricao_razao",
                                           coberturas=("proprio",))},
    "identificacao.cod_usina": {"UHE": O, "PCH_CGH": _EVT_OU_HIDROLOGIA, "UTE_UTN": NAO, "EOL_UFV": NAO},
    "identificacao.nome_ons": {"UHE": O, "PCH_CGH": _EVT_OU_HIDROLOGIA, "UTE_UTN": NAO, "EOL_UFV": NAO},
    "identificacao.id_reservatorio": {"UHE": O, "PCH_CGH": _c("hidrologia"), "UTE_UTN": NAO, "EOL_UFV": NAO},
    "identificacao.id_conjunto": {"UHE": NAO, "PCH_CGH": _ID_CONJUNTO, "UTE_UTN": _ID_CONJUNTO, "EOL_UFV": _ID_CONJUNTO},
    "identificacao.planejamento": {"UHE": NAO, "PCH_CGH": NAO, "UTE_UTN": _c("despacho", "cvu"), "EOL_UFV": NAO},
    "identificacao.membros": {"UHE": NAO, "PCH_CGH": OPC, "UTE_UTN": NAO, "EOL_UFV": OPC},
    **{f"parametros.{campo}": {"UHE": O, "PCH_CGH": _EVT_OU_HIDROLOGIA, "UTE_UTN": NAO, "EOL_UFV": NAO}
       for campo in HIDRAULICOS},
    "parametros.garantia_fisica_mwmed": {"UHE": O, "PCH_CGH": OPC, "UTE_UTN": OPC, "EOL_UFV": OPC},
    "parametros.ip_referencia": {"UHE": O, "PCH_CGH": OPC, "UTE_UTN": OPC, "EOL_UFV": NAO},
    "parametros.teif_referencia": {"UHE": O, "PCH_CGH": OPC, "UTE_UTN": OPC, "EOL_UFV": NAO},
    "parametros.combustivel": {"UHE": NAO, "PCH_CGH": NAO, "UTE_UTN": O, "EOL_UFV": NAO},
    "usina.subsistema": {"UHE": OPC, "PCH_CGH": OPC, "UTE_UTN": _c("cvu"), "EOL_UFV": OPC},
    "analises": {"UHE": O, "PCH_CGH": _c("evt"), "UTE_UTN": NAO, "EOL_UFV": NAO},
}


def exigencia(campo: str, tipo: str) -> Exigencia:
    """Exigência do ``campo`` para o ``tipo`` de usina."""
    return CAMPOS[campo][GRUPO_DO_TIPO[tipo]]


def _valores(valor: Any) -> Tuple[str, ...]:
    return tuple(valor) if isinstance(valor, (list, tuple)) else (valor,)


def exigido_pela_cobertura(campo: str, tipo: str, cobertura: Dict[str, Any]) -> Optional[Tuple[str, Tuple[str, ...]]]:
    """Num campo ``C``: o nível e os conjuntos da ``cobertura`` que o tornam obrigatório; None se não é exigido."""
    e = exigencia(campo, tipo)
    if e.nivel != COM_COBERTURA:
        return None
    gatilhos = [(chave, v) for chave in e.conjuntos for v in _valores(cobertura.get(chave)) if v in e.coberturas]
    if not gatilhos:
        return None
    return gatilhos[0][1], tuple(dict.fromkeys(chave for chave, _ in gatilhos))
