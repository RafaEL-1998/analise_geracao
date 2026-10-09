"""Gera ``tests/fixtures/invariantes_uhe.json``, a fotografia dos invariantes do relatório da hidrelétrica com EVT.

Tarefa T010 da spec 006 (decisão R29): roda a usina fictícia com o código aprovado, ANTES de qualquer mudança da
ampliação, e grava o que os testes de ``tests/relatorio/test_invariantes_uhe.py`` passam a exigir. Só deve ser
executado de novo com a aprovação do usuário, porque refazer a fotografia aceita qualquer mudança no relatório.

Execução: ``python -m tests.fixtures.gerar_invariantes_uhe`` na raiz do projeto, sem rede.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tests.fixtures.execucao_ficticia import ARQUIVO_INVARIANTES, executar_usina_ficticia, extrair_invariantes


def gerar(destino: Path = ARQUIVO_INVARIANTES) -> None:
    with tempfile.TemporaryDirectory() as pasta:
        execucao = executar_usina_ficticia(Path(pasta))
        if execucao["codigo"] != 0:
            raise SystemExit(f"o fluxo da usina fictícia terminou com o código {execucao['codigo']}")
        invariantes = extrair_invariantes(execucao)
    destino.write_text(json.dumps(invariantes, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Fotografia gravada em {destino}: {len(invariantes['secoes'])} seções, "
          f"{len(invariantes['planilha_abas'])} abas, {len(invariantes['coleta'])} arquivos da Coleta.")


if __name__ == "__main__":
    gerar()
