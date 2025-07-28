"""DOE Python package."""

from .datasets.sample_data import load_manufacturing
from .designs.factorial import FactorialDesign
from .designs.fractional_factorial import FractionalFactorialDesign
from .designs.rcbd import RandomizedCompleteBlockDesign
from .designs.screening import DefinitiveScreeningDesign, PlackettBurmanDesign
from .utils.data_generation import DataSimulator
from .utils.export import export_to_csv, export_to_excel, export_to_json
from .utils.transforms import center, log_transform, standardize
from .utils.validation import DesignValidator

__all__ = [
    "__version__",
    "PlackettBurmanDesign",
    "FactorialDesign",
    "RandomizedCompleteBlockDesign",
    "FractionalFactorialDesign",
    "DefinitiveScreeningDesign",
    "DataSimulator",
    "DesignValidator",
    "export_to_csv",
    "export_to_excel",
    "export_to_json",
    "center",
    "standardize",
    "log_transform",
    "load_manufacturing",
]

__version__ = "0.1.0"


def get_version() -> str:
    """Return the current package version."""
    return __version__
