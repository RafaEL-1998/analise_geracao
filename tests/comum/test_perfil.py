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
