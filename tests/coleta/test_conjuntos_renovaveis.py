"""Conjuntos das eólicas e solares na Coleta (plano da Coleta de dados, D24 e D27).

Com brutos sintéticos: o Fator de capacidade pela usina (CEG) ou pelo conjunto (estado, CEG "-"); a restrição com
detalhe semi-horária, pelo id ONS e pelo CEG, com as colunas que faltam em parte dos arquivos aceitas e contadas, sem
servir de conferência; a restrição com a razão pela usina ou pelo conjunto; as variantes eólica e fotovoltaica pelo
tipo; e a restrição com detalhe como série de referência das eólicas e solares em conjunto com série própria.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from src.coleta import registro, serie_referencia
from src.coleta.conjuntos import extrair_arquivo
from src.comum.perfil import Membro

ID_UFV, CEG_UFV = "GOUFXX", "UFV.RS.GO.999991-0.01"
ID_EOL, CEG_EOL = "GOEOXX", "EOL.CV.GO.999992-0.01"
CONJUNTO = "CJU_GOCJXX"


def _perfil(tipo: str, cobertura: dict, membros=()) -> SimpleNamespace:
    id_ons, ceg = (ID_UFV, CEG_UFV) if tipo == "UFV" else (ID_EOL, CEG_EOL)
    ident = SimpleNamespace(ceg=ceg, id_ons=id_ons, cod_usina=None, nome_ons=None, id_reservatorio=None,
                            cod_programacao=id_ons, codigos_programacao=(id_ons,), id_conjunto=CONJUNTO,
                            planejamento=(), membros=tuple(membros))
    usina = SimpleNamespace(slug="teste", estado="GO", tipo=tipo, modalidade="TIPO II-C", subsistema=None)
    return SimpleNamespace(identificacao=ident, usina=usina, cobertura=cobertura)


def _gravar(caminho: Path, tabela: pd.DataFrame) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_parquet(caminho, index=False) if caminho.suffix == ".parquet" else \
        tabela.to_csv(caminho, sep=";", index=False)
    return caminho


SEMI = pd.date_range("2024-02-01 00:00", periods=4, freq="30min")


def _detalhe(id_ons: str, ceg: str, recurso: str = "val_irradianciaverificado",
             invalido: str = "flg_dadoirradianciainvalido", completo: bool = True) -> pd.DataFrame:
    t = pd.DataFrame({"id_ons": id_ons, "ceg": ceg, "din_instante": SEMI, "nom_modalidadeoperacao": "TIPO II-C",
                      recurso: 500.0, invalido: 0, "val_geracaoestimada": 12.0, "val_geracaoverificada": 10.0})
    if completo:  # as cinco colunas que a fotovoltaica de 05 a 12/2024 não trazia (FR-058)
        t = t.assign(id_ons_conjuntousina=CONJUNTO, flg_geracaorestrita=1, val_geracaoreferenciafinal=None,
                     nom_origemirradiancia="x", flg_dadoirradianciasupervisaoinvalido=0)
    return t


# ---------------------------------------------------------------------------
# Registro e variantes
# ---------------------------------------------------------------------------


def test_variantes_pelo_tipo_e_os_pacotes_da_usina() -> None:
    ufv = _perfil("UFV", {"geracao": "conjunto", "restricao_detalhe": "proprio", "restricao_razao": "conjunto",
                          "fator_capacidade": "conjunto"})
    eol = _perfil("EOL", {"geracao": "proprio", "restricao_detalhe": "proprio", "restricao_razao": "proprio",
                          "fator_capacidade": "proprio"})
    d_ufv, d_eol = registro.descricoes(ufv), registro.descricoes(eol)
    assert d_ufv["restricao_detalhe"].pacote == "restricao_coff_fotovoltaica_detail"
    assert d_eol["restricao_detalhe"].pacote == "restricao_coff_eolica_detail"
    assert d_ufv["restricao_razao"].pacote == "restricao_coff_fotovoltaica"
    assert d_eol["restricao_razao"].pacote == "restricao_coff_eolica_usi"
    assert "val_irradianciaverificado" in d_ufv["restricao_detalhe"].colunas_valor
    assert "val_ventoverificado" in d_eol["restricao_detalhe"].colunas_valor
    assert d_ufv["restricao_detalhe"].resolucao == "semi_horaria"
    pacotes = registro.pacotes(registro.conjuntos_da_usina(ufv), "UFV")
    assert "restricao_coff_fotovoltaica_detail" in pacotes and "restricao_coff_eolica_detail" not in pacotes
    assert "fator_capacidade" in registro.chaves_da_cobertura("EOL")
    assert "restricao_detalhe" not in registro.chaves_da_cobertura("UTE")


# ---------------------------------------------------------------------------
# Fator de capacidade
# ---------------------------------------------------------------------------


def test_fator_capacidade_pela_usina_ou_pelo_conjunto(tmp_path: Path) -> None:
    horas = pd.date_range("2024-02-01", periods=3, freq="h")
    linhas = pd.concat([
        pd.DataFrame({"id_ons": ID_EOL, "ceg": CEG_EOL, "id_estado": "GO", "din_instante": horas,
                      "val_geracaoprogramada": "10", "val_geracaoverificada": "9,5", "val_capacidadeinstalada": "40",
                      "val_fatorcapacidade": "0,2375"}),
        pd.DataFrame({"id_ons": CONJUNTO, "ceg": "-", "id_estado": "GO", "din_instante": horas,
                      "val_geracaoprogramada": "30", "val_geracaoverificada": "28", "val_capacidadeinstalada": "50",
                      "val_fatorcapacidade": "0,56"}),
        pd.DataFrame({"id_ons": CONJUNTO, "ceg": "-", "id_estado": "BA", "din_instante": horas[:1],
                      "val_geracaoprogramada": "1", "val_geracaoverificada": "1", "val_capacidadeinstalada": "1",
                      "val_fatorcapacidade": "1"}),  # mesmo id em outro estado: só identificador
    ])
    caminho = _gravar(tmp_path / "FATOR_CAPACIDADE-2_2024_02.csv", linhas)
    usina = registro.descricoes(_perfil("EOL", {"geracao": "proprio", "fator_capacidade": "proprio"}))
    dados, auditoria = extrair_arquivo(usina["fator_capacidade"], caminho)
    assert usina["fator_capacidade"].nivel == "usina" and auditoria["linhas_usina"] == 3
    assert list(dados["val_geracaoverificada"]) == [9.5] * 3 and dados["val_fatorcapacidade"].iloc[0] == 0.2375
    conjunto = registro.descricoes(_perfil("UFV", {"geracao": "conjunto", "fator_capacidade": "conjunto"}))
    dados, auditoria = extrair_arquivo(conjunto["fator_capacidade"], caminho)
    assert conjunto["fator_capacidade"].nivel == "conjunto"
    assert (auditoria["linhas_usina"], auditoria["linhas_so_identificador"]) == (3, 1)


# ---------------------------------------------------------------------------
# Restrição com detalhe e com a razão
# ---------------------------------------------------------------------------


def test_restricao_com_detalhe_semi_horaria_pelo_id_e_pelo_ceg(tmp_path: Path) -> None:
    desc = registro.descricoes(_perfil("UFV", {"geracao": "conjunto", "restricao_detalhe": "proprio"}))[
        "restricao_detalhe"]
    caminho = _gravar(tmp_path / "RESTRICAO_COFF_FOTOVOLTAICA_DETAIL_2024_02.parquet", pd.concat([
        _detalhe(ID_UFV, CEG_UFV),
        _detalhe(ID_UFV, "UFV.RS.GO.000000-0.01").head(1),  # o id com outro CEG: só identificador
        _detalhe("GOOUTR", "UFV.RS.GO.999993-0.01"),  # outra usina do mesmo conjunto
    ]))
    dados, auditoria = extrair_arquivo(desc, caminho)
    assert (auditoria["linhas_usina"], auditoria["linhas_so_identificador"]) == (4, 1)
    assert list(dados["din_instante"]) == list(SEMI)  # as quatro semi-horas, como publicadas
    assert set(dados["id_ons_conjuntousina"]) == {CONJUNTO} and auditoria["mensagem"] == ""


def test_colunas_ausentes_aceitas_contadas_e_fora_da_conferencia(tmp_path: Path) -> None:
    desc = registro.descricoes(_perfil("UFV", {"geracao": "conjunto", "restricao_detalhe": "proprio"}))[
        "restricao_detalhe"]
    # nesses arquivos a marca de irradiância inválida é booleana: vira 1 e 0, sem contar como valor inválido
    caminho = _gravar(tmp_path / "RESTRICAO_COFF_FOTOVOLTAICA_DETAIL_2024_06.parquet",
                      _detalhe(ID_UFV, CEG_UFV, completo=False).assign(
                          flg_dadoirradianciainvalido=[False, True, False, None]))
    dados, auditoria = extrair_arquivo(desc, caminho)
    assert auditoria["status"] == "PROCESSADO" and auditoria["linhas_usina"] == 4
    assert "flg_geracaorestrita" in auditoria["mensagem"] and "id_ons_conjuntousina" in auditoria["mensagem"]
    assert dados["flg_geracaorestrita"].isna().all() and (dados["id_ons_conjuntousina"] == "").all()
    assert dados["flg_dadoirradianciainvalido"].tolist()[:3] == [0.0, 1.0, 0.0]
    assert auditoria["valores_invalidos"] == 0 and not dados["_nao_numerico"].any()


def test_restricao_com_a_razao_pela_usina_ou_pelo_conjunto(tmp_path: Path) -> None:
    linhas = pd.concat([
        pd.DataFrame({"id_ons": ID_EOL, "ceg": CEG_EOL, "id_estado": "GO", "din_instante": SEMI, "val_geracao": 8.0,
                      "cod_razaorestricao": ["REL", "", "CNF", "ENE"], "num_minutos_rel": [30, 0, 0, 0],
                      "num_minutos_cnf": [0, 0, 30, 0], "num_minutos_ene": [0, 0, 0, 30]}),
        pd.DataFrame({"id_ons": CONJUNTO, "ceg": "-", "id_estado": "GO", "din_instante": SEMI, "val_geracao": 20.0,
                      "cod_razaorestricao": "ENE", "num_minutos_rel": 0, "num_minutos_cnf": 0,
                      "num_minutos_ene": 30}),
    ])
    caminho = _gravar(tmp_path / "RESTRICAO_COFF_EOLICA_2024_02.parquet", linhas)
    usina = registro.descricoes(_perfil("EOL", {"geracao": "proprio", "restricao_razao": "proprio"}))
    dados, _ = extrair_arquivo(usina["restricao_razao"], caminho)
    assert list(dados["cod_razaorestricao"]) == ["REL", "", "CNF", "ENE"] and list(dados["num_minutos_rel"])[0] == 30
    conjunto = registro.descricoes(_perfil("EOL", {"geracao": "proprio", "restricao_razao": "conjunto"}))
    dados, _ = extrair_arquivo(conjunto["restricao_razao"], caminho)
    assert conjunto["restricao_razao"].nivel == "conjunto" and set(dados["val_geracao"]) == {20.0}


# ---------------------------------------------------------------------------
# Série de referência (linha da FR-059 na tabela da FR-054)
# ---------------------------------------------------------------------------


def test_serie_de_referencia_na_restricao_com_detalhe(tmp_path: Path) -> None:
    em_conjunto = _perfil("UFV", {"geracao": "conjunto", "restricao_detalhe": "proprio"},
                          membros=(Membro(ID_UFV, CEG_UFV, "2023-01-01"), Membro("GOOUTR", "UFV.RS.GO.999993-0.01",
                                                                                 "2023-01-01")))
    escolha = serie_referencia.escolher(em_conjunto)
    assert (escolha.conjunto, escolha.niveis) == ("restricao_detalhe", ("usina",))
    assert "restrição com detalhe" in escolha.motivo
    propria = _perfil("EOL", {"geracao": "proprio", "restricao_detalhe": "proprio"})
    assert serie_referencia.escolher(propria).conjunto == "geracao"  # com geração própria, a Geração por usina
    pasta = tmp_path / "raw" / "restricao_coff_fotovoltaica_detail"
    _gravar(pasta / "RESTRICAO_COFF_FOTOVOLTAICA_DETAIL_2024_02.parquet",
            pd.concat([_detalhe(ID_UFV, CEG_UFV).assign(val_geracaoverificada=[None, 5.0, 6.0, None]),
                       _detalhe("GOOUTR", "UFV.RS.GO.999993-0.01")]))
    series, auditoria = serie_referencia.extrair_referencia(em_conjunto, escolha, tmp_path / "raw")
    inicio, fim = serie_referencia.periodo(series, serie_referencia.COLUNA_VALOR[escolha.conjunto])
    assert (inicio, fim) == (SEMI[1], SEMI[2])  # da primeira à última semi-hora com valor
    complemento = serie_referencia.complemento(series, "val_geracaoverificada", semi_horaria=True)
    assert list(complemento["din_instante"]) == [SEMI[0], SEMI[2]]  # uma linha por hora cheia
    assert set(complemento["cod_modalidadeoperacao"]) == {"TIPO II-C"}
    assert serie_referencia.resumo(escolha, em_conjunto, inicio, fim, auditoria)["identificador"] == f"id_ons={ID_UFV}"
