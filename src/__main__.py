"""Linha de comando única do fluxo: ``python -m src <comando> --usina <slug> [opções]``.

Comandos de etapa: ``coleta``, ``tratamento``, ``conferencia``, ``analises``, ``relatorio`` e ``completo``.
Ferramentas: ``copia-seguranca --motivo <texto>`` e ``comparar --usina <slug> --referencia <pasta>``.
Códigos de saída: 0 sucesso; 1 erro; 2 dado não obtido ou opção inválida; 3 meta das vazões não atingida;
4 perfil inválido; 5 etapa anterior sem resultado concluído; 6 o ``comparar`` encontrou diferenças.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src import pipeline
from src.comum.logger import NIVEIS_LOG, configurar_nivel_log, setup_logger
from src.comum.perfil import PerfilInvalido, carregar_perfil

logger = setup_logger("pipeline")


def ler_data_geracao(texto: str) -> datetime:
    """``--data-geracao`` no formato "DD/MM/AAAA HH:MM"; formato inválido é recusado antes de qualquer execução."""
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y %H:%M")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"data de geração inválida: {texto!r} (use \"DD/MM/AAAA HH:MM\")") from exc


def construir_parser() -> argparse.ArgumentParser:
    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument("--log-level", choices=NIVEIS_LOG, default="INFO",
                       help="nível de log de todos os módulos executados na chamada (padrão: INFO)")
    parser = argparse.ArgumentParser(prog="python -m src", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="comando", required=True, metavar="comando")

    def com_usina(nome: str, ajuda: str) -> argparse.ArgumentParser:
        p = sub.add_parser(nome, parents=[comum], help=ajuda)
        p.add_argument("--usina", required=True, help="slug da usina (nome da pasta em usinas/)")
        return p

    def opcoes_coleta(p: argparse.ArgumentParser) -> None:
        p.add_argument("--sem-portal", action="store_true", help="não consulta o portal; extrai só dos arquivos locais")
        p.add_argument("--forcar-download", action="store_true", help="baixa de novo todos os arquivos de dados")

    def opcoes_relatorio(p: argparse.ArgumentParser) -> None:
        p.add_argument("--data-geracao", type=ler_data_geracao, default=None,
                       help='fixa a data de geração ("DD/MM/AAAA HH:MM") e torna o PDF reproduzível byte a byte')

    opcoes_coleta(com_usina("coleta", "Coleta de dados"))
    com_usina("tratamento", "Tratamento de dados")
    com_usina("conferencia", "Conferência")
    com_usina("analises", "Análises")
    opcoes_relatorio(com_usina("relatorio", "Geração do relatório"))
    completo = com_usina("completo", "as cinco etapas, na ordem")
    opcoes_coleta(completo)
    opcoes_relatorio(completo)
    copia = sub.add_parser("copia-seguranca", parents=[comum], help="cópia de segurança do projeto (no máximo duas)")
    copia.add_argument("--motivo", required=True, help="motivo da cópia, usado no nome da pasta")
    comparar = com_usina("comparar", "compara o relatório da usina com o de outra pasta")
    comparar.add_argument("--referencia", type=Path, required=True, help="pasta do relatório de referência")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = construir_parser().parse_args(argv)  # opção inválida: o argparse sai com código 2
    configurar_nivel_log(args.log_level)

    if args.comando == "copia-seguranca":
        from src.comum.copia_seguranca import criar_copia

        return criar_copia(args.motivo)

    try:
        perfil = carregar_perfil(args.usina)
    except PerfilInvalido as exc:
        print(str(exc), file=sys.stderr)
        return pipeline.CODIGO_PERFIL_INVALIDO

    if args.comando == "comparar":
        from src.comum.caminhos import pasta_relatorio
        from src.comum.comparacao import executar_comparacao

        return executar_comparacao(pasta_relatorio(perfil.usina.slug), args.referencia)
    if args.comando == "completo":
        return pipeline.executar_completo(perfil, sem_portal=args.sem_portal, forcar_download=args.forcar_download,
                                          data_geracao=args.data_geracao)
    opcoes = {}
    if args.comando == "coleta":
        opcoes = {"sem_portal": args.sem_portal, "forcar_download": args.forcar_download}
    elif args.comando == "relatorio":
        opcoes = {"data_geracao": args.data_geracao}
    return pipeline.executar_etapa(args.comando, perfil, **opcoes)


if __name__ == "__main__":
    sys.exit(main())
