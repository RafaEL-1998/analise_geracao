"""Modelos de dados e entidades do pipeline ONS."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class RecursoONS:
    """Representa um recurso de dados (arquivo CSV) no catálogo CKAN do ONS."""
    id_recurso: str
    nome_recurso: str
    url_download: str
    formato: str
    tamanho_bytes: int = 0  # tamanho publicado no catálogo CKAN
    ultima_modificacao: str = ""  # last_modified publicado no catálogo CKAN
    arquivo_local: Optional[str] = None
    status_sincronizacao: str = "PENDING"  # PENDING, DOWNLOADED, UPDATED, CACHED, FAILED


@dataclass
class RegistroEnergiaVertida:
    """Representa uma linha horária de medição de energia vertida da usina."""
    id_subsistema: str
    nom_subsistema: str
    nom_bacia: str
    nom_rio: str
    nom_agente: str
    nom_reservatorio: str
    cod_usina: str
    din_instante: str  # YYYY-MM-DD HH:MM:SS
    val_geracao: Optional[float] = None
    val_disponibilidade: Optional[float] = None
    val_vazaoturbinada: Optional[float] = None
    val_vazaovertida: Optional[float] = None
    val_vazaovertidanaoturbinavel: Optional[float] = None
    val_produtividade: Optional[float] = None
    val_folgadegeracao: Optional[float] = None
    val_energiavertida: Optional[float] = None
    val_vazaovertidaturbinavel: Optional[float] = None
    val_energiavertidaturbinavel: Optional[float] = None
    arquivo_origem: str = ""
    tipo_match: str = "CODIGO_E_NOME"  # cod_usina e nome do reservatório conferem


@dataclass
class AuditoriaArquivo:
    """Representa o sumário de auditoria da varredura de um arquivo CSV."""
    nome_arquivo: str
    periodo_referencia: str
    total_linhas_arquivo: int = 0
    registros_extraidos: int = 0
    registros_codigo_sem_nome: int = 0  # cod_usina confere, nome do reservatório não
    registros_nome_sem_codigo: int = 0  # nome do reservatório confere, cod_usina não
    codificacao: str = "utf-8"
    status_processamento: str = "PROCESSADO"  # PROCESSADO, SEM_REGISTROS, FALHA
    data_hora_processamento: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    )
    registros_formato_irregular: int = 0  # linhas não vazias com nº de campos diferente do cabeçalho (não extraídas)
    formato: str = "CSV"
    data_publicacao: str = ""  # data de publicação no portal, pelo manifesto
    obtido: bool = True  # False: arquivo publicado que não pôde ser obtido nesta execução
    mensagem: str = ""  # motivo da falha
    valores_invalidos: int = 0  # valores numéricos ilegíveis nas linhas extraídas (ficam vazios)
