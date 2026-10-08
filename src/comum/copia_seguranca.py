"""Cópia de segurança do projeto (constituição, Requisito Técnico 5; spec da Coleta de dados, FR-014 e FR-015).

``python -m src copia-seguranca --motivo <texto>`` cria ``_backup_<AAAA-MM-DD>_<motivo>/`` com o código, os testes, as
specs, os relatórios, as configurações do Spec Kit, os perfis das usinas (sem os documentos), o README e a lista de
dependências, mais ``LEIA-ME.txt``, ``conftest.py`` e ``copia.json``. Depois de conferir a cópia (quantidade de arquivos
e SHA-256 de cada um), exclui as cópias mais antigas até ficarem duas. Se a criação ou a conferência falhar, apaga a
cópia incompleta e não exclui nenhuma outra. Dados brutos, dados das etapas e documentos de referência ficam fora.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from src.comum.caminhos import RAIZ_PROJETO
from src.comum.logger import setup_logger

logger = setup_logger("pipeline")

PASTAS = ("src", "tests", "specs", "reports", ".specify")
ARQUIVOS = ("README.md", "requirements.txt")
MAXIMO_COPIAS = 2
_PADRAO_MOTIVO = re.compile(r"^[A-Za-z0-9_\-]+$")
_PADRAO_PASTA = re.compile(r"^_backup_(\d{4}-\d{2}-\d{2})_")
_IGNORAR = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def copias_existentes(raiz: Path) -> List[Path]:
    """Cópias ``_backup_*`` da raiz, da mais antiga para a mais recente (data do nome; empate, data de criação)."""
    copias = [p for p in raiz.glob("_backup_*") if p.is_dir() and _PADRAO_PASTA.match(p.name)]
    return sorted(copias, key=lambda p: (_PADRAO_PASTA.match(p.name).group(1), p.stat().st_ctime, p.name))


def _copiar(raiz: Path, destino: Path) -> List[Dict[str, object]]:
    for pasta in PASTAS:
        if (raiz / pasta).is_dir():
            shutil.copytree(raiz / pasta, destino / pasta, ignore=_IGNORAR)
    for arquivo in ARQUIVOS:
        if (raiz / arquivo).is_file():
            shutil.copy2(raiz / arquivo, destino / arquivo)
    for perfil in sorted((raiz / "usinas").glob("*/perfil.toml")):
        alvo = destino / perfil.relative_to(raiz)
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(perfil, alvo)
    registro = []
    for p in sorted(destino.rglob("*")):
        if p.is_file():
            rel = p.relative_to(destino)
            h = _sha256(p)
            if _sha256(raiz / rel) != h:
                raise RuntimeError(f"cópia diferente da origem: {rel.as_posix()}")
            registro.append({"arquivo": rel.as_posix(), "bytes": p.stat().st_size, "sha256": h})
    return registro


def _conferir(destino: Path, registro: List[Dict[str, object]]) -> None:
    copiados = [p for p in destino.rglob("*")
                if p.is_file() and not (p.parent == destino and p.name in ("copia.json", "conftest.py", "LEIA-ME.txt"))]
    if len(copiados) != len(registro):
        raise RuntimeError(f"cópia com {len(copiados)} arquivos para {len(registro)} registrados")
    for item in registro:
        if _sha256(destino / str(item["arquivo"])) != item["sha256"]:
            raise RuntimeError(f"SHA-256 diferente na cópia: {item['arquivo']}")


def criar_copia(motivo: str, raiz: Optional[Path] = None, hoje: Optional[date] = None) -> int:
    """Cria e confere a cópia; depois mantém só as duas mais recentes. Devolve o código de saída (0 ou 1)."""
    raiz = raiz or RAIZ_PROJETO
    if not _PADRAO_MOTIVO.match(motivo or ""):
        logger.error("Motivo inválido para a cópia: %r (use letras, algarismos, _ ou -).", motivo)
        return 1
    destino = raiz / f"_backup_{(hoje or date.today()).isoformat()}_{motivo}"
    if destino.exists():
        logger.error("A cópia %s já existe; escolha outro motivo.", destino.name)
        return 1
    try:
        registro = _copiar(raiz, destino)
        (destino / "copia.json").write_text(json.dumps(registro, ensure_ascii=False, indent=1), encoding="utf-8")
        (destino / "conftest.py").write_text('collect_ignore_glob = ["*"]\n', encoding="utf-8")
        (destino / "LEIA-ME.txt").write_text(
            f"Cópia de segurança de {(hoje or date.today()).strftime('%d/%m/%Y')} ({motivo}), conforme o Requisito "
            "Técnico 5 da constituição (no máximo duas cópias do projeto).\n"
            f"Conteúdo: {', '.join(p + '/' for p in PASTAS)}, usinas/*/perfil.toml, {', '.join(ARQUIVOS)}.\n"
            "copia.json lista cada arquivo com o SHA-256 conferido contra a origem. O conftest.py impede a coleta pelo "
            "pytest. Dados brutos, dados das etapas e documentos de referência não entram na cópia.\n",
            encoding="utf-8")
        _conferir(destino, registro)
    except Exception as exc:
        shutil.rmtree(destino, ignore_errors=True)  # a cópia incompleta sai; as outras não são tocadas
        logger.error("Falha ao criar a cópia %s: %s. Nenhuma cópia existente foi excluída.", destino.name, exc)
        return 1
    logger.info("Cópia %s criada e conferida: %d arquivos.", destino.name, len(registro))
    for antiga in copias_existentes(raiz)[:-MAXIMO_COPIAS]:
        if antiga != destino:
            shutil.rmtree(antiga)
            logger.info("Cópia mais antiga excluída: %s.", antiga.name)
    return 0
