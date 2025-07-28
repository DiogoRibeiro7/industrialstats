"""Command line interface for DOE Python."""

from __future__ import annotations

import argparse
from typing import List

from .designs.base import Factor
from .designs.factorial import FactorialDesign


def parse_factors(factors: List[str]) -> List[Factor]:
    """Parse factor specifications.

    Args:
        factors: Strings formatted as ``NAME=level1,level2``.

    Returns:
        List of parsed ``Factor`` objects.

    Raises:
        argparse.ArgumentTypeError: If a factor specification is invalid.
    """
    parsed = []
    for fstr in factors:
        if "=" not in fstr:
            raise argparse.ArgumentTypeError(
                f"Factor specification '{fstr}' is invalid. Use NAME=level1,level2"
            )
        name, levels_str = fstr.split("=", 1)
        levels = [try_parse(x) for x in levels_str.split(",")]
        parsed.append(Factor(name, levels))
    return parsed


def try_parse(value: str):
    """Parse a value into ``int`` or ``float`` when possible.

    Args:
        value: String representation of the value.

    Returns:
        Parsed number or original string if conversion fails.
    """
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


def factorial_command(args: argparse.Namespace) -> None:
    """Execute the ``factorial`` CLI command.

    Args:
        args: Parsed command-line arguments.
    """
    factors = parse_factors(args.factor)
    design = FactorialDesign(
        factors,
        replicates=args.replicates,
        center_points=args.center_points,
    )
    design_matrix = design.generate_design()
    if args.output:
        design_matrix.to_csv(args.output, index=False)
    else:
        print(design_matrix.to_string(index=False))


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI argument parser."""
    parser = argparse.ArgumentParser(description="DOE Python command line interface")
    subparsers = parser.add_subparsers(dest="command", required=True)

    factorial_parser = subparsers.add_parser(
        "factorial", help="Generate a full factorial design"
    )
    factorial_parser.add_argument(
        "-f",
        "--factor",
        action="append",
        required=True,
        help="Factor specification NAME=level1,level2",
    )
    factorial_parser.add_argument(
        "-r", "--replicates", type=int, default=1, help="Number of replicates"
    )
    factorial_parser.add_argument(
        "-c", "--center-points", type=int, default=0, help="Number of center points"
    )
    factorial_parser.add_argument("-o", "--output", help="CSV file to save the design")
    factorial_parser.set_defaults(func=factorial_command)

    return parser


def main(argv: List[str] | None = None) -> None:
    """Entry point for the command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
