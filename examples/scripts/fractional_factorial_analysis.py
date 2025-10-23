"""Example analysis of a fractional factorial design.

This script demonstrates how to generate a two-level fractional factorial
 design, compute the alias structure, and evaluate resolution metrics using the
 :class:`industrialstats.designs.fractional_factorial.FractionalFactorialDesign`
 class.  The results mirror the ``FrF2`` R package output for the
 ``2^(7-3)`` minimum aberration design discussed in Montgomery (2017).
"""

from __future__ import annotations

from pprint import pprint

from industrialstats.designs.base import Factor
from industrialstats.designs.fractional_factorial import FractionalFactorialDesign


def main() -> None:
    """Generate a 2^(7-3) design and display key diagnostics."""

    factors = [Factor(chr(ord("A") + i), [-1, 1]) for i in range(7)]
    design = FractionalFactorialDesign(factors, fraction="1/8", randomize=False)

    print("Generators (minimum aberration):")
    print(design.generators)
    print()

    resolution = design.resolution_analysis()
    print("Resolution analysis:")
    pprint(resolution)
    print()

    alias = design.alias_structure()
    print("Alias chain for main effect A:")
    pprint(alias["A"])
    print()

    print("Recommended foldover strategies:")
    for option in design.foldover_options():
        pprint(option)
        print()


if __name__ == "__main__":
    main()
