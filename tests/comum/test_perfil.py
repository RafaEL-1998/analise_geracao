"""Perfil da usina (spec da Coleta de dados, FR-006 a FR-009): leitura, recusa e valores derivados."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from src.comum.perfil import PerfilInvalido, arquivo_perfil, carregar_perfil

PERFIL_SD = arquivo_perfil("sao_domingos").read_text(encoding="utf-8")


def _gravar(raiz: Path, texto: str, slug: str = "sao_domingos") -> Path:
    destino = raiz / "usinas" / slug / "perfil.toml"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    return raiz


def _trocar(texto: str, velho: str, novo: str) -> str:
    assert texto.count(velho) == 1, velho
    return texto.replace(velho, novo)


def _problemas(raiz: Path, slug: str = "sao_domingos") -> list:
    with pytest.raises(PerfilInvalido) as erro:
        carregar_perfil(slug, raiz=raiz)
    return erro.value.problemas


def test_perfil_da_sao_domingos() -> None:
    p = carregar_perfil("sao_domingos")
    assert (p.usina.slug, p.usina.nome, p.usina.nome_curto, p.usina.estado) == (
        "sao_domingos", "UHE São Domingos", "São Domingos", "MS")
    assert (p.identificacao.cod_usina, p.identificacao.ceg, p.identificacao.id_ons) == (
        153, "UHE.PH.MS.028761-0.01", "MSUHSD")
    assert p.parametros.unidades_geradoras == 2 and p.parametros.garantia_fisica_mwmed == 36.4
    assert p.analises.faixas_geracao_mw == (10.0, 20.0, 30.0, 40.0)
    assert p.parametros.fontes.ip_teif.endswith("36,9 MWmed")
    assert p.analises.fontes.vertimento_minimo == "patamar de 5 a 6 m³/s observado na série"
    assert p.textos.ressalva_volume_util.startswith("O volume útil é apresentado como informado")


def test_valores_derivados_iguais_aos_de_hoje() -> None:
    """Os valores derivados do perfil são os mesmos que o projeto usava, com a mesma conta."""
    p = carregar_perfil("sao_domingos")
    assert p.engolimento_maximo_m3s == 163.0
    assert p.potencia_autorizada_esperada_mw == 48.0
    assert p.disponibilidade_referencia == (1.0 - 0.06861) * (1.0 - 0.02333)
    assert p.produtividade_nominal_mw_m3s == 1000.0 * 9.81 * (35.24 - 0.747) * 0.9053 / 1e6
    assert p.limites_fisicos_superiores == {
        "val_geracao": 48.0 * 1.05, "val_disponibilidade": 48.0 * 1.05, "val_folgadegeracao": 48.0 * 1.05,
        "val_energiavertidaturbinavel": 48.0 * 1.05, "val_vazaoturbinada": 163.0 * 1.05,
        "val_vazaovertidaturbinavel": 163.0 * 1.05,
    }
    assert p.plena_carga_mw == pytest.approx(43.2)


def test_campo_obrigatorio_ausente(tmp_path: Path) -> None:
    raiz = _gravar(tmp_path, _trocar(PERFIL_SD, "garantia_fisica_mwmed = 36.4\n", ""))
    assert _problemas(raiz) == ["parametros.garantia_fisica_mwmed: campo obrigatório ausente"]


@pytest.mark.parametrize(("velho", "novo", "trecho"), [
    ('estado = "MS"', 'estado = "ms"', "usina.estado"),
    ('ceg = "UHE.PH.MS.028761-0.01"', 'ceg = "UHE-PH-MS-028761"', "identificacao.ceg"),
    ("unidades_geradoras = 2", "unidades_geradoras = 0", "unidades_geradoras: deve ser pelo menos 1"),
    ("potencia_unitaria_mw = 24.0", "potencia_unitaria_mw = 25.0", "diferente da potência instalada"),
    ("ip_referencia = 0.06861", "ip_referencia = 1.0", "parametros.ip_referencia"),
    ("teif_referencia = 0.02333", "teif_referencia = -0.1", "parametros.teif_referencia"),
    ("rendimento_turbina_gerador = 0.9053", "rendimento_turbina_gerador = 1.2", "rendimento_turbina_gerador"),
    ("perda_hidraulica_m = 0.747", "perda_hidraulica_m = 40.0", "perda_hidraulica_m: deve ser menor"),
    ("faixas_geracao_mw = [10.0, 20.0, 30.0, 40.0]", "faixas_geracao_mw = [10.0, 30.0, 20.0]", "deve ser crescente"),
    ("faixas_geracao_mw = [10.0, 20.0, 30.0, 40.0]", "faixas_geracao_mw = [0.5, 20.0]", "acima de 1 MW"),
    ("faixas_geracao_mw = [10.0, 20.0, 30.0, 40.0]", "faixas_geracao_mw = [10.0, 45.0]", "abaixo da plena carga"),
    ('nome_ons = "SAO DOMINGOS"', 'nome_ons = "São Domingos"', "identificacao.nome_ons"),
    ("garantia_fisica_mwmed = 36.4", "garantia_fisica_mwmed = 50.0", "maior que a potência instalada"),
])
def test_recusa_de_valor_invalido(tmp_path: Path, velho: str, novo: str, trecho: str) -> None:
    problemas = _problemas(_gravar(tmp_path, _trocar(PERFIL_SD, velho, novo)))
    assert any(trecho in p for p in problemas), problemas


def test_slug_fora_do_padrao_ou_diferente_da_pasta(tmp_path: Path) -> None:
    raiz = _gravar(tmp_path, PERFIL_SD, slug="outra_usina")
    assert any("diferente do nome da pasta" in p for p in _problemas(raiz, "outra_usina"))
    raiz = _gravar(tmp_path, _trocar(PERFIL_SD, 'slug = "sao_domingos"', 'slug = "Sao-Domingos"'), slug="Sao-Domingos")
    assert any("só letras minúsculas" in p for p in _problemas(raiz, "Sao-Domingos"))


def test_texto_opcional_ausente_aceito_e_vazio_recusado(tmp_path: Path) -> None:
    sem = _trocar(PERFIL_SD, re.search(r"\[textos\]\n.*\n", PERFIL_SD, flags=re.S).group(0), "")
    perfil = carregar_perfil("sao_domingos", raiz=_gravar(tmp_path / "a", sem))
    assert perfil.textos.ressalva_volume_util is None
    vazio = re.sub(r'ressalva_volume_util = ".*"', 'ressalva_volume_util = ""', PERFIL_SD)
    assert any("textos.ressalva_volume_util: não pode ser vazio" in p for p in _problemas(_gravar(tmp_path / "b", vazio)))


def test_mensagem_lista_todos_os_problemas(tmp_path: Path) -> None:
    texto = _trocar(PERFIL_SD, 'estado = "MS"', 'estado = "M"')
    texto = _trocar(texto, "unidades_geradoras = 2", "unidades_geradoras = 0")
    texto = _trocar(texto, 'tipo_turbina = "Kaplan de eixo vertical"\n', "")
    with pytest.raises(PerfilInvalido) as erro:
        carregar_perfil("sao_domingos", raiz=_gravar(tmp_path, texto))
    mensagem = str(erro.value)
    assert mensagem.startswith("Perfil da usina 'sao_domingos' inválido (usinas/sao_domingos/perfil.toml):")
    assert len(erro.value.problemas) >= 3 and all(p in mensagem for p in erro.value.problemas)


def test_perfil_ausente_ou_ilegivel(tmp_path: Path) -> None:
    assert any("não encontrado" in p for p in _problemas(tmp_path, "nao_existe"))
    assert any("ilegível" in p for p in _problemas(_gravar(tmp_path, "[usina\nslug = 1")))


# ---------------------------------------------------------------------------
# Perfil por tipo (spec 006, decisão R4; data-model 3.1 a 3.5; contrato perfil-multitipo.md; tarefa T038)
# ---------------------------------------------------------------------------

FONTES_FICTICIAS = '[parametros.fontes]\ngeral = "perfil fictício de teste"\n'

PERFIL_UTE = """
[usina]
slug = "ute_ficticia"
nome = "UTE Fictícia"
nome_curto = "Fictícia"
estado = "GO"
inicio_operacao_comercial = 2010
tipo = "UTE"
modalidade = "TIPO I"

[identificacao]
ceg = "UTE.GN.GO.000002-0.01"
id_ons = "GOUTFI"
cod_programacao = "GOUTFI"

[cobertura]
indicadores = "proprio"
programacao = "proprio"
disponibilidade = "proprio"
geracao = "proprio"

[parametros]
potencia_instalada_mw = 100.0
unidades_geradoras = 2
potencias_unidades_mw = [60.0, 40.0]
combustivel = "gás natural"
""" + FONTES_FICTICIAS

PERFIL_PCH = """
[usina]
slug = "pch_ficticia"
nome = "PCH Fictícia"
nome_curto = "Fictícia"
estado = "GO"
inicio_operacao_comercial = 2008
tipo = "PCH"
modalidade = "TIPO II-C"

[identificacao]
ceg = "PCH.PH.GO.000003-0.01"
cod_programacao = "GOCJFI"
id_conjunto = "GOCJFI"

[cobertura]
programacao = "conjunto"
geracao = "conjunto"

[parametros]
potencia_instalada_mw = 20.0
unidades_geradoras = 2
potencia_unitaria_mw = 10.0
""" + FONTES_FICTICIAS

PERFIL_UFV = """
[usina]
slug = "ufv_ficticia"
nome = "UFV Fictícia"
nome_curto = "Fictícia"
estado = "GO"
inicio_operacao_comercial = 2022
tipo = "UFV"
modalidade = "TIPO II-C"

[identificacao]
ceg = "UFV.RS.GO.000004-0.01"
id_ons = "GOUFFI"
codigos_programacao = ["GOCJSO", "GOCJS2"]
id_conjunto = "GOCJSO"

[cobertura]
programacao = "conjunto"
geracao = ["proprio", "conjunto"]

[parametros]
potencia_instalada_mw = 30.0
unidades_geradoras = 1
potencia_unitaria_mw = 30.0
""" + FONTES_FICTICIAS


def _carregar(tmp_path: Path, texto: str, slug: str):
    return carregar_perfil(slug, raiz=_gravar(tmp_path, texto, slug=slug))


def test_sao_domingos_com_tipo_e_modalidade_continua_valida_e_igual() -> None:
    """FR-011: o perfil da São Domingos ganha só ``tipo`` e ``modalidade``; sem ``[cobertura]`` e conferido."""
    p = carregar_perfil("sao_domingos")
    assert (p.usina.tipo, p.usina.modalidade, p.usina.situacao, p.usina.pendentes) == ("UHE", "TIPO II-A",
                                                                                       "conferido", ())
    assert p.cobertura == {} and p.analises is not None
    assert p.identificacao.codigos_programacao == ("PRUHSD",) and p.identificacao.cod_programacao == "PRUHSD"
    assert p.potencias_das_unidades_mw == (24.0, 24.0)
    assert p.engolimento_maximo_m3s == 163.0 and p.produtividade_nominal_mw_m3s > 0


def test_tipo_obrigatorio_e_igual_ao_prefixo_do_ceg(tmp_path: Path) -> None:
    sem_tipo = _trocar(PERFIL_SD, 'tipo = "UHE"\n', "")
    assert "usina.tipo: campo obrigatório ausente" in _problemas(_gravar(tmp_path / "a", sem_tipo))
    outro = _trocar(PERFIL_SD, 'tipo = "UHE"', 'tipo = "PCH"')
    assert 'usina.tipo: "PCH" diferente do prefixo do CEG ("UHE")' in _problemas(_gravar(tmp_path / "b", outro))
    invalido = _trocar(PERFIL_SD, 'tipo = "UHE"', 'tipo = "BIO"')
    assert any(p.startswith("usina.tipo: use ") for p in _problemas(_gravar(tmp_path / "c", invalido)))


@pytest.mark.parametrize("modalidade", ["TIPO III", "TIPO III (EM DIT)"])
def test_tipo_iii_recusado(tmp_path: Path, modalidade: str) -> None:
    texto = _trocar(PERFIL_SD, 'modalidade = "TIPO II-A"', f'modalidade = "{modalidade}"')
    assert ("usina.modalidade: Tipo III não tem relatório por usina; o ONS só publica o agregado (ver a carteira do "
            "estado)") in _problemas(_gravar(tmp_path, texto))


def test_modalidade_obrigatoria_e_da_lista(tmp_path: Path) -> None:
    assert "usina.modalidade: campo obrigatório ausente" in _problemas(
        _gravar(tmp_path / "a", _trocar(PERFIL_SD, 'modalidade = "TIPO II-A"\n', "")))
    assert any(p.startswith("usina.modalidade: use ") for p in _problemas(
        _gravar(tmp_path / "b", _trocar(PERFIL_SD, 'modalidade = "TIPO II-A"', 'modalidade = "TIPO 2"'))))


def test_rascunho_recusado_com_os_pendentes(tmp_path: Path) -> None:
    texto = _trocar(PERFIL_UTE, 'modalidade = "TIPO I"\n', 'modalidade = "TIPO I"\nsituacao = "rascunho"\n'
                                                            'pendentes = ["parametros.combustivel", "identificacao.id_ons"]\n')
    problemas = _problemas(_gravar(tmp_path, texto, slug="ute_ficticia"), "ute_ficticia")
    assert ('usina.situacao: perfil em rascunho; complete os pendentes com a fonte e troque para "conferido"'
            in problemas)
    assert "pendente: parametros.combustivel" in problemas and "pendente: identificacao.id_ons" in problemas


def test_conferido_com_pendentes_recusado_e_situacao_invalida(tmp_path: Path) -> None:
    texto = _trocar(PERFIL_UTE, 'modalidade = "TIPO I"\n', 'modalidade = "TIPO I"\nsituacao = "conferido"\n'
                                                            'pendentes = ["parametros.combustivel"]\n')
    assert any(p.startswith("usina.pendentes:") for p in
               _problemas(_gravar(tmp_path / "a", texto, slug="ute_ficticia"), "ute_ficticia"))
    texto = _trocar(PERFIL_UTE, 'modalidade = "TIPO I"\n', 'modalidade = "TIPO I"\nsituacao = "pronto"\n')
    assert any(p.startswith("usina.situacao: use ") for p in
               _problemas(_gravar(tmp_path / "b", texto, slug="ute_ficticia"), "ute_ficticia"))


@pytest.mark.parametrize("ceg, valido", [
    ("UTE.GN.GO.000002-0.01", True),
    ("UTE.GN.GO.00002-0.01", False),
    ("BIO.GN.GO.000002-0.01", False),
])
def test_ceg_com_os_sete_prefixos(tmp_path: Path, ceg: str, valido: bool) -> None:
    texto = _trocar(PERFIL_UTE, 'ceg = "UTE.GN.GO.000002-0.01"', f'ceg = "{ceg}"')
    raiz = _gravar(tmp_path, texto, slug="ute_ficticia")
    if valido:
        assert carregar_perfil("ute_ficticia", raiz=raiz).identificacao.ceg == ceg
    else:
        assert any(p.startswith("identificacao.ceg:") for p in _problemas(raiz, "ute_ficticia"))


def test_slug_carteiras_recusado(tmp_path: Path) -> None:
    texto = _trocar(PERFIL_UTE, 'slug = "ute_ficticia"', 'slug = "carteiras"')
    assert any("carteiras" in p and p.startswith("usina.slug") for p in
               _problemas(_gravar(tmp_path, texto, slug="carteiras"), "carteiras"))


def test_perfis_validos_de_outros_tipos(tmp_path: Path) -> None:
    ute = _carregar(tmp_path / "ute", PERFIL_UTE, "ute_ficticia")
    assert ute.usina.tipo == "UTE" and ute.parametros.combustivel == "gás natural"
    assert ute.potencias_das_unidades_mw == (60.0, 40.0) and ute.analises is None
    assert ute.cobertura == {"indicadores": "proprio", "programacao": "proprio", "disponibilidade": "proprio",
                             "geracao": "proprio"}
    pch = _carregar(tmp_path / "pch", PERFIL_PCH, "pch_ficticia")
    assert pch.identificacao.id_conjunto == "GOCJFI" and pch.identificacao.id_ons is None
    ufv = _carregar(tmp_path / "ufv", PERFIL_UFV, "ufv_ficticia")
    assert ufv.identificacao.codigos_programacao == ("GOCJSO", "GOCJS2")
    assert ufv.identificacao.cod_programacao == "GOCJSO"
    assert ufv.cobertura["geracao"] == ["proprio", "conjunto"]


def test_valores_hidraulicos_so_nas_hidreletricas_com_evt_ou_hidrologia(tmp_path: Path) -> None:
    ute = _carregar(tmp_path, PERFIL_UTE, "ute_ficticia")
    for valor in ("engolimento_maximo_m3s", "produtividade_nominal_mw_m3s", "limite_vazao_turbinavel_m3s"):
        with pytest.raises(ValueError, match="hidrelétricas"):
            getattr(ute, valor)
    assert ute.plena_carga_mw == pytest.approx(90.0) and ute.limite_potencia_mw == pytest.approx(105.0)


def test_cobertura_obrigatoria_fora_da_uhe(tmp_path: Path) -> None:
    texto = re.sub(r"\[cobertura\]\n(.+\n)+?\n", "", PERFIL_PCH)
    assert "cobertura: tabela obrigatória para PCH" in _problemas(_gravar(tmp_path, texto, slug="pch_ficticia"),
                                                                  "pch_ficticia")


@pytest.mark.parametrize("linha, mensagem", [
    ('hidrologia = "proprio"', "cobertura.hidrologia: conjunto do ONS desconhecido ou que não serve a UFV"),
    ('despacho = "proprio"', "cobertura.despacho: conjunto do ONS desconhecido ou que não serve a UFV"),
    ('fator_capacidade = "parcial"', "cobertura.fator_capacidade: conjunto do ONS desconhecido ou que não serve a UFV"),
    ('geracao = "parcial"', 'cobertura.geracao: use proprio, conjunto, agregado, ausente ou a lista ["proprio", '
                            '"conjunto"]'),
])
def test_cobertura_com_chave_ou_valor_invalido(tmp_path: Path, linha: str, mensagem: str) -> None:
    texto = PERFIL_UFV.replace('geracao = ["proprio", "conjunto"]\n', "") if linha.startswith("geracao") else PERFIL_UFV
    texto = _trocar(texto, '[cobertura]\n', f"[cobertura]\n{linha}\n")
    assert mensagem in _problemas(_gravar(tmp_path, texto, slug="ufv_ficticia"), "ufv_ficticia")


def test_campo_exigido_pela_cobertura(tmp_path: Path) -> None:
    sem_conjunto = _trocar(PERFIL_PCH, 'id_conjunto = "GOCJFI"\n', "")
    assert ('identificacao.id_conjunto: obrigatório para PCH com a cobertura "conjunto" em geracao'
            in _problemas(_gravar(tmp_path / "a", sem_conjunto, slug="pch_ficticia"), "pch_ficticia"))
    com_evt = _trocar(PERFIL_PCH, "[cobertura]\n", '[cobertura]\nevt = "proprio"\n')
    problemas = _problemas(_gravar(tmp_path / "b", com_evt, slug="pch_ficticia"), "pch_ficticia")
    assert 'identificacao.cod_usina: obrigatório para PCH com a cobertura "proprio" em evt' in problemas
    assert 'parametros.queda_bruta_m: obrigatório para PCH com a cobertura "proprio" em evt' in problemas
    assert 'analises: obrigatório para PCH com a cobertura "proprio" em evt' in problemas


@pytest.mark.parametrize("trecho, mensagem", [
    ('combustivel = "gás natural"\n', None),
    ('cod_usina = 10\n', "identificacao.cod_usina: não se aplica a UTE"),
    ('queda_bruta_m = 10.0\n', "parametros.queda_bruta_m: não se aplica a UTE"),
])
def test_campo_por_tipo_obrigatorio_ou_que_nao_se_aplica(tmp_path: Path, trecho: str, mensagem) -> None:
    if mensagem is None:  # combustível é obrigatório em UTE
        texto = _trocar(PERFIL_UTE, trecho, "")
        mensagem = "parametros.combustivel: campo obrigatório ausente"
    elif trecho.startswith("cod_usina"):
        texto = _trocar(PERFIL_UTE, 'id_ons = "GOUTFI"\n', f'id_ons = "GOUTFI"\n{trecho}')
    else:
        texto = _trocar(PERFIL_UTE, "combustivel", f"{trecho}combustivel")
    assert mensagem in _problemas(_gravar(tmp_path, texto, slug="ute_ficticia"), "ute_ficticia")


def test_combustivel_nao_se_aplica_a_ufv_e_analises_nao_se_aplicam_a_ute(tmp_path: Path) -> None:
    texto = _trocar(PERFIL_UFV, "potencia_unitaria_mw = 30.0\n", 'potencia_unitaria_mw = 30.0\ncombustivel = "sol"\n')
    assert "parametros.combustivel: não se aplica a UFV" in _problemas(
        _gravar(tmp_path / "a", texto, slug="ufv_ficticia"), "ufv_ficticia")
    texto = PERFIL_UTE + "\n[analises]\nvertimento_minimo_m3s = 1.0\nfaixas_geracao_mw = [10.0, 20.0]\n"
    assert "analises: não se aplica a UTE" in _problemas(_gravar(tmp_path / "b", texto, slug="ute_ficticia"),
                                                         "ute_ficticia")


def test_potencias_das_unidades(tmp_path: Path) -> None:
    poucas = _trocar(PERFIL_UTE, "potencias_unidades_mw = [60.0, 40.0]", "potencias_unidades_mw = [60.0]")
    assert "parametros.potencias_unidades_mw: 1 valores para 2 unidades" in _problemas(
        _gravar(tmp_path / "a", poucas, slug="ute_ficticia"), "ute_ficticia")
    soma = _trocar(PERFIL_UTE, "potencias_unidades_mw = [60.0, 40.0]", "potencias_unidades_mw = [60.0, 30.0]")
    assert ("parametros: soma das unidades (90 MW) diferente da potência instalada (100 MW) em mais de 0,1 MW"
            in _problemas(_gravar(tmp_path / "b", soma, slug="ute_ficticia"), "ute_ficticia"))
    as_duas = _trocar(PERFIL_UTE, "potencias_unidades_mw = [60.0, 40.0]",
                      "potencias_unidades_mw = [60.0, 40.0]\npotencia_unitaria_mw = 50.0")
    assert any(p.startswith("parametros: use potencia_unitaria_mw ou potencias_unidades_mw") for p in _problemas(
        _gravar(tmp_path / "c", as_duas, slug="ute_ficticia"), "ute_ficticia"))
    lista_na_uhe = _trocar(PERFIL_SD, "potencia_unitaria_mw = 24.0", "potencias_unidades_mw = [24.0, 24.0]")
    assert "parametros.potencia_unitaria_mw: campo obrigatório ausente" in _problemas(_gravar(tmp_path / "d",
                                                                                              lista_na_uhe))


def _planejamento(*periodos) -> str:
    return "".join(f'\n[[identificacao.planejamento]]\ncodigo = {c}\ninicio = "{i}"\nfim = "{f}"\n'
                   for c, i, f in periodos)


def test_planejamento_com_codigos_vigentes(tmp_path: Path) -> None:
    from datetime import date

    texto = PERFIL_UTE.replace("[cobertura]", _planejamento((101, "2018-01", "2021-06"), (205, "2021-07", ""),
                                                            (300, "2019-01", "2019-12")).lstrip() + "\n[cobertura]")
    p = _carregar(tmp_path, texto, "ute_ficticia")
    assert [x.codigo for x in p.identificacao.planejamento] == [101, 205, 300]
    assert p.codigos_planejamento_em(date(2019, 5, 1)) == (101, 300)
    assert p.codigos_planejamento_em(date(2024, 1, 1)) == (205,)


def test_planejamento_com_o_mesmo_codigo_sobreposto_recusado(tmp_path: Path) -> None:
    texto = PERFIL_UTE.replace("[cobertura]", _planejamento((101, "2018-01", "2021-06"),
                                                            (101, "2021-01", "")).lstrip() + "\n[cobertura]")
    assert "identificacao.planejamento: código 101 com períodos sobrepostos" in _problemas(
        _gravar(tmp_path, texto, slug="ute_ficticia"), "ute_ficticia")


def test_planejamento_nao_se_aplica_a_uhe(tmp_path: Path) -> None:
    texto = PERFIL_SD.replace("[parametros]\n", _planejamento((1, "2018-01", "")).lstrip() + "\n[parametros]\n", 1)
    assert "identificacao.planejamento: não se aplica a UHE" in _problemas(_gravar(tmp_path, texto))
