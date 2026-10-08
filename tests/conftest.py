"""Fixtures e geradores de dados para a suíte de testes pytest."""

import pytest
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from src.comum.perfil import carregar_perfil, definir_perfil_ativo

_PERFIL_SAO_DOMINGOS = carregar_perfil("sao_domingos")


@pytest.fixture(autouse=True)
def perfil_sao_domingos_ativo():
    """Perfil ativo durante cada teste, como ``src.pipeline`` faz em cada etapa (as Análises e o relatório o leem)."""
    definir_perfil_ativo(_PERFIL_SAO_DOMINGOS)
    yield _PERFIL_SAO_DOMINGOS
    definir_perfil_ativo(None)

ONS_CSV_HEADER = (
    "id_subsistema;nom_subsistema;nom_bacia;nom_rio;nom_agente;nom_reservatorio;"
    "cod_usina;din_instante;val_geracao;val_disponibilidade;val_vazaoturbinada;"
    "val_vazaovertida;val_vazaovertidanaoturbinavel;val_produtividade;"
    "val_folgadegeracao;val_energiavertida;val_vazaovertidaturbinavel;val_energiavertidaturbinavel"
)

# Linha da UHE São Domingos com as identidades do ONS respeitadas:
# folga = 46,8 - 30,5; vertida = 1 + 5; EVT = 1 x 0,305; energia vertida = 6 x 0,305
SAMPLE_SAO_DOMINGOS_LINE = (
    "SE;SUDESTE;PARANA;VERDE;AXIA SUL;SAO DOMINGOS;153;2026-08-01 00:00:00;"
    "30.5;46.8;100.0;6.0;5.0;0.305;16.3;1.83;1.0;0.305"
)

# Mesma usina com o nome antigo do agente (deve ser extraída: o filtro usa código e reservatório)
SAMPLE_SAO_DOMINGOS_AGENTE_ANTIGO_LINE = (
    "SE;SUDESTE;PARANA;VERDE;CGT ELETROSUL;SAO DOMINGOS;153;2026-08-01 01:00:00;"
    "31.0;46.8;101.6;6.0;5.0;0.305;15.8;1.83;1.0;0.305"
)

# cod_usina 153 com outro reservatório (não deve ser extraída; conta como divergência)
SAMPLE_CODIGO_OUTRO_RESERVATORIO_LINE = (
    "SE;SUDESTE;PARANA;VERDE;OUTRO AGENTE;OUTRA USINA;153;2026-08-01 00:00:00;"
    "10.0;20.0;30.0;0.0;0.0;0.333;10.0;0.0;0.0;0.0"
)

# Reservatório homônimo com outro cod_usina (não deve ser extraída; conta como divergência)
SAMPLE_RESERVATORIO_OUTRO_CODIGO_LINE = (
    "SE;SUDESTE;PARANA;VERDE;OUTRO AGENTE;SAO DOMINGOS II;999;2026-08-01 00:00:00;"
    "10.0;20.0;30.0;0.0;0.0;0.333;10.0;0.0;0.0;0.0"
)

SAMPLE_OTHER_LINE = (
    "N;NORTE;AMAZONAS;UATUMA;AXIA NORTE;BALBINA;277;2026-08-01 00:00:00;"
    "78.135;250.0;367.0;0.0;0.0;0.2129;171.865;0.0;0.0;0.0"
)


def gerar_df_sintetico() -> pd.DataFrame:
    """Série horária sintética (nov/2023 a fev/2024) com identidades do ONS respeitadas.

    Contém: 30 h de indisponibilidade total, 5 h de usina parada com vertimento turbinável,
    mudança de classificação do vertimento contínuo em jan/2024 e um registro anômalo
    (geração acima da potência instalada).
    """
    produtividade = 0.305
    linhas = []
    for t in pd.date_range("2023-11-01 00:00", "2024-02-29 23:00", freq="h"):
        disp = 0.0 if pd.Timestamp("2023-11-10 00:00") <= t <= pd.Timestamp("2023-11-11 05:00") else 46.8
        parada = pd.Timestamp("2024-02-10 09:00") <= t <= pd.Timestamp("2024-02-10 13:00")
        ger = 0.0 if (parada or disp == 0) else 30.0
        if t == pd.Timestamp("2024-02-20 10:00"):
            ger = 60.0  # anomalia: acima da potência instalada e da disponibilidade
        vazao_vertida = 80.0 if parada else 6.0
        folga = max(0.0, disp - ger)
        if disp == 0:
            nao_turbinavel = vazao_vertida
        elif t < pd.Timestamp("2024-01-01"):
            nao_turbinavel = 0.0
        else:
            nao_turbinavel = 5.0
        vazao_turbinavel = min(vazao_vertida - nao_turbinavel, folga / produtividade)
        linhas.append(
            {
                "id_subsistema": "SE",
                "nom_subsistema": "SUDESTE",
                "nom_bacia": "PARANA",
                "nom_rio": "VERDE",
                "nom_agente": "AXIA SUL",
                "nom_reservatorio": "SAO DOMINGOS",
                "cod_usina": 153,
                "din_instante": t,
                "val_geracao": ger,
                "val_disponibilidade": disp,
                "val_vazaoturbinada": ger / produtividade,
                "val_vazaovertida": vazao_vertida,
                "val_vazaovertidanaoturbinavel": nao_turbinavel,
                "val_produtividade": produtividade,
                "val_folgadegeracao": folga,
                "val_energiavertida": vazao_vertida * produtividade,
                "val_vazaovertidaturbinavel": vazao_turbinavel,
                "val_energiavertidaturbinavel": vazao_turbinavel * produtividade,
            }
        )
    return pd.DataFrame(linhas)


@pytest.fixture
def df_sintetico() -> pd.DataFrame:
    return gerar_df_sintetico()


@pytest.fixture
def mock_ckan_response() -> Dict[str, Any]:
    """Mock da resposta da API CKAN com múltiplos recursos."""
    return {
        "success": True,
        "result": {
            "name": "energia-vertida-turbinavel",
            "title": "Energia Vertida Turbinável",
            "resources": [
                {
                    "id": "res-pdf-01",
                    "name": "Dicionário de Dados",
                    "format": "PDF",
                    "url": "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/Dicionario.pdf",
                    "size": 150000,
                    "last_modified": "2022-11-07T20:40:37.770097",
                },
                {
                    "id": "res-csv-2015",
                    "name": "Energia_Vertida_Turbinavel-2015",
                    "format": "CSV",
                    "url": "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/ENERGIA_VERTIDA_TURBINAVEL_2015.csv",
                    "size": 500000,
                    "last_modified": "2026-01-08T17:19:56.674707",
                },
                {
                    "id": "res-csv-2026-08",
                    "name": "Energia_Vertida_Turbinavel-2026-08",
                    "format": "CSV",
                    "url": "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/ENERGIA_VERTIDA_TURBINAVEL_2026_08.csv",
                    "size": 800000,
                    "last_modified": "2026-09-30T15:06:00.141888",
                },
            ],
        },
    }


@pytest.fixture
def sample_csv_with_matches(tmp_path: Path) -> Path:
    """CSV com registros da usina, divergências de identificação e outra usina."""
    file_path = tmp_path / "sample_match.csv"
    content = "\n".join([
        ONS_CSV_HEADER,
        SAMPLE_SAO_DOMINGOS_LINE,
        SAMPLE_SAO_DOMINGOS_AGENTE_ANTIGO_LINE,
        SAMPLE_CODIGO_OUTRO_RESERVATORIO_LINE,
        SAMPLE_RESERVATORIO_OUTRO_CODIGO_LINE,
        SAMPLE_OTHER_LINE,
    ])
    file_path.write_text(content, encoding="utf-8")
    return file_path


@pytest.fixture
def sample_csv_without_matches(tmp_path: Path) -> Path:
    """CSV que não contém registros de São Domingos (ex: histórico inicial)."""
    file_path = tmp_path / "sample_empty_matches.csv"
    content = "\n".join([
        ONS_CSV_HEADER,
        SAMPLE_OTHER_LINE,
    ])
    file_path.write_text(content, encoding="utf-8")
    return file_path
