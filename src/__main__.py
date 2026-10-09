"""Linha de comando única do fluxo: ``python -m src <comando> --usina <slug> [opções]``.

Comandos de etapa: ``coleta``, ``tratamento``, ``conferencia``, ``analises``, ``relatorio`` e ``completo``.
Ferramentas: ``copia-seguranca --motivo <texto>``; ``comparar --usina <slug> --referencia <pasta>`` ou
``comparar --todas [--coleta]``, que refaz e compara cada relatório de ``relatorios_referencia/``; e
``referencia --usina <slug> --data-geracao <data> --aprovado-em <data>``, que registra o relatório aprovado.
Códigos de saída: 0 sucesso; 1 erro; 2 dado não obtido ou opção inválida; 3 meta das vazões não atingida;
4 perfil inválido; 5 etapa anterior sem resultado concluído; 6 o ``comparar`` encontrou diferenças.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime
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


def ler_data_aprovacao(texto: str) -> date:
    """``--aprovado-em`` no formato "DD/MM/AAAA"."""
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"data de aprovação inválida: {texto!r} (use \"DD/MM/AAAA\")") from exc


class _Parser(argparse.ArgumentParser):
    """Confere, depois da leitura, as combinações de opções do ``comparar`` (código 2, como as demais opções)."""

    def parse_args(self, args=None, namespace=None):  # type: ignore[override]
        lidos = super().parse_args(args, namespace)
        if getattr(lidos, "comando", None) == "comparar":
            if lidos.todas and (lidos.usina or lidos.referencia):
                self.error("comparar: --todas não aceita --usina nem --referencia")
            if not lidos.todas and not (lidos.usina and lidos.referencia):
                self.error("comparar: use --usina com --referencia, ou --todas")
            if lidos.coleta and not lidos.todas:
                self.error("comparar: --coleta só vale com --todas")
        return lidos


def construir_parser() -> argparse.ArgumentParser:
    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument("--log-level", choices=NIVEIS_LOG, default="INFO",
                       help="nível de log de todos os módulos executados na chamada (padrão: INFO)")
    parser = _Parser(prog="python -m src", description=__doc__.splitlines()[0])
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
    comparar = sub.add_parser("comparar", parents=[comum],
                              help="compara o relatório da usina com o de outra pasta, ou refaz e compara todas as "
                                   "referências (--todas)")
    comparar.add_argument("--usina", help="slug da usina (nome da pasta em usinas/)")
    comparar.add_argument("--referencia", type=Path, help="pasta do relatório de referência")
    comparar.add_argument("--todas", action="store_true",
                          help="refaz, num espaço isolado, cada relatório de relatorios_referencia/ e compara")
    comparar.add_argument("--coleta", action="store_true",
                          help="com --todas, refaz também a Coleta (--sem-portal) e a compara com a congelada")
    referencia = com_usina("referencia", "registra o relatório aprovado em relatorios_referencia/<slug>/")
    referencia.add_argument("--data-geracao", type=ler_data_geracao, required=True,
                            help='data de geração do relatório aprovado ("DD/MM/AAAA HH:MM")')
    referencia.add_argument("--aprovado-em", type=ler_data_aprovacao, required=True,
                            help='data da aprovação pelo usuário ("DD/MM/AAAA")')
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = construir_parser().parse_args(argv)  # opção inválida: o argparse sai com código 2
    configurar_nivel_log(args.log_level)

    if args.comando == "copia-seguranca":
        from src.comum.copia_seguranca import criar_copia

        return criar_copia(args.motivo)
    if args.comando == "comparar" and args.todas:
        from src.comum.comparacao import executar_comparacao_todas

        return executar_comparacao_todas(coleta=args.coleta)

    try:
        perfil = carregar_perfil(args.usina)
    except PerfilInvalido as exc:
        print(str(exc), file=sys.stderr)
        return pipeline.CODIGO_PERFIL_INVALIDO

    if args.comando == "comparar":
        from src.comum.caminhos import pasta_relatorio
        from src.comum.comparacao import executar_comparacao

        return executar_comparacao(pasta_relatorio(perfil.usina.slug), args.referencia)
    if args.comando == "referencia":
        from src.comum.referencias import registrar_referencia

        return registrar_referencia(perfil.usina.slug, args.data_geracao, args.aprovado_em)
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
