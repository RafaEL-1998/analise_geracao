"""Rascunho do perfil: ``python -m src perfil --ceg <CEG> [--slug <slug>]`` (plano da Coleta de dados, D23 e D33;
contratos cli-perfil e perfil-usina da Coleta de dados).

Lê só ``data/catalogo/``: não acessa o portal, não lê os brutos e não executa nenhuma etapa. Nunca sobrescreve um
perfil (FR-053). Na ordem:

1. catálogo ausente ou em formato antigo: código 5;
2. CEG fora do catálogo, tipo fora dos atendidos, usina Tipo III ou só com cobertura agregada ou ausente: código 2;
3. perfil existente (na pasta do slug ou em outra, com o mesmo CEG): nada é gravado; mostra as diferenças em relação ao
   catálogo e sai com 6, ou com 0 sem diferença;
4. grava ``usinas/<slug>/perfil.toml`` com ``situacao = "rascunho"``: os identificadores, o subsistema, a
   ``[cobertura]`` dos conjuntos implementados, os códigos de programação ligados pelo id ONS ou pelo id do conjunto,
   os membros do conjunto vigente, as unidades ativas, nas térmicas os códigos de planejamento do despacho e, nas
   hidrelétricas, os códigos dos Reservatórios. Cada valor
   traz a origem em comentário; os demais campos ficam pendentes, como linhas comentadas.
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, TextIO, Tuple

import pandas as pd

from src.coleta import registro
from src.coleta.catalogo_usinas import ler_catalogo, perfis_por_ceg
from src.coleta.registro import normalizar_texto
from src.comum import caminhos, perfil_campos
from src.comum.formatacao import fmt_data, fmt_num
from src.comum.logger import setup_logger
from src.comum.persistencia import gravar_bytes
from src.comum.regras import MODALIDADES_TIPO_III, TIPOS_USINA, TOLERANCIA_POTENCIA_PERFIL_MW

logger = setup_logger("coleta")

CODIGO_SUCESSO, CODIGO_ERRO, CODIGO_INVALIDO, CODIGO_CATALOGO, CODIGO_DIFERENCAS = 0, 1, 2, 5, 6
SLUG_RESERVADO = caminhos.PASTA_CARTEIRAS
_PADRAO_SLUG = re.compile(r"^[a-z0-9_]+$")
_PADRAO_CEG = re.compile(r"^(UHE|PCH|CGH|UTE|UTN|EOL|UFV)\.[A-Z]{2}\.[A-Z]{2}\.\d{6}-\d\.\d{2}$")
COLUNA_COMENTARIO = 38  # coluna dos comentários de origem, para o rascunho ficar legível
ORIGEM = {"cadastro": "Modalidade das usinas", "composicao": "Composição dos conjuntos",
          "capacidade": "Capacidade de geração", "reservatorio": "Reservatórios", "programacao": "Programação diária",
          "despacho": "Geração térmica por motivo de despacho"}
PACOTE_ORIGEM = {"cadastro": "modalidade-usina", "composicao": "usina_conjunto", "capacidade": "capacidade-geracao",
                 "reservatorio": "reservatorio"}


def slug_do_nome(nome: str) -> str:
    """Slug a partir do nome: sem acento, em minúsculas, com ``_`` no lugar do que não é letra ou algarismo."""
    sem_acento = "".join(c for c in unicodedata.normalize("NFKD", nome) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", sem_acento.lower()).strip("_")


def _toml(valor: Any) -> str:
    """Valor em TOML: texto (com os escapes de JSON, compatíveis), número, booleano ou lista."""
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, int):
        return str(valor)
    if isinstance(valor, float):
        return repr(round(valor, 4))
    if isinstance(valor, (list, tuple)):
        return "[" + ", ".join(_toml(v) for v in valor) + "]"
    return json.dumps(str(valor), ensure_ascii=False)


def _linha(chave: str, valor: Any, comentario: str = "") -> str:
    texto = f"{chave} = {_toml(valor)}"
    return f"{texto:<{COLUNA_COMENTARIO - 1}} # {comentario}" if comentario else texto


def _pendente(chave: str, comentario: str) -> str:
    return f"{'# ' + chave + ' =':<{COLUNA_COMENTARIO - 1}} # pendente: {comentario}"


def _origem(info: Dict[str, Any], chave: str) -> str:
    """Nome do conjunto do ONS e data de publicação do arquivo usado no catálogo."""
    publicacao = (info.get("cadastro", {}).get(PACOTE_ORIGEM.get(chave, ""), {}) or {}).get("publicacao", "")
    if chave == "programacao":
        publicacao = next((c.get("publicacao", "") for c in info.get("cobertura", []) if c.get("conjunto") == "programacao"),
                          "")
    try:
        quando = f", publicado em {fmt_data(publicacao)}" if publicacao else ""
    except (ValueError, TypeError):
        quando = ""
    return f"{ORIGEM[chave]}{quando}"


def _numero(valor: Any) -> Optional[float]:
    try:
        return float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# O que o catálogo diz da usina
# ---------------------------------------------------------------------------


def _esperado(catalogo: Dict[str, Any], u: pd.Series, hoje: date) -> Dict[str, Any]:
    """Os valores do catálogo para o perfil da usina: identificação, cobertura, membros, unidades e códigos."""
    tipo = u["tipo"]
    cobertura_tab = catalogo["cobertura"]
    cobertura = {r["conjunto_ons"]: r["nivel"] for _, r in cobertura_tab[cobertura_tab["ceg"] == u["ceg"]].iterrows()}
    programacao = catalogo["programacao"]
    codigos: List[str] = []
    periodos: Dict[str, Tuple[str, str]] = {}
    for valor in (u["id_ons"], u["id_conjunto"]):
        if valor:
            ligados = programacao[programacao["id_usina_ou_conjunto"] == valor]
            codigos = list(ligados["codigo_exibicao"])  # todos os do período, na ordem do primeiro dia (FR-053)
            periodos = {r["codigo_exibicao"]: (r.get("primeiro_dia", ""), r.get("ultimo_dia", ""))
                        for _, r in ligados.iterrows()}
            if codigos:
                break
    codigos_estado = sorted(programacao.loc[programacao["estado"] == u["id_estado"], "codigo_exibicao"])
    conjuntos = catalogo["conjuntos"]
    membros = []
    if u["id_conjunto"]:
        do_conjunto = conjuntos[conjuntos["id_conjunto"] == u["id_conjunto"]]
        for _, m in do_conjunto.iterrows():
            inicio = m["inicio"] or ""
            if (not inicio or inicio <= hoje.isoformat()) and (not m["fim"] or m["fim"] > hoje.isoformat()):
                membros.append({"id_ons": m["id_ons_usina"], "ceg": m["ceg"], "inicio": inicio, "fim": m["fim"]})
    ultimo_dia = max((str(d) for d in programacao.get("ultimo_dia", pd.Series(dtype=str)) if str(d)), default="")
    return {"tipo": tipo, "cobertura": cobertura, "codigos": codigos, "codigos_estado": codigos_estado,
            "periodos_codigos": periodos, "ultimo_dia_programacao": ultimo_dia,
            "membros": membros, "planejamento": planejamento_da_usina(catalogo, u["ceg"])}


def texto_periodos_codigos(esperado: Dict[str, Any]) -> str:
    """"MSCAO-9761 de 01/10/2024 a 02/07/2025; MSCAO-9764 desde 05/07/2025" (vigente: presente no último dia publicado
    da Programação diária); vazio sem os dias no catálogo."""
    partes = []
    for codigo in esperado["codigos"]:
        inicio, fim = esperado.get("periodos_codigos", {}).get(codigo, ("", ""))
        if not inicio:
            return ""
        if fim and fim != esperado.get("ultimo_dia_programacao"):
            partes.append(f"{codigo} de {fmt_data(inicio)} a {fmt_data(fim)}")
        else:
            partes.append(f"{codigo} desde {fmt_data(inicio)}")
    return "; ".join(partes)


def planejamento_da_usina(catalogo: Dict[str, Any], ceg: str) -> List[Dict[str, Any]]:
    """Códigos de planejamento do CEG no despacho (``planejamento.csv``), na ordem do início: ``codigo``, ``inicio`` e
    ``fim`` (AAAA-MM; vazio quando o código está no último mês publicado, ou seja, vigente) e os nomes publicados."""
    tabela = catalogo.get("planejamento")
    if tabela is None or tabela.empty:
        return []
    ultimo = tabela["ultimo_mes"].max()
    da_usina = tabela[tabela["ceg"].map(normalizar_texto) == normalizar_texto(ceg)]
    saida = []
    for r in da_usina.sort_values(["primeiro_mes", "codigo"]).itertuples():
        numero = float(r.codigo)
        saida.append({"codigo": int(numero) if numero.is_integer() else numero, "inicio": r.primeiro_mes,
                      "fim": "" if r.ultimo_mes == ultimo else r.ultimo_mes, "nomes": r.nomes_publicados})
    return saida


def _texto_planejamento(entradas: Sequence[Any]) -> str:
    """"34 de 2013-01 a 2018-08; 334 desde 2021-07" (dicionários do perfil ou do catálogo)."""
    partes = []
    for p in entradas:
        codigo, inicio, fim = p.get("codigo"), p.get("inicio", ""), p.get("fim", "")
        partes.append(f"{codigo} de {inicio} a {fim}" if fim else f"{codigo} desde {inicio}")
    return "; ".join(partes)


def _resolver_usina(catalogo: Dict[str, Any], ceg: str) -> Tuple[Optional[pd.Series], int, str]:
    """A linha da usina no catálogo, ou o código e a mensagem da recusa (código 2)."""
    usinas = catalogo["usinas"]
    linhas = usinas[usinas["ceg"].map(normalizar_texto) == normalizar_texto(ceg)]
    if linhas.empty:
        return None, CODIGO_INVALIDO, f"CEG {ceg} fora do catálogo de usinas (data/catalogo/usinas.csv)."
    u = linhas.iloc[0]
    if u["tipo"] not in TIPOS_USINA:
        return None, CODIGO_INVALIDO, (f'A usina {u["nom_usina"]} ({u["ceg"]}) tem o tipo "{u["tipo"]}" pelo CEG, fora dos '
                                       f"tipos atendidos ({', '.join(TIPOS_USINA)}).")
    so_agregado = (normalizar_texto(u["modalidade"]) in MODALIDADES_TIPO_III
                   or u["cobertura_resumo"] in ("agregado", "ausente", ""))
    if so_agregado:
        return None, CODIGO_INVALIDO, (f"O ONS publica a usina {u['nom_usina']} ({u['ceg']}) só em agregado "
                                       f"({u['modalidade']}), sem dados próprios nem de conjunto. Ela aparece no panorama "
                                       f"da carteira: python -m src carteira --estado {u['id_estado']}")
    return u, CODIGO_SUCESSO, ""


# ---------------------------------------------------------------------------
# Diferenças com um perfil existente
# ---------------------------------------------------------------------------


def _ausente(valor: Any) -> str:
    return "(ausente)" if valor in (None, "", [], ()) else str(valor)


def diferencas(perfil: Dict[str, Any], u: pd.Series, esperado: Dict[str, Any]) -> List[str]:
    """Campos do perfil existente diferentes do catálogo (``- campo: perfil X; catálogo Y``).

    Sempre: tipo, modalidade, estado e CEG. Os demais identificadores, quando o perfil os traz. A ``[cobertura]``
    em cada conjunto do catálogo; numa UHE sem a tabela, valem os conjuntos de hoje com ``proprio``.
    """
    usina, ident = perfil.get("usina") or {}, perfil.get("identificacao") or {}
    linhas: List[str] = []

    def comparar(campo: str, no_perfil: Any, no_catalogo: Any) -> None:
        if str(no_perfil if no_perfil is not None else "").strip() != str(no_catalogo if no_catalogo is not None else "").strip():
            linhas.append(f"- {campo}: perfil {_ausente(no_perfil)}; catálogo {_ausente(no_catalogo)}")

    for campo, catalogo_valor in (("tipo", u["tipo"]), ("modalidade", u["modalidade"]), ("estado", u["id_estado"])):
        comparar(f"usina.{campo}", usina.get(campo), catalogo_valor)
    comparar("identificacao.ceg", ident.get("ceg"), u["ceg"])
    for campo, catalogo_valor in (("id_ons", u["id_ons"]), ("id_conjunto", u["id_conjunto"]),
                                  ("cod_usina", u["cod_usina"]), ("nome_ons", normalizar_texto(u["nom_reservatorio"])),
                                  ("id_reservatorio", u["id_reservatorio"])):
        if campo in ident:
            comparar(f"identificacao.{campo}", ident.get(campo), catalogo_valor)
    codigos_perfil = ident.get("codigos_programacao") or ([ident["cod_programacao"]] if ident.get("cod_programacao")
                                                          else [])
    if codigos_perfil and esperado["codigos"]:
        comparar("identificacao.codigos_programacao", ";".join(sorted(codigos_perfil)),
                 ";".join(sorted(esperado["codigos"])))
    if u["tipo"] in registro.TERMICAS:  # térmicas: subsistema (CMO) e códigos de planejamento (despacho e CVU)
        if usina.get("subsistema") or u["subsistema"]:
            comparar("usina.subsistema", usina.get("subsistema"), u["subsistema"])
        if ident.get("planejamento") or esperado["planejamento"]:
            comparar("identificacao.planejamento", _texto_planejamento(ident.get("planejamento") or []),
                     _texto_planejamento(esperado["planejamento"]))
    cobertura_perfil = perfil.get("cobertura")
    if cobertura_perfil is None and u["tipo"] == "UHE":
        cobertura_perfil = {chave: "proprio" for chave in registro.CHAVES_SEM_COBERTURA if chave in esperado["cobertura"]}
    for chave, nivel in esperado["cobertura"].items():
        valor = (cobertura_perfil or {}).get(chave)
        valor = ";".join(valor) if isinstance(valor, list) else valor
        comparar(f"cobertura.{chave}", valor, nivel)
    return linhas


# ---------------------------------------------------------------------------
# Rascunho
# ---------------------------------------------------------------------------


def _unidades(catalogo_unidades: pd.Series) -> Tuple[Optional[float], Optional[int]]:
    return _numero(catalogo_unidades.get("potencia_efetiva_mw")), (
        int(_numero(catalogo_unidades.get("unidades_geradoras")) or 0) or None)


def montar_rascunho(catalogo: Dict[str, Any], u: pd.Series, esperado: Dict[str, Any], slug: str,
                    potencias_unidades: Sequence[float]) -> Tuple[str, int, List[str]]:
    """Texto TOML do rascunho, quantidade de campos preenchidos com dados do ONS e lista de pendentes."""
    info = catalogo["json"]
    tipo, cobertura = u["tipo"], esperado["cobertura"]
    pendentes: List[str] = []
    preenchidos = 0
    hidreletrica_com_codigos = tipo in ("UHE", "PCH", "CGH") and bool(u["cod_usina"])

    def exigido(campo: str) -> bool:
        e = perfil_campos.exigencia(campo, tipo)
        if e.nivel == perfil_campos.OBRIGATORIO:
            return True
        return e.nivel == perfil_campos.COM_COBERTURA and perfil_campos.exigido_pela_cobertura(campo, tipo, cobertura) is not None

    def aplica(campo: str) -> bool:
        return perfil_campos.exigencia(campo, tipo).nivel != perfil_campos.NAO_SE_APLICA

    linhas = [
        '# Rascunho gerado por "python -m src perfil" a partir do catálogo de usinas (data/catalogo/, montado em '
        f'{info.get("montado_em_utc", "")} UTC).',
        '# Confira cada valor com a fonte, complete os pendentes e troque situacao para "conferido".',
        "# Identificação só pelos códigos (CEG, id ONS, id do conjunto e códigos de programação), nunca pelo nome.",
        "",
        "[usina]",
        _linha("slug", slug),
    ]
    linhas.append(_linha("nome", u["nom_usina"], f"{_origem(info, 'cadastro')}; ajuste para o nome do relatório"))
    linhas.append(_linha("nome_curto", u["nom_usina"], "a conferir"))
    linhas.append(_linha("estado", u["id_estado"], ORIGEM["cadastro"]))
    linhas.append(_linha("tipo", tipo, "prefixo do CEG"))
    linhas.append(_linha("modalidade", u["modalidade"], ORIGEM["cadastro"]))
    preenchidos += 5
    if u["subsistema"]:
        linhas.append(_linha("subsistema", u["subsistema"], f"{ORIGEM['capacidade']} ou {ORIGEM['composicao']}"))
        preenchidos += 1
    if u["entrada_operacao"]:
        linhas.append(_linha("inicio_operacao_comercial", int(u["entrada_operacao"][:4]),
                             f"{ORIGEM['capacidade']}: primeira unidade ativa em {fmt_data(u['entrada_operacao'])}; "
                             "a conferir"))
        preenchidos += 1
    else:
        linhas.append(_pendente("inicio_operacao_comercial", "ano de início da operação comercial, com a fonte"))
        pendentes.append("usina.inicio_operacao_comercial")
    linhas.append(_linha("situacao", "rascunho"))
    indice_pendentes = len(linhas)  # a lista de pendentes entra aqui, no fim

    # [identificacao]
    linhas += ["", "[identificacao]", _linha("ceg", u["ceg"], ORIGEM["cadastro"])]
    preenchidos += 1
    if u["id_ons"]:
        linhas.append(_linha("id_ons", u["id_ons"], ORIGEM["cadastro"]))
        preenchidos += 1
    elif exigido("identificacao.id_ons"):
        linhas.append(_pendente("id_ons", "id ONS da usina, com a fonte"))
        pendentes.append("identificacao.id_ons")
    if aplica("identificacao.id_conjunto") and u["id_conjunto"]:
        linhas.append(_linha("id_conjunto", u["id_conjunto"], f"{ORIGEM['composicao']}: {u['nom_conjunto']}"))
        preenchidos += 1
    if hidreletrica_com_codigos:
        linhas.append(_linha("cod_usina", int(_numero(u["cod_usina"]) or 0), ORIGEM["reservatorio"]))
        linhas.append(_linha("nome_ons", normalizar_texto(u["nom_reservatorio"]), f"{ORIGEM['reservatorio']}: nome do "
                                                                                    "reservatório"))
        linhas.append(_linha("id_reservatorio", u["id_reservatorio"], ORIGEM["reservatorio"]))
        preenchidos += 3
    else:
        for campo in ("cod_usina", "nome_ons", "id_reservatorio"):
            if aplica(f"identificacao.{campo}") and exigido(f"identificacao.{campo}"):
                linhas.append(_pendente(campo, "código da usina na EVT e nos dados hidrológicos, com a fonte"))
                pendentes.append(f"identificacao.{campo}")
    if esperado["codigos"]:
        linhas.append(_linha("codigos_programacao", esperado["codigos"], _origem(info, "programacao")))
        periodos = texto_periodos_codigos(esperado)
        if periodos:  # o Tratamento soma os códigos por patamar: confira se os períodos não se sobrepõem (FR-053)
            linhas.append(f"#   períodos na Programação diária: {periodos}")
        preenchidos += 1
    else:
        linhas.append(_pendente("codigos_programacao", "código de exibição na Programação diária; nenhum código ligado "
                                                       "pelo id ONS nem pelo conjunto"))
        estado = esperado["codigos_estado"]
        for inicio in range(0, len(estado), 8):
            linhas.append(f"#   códigos de {u['id_estado']}: {', '.join(estado[inicio:inicio + 8])}")
        pendentes.append("identificacao.codigos_programacao")
    if aplica("identificacao.membros"):
        for m in esperado["membros"]:
            if not m["id_ons"] or not _PADRAO_CEG.match(m["ceg"]) or not m["inicio"]:
                linhas.append(f"# membro do conjunto sem id ONS, CEG ou início na Composição: {m['ceg'] or m['id_ons']}")
                continue
            linhas += ["", "[[identificacao.membros]]".ljust(COLUNA_COMENTARIO - 1) + f" # {ORIGEM['composicao']}",
                       _linha("id_ons", m["id_ons"]), _linha("ceg", m["ceg"]), _linha("inicio", m["inicio"]),
                       _linha("fim", m["fim"], "vazio = vigente")]

    if aplica("identificacao.planejamento"):
        for p in esperado["planejamento"]:
            comentario = f"{ORIGEM['despacho']}; publicado como {p['nomes']}" if p["nomes"] else ORIGEM["despacho"]
            linhas += ["", "[[identificacao.planejamento]]".ljust(COLUNA_COMENTARIO - 1) + f" # {comentario}",
                       _linha("codigo", p["codigo"]), _linha("inicio", p["inicio"]),
                       _linha("fim", p["fim"], "vazio = vigente")]
            preenchidos += 1
        if not esperado["planejamento"] and exigido("identificacao.planejamento"):
            linhas.append(_pendente("[[identificacao.planejamento]]", "código de planejamento do despacho, com o "
                                                                      "período; nenhum código no despacho para o CEG"))
            pendentes.append("identificacao.planejamento")

    # [cobertura]
    linhas += ["", "[cobertura]".ljust(COLUNA_COMENTARIO - 1) + " # catálogo de usinas; a conferir"]
    linhas += [_linha(chave, nivel) for chave, nivel in cobertura.items()]
    preenchidos += len(cobertura)

    # [parametros]
    linhas += ["", "[parametros]"]
    potencia, unidades = _unidades(u)
    if potencia and unidades:
        linhas.append(_linha("potencia_instalada_mw", potencia, f"{ORIGEM['capacidade']}: {unidades} unidades ativas"))
        linhas.append(_linha("unidades_geradoras", unidades))
        iguais = len(set(round(p, 4) for p in potencias_unidades)) <= 1
        if tipo == "UHE" or iguais:
            linhas.append(_linha("potencia_unitaria_mw", round(potencia / unidades, 4)))
        else:
            linhas.append(_linha("potencias_unidades_mw", [round(p, 4) for p in potencias_unidades]))
        preenchidos += 3
        autorizada = _numero(u["potencia_autorizada_mw"])
        if autorizada is not None and abs(autorizada - potencia) > TOLERANCIA_POTENCIA_PERFIL_MW:
            linhas.append(f"# Divergência: potência autorizada no cadastro do ONS = {fmt_num(autorizada, 3)} MW. "
                          "Confira com a fonte.")
    else:
        for campo in ("potencia_instalada_mw", "unidades_geradoras", "potencia_unitaria_mw"):
            linhas.append(_pendente(campo, "da documentação da usina, com a fonte"))
            pendentes.append(f"parametros.{campo}")
    if aplica("parametros.combustivel"):
        if u["combustivel"]:
            linhas.append(_linha("combustivel", u["combustivel"], ORIGEM["capacidade"]))
            preenchidos += 1
        else:
            linhas.append(_pendente("combustivel", "combustível, com a fonte"))
            pendentes.append("parametros.combustivel")
    for campo in ("garantia_fisica_mwmed", "ip_referencia", "teif_referencia", *perfil_campos.HIDRAULICOS):
        caminho = f"parametros.{campo}"
        if not aplica(caminho):
            continue
        if exigido(caminho):
            linhas.append(_pendente(campo, "valor e fonte"))
            pendentes.append(caminho)
        elif perfil_campos.exigencia(caminho, tipo).nivel == perfil_campos.OPCIONAL:
            linhas.append(_pendente(campo, "opcional; valor e fonte"))
            pendentes.append(f"{caminho} (opcional)")
    linhas += ["", "[parametros.fontes]", _pendente("geral", "documento e data dos parâmetros")]
    pendentes.insert(0, "parametros.fontes.geral")
    if exigido("parametros.garantia_fisica_mwmed"):
        linhas.append(_pendente("garantia_fisica", "fonte da garantia física"))
        pendentes.append("parametros.fontes.garantia_fisica")
    if aplica("analises") and exigido("analises"):
        linhas += ["", "[analises]", _pendente("vertimento_minimo_m3s", "patamar contínuo do vertimento"),
                   _pendente("faixas_geracao_mw", "faixas de geração das tabelas de EVT")]
        pendentes += ["analises.vertimento_minimo_m3s", "analises.faixas_geracao_mw"]
    linhas.insert(indice_pendentes, _linha("pendentes", pendentes))
    return "\n".join(linhas) + "\n", preenchidos, pendentes


def executar_perfil(ceg: str, slug: Optional[str] = None, pasta_catalogo: Optional[Path] = None,
                    raiz_usinas: Optional[Path] = None, hoje: Optional[date] = None,
                    saida: Optional[TextIO] = None) -> int:
    """Executa o comando ``perfil`` e devolve o código de saída do contrato."""
    pasta_catalogo = Path(pasta_catalogo or caminhos.pasta_catalogo())
    raiz_usinas = Path(raiz_usinas or caminhos.USINAS_DIR)
    hoje = hoje or date.today()
    saida = saida or sys.stdout
    try:
        if slug is not None and (not _PADRAO_SLUG.match(slug) or slug == SLUG_RESERVADO):
            logger.error('Slug inválido: %r (letras minúsculas, algarismos e _; "%s" é reservado).', slug, SLUG_RESERVADO)
            return CODIGO_INVALIDO
        catalogo = ler_catalogo(pasta_catalogo)
        if catalogo is None:
            logger.error("O catálogo de usinas não foi montado. Execute antes: python -m src usinas")
            return CODIGO_CATALOGO
        u, codigo, mensagem = _resolver_usina(catalogo, ceg)
        if u is None:
            logger.error(mensagem)
            return codigo
        esperado = _esperado(catalogo, u, hoje)
        slug = slug or slug_do_nome(u["nom_usina"])
        if not _PADRAO_SLUG.match(slug) or slug == SLUG_RESERVADO:
            logger.error("Slug derivado do nome inválido: %r; informe --slug.", slug)
            return CODIGO_INVALIDO
        existente = raiz_usinas / slug / "perfil.toml"
        mesmo_ceg = perfis_por_ceg(raiz_usinas).get(normalizar_texto(u["ceg"]))
        if mesmo_ceg:
            existente = raiz_usinas / mesmo_ceg / "perfil.toml"
        if existente.is_file():
            return _comparar_existente(existente, raiz_usinas, u, esperado, saida)
        texto, preenchidos, pendentes = montar_rascunho(catalogo, u, esperado, slug, _potencias(catalogo, u))
        existente.parent.mkdir(parents=True, exist_ok=True)
        gravar_bytes(texto.encode("utf-8"), existente, copia=False)  # gravação conferida no disco
        tomllib.loads(existente.read_text(encoding="utf-8"))  # o rascunho é TOML válido
        logger.info('Rascunho do perfil gravado em usinas/%s/perfil.toml: %d campos preenchidos com dados do ONS e %d '
                    'pendentes. Confira, complete com a fonte e troque situacao para "conferido".', slug, preenchidos,
                    len(pendentes))
        return CODIGO_SUCESSO
    except KeyboardInterrupt:
        logger.error("Rascunho do perfil interrompido pelo usuário.")
        return CODIGO_ERRO
    except Exception as exc:
        logger.exception("Rascunho do perfil: erro inesperado: %s", exc)
        return CODIGO_ERRO


def _potencias(catalogo: Dict[str, Any], u: pd.Series) -> List[float]:
    """Potência de cada unidade ativa, da coluna ``potencias_unidades_mw`` do catálogo (valores separados por ``;``)."""
    return [v for v in (_numero(p) for p in str(u.get("potencias_unidades_mw", "")).split(";") if p.strip())
            if v is not None]


def _comparar_existente(arquivo: Path, raiz_usinas: Path, u: pd.Series, esperado: Dict[str, Any], saida: TextIO) -> int:
    relativo = arquivo.relative_to(raiz_usinas.parent).as_posix() if raiz_usinas.parent in arquivo.parents else str(arquivo)
    try:
        perfil = tomllib.loads(arquivo.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        logger.error("Perfil existente ilegível (%s): %s", relativo, exc)
        return CODIGO_ERRO
    linhas = diferencas(perfil, u, esperado)
    if not linhas:
        print(f"O perfil {relativo} já existe e não foi alterado; sem diferença em relação ao catálogo.", file=saida)
        return CODIGO_SUCESSO
    print(f"O perfil {relativo} já existe e não foi alterado. Diferenças em relação ao catálogo:", file=saida)
    for linha in linhas:
        print(linha, file=saida)
    return CODIGO_DIFERENCAS
