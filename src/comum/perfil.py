"""Perfil da usina: leitura, validação e valores derivados (spec da Coleta de dados, FR-006 a FR-009; spec 006).

O perfil (``usinas/<slug>/perfil.toml``) reúne tudo o que é próprio de uma usina: tipo e modalidade, identificação nos
conjuntos do ONS, cobertura de cada conjunto, parâmetros técnicos com a fonte, características usadas nas análises e
textos próprios do relatório. As regras gerais ficam em ``src.comum.regras``; a exigência de cada campo por tipo de
usina, em ``src.comum.perfil_campos``. Um perfil com problema é recusado com ``PerfilInvalido``, que lista todos os
problemas de uma vez; a linha de comando o converte no código de saída 4. Na UHE, os campos e as regras de hoje
continuam iguais, mais ``tipo`` e ``modalidade``.
"""

from __future__ import annotations

import datetime as _dt
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.comum import perfil_campos
from src.comum.perfil_campos import COM_COBERTURA, NAO_SE_APLICA, OBRIGATORIO
from src.comum.regras import (
    COBERTURAS,
    FRACAO_PLENA_CARGA,
    LIMIAR_GERACAO_PARADA_MW,
    MODALIDADES_COM_PERFIL,
    MODALIDADES_TIPO_III,
    SUBSISTEMAS,
    TIPOS_USINA,
    TOLERANCIA_LIMITES_FISICOS,
    TOLERANCIA_POTENCIA_PERFIL_MW,
)

RAIZ_PROJETO: Path = Path(__file__).resolve().parents[2]
CODIGO_PERFIL_INVALIDO: int = 4
SLUG_RESERVADO = "carteiras"  # pasta das carteiras em reports/
SITUACOES = ("rascunho", "conferido")

_PADRAO_SLUG = re.compile(r"^[a-z0-9_]+$")
_PADRAO_ESTADO = re.compile(r"^[A-Z]{2}$")
_PADRAO_CEG = re.compile(r"^(UHE|PCH|CGH|UTE|UTN|EOL|UFV)\.[A-Z]{2}\.[A-Z]{2}\.\d{6}-\d\.\d{2}$")
_PADRAO_NOME_ONS = re.compile(r"^[A-Z0-9 .\-/]+$")  # maiúsculas, sem acento
_PADRAO_MES = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
_PADRAO_DIA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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
    tipo: str
    modalidade: str
    situacao: str = "conferido"
    pendentes: Tuple[str, ...] = ()
    subsistema: Optional[str] = None


@dataclass(frozen=True)
class Planejamento:
    """Código de planejamento de uma térmica e o período em que vale (``fim`` vazio: vigente)."""

    codigo: int
    inicio: str  # AAAA-MM
    fim: str = ""


@dataclass(frozen=True)
class Membro:
    """Usina de um conjunto, com o período em que fez parte dele (``fim`` vazio: vigente)."""

    id_ons: str
    ceg: str
    inicio: str  # AAAA-MM-DD
    fim: str = ""


@dataclass(frozen=True)
class Identificacao:
    cod_usina: Optional[int]
    nome_ons: Optional[str]
    ceg: str
    id_ons: Optional[str]
    cod_programacao: str  # o primeiro dos códigos de programação
    id_reservatorio: Optional[str]
    codigos_programacao: Tuple[str, ...] = ()
    id_conjunto: Optional[str] = None
    planejamento: Tuple[Planejamento, ...] = ()
    membros: Tuple[Membro, ...] = ()


@dataclass(frozen=True)
class FontesParametros:
    geral: str
    garantia_fisica: Optional[str]
    inicio_operacao_comercial: Optional[str] = None
    ip_teif: Optional[str] = None


@dataclass(frozen=True)
class Parametros:
    potencia_instalada_mw: float
    unidades_geradoras: int
    potencia_unitaria_mw: Optional[float]
    tipo_turbina: Optional[str]
    engolimento_nominal_ug_m3s: Optional[float]
    garantia_fisica_mwmed: Optional[float]
    ip_referencia: Optional[float]
    teif_referencia: Optional[float]
    queda_bruta_m: Optional[float]
    perda_hidraulica_m: Optional[float]
    rendimento_turbina_gerador: Optional[float]
    vazao_remanescente_m3s: Optional[float]
    fontes: FontesParametros
    potencias_unidades_mw: Tuple[float, ...] = ()
    combustivel: Optional[str] = None


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
    analises: Optional[Analises]  # só onde há EVT
    textos: Textos
    arquivo: Path
    cobertura: Dict[str, Any] = field(default_factory=dict)  # vazia na UHE que não a declara

    # Valores derivados (calculados aqui; o perfil não os traz)
    def _hidraulico(self, campo: str) -> float:
        valor = getattr(self.parametros, campo)
        if valor is None:
            raise ValueError(f"parametros.{campo}: só existe nas hidrelétricas com EVT ou hidrologia "
                             f"(usina '{self.usina.slug}', {self.usina.tipo})")
        return valor

    @property
    def engolimento_maximo_m3s(self) -> float:
        return self.parametros.unidades_geradoras * self._hidraulico("engolimento_nominal_ug_m3s")

    @property
    def potencia_autorizada_esperada_mw(self) -> float:
        return self.parametros.potencia_instalada_mw

    @property
    def disponibilidade_referencia(self) -> float:
        """(1 − IP) × (1 − TEIF) de referência da garantia física."""
        p = self.parametros
        if p.ip_referencia is None or p.teif_referencia is None:
            raise ValueError(f"parametros.ip_referencia e teif_referencia: não informados no perfil da usina "
                             f"'{self.usina.slug}'")
        return (1.0 - p.ip_referencia) * (1.0 - p.teif_referencia)

    @property
    def produtividade_nominal_mw_m3s(self) -> float:
        """ρ × g × queda líquida × rendimento, em MW/(m³/s)."""
        queda, perda = self._hidraulico("queda_bruta_m"), self._hidraulico("perda_hidraulica_m")
        return 1000.0 * 9.81 * (queda - perda) * self._hidraulico("rendimento_turbina_gerador") / 1e6

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

    @property
    def potencias_das_unidades_mw(self) -> Tuple[float, ...]:
        """A lista do perfil ou, sem ela, a potência unitária repetida pelas unidades."""
        p = self.parametros
        if p.potencias_unidades_mw:
            return tuple(p.potencias_unidades_mw)
        return (float(p.potencia_unitaria_mw),) * p.unidades_geradoras

    def codigos_planejamento_em(self, data: _dt.date) -> Tuple[int, ...]:
        """Códigos de planejamento vigentes no mês da ``data``, na ordem do perfil (UTE e UTN)."""
        mes = f"{data.year:04d}-{data.month:02d}"
        return tuple(p.codigo for p in self.identificacao.planejamento
                     if p.inicio <= mes and (not p.fim or mes <= p.fim))


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

    def presente(self, caminho: str) -> bool:
        return self._valor(caminho) is not None

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

    def lista_textos(self, caminho: str, obrigatorio: bool = True) -> Optional[Tuple[str, ...]]:
        v = self._valor(caminho)
        if v is None:
            if obrigatorio:
                self.problemas.append(f"{caminho}: campo obrigatório ausente")
            return None
        if not isinstance(v, list) or any(not isinstance(x, str) or not x.strip() for x in v):
            self.problemas.append(f"{caminho}: deve ser lista de textos não vazios")
            return None
        return tuple(v)

    def tabelas(self, caminho: str) -> List[Dict[str, Any]]:
        """Lista de tabelas (``[[...]]``); vazia se ausente."""
        v = self._valor(caminho)
        if v is None:
            return []
        if not isinstance(v, list) or any(not isinstance(x, dict) for x in v):
            self.problemas.append(f"{caminho}: deve ser uma lista de tabelas [[{caminho}]]")
            return []
        return v

    def confere(self, condicao: bool, mensagem: str) -> None:
        if not condicao:
            self.problemas.append(mensagem)


def _campo_por_tipo(le: _Leitor, campo: str, tipo: Optional[str], cobertura: Dict[str, Any]) -> bool:
    """Confere a exigência do ``campo`` para o tipo (data-model 3.2); devolve se ele deve ser lido."""
    if tipo is None:  # tipo desconhecido: sem as regras por tipo, o campo é lido se estiver presente
        return le.presente(campo)
    e = perfil_campos.exigencia(campo, tipo)
    presente = le.presente(campo)
    if e.nivel == NAO_SE_APLICA:
        le.confere(not presente, f"{campo}: não se aplica a {tipo}")
        return False
    if e.nivel == COM_COBERTURA and not presente:
        gatilho = perfil_campos.exigido_pela_cobertura(campo, tipo, cobertura)
        if gatilho:
            nivel, conjuntos = gatilho
            le.problemas.append(f'{campo}: obrigatório para {tipo} com a cobertura "{nivel}" em {", ".join(conjuntos)}')
        return False
    return e.nivel == OBRIGATORIO or presente


def _cobertura(le: _Leitor, tipo: Optional[str]) -> Dict[str, Any]:
    """``[cobertura]``: uma chave por conjunto de série do registro que serve ao tipo (data-model 3.3)."""
    from src.coleta.registro import chaves_da_cobertura  # o registro é o único lugar dos conjuntos por tipo

    tabela = le.dados.get("cobertura")
    if tabela is None:
        le.confere(tipo in (None, "UHE"), f"cobertura: tabela obrigatória para {tipo}")
        return {}
    if not isinstance(tabela, dict):
        le.problemas.append("cobertura: deve ser uma tabela [cobertura]")
        return {}
    if tipo is None:
        return {}
    validas, cobertura = chaves_da_cobertura(tipo), {}
    for chave, valor in tabela.items():
        if chave not in validas:
            le.problemas.append(f"cobertura.{chave}: conjunto do ONS desconhecido ou que não serve a {tipo}")
        elif (isinstance(valor, str) and valor in COBERTURAS) or (
                isinstance(valor, list) and sorted(valor) == ["conjunto", "proprio"]):
            cobertura[chave] = valor
        else:
            le.problemas.append(f'cobertura.{chave}: use proprio, conjunto, agregado, ausente ou a lista '
                                f'["proprio", "conjunto"]')
    return cobertura


def _planejamento(le: _Leitor) -> Tuple[Planejamento, ...]:
    entradas: List[Planejamento] = []
    for i, t in enumerate(le.tabelas("identificacao.planejamento"), start=1):
        codigo, inicio, fim = t.get("codigo"), t.get("inicio"), t.get("fim", "")
        ok = isinstance(codigo, int) and not isinstance(codigo, bool) and codigo > 0
        le.confere(ok, f"identificacao.planejamento {i}: codigo deve ser inteiro maior que zero")
        ok_inicio = isinstance(inicio, str) and bool(_PADRAO_MES.match(inicio))
        le.confere(ok_inicio, f"identificacao.planejamento {i}: inicio no formato AAAA-MM")
        ok_fim = isinstance(fim, str) and (fim == "" or bool(_PADRAO_MES.match(fim)))
        le.confere(ok_fim, f"identificacao.planejamento {i}: fim no formato AAAA-MM ou vazio (vigente)")
        if ok and ok_inicio and ok_fim:
            le.confere(not fim or fim >= inicio, f"identificacao.planejamento {i}: fim antes do início")
            entradas.append(Planejamento(codigo, inicio, fim))
    for a, b in ((a, b) for n, a in enumerate(entradas) for b in entradas[n + 1:] if a.codigo == b.codigo):
        if a.inicio <= (b.fim or "9999-12") and b.inicio <= (a.fim or "9999-12"):
            le.problemas.append(f"identificacao.planejamento: código {a.codigo} com períodos sobrepostos")
    return tuple(entradas)


def _membros(le: _Leitor) -> Tuple[Membro, ...]:
    membros: List[Membro] = []
    for i, t in enumerate(le.tabelas("identificacao.membros"), start=1):
        id_ons, ceg, inicio, fim = t.get("id_ons"), t.get("ceg"), t.get("inicio"), t.get("fim", "")
        ok = (isinstance(id_ons, str) and id_ons.strip() and isinstance(ceg, str) and bool(_PADRAO_CEG.match(ceg))
              and isinstance(inicio, str) and bool(_PADRAO_DIA.match(inicio))
              and isinstance(fim, str) and (fim == "" or bool(_PADRAO_DIA.match(fim))))
        le.confere(bool(ok), f"identificacao.membros {i}: id_ons, ceg no padrão, inicio AAAA-MM-DD e fim AAAA-MM-DD "
                             f"ou vazio")
        if ok:
            membros.append(Membro(id_ons, ceg, inicio, fim))
    return tuple(membros)


def validar_perfil(dados: Dict[str, Any], slug_pasta: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Valida o conteúdo de um perfil; devolve os campos lidos e a lista de problemas (vazia se válido)."""
    le = _Leitor(dados)
    c: Dict[str, Any] = {}
    # usina
    c["slug"] = le.texto("usina.slug")
    if c["slug"] is not None:
        le.confere(bool(_PADRAO_SLUG.match(c["slug"])), "usina.slug: só letras minúsculas, algarismos e _")
        le.confere(c["slug"] == slug_pasta, f"usina.slug: '{c['slug']}' diferente do nome da pasta '{slug_pasta}'")
        le.confere(c["slug"] != SLUG_RESERVADO,
                   f'usina.slug: "{SLUG_RESERVADO}" é o nome da pasta das carteiras em reports/; escolha outro')
    c["nome"] = le.texto("usina.nome")
    c["nome_curto"] = le.texto("usina.nome_curto")
    c["estado"] = le.texto("usina.estado")
    if c["estado"] is not None:
        le.confere(bool(_PADRAO_ESTADO.match(c["estado"])), "usina.estado: deve ter 2 letras maiúsculas")
    c["inicio"] = le.inteiro("usina.inicio_operacao_comercial")
    if c["inicio"] is not None:
        le.confere(1900 <= c["inicio"] <= _dt.date.today().year,
                   "usina.inicio_operacao_comercial: deve estar entre 1900 e o ano atual")
    c["tipo"] = le.texto("usina.tipo")
    if c["tipo"] is not None and c["tipo"] not in TIPOS_USINA:
        le.problemas.append(f"usina.tipo: use {', '.join(TIPOS_USINA[:-1])} ou {TIPOS_USINA[-1]}")
        c["tipo"] = None
    c["modalidade"] = le.texto("usina.modalidade")
    if c["modalidade"] in MODALIDADES_TIPO_III:
        le.problemas.append("usina.modalidade: Tipo III não tem relatório por usina; o ONS só publica o agregado (ver "
                            "a carteira do estado)")
    elif c["modalidade"] is not None and c["modalidade"] not in MODALIDADES_COM_PERFIL:
        le.problemas.append(f"usina.modalidade: use {', '.join(MODALIDADES_COM_PERFIL[:-1])} ou "
                            f"{MODALIDADES_COM_PERFIL[-1]}")
    c["situacao"] = le.texto("usina.situacao", obrigatorio=False) or "conferido"
    c["pendentes"] = le.lista_textos("usina.pendentes", obrigatorio=False) or ()
    if c["situacao"] not in SITUACOES:
        le.problemas.append("usina.situacao: use rascunho ou conferido")
    elif c["situacao"] == "rascunho":
        le.problemas.append('usina.situacao: perfil em rascunho; complete os pendentes com a fonte e troque para '
                            '"conferido"')
        le.problemas += [f"pendente: {p}" for p in c["pendentes"]]
    elif c["pendentes"]:
        le.problemas.append('usina.pendentes: deve estar vazia quando a situação é "conferido"')
    # identificação comum e tipo usado nas regras por tipo (o do CEG, que é a referência; decisão R1)
    c["ceg"] = le.texto("identificacao.ceg")
    prefixo = None
    if c["ceg"] is not None:
        if _PADRAO_CEG.match(c["ceg"]):
            prefixo = c["ceg"].split(".", 1)[0]
        else:
            le.problemas.append("identificacao.ceg: fora do padrão TIPO.XX.UF.NNNNNN-D.DD (TIPO: UHE, PCH, CGH, UTE, "
                                "UTN, EOL ou UFV)")
    if c["tipo"] is not None and prefixo is not None:
        le.confere(c["tipo"] == prefixo, f'usina.tipo: "{c["tipo"]}" diferente do prefixo do CEG ("{prefixo}")')
    tipo = prefixo or c["tipo"]
    c["tipo"] = c["tipo"] or tipo
    cobertura = c["cobertura"] = _cobertura(le, tipo)
    # códigos de programação: cod_programacao ou a lista codigos_programacao
    if le.presente("identificacao.cod_programacao") and le.presente("identificacao.codigos_programacao"):
        le.problemas.append("identificacao: use cod_programacao ou codigos_programacao, não os dois")
        c["codigos_programacao"] = ()
    elif le.presente("identificacao.codigos_programacao"):
        lista = le.lista_textos("identificacao.codigos_programacao")
        le.confere(lista is None or len(lista) > 0, "identificacao.codigos_programacao: lista vazia")
        c["codigos_programacao"] = tuple(lista or ())
    else:
        codigo = le.texto("identificacao.cod_programacao")
        c["codigos_programacao"] = (codigo,) if codigo else ()
    # identificação por tipo e cobertura
    for campo in ("id_ons", "id_reservatorio", "id_conjunto"):
        c[campo] = le.texto(f"identificacao.{campo}") if _campo_por_tipo(le, f"identificacao.{campo}", tipo,
                                                                         cobertura) else None
    c["cod_usina"] = None
    if _campo_por_tipo(le, "identificacao.cod_usina", tipo, cobertura):
        c["cod_usina"] = le.inteiro("identificacao.cod_usina")
        if c["cod_usina"] is not None:
            le.confere(c["cod_usina"] > 0, "identificacao.cod_usina: deve ser maior que zero")
    c["nome_ons"] = None
    if _campo_por_tipo(le, "identificacao.nome_ons", tipo, cobertura):
        c["nome_ons"] = le.texto("identificacao.nome_ons")
        if c["nome_ons"] is not None:
            le.confere(bool(_PADRAO_NOME_ONS.match(c["nome_ons"])),
                       "identificacao.nome_ons: em maiúsculas e sem acento, como nos conjuntos do ONS")
    c["planejamento"] = _planejamento(le) if _campo_por_tipo(le, "identificacao.planejamento", tipo, cobertura) else ()
    c["membros"] = _membros(le) if _campo_por_tipo(le, "identificacao.membros", tipo, cobertura) else ()
    c["subsistema"] = None
    if _campo_por_tipo(le, "usina.subsistema", tipo, cobertura):
        c["subsistema"] = le.texto("usina.subsistema")
        if c["subsistema"] is not None:
            le.confere(c["subsistema"] in SUBSISTEMAS, f"usina.subsistema: use {', '.join(SUBSISTEMAS)}")
    # parâmetros comuns
    c["potencia_instalada_mw"] = le.real("parametros.potencia_instalada_mw")
    c["unidades_geradoras"] = le.inteiro("parametros.unidades_geradoras")
    pot, n = c["potencia_instalada_mw"], c["unidades_geradoras"]
    if pot is not None:
        le.confere(pot > 0, "parametros.potencia_instalada_mw: deve ser maior que zero")
    if n is not None:
        le.confere(n >= 1, "parametros.unidades_geradoras: deve ser pelo menos 1")
    c["potencia_unitaria_mw"], c["potencias_unidades_mw"] = None, ()
    com_lista = le.presente("parametros.potencias_unidades_mw")
    if tipo == "UHE":  # a UHE continua com a potência unitária
        le.confere(not com_lista, "parametros.potencias_unidades_mw: não se aplica a UHE")
        com_lista = False
    elif com_lista and le.presente("parametros.potencia_unitaria_mw"):
        le.problemas.append("parametros: use potencia_unitaria_mw ou potencias_unidades_mw, não os dois")
        com_lista = None
    if com_lista:
        lista = le.lista_reais("parametros.potencias_unidades_mw")
        if lista is not None:
            le.confere(all(x > 0 for x in lista), "parametros.potencias_unidades_mw: cada valor deve ser maior que zero")
            c["potencias_unidades_mw"] = lista
            if n is not None:
                le.confere(len(lista) == n, f"parametros.potencias_unidades_mw: {len(lista)} valores para {n} unidades")
            if pot is not None and abs(sum(lista) - pot) > TOLERANCIA_POTENCIA_PERFIL_MW:
                le.problemas.append(f"parametros: soma das unidades ({sum(lista):g} MW) diferente da potência instalada "
                                    f"({pot:g} MW) em mais de {TOLERANCIA_POTENCIA_PERFIL_MW:g} MW".replace(".", ","))
    elif com_lista is not None:
        unit = c["potencia_unitaria_mw"] = le.real("parametros.potencia_unitaria_mw")
        if unit is not None:
            le.confere(unit > 0, "parametros.potencia_unitaria_mw: deve ser maior que zero")
            if None not in (pot, n) and n >= 1:
                le.confere(abs(unit * n - pot) <= TOLERANCIA_POTENCIA_PERFIL_MW,
                           f"parametros.potencia_unitaria_mw × unidades_geradoras ({unit * n:g} MW) diferente da "
                           f"potência instalada ({pot:g} MW) em mais de {TOLERANCIA_POTENCIA_PERFIL_MW:g} MW")
    # parâmetros por tipo
    for campo in ("engolimento_nominal_ug_m3s", "garantia_fisica_mwmed", "ip_referencia", "teif_referencia",
                  "queda_bruta_m", "perda_hidraulica_m", "rendimento_turbina_gerador", "vazao_remanescente_m3s"):
        caminho = f"parametros.{campo}"
        c[campo] = le.real(caminho) if _campo_por_tipo(le, caminho, tipo, cobertura) else None
    for campo in ("tipo_turbina", "combustivel"):
        caminho = f"parametros.{campo}"
        c[campo] = le.texto(caminho) if _campo_por_tipo(le, caminho, tipo, cobertura) else None
    for campo in ("engolimento_nominal_ug_m3s", "garantia_fisica_mwmed", "queda_bruta_m"):
        if c[campo] is not None:
            le.confere(c[campo] > 0, f"parametros.{campo}: deve ser maior que zero")
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
    c["fonte_gf"] = le.texto("parametros.fontes.garantia_fisica", obrigatorio=c["garantia_fisica_mwmed"] is not None)
    c["fonte_inicio"] = le.texto("parametros.fontes.inicio_operacao_comercial", obrigatorio=False)
    c["fonte_ip_teif"] = le.texto("parametros.fontes.ip_teif", obrigatorio=False)
    # análises (só onde há EVT)
    c["analises"] = None
    if _campo_por_tipo(le, "analises", tipo, cobertura):
        vertimento = le.real("analises.vertimento_minimo_m3s")
        if vertimento is not None:
            le.confere(vertimento >= 0, "analises.vertimento_minimo_m3s: não pode ser negativo")
        faixas = le.lista_reais("analises.faixas_geracao_mw")
        if faixas is not None:
            le.confere(all(a < b for a, b in zip(faixas, faixas[1:])), "analises.faixas_geracao_mw: deve ser crescente")
            if pot is not None:
                plena = FRACAO_PLENA_CARGA * pot
                le.confere(all(LIMIAR_GERACAO_PARADA_MW < x < plena for x in faixas),
                           f"analises.faixas_geracao_mw: cada valor deve ficar acima de {LIMIAR_GERACAO_PARADA_MW:g} MW "
                           f"(usina parada) e abaixo da plena carga ({plena:g} MW)")
        c["analises"] = (vertimento, faixas, le.texto("analises.descricao_vertimento_minimo", obrigatorio=False),
                         le.texto("analises.fontes.vertimento_minimo", obrigatorio=False))
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
    analises = None
    if c["analises"] is not None:
        vertimento, faixas, descricao, fonte = c["analises"]
        analises = Analises(vertimento, faixas, descricao, FontesAnalises(fonte))
    return Perfil(
        usina=Usina(c["slug"], c["nome"], c["nome_curto"], c["estado"], c["inicio"], c["tipo"], c["modalidade"],
                    c["situacao"], tuple(c["pendentes"]), c["subsistema"]),
        identificacao=Identificacao(c["cod_usina"], c["nome_ons"], c["ceg"], c["id_ons"], c["codigos_programacao"][0],
                                    c["id_reservatorio"], c["codigos_programacao"], c["id_conjunto"],
                                    c["planejamento"], c["membros"]),
        parametros=Parametros(
            c["potencia_instalada_mw"], c["unidades_geradoras"], c["potencia_unitaria_mw"], c["tipo_turbina"],
            c["engolimento_nominal_ug_m3s"], c["garantia_fisica_mwmed"], c["ip_referencia"], c["teif_referencia"],
            c["queda_bruta_m"], c["perda_hidraulica_m"], c["rendimento_turbina_gerador"], c["vazao_remanescente_m3s"],
            FontesParametros(c["fonte_geral"], c["fonte_gf"], c["fonte_inicio"], c["fonte_ip_teif"]),
            c["potencias_unidades_mw"], c["combustivel"],
        ),
        analises=analises,
        textos=Textos(c["ressalva_volume_util"]),
        arquivo=arquivo,
        cobertura=dict(c["cobertura"]),
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
