"""Base class for all experimental designs."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass


@dataclass
class Factor:
    """Represents a factor in an experimental design."""
    name: str
    levels: List[Union[str, float, int]]
    factor_type: str = "categorical"  # "categorical" or "continuous"
    
    def __post_init__(self):
        if self.factor_type not in ["categorical", "continuous"]:
            raise ValueError("factor_type must be 'categorical' or 'continuous'")
        if len(self.levels) < 2:
            raise ValueError("Factor must have at least 2 levels")


class ExperimentalDesign(ABC):
    """Abstract base class for all experimental designs."""
    
    def __init__(self, name: str):
        self.name = name
        self.factors: List[Factor] = []
        self.design_matrix: Optional[pd.DataFrame] = None
        self.randomized: bool = False
        self.seed: Optional[int] = None
        
    @abstractmethod
    def generate_design(self) -> pd.DataFrame:
        """Generate the experimental design matrix."""
        pass
        
    @abstractmethod
    def validate_design(self) -> bool:
        """Validate the experimental design."""
        pass
        
    def add_factor(self, factor: Factor) -> None:
        """Add a factor to the design."""
        if not isinstance(factor, Factor):
            raise TypeError("factor must be a Factor instance")
        self.factors.append(factor)
        
    def randomize(self, seed: Optional[int] = None) -> None:
        """Randomize the run order of the experiment."""
        if self.design_matrix is None:
            raise ValueError("Design matrix not generated yet. Call generate_design() first.")
            
        if seed is not None:
            np.random.seed(seed)
            self.seed = seed
            
        # Shuffle the design matrix
        self.design_matrix = self.design_matrix.sample(frac=1).reset_index(drop=True)
        
        # Add run order column
        self.design_matrix.insert(0, 'RunOrder', range(1, len(self.design_matrix) + 1))
        self.randomized = True
        
    def to_csv(self, filename: str) -> None:
        """Export design to CSV file."""
        if self.design_matrix is None:
            raise ValueError("No design matrix to export.")
        self.design_matrix.to_csv(filename, index=False)
        
    def to_excel(self, filename: str) -> None:
        """Export design to Excel file."""
        if self.design_matrix is None:
            raise ValueError("No design matrix to export.")
        self.design_matrix.to_excel(filename, index=False)
        
    def summary(self) -> Dict[str, Any]:
        """Return summary information about the design."""
        if self.design_matrix is None:
            return {"status": "Design not generated"}
            
        return {
            "design_name": self.name,
            "n_factors": len(self.factors),
            "n_runs": len(self.design_matrix),
            "randomized": self.randomized,
            "factors": [f.name for f in self.factors],
            "factor_levels": {f.name: f.levels for f in self.factors},
            "design_matrix_shape": self.design_matrix.shape,
        }
        
    def __str__(self) -> str:
        """String representation of the design."""
        summary = self.summary()
        if summary["status"] == "Design not generated":
            return f"{self.name} (not generated)"
        
        return (f"{self.name}\n"
                f"Factors: {summary['n_factors']}\n"
                f"Runs: {summary['n_runs']}\n"
                f"Randomized: {summary['randomized']}")
        
    def __repr__(self) -> str:
        """Detailed representation of the design."""
        return f"ExperimentalDesign(name='{self.name}', factors={len(self.factors)})"
