# Choosing a design

The right design depends on what stage of experimentation you are in, how many
factors you have, and how many runs you can afford.

## By experimental goal

| Goal | Typical situation | Design family |
| --- | --- | --- |
| Screen many factors | 6+ factors, few runs, want the vital few | Plackett-Burman, fractional factorial |
| Estimate main effects and interactions | 2–5 factors, moderate budget | Full factorial |
| Compare treatments | One factor, homogeneous units | Completely randomized design |
| Compare treatments with a nuisance source | Batches, days, operators | Randomized complete block design |
| Find an optimum | Few factors, curvature expected | Response surface (CCD, Box-Behnken) |
| Work under constraints | Irregular region, fixed run count | Optimal design (D, A, G, I) |
| Hard-to-change factors | Temperature changes are expensive | Split-plot |
| Formulation work | Components sum to a total | Mixture |

## Screening

With many factors and a small budget, start by finding which factors matter.

```python
from industrialstats.designs.base import Factor
from industrialstats.designs.screening import PlackettBurmanDesign

factors = [Factor(f"X{i}", [-1, 1], "continuous") for i in range(1, 8)]
design = PlackettBurmanDesign(factors, seed=42)
print(design.generate_design())
```

Plackett-Burman designs estimate main effects in very few runs, but their
interaction aliasing is complex. Treat the result as a shortlist, not as a
final model.

!!! warning "Definitive screening designs are experimental"
    `DefinitiveScreeningDesign` exposes a public API, but its construction is
    scheduled for statistical correction. Do not rely on it for production
    experiments until that work lands. See the [roadmap](../roadmap.md).

## Factorials and resolution

A regular fractional factorial trades run count for aliasing. Its **resolution**
summarises the cost:

| Resolution | Meaning |
| --- | --- |
| III | Main effects aliased with two-factor interactions |
| IV | Main effects clear of two-factor interactions; those interactions aliased with each other |
| V | Main effects and two-factor interactions clear of each other |

Prefer resolution V when you intend to interpret interactions, and resolution
IV when you mainly need clean main effects.

```python
from industrialstats.designs.base import Factor
from industrialstats.designs.fractional_factorial import FractionalFactorialDesign

factors = [Factor(name, [-1, 1], "continuous") for name in "ABCDE"]

design = FractionalFactorialDesign(factors, fraction="1/4", randomize=False)
design.generate_design()
print(design.resolution_analysis())
```

If a screening run leaves ambiguity, `foldover` augments the design to break
the aliases that matter.

## Response surface designs

Once the important factors are known and you expect curvature, move to a
response surface design.

- **Central composite (CCD)** augments a factorial with axial and centre
  points. It estimates a full quadratic model and can be built from an existing
  factorial you have already run.
- **Box-Behnken** needs no extreme corner points, which helps when running all
  factors at their high settings simultaneously is impractical or unsafe.

```python
from industrialstats.designs.base import Factor
from industrialstats.designs.response_surface import ResponseSurfaceDesign

factors = [
    Factor("temperature", [180, 220], factor_type="continuous"),
    Factor("pressure", [10, 20], factor_type="continuous"),
]

design = ResponseSurfaceDesign(factors, design_type="CCD", center_points=4)
```

Centre points matter: they give a pure-error estimate and a lack-of-fit test.
Include several.

## Blocking

When a nuisance source such as batch, day, or operator varies during the
experiment, block on it rather than hoping randomization absorbs it.

```python
from industrialstats.designs.rcbd import RandomizedCompleteBlockDesign

design = RandomizedCompleteBlockDesign(
    treatments=["A", "B", "C"],
    blocks=["Day1", "Day2", "Day3"],
    blocking_factor="Day",
    seed=42,
)
```

## Optimal designs

When the design region is constrained, the run budget is fixed, or the model is
non-standard, a coordinate-exchange search over a candidate set is more
appropriate than a catalogue design. Criteria available are D (parameter
precision), A (average variance), G (worst-case prediction variance), and I
(average prediction variance).

Choose I or G when prediction across the region is the goal, and D when
estimating coefficients precisely is the goal.

## Randomization and reproducibility

Every generator accepts a `seed`. Record it alongside the experiment: it is
what lets you reconstruct the exact run order later.

Where randomization must be restricted — as in split-plot designs, where whole
plots are hard to change — use the design family that encodes that restriction
rather than reordering a fully randomized design by hand. The analysis has to
match the randomization structure to give correct standard errors.
