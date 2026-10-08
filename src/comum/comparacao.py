"""Comparação do relatório com uma versão de referência (spec da Geração do relatório, ferramenta ``comparar``).

PDF, Markdown, CSV e figuras são comparados byte a byte; a planilha, célula a célula, aba a aba e na mesma ordem de
abas, porque os bytes do XLSX mudam a cada gravação sem mudar o conteúdo. Células numéricas são iguais quando
coincidem até a 12ª casa relativa: a diferença abaixo disso é resto de ponto flutuante (por exemplo, um número lido
de um CSV pelo leitor padrão do pandas), não muda nenhum texto nem nenhuma figura. O ``etapa.json`` fica fora da
comparação. A comparação não grava nada.

Execução: ``python -m src comparar --usina <slug> --referencia <pasta>``, com código 0 sem diferença, 6 com diferença
e 1 em erro.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Dict, List

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

IGNORADOS = {"etapa.json"}
CODIGO_SEM_DIFERENCA = 0
CODIGO_ERRO = 1
CODIGO_DIFERENCAS = 6
MAXIMO_CELULAS_POR_ABA = 20  # células listadas por aba; o total aparece numa linha à parte
TOLERANCIA_RELATIVA_CELULA = 1e-12  # células numéricas: diferença abaixo disso é resto de ponto flutuante


def _arquivos(pasta: Path) -> Dict[str, Path]:
    return {p.relative_to(pasta).as_posix(): p for p in sorted(pasta.rglob("*"))
            if p.is_file() and p.name not in IGNORADOS}


def _iguais(a: object, b: object) -> bool:
    if isinstance(a, float) and isinstance(b, float) and a != a and b != b:  # NaN nas duas
        return True
    numeros = (int, float)
    if isinstance(a, numeros) and isinstance(b, numeros) and not isinstance(a, bool) and not isinstance(b, bool):
        return math.isclose(a, b, rel_tol=TOLERANCIA_RELATIVA_CELULA, abs_tol=0.0)
    return a == b


def _comparar_planilhas(atual: Path, referencia: Path, nome: str) -> List[str]:
    """Diferenças entre duas planilhas: ordem das abas, quantidade de linhas e cada célula."""
    wa = load_workbook(atual, read_only=True, data_only=True)
    wr = load_workbook(referencia, read_only=True, data_only=True)
    try:
        if wa.sheetnames != wr.sheetnames:
            so_atual = [a for a in wa.sheetnames if a not in wr.sheetnames]
            so_ref = [a for a in wr.sheetnames if a not in wa.sheetnames]
            return [f"{nome}: abas diferentes ou em outra ordem (só na atual: {so_atual}; só na referência: {so_ref})"]
        diferencas: List[str] = []
        for aba in wa.sheetnames:
            linhas_a = list(wa[aba].iter_rows(values_only=True))
            linhas_r = list(wr[aba].iter_rows(values_only=True))
            if len(linhas_a) != len(linhas_r):
                diferencas.append(f"{nome} [{aba}]: {len(linhas_a)} linhas na atual e {len(linhas_r)} na referência")
            celulas: List[str] = []
            for i, (la, lr) in enumerate(zip(linhas_a, linhas_r), start=1):
                n = max(len(la), len(lr))
                la = tuple(la) + (None,) * (n - len(la))
                lr = tuple(lr) + (None,) * (n - len(lr))
                for j, (va, vr) in enumerate(zip(la, lr), start=1):
                    if not _iguais(va, vr):
                        celulas.append(f"{nome} [{aba}] {get_column_letter(j)}{i}: {va!r} na atual, {vr!r} na referência")
            diferencas += celulas[:MAXIMO_CELULAS_POR_ABA]
            if len(celulas) > MAXIMO_CELULAS_POR_ABA:
                diferencas.append(f"{nome} [{aba}]: mais {len(celulas) - MAXIMO_CELULAS_POR_ABA} células diferentes "
                                  f"({len(celulas)} no total)")
        return diferencas
    finally:
        wa.close()
        wr.close()


def comparar(pasta_atual: Path, pasta_referencia: Path) -> List[str]:
    """Lista as diferenças entre o relatório de ``pasta_atual`` e o de ``pasta_referencia`` (vazia se não houver)."""
    for pasta in (pasta_atual, pasta_referencia):
        if not Path(pasta).is_dir():
            raise FileNotFoundError(f"pasta inexistente: {pasta}")
    atual, referencia = _arquivos(Path(pasta_atual)), _arquivos(Path(pasta_referencia))
    diferencas: List[str] = []
    for nome in sorted(set(atual) | set(referencia)):
        if nome not in atual:
            diferencas.append(f"{nome}: só na referência")
        elif nome not in referencia:
            diferencas.append(f"{nome}: só na pasta atual")
        elif nome.lower().endswith(".xlsx"):
            diferencas += _comparar_planilhas(atual[nome], referencia[nome], nome)
        elif atual[nome].read_bytes() != referencia[nome].read_bytes():
            diferencas.append(f"{nome}: conteúdo diferente ({atual[nome].stat().st_size} bytes na atual, "
                              f"{referencia[nome].stat().st_size} na referência)")
    return diferencas


def executar_comparacao(pasta_atual: Path, pasta_referencia: Path) -> int:
    """Compara, lista as diferenças na saída padrão e devolve o código (0, 6 ou 1)."""
    try:
        diferencas = comparar(Path(pasta_atual), Path(pasta_referencia))
    except Exception as exc:  # inclui planilha ilegível ou corrompida
        print(f"Erro na comparação: {exc}", file=sys.stderr)
        return CODIGO_ERRO
    for d in diferencas:
        print(d)
    print(f"{len(diferencas)} diferença(s)." if diferencas else "Nenhuma diferença.")
    return CODIGO_DIFERENCAS if diferencas else CODIGO_SEM_DIFERENCA
