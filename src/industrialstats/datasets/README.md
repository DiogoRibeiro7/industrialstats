# Datasets

Built-in datasets for examples and testing.

## Sample Manufacturing Data

The `load_manufacturing` function provides a small manufacturing dataset
with tensile-strength measurements across processing conditions. The data
follow a balanced factorial structure where factor effects are estimated
via the linear model

.. math:: y_{ijk} = \mu + \alpha_i + \beta_j + (\alpha\beta)_{ij} + \epsilon_{ijk}

### Example
```python
from industrialstats.datasets import load_manufacturing

df = load_manufacturing()
print(df.head())
```

## References

.. [1] Montgomery, D.C. (2017). *Design and Analysis of Experiments*, 9th ed.
