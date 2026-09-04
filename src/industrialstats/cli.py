"""Command line interface for industrialstats."""

from __future__ import annotations

import argparse
from typing import List

import pandas as pd

from .analysis.anova import ANOVAAnalysis
from .analysis.model_fitting import ModelFitting
from .analysis.power_analysis import PowerAnalysis
from .designs.base import Factor
from .designs.crd import CompletelyRandomizedDesign
from .designs.factorial import FactorialDesign
from .designs.fractional_factorial import FractionalFactorialDesign
from .designs.rcbd import RandomizedCompleteBlockDesign
from .designs.screening import DefinitiveScreeningDesign, PlackettBurmanDesign
from .utils.export import export_to_csv
from .utils.io import load_csv


def parse_factors(factors: List[str]) -> List[Factor]:
    """Parse factor specifications.

    Parameters
    ----------
    factors : list of str
        Strings formatted as ``NAME=level1,level2``.

    Returns
    -------
    list of Factor
        Parsed factor objects.

    Raises
    ------
    argparse.ArgumentTypeError
        If a factor specification is invalid.
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

    Parameters
    ----------
    value : str
        String representation of the value.

    Returns
    -------
    int, float or str
        Parsed number or original string if conversion fails.
    """
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


def factorial_command(args: argparse.Namespace) -> None:
    """Execute the ``factorial`` CLI command.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.
    """
    factors = parse_factors(args.factor)
    design = FactorialDesign(
        factors,
        replicates=args.replicates,
        center_points=args.center_points,
    )
    design_matrix = design.generate_design()
    if args.output:
        export_to_csv(design_matrix, args.output)
    else:
        print(design_matrix.to_string(index=False))


def rcbd_command(args: argparse.Namespace) -> None:
    """Execute the ``rcbd`` CLI command.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.
    """
    design = RandomizedCompleteBlockDesign(
        treatments=args.treatment,
        blocks=args.block,
        blocking_factor=args.blocking_factor,
        seed=args.seed,
    )
    design_matrix = design.generate_design()
    if args.output:
        export_to_csv(design_matrix, args.output)
    else:
        print(design_matrix.to_string(index=False))


def crd_command(args: argparse.Namespace) -> None:
    """Execute the ``crd`` CLI command."""
    design = CompletelyRandomizedDesign(
        treatments=args.treatment, replicates=args.replicates, seed=args.seed
    )
    design_matrix = design.generate_design()
    if args.output:
        export_to_csv(design_matrix, args.output)
    else:
        print(design_matrix.to_string(index=False))


def screening_command(args: argparse.Namespace) -> None:
    """Execute the ``screening`` CLI command."""
    factors = parse_factors(args.factor)
    if args.design == "pb":
        design = PlackettBurmanDesign(factors, seed=args.seed)
    else:
        design = DefinitiveScreeningDesign(factors, seed=args.seed)
    design_matrix = design.generate_design()
    if args.output:
        export_to_csv(design_matrix, args.output)
    else:
        print(design_matrix.to_string(index=False))


def anova_command(args: argparse.Namespace) -> None:
    """Execute the ``anova`` CLI command."""
    data = load_csv(args.data)
    analysis = ANOVAAnalysis(data, response_column=args.response)
    analysis.fit_model(args.formula)
    table = analysis.anova_table_calculation(typ=args.typ)
    if args.output:
        export_to_csv(table.reset_index(), args.output)
    else:
        print(table.to_string())


def power_command(args: argparse.Namespace) -> None:
    """Execute the ``power`` CLI command.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.
    """
    analysis = PowerAnalysis()
    if args.analysis == "t-test":
        result = analysis.t_test_power(
            effect_size=args.effect_size,
            alpha=args.alpha,
            power=args.power,
            sample_size=args.sample_size,
            test_type=args.test_type,
        )
    else:
        result = analysis.anova_power(
            effect_size=args.effect_size,
            alpha=args.alpha,
            power=args.power,
            sample_size=args.sample_size,
            n_groups=args.n_groups,
        )
    df = pd.DataFrame([result.__dict__])
    if args.output:
        export_to_csv(df, args.output)
    else:
        print(df.to_string(index=False))


def model_command(args: argparse.Namespace) -> None:
    """Execute the ``model`` CLI command.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.
    """
    data = load_csv(args.data)
    fitter = ModelFitting(data, response_column=args.response)
    result = fitter.stepwise_selection(
        entry_threshold=args.entry_threshold,
        removal_threshold=args.removal_threshold,
    )
    df = pd.DataFrame({"selected_terms": result["selected_terms"]})
    if args.output:
        export_to_csv(df, args.output)
    else:
        print(df.to_string(index=False))


def fractional_command(args: argparse.Namespace) -> None:
    """Execute the ``fractional`` CLI command.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.
    """
    factors = parse_factors(args.factor)
    design = FractionalFactorialDesign(
        factors,
        fraction=args.fraction,
        generators=args.generator,
        replicates=args.replicates,
    )
    design_matrix = design.generate_design()
    if args.output:
        export_to_csv(design_matrix, args.output)
    else:
        print(design_matrix.to_string(index=False))


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="industrialstats command line interface"
    )
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

    rcbd_parser = subparsers.add_parser(
        "rcbd", help="Generate a randomized complete block design"
    )
    rcbd_parser.add_argument(
        "-t",
        "--treatment",
        action="append",
        required=True,
        help="Treatment levels",
    )
    rcbd_parser.add_argument(
        "-b",
        "--block",
        action="append",
        required=True,
        help="Block levels",
    )
    rcbd_parser.add_argument(
        "--blocking-factor",
        default="Block",
        help="Name of the blocking factor column",
    )
    rcbd_parser.add_argument("--seed", type=int, help="Random seed")
    rcbd_parser.add_argument("-o", "--output", help="CSV file to save the design")
    rcbd_parser.set_defaults(func=rcbd_command)

    fractional_parser = subparsers.add_parser(
        "fractional", help="Generate a fractional factorial design"
    )
    fractional_parser.add_argument(
        "-f",
        "--factor",
        action="append",
        required=True,
        help="Factor specification NAME=level1,level2",
    )
    fractional_parser.add_argument(
        "--fraction",
        default="1/2",
        help="Fraction of the full design, e.g. 1/2",
    )
    fractional_parser.add_argument(
        "-g",
        "--generator",
        action="append",
        help="Generator strings",
    )
    fractional_parser.add_argument(
        "-r", "--replicates", type=int, default=1, help="Number of replicates"
    )
    fractional_parser.add_argument("-o", "--output", help="CSV file to save the design")
    fractional_parser.set_defaults(func=fractional_command)

    crd_parser = subparsers.add_parser(
        "crd", help="Generate a completely randomized design"
    )
    crd_parser.add_argument(
        "-t",
        "--treatment",
        action="append",
        required=True,
        help="Treatment levels",
    )
    crd_parser.add_argument(
        "-r",
        "--replicates",
        type=int,
        default=1,
        help="Replicates per treatment",
    )
    crd_parser.add_argument("--seed", type=int, help="Random seed")
    crd_parser.add_argument("-o", "--output", help="CSV file to save the design")
    crd_parser.set_defaults(func=crd_command)

    screening_parser = subparsers.add_parser(
        "screening", help="Generate a screening design"
    )
    screening_parser.add_argument(
        "-f",
        "--factor",
        action="append",
        required=True,
        help="Factor specification NAME=level1,level2",
    )
    screening_parser.add_argument(
        "--design",
        choices=["pb", "dsd"],
        default="pb",
        help="Screening design type: pb (Plackett-Burman) or dsd (definitive)",
    )
    screening_parser.add_argument("--seed", type=int, help="Random seed")
    screening_parser.add_argument("-o", "--output", help="CSV file to save the design")
    screening_parser.set_defaults(func=screening_command)

    anova_parser = subparsers.add_parser("anova", help="Run a simple ANOVA")
    anova_parser.add_argument("--data", required=True, help="CSV file with data")
    anova_parser.add_argument(
        "--response", required=True, help="Name of the response column"
    )
    anova_parser.add_argument(
        "--formula",
        required=True,
        help='Model formula e.g. "y ~ A * B"',
    )
    anova_parser.add_argument("--typ", type=int, default=2, help="ANOVA type")
    anova_parser.add_argument("-o", "--output", help="CSV file to save the table")
    anova_parser.set_defaults(func=anova_command)

    power_parser = subparsers.add_parser("power", help="Perform power analysis")
    power_parser.add_argument(
        "--analysis", choices=["t-test", "anova"], default="t-test"
    )
    power_parser.add_argument("--effect-size", type=float)
    power_parser.add_argument("--alpha", type=float, default=0.05)
    power_parser.add_argument("--power", type=float)
    power_parser.add_argument("--sample-size", type=int)
    power_parser.add_argument(
        "--test-type",
        choices=["one_sample", "two_sample", "paired"],
        default="two_sample",
    )
    power_parser.add_argument("--n-groups", type=int, default=3)
    power_parser.add_argument("-o", "--output", help="CSV file to save results")
    power_parser.set_defaults(func=power_command)

    model_parser = subparsers.add_parser("model", help="Run stepwise model fitting")
    model_parser.add_argument("--data", required=True, help="CSV file with data")
    model_parser.add_argument(
        "--response", required=True, help="Name of the response column"
    )
    model_parser.add_argument(
        "--entry-threshold", type=float, default=0.05, help="Entry p-value"
    )
    model_parser.add_argument(
        "--removal-threshold",
        type=float,
        default=0.10,
        help="Removal p-value",
    )
    model_parser.add_argument("-o", "--output", help="CSV file to save selected terms")
    model_parser.set_defaults(func=model_command)

    return parser


def main(argv: List[str] | None = None) -> None:
    """Entry point for the command-line interface.

    Parameters
    ----------
    argv : list of str, optional
        Command-line arguments.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
