"""industrialstats package."""

from .config import config, load_config
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
    "DataSimulator",
    "DefinitiveScreeningDesign",
    "DesignValidator",
    "FactorialDesign",
    "FractionalFactorialDesign",
    "PlackettBurmanDesign",
    "RandomizedCompleteBlockDesign",
    "__version__",
    "center",
    "config",
    "export_to_csv",
    "export_to_excel",
    "export_to_json",
    "load_config",
    "load_manufacturing",
    "log_transform",
    "standardize",
]

__version__ = "0.2.0"


def get_version() -> str:
    """Return the current package version."""
    return __version__
