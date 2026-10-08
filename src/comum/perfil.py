"""Perfil da usina: leitura, validação e valores derivados (spec da Coleta de dados, FR-006 a FR-009).

O perfil (``usinas/<slug>/perfil.toml``) reúne tudo o que é próprio de uma usina: identificação nos conjuntos do ONS,
parâmetros técnicos com a fonte, características usadas nas análises e textos próprios do relatório. As regras gerais
ficam em ``src.comum.regras``. Um perfil com problema é recusado com ``PerfilInvalido``, que lista todos os problemas
de uma vez; a linha de comando o converte no código de saída 4.
"""

from __future__ import annotations

import datetime as _dt
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.comum.regras import (
    FRACAO_PLENA_CARGA,
    LIMIAR_GERACAO_PARADA_MW,
    TOLERANCIA_LIMITES_FISICOS,
    TOLERANCIA_POTENCIA_PERFIL_MW,
)

RAIZ_PROJETO: Path = Path(__file__).resolve().parents[2]
CODIGO_PERFIL_INVALIDO: int = 4

_PADRAO_SLUG = re.compile(r"^[a-z0-9_]+$")
_PADRAO_ESTADO = re.compile(r"^[A-Z]{2}$")
_PADRAO_CEG = re.compile(r"^UHE\.PH\.[A-Z]{2}\.\d{6}-\d\.\d{2}$")
_PADRAO_NOME_ONS = re.compile(r"^[A-Z0-9 .\-/]+$")  # maiúsculas, sem acento


class PerfilInvalido(Exception):
    """Perfil ausente, ilegível ou com problemas; ``problemas`` traz um por linha."""

    def __init__(self, slug: str, arquivo: Path, problemas: List[str]) -> None:
        self.slug, self.arquivo, self.problemas = slug, arquivo, list(problemas)
        try:
            rel = arquivo.relative_to(arquivo.parents[2]).as_posix()
        except (ValueError, IndexError):
            rel = arquivo.as_posix()
        super().__init__(f"Perfil da usina '{slug}' inválido ({rel}):\n" + "\n".join(f"- {p}" for p in self.problemas))


@dataclass(frozen=True)
class Usina:
    slug: str
    nome: str
    nome_curto: str
    estado: str
    inicio_operacao_comercial: int


@dataclass(frozen=True)
class Identificacao:
    cod_usina: int
    nome_ons: str
    ceg: str
    id_ons: str
    cod_programacao: str
    id_reservatorio: str


@dataclass(frozen=True)
class FontesParametros:
    geral: str
    garantia_fisica: str
    inicio_operacao_comercial: Optional[str] = None
    ip_teif: Optional[str] = None


@dataclass(frozen=True)
class Parametros:
    potencia_instalada_mw: float
    unidades_geradoras: int
    potencia_unitaria_mw: float
    tipo_turbina: str
    engolimento_nominal_ug_m3s: float
    garantia_fisica_mwmed: float
    ip_referencia: float
    teif_referencia: float
    queda_bruta_m: float
    perda_hidraulica_m: float
    rendimento_turbina_gerador: float
    vazao_remanescente_m3s: float
    fontes: FontesParametros


@dataclass(frozen=True)
class FontesAnalises:
    vertimento_minimo: Optional[str] = None


@dataclass(frozen=True)
class Analises:
    vertimento_minimo_m3s: float
    faixas_geracao_mw: Tuple[float, ...]
    descricao_vertimento_minimo: Optional[str] = None
    fontes: FontesAnalises = field(default_factory=FontesAnalises)


@dataclass(frozen=True)
class Textos:
    ressalva_volume_util: Optional[str] = None


@dataclass(frozen=True)
class Perfil:
    usina: Usina
    identificacao: Identificacao
    parametros: Parametros
    analises: Analises
    textos: Textos
    arquivo: Path

    # Valores derivados (calculados aqui; o perfil não os traz)
    @property
    def engolimento_maximo_m3s(self) -> float:
        return self.parametros.unidades_geradoras * self.parametros.engolimento_nominal_ug_m3s

    @property
    def potencia_autorizada_esperada_mw(self) -> float:
        return self.parametros.potencia_instalada_mw

    @property
    def disponibilidade_referencia(self) -> float:
        """(1 − IP) × (1 − TEIF) de referência da garantia física."""
        return (1.0 - self.parametros.ip_referencia) * (1.0 - self.parametros.teif_referencia)

    @property
    def produtividade_nominal_mw_m3s(self) -> float:
        """ρ × g × queda líquida × rendimento, em MW/(m³/s)."""
        p = self.parametros
        return 1000.0 * 9.81 * (p.queda_bruta_m - p.perda_hidraulica_m) * p.rendimento_turbina_gerador / 1e6

    @property
    def plena_carga_mw(self) -> float:
        return FRACAO_PLENA_CARGA * self.parametros.potencia_instalada_mw

    @property
    def limite_potencia_mw(self) -> float:
        return self.parametros.potencia_instalada_mw * (1.0 + TOLERANCIA_LIMITES_FISICOS)

    @property
    def limite_vazao_turbinavel_m3s(self) -> float:
        return self.engolimento_maximo_m3s * (1.0 + TOLERANCIA_LIMITES_FISICOS)

    @property
    def limites_fisicos_superiores(self) -> Dict[str, float]:
        """Limite superior por grandeza da base de EVT (regra R6)."""
        return {
            "val_geracao": self.limite_potencia_mw,
            "val_disponibilidade": self.limite_potencia_mw,
            "val_folgadegeracao": self.limite_potencia_mw,
            "val_energiavertidaturbinavel": self.limite_potencia_mw,
            "val_vazaoturbinada": self.limite_vazao_turbinavel_m3s,
            "val_vazaovertidaturbinavel": self.limite_vazao_turbinavel_m3s,
        }


# ---------------------------------------------------------------------------
# Leitura e validação
# ---------------------------------------------------------------------------

def arquivo_perfil(slug: str, raiz: Optional[Path] = None) -> Path:
    return (raiz or RAIZ_PROJETO) / "usinas" / slug / "perfil.toml"


class _Leitor:
    """Lê os campos de um perfil já interpretado, acumulando os problemas em vez de parar no primeiro."""

    def __init__(self, dados: Dict[str, Any]) -> None:
        self.dados = dados
        self.problemas: List[str] = []

    def _valor(self, caminho: str) -> Any:
        atual: Any = self.dados
        for parte in caminho.split("."):
            if not isinstance(atual, dict) or parte not in atual:
                return None
            atual = atual[parte]
        return atual

    def texto(self, caminho: str, obrigatorio: bool = True) -> Optional[str]:
        v = self._valor(caminho)
        if v is None:
            if obrigatorio:
                self.problemas.append(f"{caminho}: campo obrigatório ausente")
            return None
        if not isinstance(v, str):
            self.problemas.append(f"{caminho}: deve ser texto")
            return None
        if not v.strip():
            self.problemas.append(f"{caminho}: não pode ser vazio" + ("" if obrigatorio else " (campo opcional presente)"))
            return None
        return v

    def inteiro(self, caminho: str) -> Optional[int]:
        v = self._valor(caminho)
        if v is None:
            self.problemas.append(f"{caminho}: campo obrigatório ausente")
            return None
        if isinstance(v, bool) or not isinstance(v, int):
            self.problemas.append(f"{caminho}: deve ser número inteiro")
            return None
        return v

    def real(self, caminho: str) -> Optional[float]:
        v = self._valor(caminho)
        if v is None:
            self.problemas.append(f"{caminho}: campo obrigatório ausente")
            return None
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            self.problemas.append(f"{caminho}: deve ser número")
            return None
        return float(v)

    def lista_reais(self, caminho: str) -> Optional[Tuple[float, ...]]:
        v = self._valor(caminho)
        if v is None:
            self.problemas.append(f"{caminho}: campo obrigatório ausente")
            return None
        if not isinstance(v, list) or not v or any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in v):
            self.problemas.append(f"{caminho}: deve ser lista não vazia de números")
            return None
        return tuple(float(x) for x in v)

    def confere(self, condicao: bool, mensagem: str) -> None:
        if not condicao:
            self.problemas.append(mensagem)


def validar_perfil(dados: Dict[str, Any], slug_pasta: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Valida o conteúdo de um perfil; devolve os campos lidos e a lista de problemas (vazia se válido)."""
    le = _Leitor(dados)
    c: Dict[str, Any] = {}
    # usina
    c["slug"] = le.texto("usina.slug")
    if c["slug"] is not None:
        le.confere(bool(_PADRAO_SLUG.match(c["slug"])), "usina.slug: só letras minúsculas, algarismos e _")
        le.confere(c["slug"] == slug_pasta, f"usina.slug: '{c['slug']}' diferente do nome da pasta '{slug_pasta}'")
    c["nome"] = le.texto("usina.nome")
    c["nome_curto"] = le.texto("usina.nome_curto")
    c["estado"] = le.texto("usina.estado")
    if c["estado"] is not None:
        le.confere(bool(_PADRAO_ESTADO.match(c["estado"])), "usina.estado: deve ter 2 letras maiúsculas")
    c["inicio"] = le.inteiro("usina.inicio_operacao_comercial")
    if c["inicio"] is not None:
        le.confere(1900 <= c["inicio"] <= _dt.date.today().year,
                   "usina.inicio_operacao_comercial: deve estar entre 1900 e o ano atual")
    # identificação
    c["cod_usina"] = le.inteiro("identificacao.cod_usina")
    if c["cod_usina"] is not None:
        le.confere(c["cod_usina"] > 0, "identificacao.cod_usina: deve ser maior que zero")
    c["nome_ons"] = le.texto("identificacao.nome_ons")
    if c["nome_ons"] is not None:
        le.confere(bool(_PADRAO_NOME_ONS.match(c["nome_ons"])),
                   "identificacao.nome_ons: em maiúsculas e sem acento, como nos conjuntos do ONS")
    c["ceg"] = le.texto("identificacao.ceg")
    if c["ceg"] is not None:
        le.confere(bool(_PADRAO_CEG.match(c["ceg"])), "identificacao.ceg: fora do padrão UHE.PH.UF.NNNNNN-D.DD")
    for campo in ("id_ons", "cod_programacao", "id_reservatorio"):
        c[campo] = le.texto(f"identificacao.{campo}")
    # parâmetros
    for campo in ("potencia_instalada_mw", "potencia_unitaria_mw", "engolimento_nominal_ug_m3s", "garantia_fisica_mwmed",
                  "ip_referencia", "teif_referencia", "queda_bruta_m", "perda_hidraulica_m",
                  "rendimento_turbina_gerador", "vazao_remanescente_m3s"):
        c[campo] = le.real(f"parametros.{campo}")
    c["unidades_geradoras"] = le.inteiro("parametros.unidades_geradoras")
    c["tipo_turbina"] = le.texto("parametros.tipo_turbina")
    pot, n, unit = c["potencia_instalada_mw"], c["unidades_geradoras"], c["potencia_unitaria_mw"]
    for campo in ("potencia_instalada_mw", "potencia_unitaria_mw", "engolimento_nominal_ug_m3s", "garantia_fisica_mwmed",
                  "queda_bruta_m"):
        if c[campo] is not None:
            le.confere(c[campo] > 0, f"parametros.{campo}: deve ser maior que zero")
    if n is not None:
        le.confere(n >= 1, "parametros.unidades_geradoras: deve ser pelo menos 1")
    if None not in (pot, n, unit) and n >= 1:
        le.confere(abs(unit * n - pot) <= TOLERANCIA_POTENCIA_PERFIL_MW,
                   f"parametros.potencia_unitaria_mw × unidades_geradoras ({unit * n:g} MW) diferente da potência "
                   f"instalada ({pot:g} MW) em mais de {TOLERANCIA_POTENCIA_PERFIL_MW:g} MW")
    if None not in (c["garantia_fisica_mwmed"], pot):
        le.confere(c["garantia_fisica_mwmed"] <= pot, "parametros.garantia_fisica_mwmed: maior que a potência instalada")
    for campo in ("ip_referencia", "teif_referencia"):
        if c[campo] is not None:
            le.confere(0 <= c[campo] < 1, f"parametros.{campo}: deve estar entre 0 (inclusive) e 1 (exclusive)")
    if c["rendimento_turbina_gerador"] is not None:
        le.confere(0 < c["rendimento_turbina_gerador"] <= 1, "parametros.rendimento_turbina_gerador: deve estar entre 0 "
                                                             "(exclusive) e 1 (inclusive)")
    if c["perda_hidraulica_m"] is not None:
        le.confere(c["perda_hidraulica_m"] >= 0, "parametros.perda_hidraulica_m: não pode ser negativa")
        if c["queda_bruta_m"] is not None:
            le.confere(c["perda_hidraulica_m"] < c["queda_bruta_m"], "parametros.perda_hidraulica_m: deve ser menor que "
                                                                     "a queda bruta")
    if c["vazao_remanescente_m3s"] is not None:
        le.confere(c["vazao_remanescente_m3s"] >= 0, "parametros.vazao_remanescente_m3s: não pode ser negativa")
    c["fonte_geral"] = le.texto("parametros.fontes.geral")
    c["fonte_gf"] = le.texto("parametros.fontes.garantia_fisica")
    c["fonte_inicio"] = le.texto("parametros.fontes.inicio_operacao_comercial", obrigatorio=False)
    c["fonte_ip_teif"] = le.texto("parametros.fontes.ip_teif", obrigatorio=False)
    # análises
    c["vertimento_minimo"] = le.real("analises.vertimento_minimo_m3s")
    if c["vertimento_minimo"] is not None:
        le.confere(c["vertimento_minimo"] >= 0, "analises.vertimento_minimo_m3s: não pode ser negativo")
    c["faixas"] = le.lista_reais("analises.faixas_geracao_mw")
    if c["faixas"] is not None:
        faixas = c["faixas"]
        le.confere(all(a < b for a, b in zip(faixas, faixas[1:])), "analises.faixas_geracao_mw: deve ser crescente")
        if pot is not None:
            plena = FRACAO_PLENA_CARGA * pot
            le.confere(all(LIMIAR_GERACAO_PARADA_MW < x < plena for x in faixas),
                       f"analises.faixas_geracao_mw: cada valor deve ficar acima de {LIMIAR_GERACAO_PARADA_MW:g} MW "
                       f"(usina parada) e abaixo da plena carga ({plena:g} MW)")
    c["descricao_vertimento"] = le.texto("analises.descricao_vertimento_minimo", obrigatorio=False)
    c["fonte_vertimento"] = le.texto("analises.fontes.vertimento_minimo", obrigatorio=False)
    c["ressalva_volume_util"] = le.texto("textos.ressalva_volume_util", obrigatorio=False)
    return (None if le.problemas else c), le.problemas


def carregar_perfil(slug: str, raiz: Optional[Path] = None) -> Perfil:
    """Lê e valida ``usinas/<slug>/perfil.toml``; levanta ``PerfilInvalido`` com todos os problemas."""
    arquivo = arquivo_perfil(slug, raiz)
    if not arquivo.is_file():
        raise PerfilInvalido(slug, arquivo, [f"arquivo do perfil não encontrado: usinas/{slug}/perfil.toml"])
    try:
        dados = tomllib.loads(arquivo.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise PerfilInvalido(slug, arquivo, [f"arquivo ilegível: {exc}"]) from exc
    c, problemas = validar_perfil(dados, slug)
    if problemas:
        raise PerfilInvalido(slug, arquivo, problemas)
    assert c is not None
    return Perfil(
        usina=Usina(c["slug"], c["nome"], c["nome_curto"], c["estado"], c["inicio"]),
        identificacao=Identificacao(c["cod_usina"], c["nome_ons"], c["ceg"], c["id_ons"], c["cod_programacao"],
                                    c["id_reservatorio"]),
        parametros=Parametros(
            c["potencia_instalada_mw"], c["unidades_geradoras"], c["potencia_unitaria_mw"], c["tipo_turbina"],
            c["engolimento_nominal_ug_m3s"], c["garantia_fisica_mwmed"], c["ip_referencia"], c["teif_referencia"],
            c["queda_bruta_m"], c["perda_hidraulica_m"], c["rendimento_turbina_gerador"], c["vazao_remanescente_m3s"],
            FontesParametros(c["fonte_geral"], c["fonte_gf"], c["fonte_inicio"], c["fonte_ip_teif"]),
        ),
        analises=Analises(c["vertimento_minimo"], c["faixas"], c["descricao_vertimento"],
                          FontesAnalises(c["fonte_vertimento"])),
        textos=Textos(c["ressalva_volume_util"]),
        arquivo=arquivo,
    )


# ---------------------------------------------------------------------------
# Perfil ativo da etapa
# ---------------------------------------------------------------------------

# Perfil da usina da etapa em execução. ``src.pipeline`` o define antes de chamar a função da etapa; as Análises e a
# Geração do relatório leem dele os valores da usina, sem repassar o perfil a cada função.
_PERFIL_ATIVO: Optional[Perfil] = None


def definir_perfil_ativo(perfil: Optional[Perfil]) -> None:
    """Define (ou, com None, limpa) o perfil da usina da etapa em execução."""
    global _PERFIL_ATIVO
    _PERFIL_ATIVO = perfil


def perfil_ativo() -> Perfil:
    """Perfil da usina da etapa em execução; erro se nenhuma etapa o definiu."""
    if _PERFIL_ATIVO is None:
        raise RuntimeError("nenhum perfil de usina ativo: a etapa deve ser executada por src.pipeline")
    return _PERFIL_ATIVO
