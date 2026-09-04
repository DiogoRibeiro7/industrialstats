# industrialstats

**Industrial statistics and design of experiments for Python.**

`industrialstats` provides reproducible experimental-design generators,
statistical analysis, diagnostics, power calculations, optimization, and
visualization for manufacturing, engineering, and research experiments.

The project is pre-1.0. Its development priority is statistical correctness and
validation against established DOE references before the catalogue of design
families is widened.

## Install

```bash
python -m pip install industrialstats
```

Supported Python versions are 3.11 through 3.14.

## A first design

```python
from industrialstats.designs.base import Factor
from industrialstats.designs.factorial import FactorialDesign

factors = [
    Factor("temperature", [180, 220], factor_type="continuous"),
    Factor("pressure", [10, 20], factor_type="continuous"),
]

design = FactorialDesign(factors=factors, replicates=2, randomize=True, seed=42)
print(design.generate_design())
```

Continue with [Getting started](getting-started.md), or jump to
[choosing a design](guides/choosing-a-design.md).

## Project principles

- **Statistical correctness first.** Implementations are validated against
  textbook results, trusted reference software, or independently derived
  properties.
- **Reproducible experiments.** Randomization is seedable and design matrices
  stay inspectable.
- **Transparent methods.** Explicit statistical calculations and documented
  assumptions are preferred over opaque abstractions.
- **Clear design semantics.** Terms such as effect, block, alias, resolution,
  whole plot, and optimality criterion carry their precise DOE meanings.
- **No false completeness.** Partially implemented or statistically provisional
  methods are labelled as such.

## Maturity of each design family

| Design family | Status |
| --- | --- |
| Full factorial | Implemented |
| Fractional factorial | Implemented |
| Completely randomized design | Implemented |
| Randomized complete block design | Implemented |
| Plackett-Burman | Implemented, limited catalogue |
| Definitive screening | Experimental — construction scheduled for correction |
| Response surface methodology | Implemented |
| Optimal designs | Implemented |
| Split-plot | Basic — error-stratum analysis incomplete |
| Mixture | Basic |

See the [roadmap](roadmap.md) for the full sequence.
