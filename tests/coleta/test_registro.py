"""Registro dos conjuntos do ONS (spec 006, decisão R8; data-model, seção 4; tarefa T034).

O registro declara, para cada conjunto, pacote e pasta, tipos de usina, nível, resolução e se pode ser série de
referência. A Coleta, os dicionários e as fontes do relatório passam a usar só os conjuntos do tipo e da cobertura da
usina. Na UHE sem ``[cobertura]``, tudo fica como hoje: os dez conjuntos, na mesma ordem.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.coleta import registro
from src.coleta.dicionarios import montar_registro
from src.comum.perfil import carregar_perfil

PACOTES_DE_HOJE = {
    "energia-vertida-turbinavel": "",
    "ind_disponibilidade_fgeracao_uge_mensal": "indicadores_ons/ind_disponibilidade_fgeracao_uge_mensal",
    "ind_disponibilidade_fgeracao_uge_anual": "indicadores_ons/ind_disponibilidade_fgeracao_uge_anual",
    "taxa_teif_teip_parametro": "indicadores_ons/taxa_teif_teip_parametro",
    "taxa_teif_teip": "indicadores_ons/taxa_teif_teip",
    "programacao_diaria": "programacao_diaria",
    "disponibilidade_usina": "disponibilidade_usina",
    "dados_hidrologicos_ho": "dados_hidrologicos_ho",
    "geracao-usina-2": "geracao_usina_2",
    "modalidade-usina": "modalidade_usina",
}
CHAVES_DE_HOJE = ["evt", "indicadores", "programacao", "disponibilidade", "hidrologia", "geracao", "cadastro"]


def _perfil(ceg: str, tipo=None, cobertura=None) -> SimpleNamespace:
    ident = SimpleNamespace(ceg=ceg, id_ons="XXUSIN", cod_usina=1, nome_ons="USINA", id_reservatorio="XXRES",
                            cod_programacao="XXUSIN")
    usina = SimpleNamespace(estado="MS", **({"tipo": tipo} if tipo else {}))
    return SimpleNamespace(identificacao=ident, usina=usina, **({"cobertura": cobertura} if cobertura else {}))


# ---------------------------------------------------------------------------
# Entradas de hoje
# ---------------------------------------------------------------------------


def test_entradas_de_hoje_na_ordem_da_coleta() -> None:
    assert [e.chave for e in registro.REGISTRO] == CHAVES_DE_HOJE
    for entrada in registro.REGISTRO:
        assert entrada.resolucao in registro.RESOLUCOES
        assert set(entrada.niveis) <= set(registro.NIVEIS)
        assert set(entrada.tipos) <= set(registro.TIPOS_USINA)


def test_tipos_e_atributos_da_tabela_do_data_model() -> None:
    e = {entrada.chave: entrada for entrada in registro.REGISTRO}
    assert e["evt"].tipos == ("UHE", "PCH", "CGH") and e["evt"].referencia and e["evt"].resolucao == "horaria"
    assert e["indicadores"].tipos == ("UHE", "PCH", "CGH", "UTE", "UTN") and e["indicadores"].resolucao == "mensal_anual"
    assert e["programacao"].tipos == registro.TIPOS_USINA and e["programacao"].resolucao == "semi_horaria"
    assert e["programacao"].niveis == ("usina", "conjunto")
    assert e["disponibilidade"].tipos == ("UHE", "PCH", "CGH", "UTE", "UTN")
    assert e["hidrologia"].tipos == ("UHE", "PCH", "CGH") and not e["hidrologia"].referencia
    assert e["geracao"].tipos == registro.TIPOS_USINA and e["geracao"].referencia
    assert e["geracao"].niveis == ("usina", "conjunto")
    assert e["cadastro"].tipos == registro.TIPOS_USINA and e["cadastro"].resolucao == "estatica"


def test_conjuntos_pipeline_sai_do_registro() -> None:
    assert registro.CONJUNTOS_PIPELINE == PACOTES_DE_HOJE
    assert list(registro.CONJUNTOS_PIPELINE) == list(PACOTES_DE_HOJE)


def test_descricoes_horarias_reproduzem_as_de_hoje() -> None:
    perfil = carregar_perfil("sao_domingos")
    ident, estado = perfil.identificacao, perfil.usina.estado
    d = registro.descricoes(perfil)
    assert list(d) == ["disponibilidade", "hidrologia", "geracao"]
    assert d["disponibilidade"].pacote == "disponibilidade_usina" and d["disponibilidade"].pasta == "disponibilidade_usina"
    assert d["disponibilidade"].identificador == registro.Regra("id_ons", ident.id_ons)
    assert d["disponibilidade"].conferencias == (registro.Regra("ceg", ident.ceg), registro.Regra("id_estado", estado))
    assert d["disponibilidade"].colunas_valor == ("val_potenciainstalada", "val_dispoperacional", "val_dispsincronizada")
    assert d["disponibilidade"].convencao_hora == "inicio" and d["disponibilidade"].filtro_parquet is None
    assert d["hidrologia"].identificador == registro.Regra("cod_usina", ident.cod_usina)
    assert d["hidrologia"].conferencias == (registro.Regra("nom_reservatorio", ident.nome_ons, "contem"),
                                             registro.Regra("id_reservatorio", ident.id_reservatorio))
    assert d["hidrologia"].convencao_hora == "fim"
    assert d["hidrologia"].colunas_valor[-3:] == ("val_nivelmontante", "val_niveljusante", "val_volumeutil")
    assert d["geracao"].identificador == registro.Regra("id_ons", ident.id_ons)
    assert d["geracao"].colunas_valor == ("val_geracao",)
    assert d["geracao"].filtro_parquet == ((("id_ons", "in", (ident.id_ons,)),), (("ceg", "in", (ident.ceg,)),))
    assert (d["geracao"].chave, d["geracao"].referencia, d["geracao"].resolucao) == ("geracao", True, "horaria")


# ---------------------------------------------------------------------------
# Filtro por tipo e cobertura (FR-015)
# ---------------------------------------------------------------------------


def test_tipo_da_usina_pelo_perfil_ou_pelo_prefixo_do_ceg() -> None:
    assert registro.tipo_da_usina(carregar_perfil("sao_domingos")) == "UHE"
    assert registro.tipo_da_usina(_perfil("UTE.GN.MS.027075-0.01")) == "UTE"
    assert registro.tipo_da_usina(_perfil("UHE.PH.MS.000001-0.01", tipo="UHE")) == "UHE"


@pytest.mark.parametrize("ceg, chaves", [
    ("UHE.PH.MS.028761-0.01", CHAVES_DE_HOJE),
    ("PCH.PH.MS.032163-0.01", CHAVES_DE_HOJE),
    ("UTE.GN.MS.027075-0.01", ["indicadores", "programacao", "disponibilidade", "geracao", "cadastro"]),
    ("UTN.NU.RJ.000001-0.01", ["indicadores", "programacao", "disponibilidade", "geracao", "cadastro"]),
    ("EOL.CV.CE.028631-1.01", ["programacao", "geracao", "cadastro"]),
    ("UFV.RS.MS.052257-0.01", ["programacao", "geracao", "cadastro"]),
])
def test_conjuntos_pelo_tipo(ceg: str, chaves: list) -> None:
    assert [e.chave for e in registro.conjuntos_da_usina(_perfil(ceg))] == chaves


def test_com_cobertura_so_os_conjuntos_proprio_ou_conjunto_e_sempre_os_cadastrais() -> None:
    """data-model 3.3: com a tabela, a Coleta obtém os conjuntos com ``proprio`` ou ``conjunto`` (ou a lista) e,
    sempre, os cadastrais; ``ausente``, ``agregado`` ou chave não declarada não são obtidos."""
    perfil = _perfil("PCH.PH.MS.032163-0.01", cobertura={
        "evt": "ausente", "indicadores": "proprio", "programacao": "conjunto", "hidrologia": "agregado",
        "geracao": ["proprio", "conjunto"]})
    assert [e.chave for e in registro.conjuntos_da_usina(perfil)] == [
        "indicadores", "programacao", "geracao", "cadastro"]


def test_nivel_da_descricao_pela_cobertura() -> None:
    perfil = _perfil("PCH.PH.MS.032163-0.01", cobertura={"geracao": "conjunto", "disponibilidade": "proprio"})
    d = registro.descricoes(perfil)
    assert list(d) == ["disponibilidade", "geracao"]
    assert (d["disponibilidade"].nivel, d["geracao"].nivel) == ("usina", "conjunto")


def test_uhe_sem_cobertura_coleta_os_dez_de_hoje_e_nao_pede_composicao_nem_capacidade() -> None:
    entradas = registro.conjuntos_da_usina(carregar_perfil("sao_domingos"))
    assert [e.chave for e in entradas] == CHAVES_DE_HOJE
    assert not {"composicao", "capacidade"} & {e.chave for e in entradas}
    assert registro.pacotes(entradas) == PACOTES_DE_HOJE


# ---------------------------------------------------------------------------
# Dicionários por usina
# ---------------------------------------------------------------------------


def test_registro_dos_dicionarios_da_uhe_sem_cobertura_tem_os_dez_de_hoje(tmp_path: Path) -> None:
    pacotes = registro.pacotes(registro.conjuntos_da_usina(carregar_perfil("sao_domingos")))
    tabela = montar_registro(tmp_path, pacotes)
    assert len(tabela) == 20
    assert list(dict.fromkeys(tabela["conjunto"])) == list(PACOTES_DE_HOJE)
    assert (tabela.groupby("conjunto").size() == 2).all()


def test_registro_dos_dicionarios_so_com_os_conjuntos_da_usina(tmp_path: Path) -> None:
    pasta = tmp_path / "geracao_usina_2" / "_dicionarios"
    pasta.mkdir(parents=True)
    (pasta / "_manifesto_ons.json").write_text(json.dumps({"_consulta": {"obtido_em_utc": "2026-10-09 10:00:00"}}),
                                               encoding="utf-8")
    pacotes = registro.pacotes(registro.conjuntos_da_usina(_perfil("EOL.CV.CE.028631-1.01")))
    tabela = montar_registro(tmp_path, pacotes)
    assert list(dict.fromkeys(tabela["conjunto"])) == ["programacao_diaria", "geracao-usina-2", "modalidade-usina"]
    assert set(tabela.loc[tabela["conjunto"] == "geracao-usina-2", "resultado_ultima_obtencao"]) == {"NAO_PUBLICADO"}
