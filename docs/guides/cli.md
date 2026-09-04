# Command-line interface

Installing the package provides an `industrialstats` command for generating
designs and running selected analyses without writing a script.

```bash
industrialstats --help
```

Every subcommand accepts `-o/--output` to write CSV instead of printing to
standard output.

## Factor specification

The `factorial`, `fractional` and `screening` subcommands take repeated
`-f/--factor` arguments in the form `NAME=level1,level2`. The `crd` and `rcbd`
subcommands instead take repeated `-t/--treatment` arguments, one per treatment
level, because they describe a single treatment factor:

```bash
industrialstats factorial -f "Temperature=180,220" -f "Pressure=10,20"
```

## Generating designs

### Full factorial

```bash
industrialstats factorial \
  -f "Temperature=180,220" \
  -f "Pressure=10,20" \
  --replicates 2 \
  --center-points 3 \
  -o design.csv
```

### Fractional factorial

Specify either a `--fraction` or explicit `--generator` strings:

```bash
industrialstats fractional -f "A=-1,1" -f "B=-1,1" -f "C=-1,1" --fraction 1/2
```

### Completely randomized design

```bash
industrialstats crd -t A -t B -t C --replicates 4 --seed 42
```

### Randomized complete block design

```bash
industrialstats rcbd \
  -t A -t B -t C \
  -b Day1 -b Day2 -b Day3 \
  --blocking-factor Day \
  --seed 42
```

### Screening

`--design pb` builds a Plackett-Burman design; `--design dsd` builds a
definitive screening design.

```bash
industrialstats screening -f "A=-1,1" -f "B=-1,1" -f "C=-1,1" --design pb --seed 42
```

!!! warning
    The `dsd` construction is experimental and scheduled for statistical
    correction. Prefer `pb` for production screening.

## Analysis

### ANOVA

```bash
industrialstats anova \
  --data results.csv \
  --response Yield \
  --formula "Yield ~ Temperature * Pressure" \
  --typ 2
```

`--typ` selects the sum-of-squares type (1, 2, or 3). Type II is the usual
choice for balanced designs without significant interactions; type III is used
when interactions are present.

### Power analysis

```bash
industrialstats power --analysis t-test --effect-size 0.5 --power 0.8
```

Supply exactly two of `--effect-size`, `--power`, and `--sample-size`; the
command solves for the third.

For a one-way ANOVA:

```bash
industrialstats power --analysis anova --effect-size 0.4 --power 0.8 --n-groups 4
```

### Stepwise model fitting

```bash
printf 'y,A,B\n1,0,0\n2,0,1\n3,1,0\n4,1,1\n' > model.csv
industrialstats model \
  --data model.csv \
  --response y \
  --entry-threshold 0.01 \
  --removal-threshold 0.2
```

!!! note "Stepwise selection inflates significance"
    p-values from a stepwise search are optimistic because the model was chosen
    using the same data. Treat the selected terms as a hypothesis to confirm,
    not as a validated model.

## Reproducibility

The `crd`, `rcbd` and `screening` subcommands accept `--seed`. Record it with
your results: it is what allows the exact run order to be reconstructed later.

!!! warning "factorial and fractional randomize without a seed"
    `FactorialDesign` randomizes by default, but the `factorial` and
    `fractional` subcommands expose no `--seed` flag, so their run order cannot
    currently be reproduced from the command line. Save the generated CSV with
    `-o`, or use the Python API, which accepts `seed`.

## Errors

File reads and writes raise structured
[DataExcept](https://github.com/DiogoRibeiro7/DataExcept) errors that name the
offending path, and the command exits with a non-zero status.
