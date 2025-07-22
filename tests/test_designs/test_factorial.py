"""Unit tests for factorial designs."""

import unittest
import numpy as np
import pandas as pd
import sys
import os

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from doe_python.designs.factorial import FactorialDesign
from doe_python.designs.base import Factor


class TestFactorialDesign(unittest.TestCase):
    """Test cases for FactorialDesign class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factors_2level = [
            Factor("A", [0, 1], "categorical"),
            Factor("B", [0, 1], "categorical"),
            Factor("C", [0, 1], "categorical")
        ]
        
        self.factors_3level = [
            Factor("Temp", [100, 150, 200], "continuous"),
            Factor("Pressure", [10, 20, 30], "continuous")
        ]
        
        self.factors_mixed = [
            Factor("Temperature", [180, 220], "continuous"),
            Factor("Material", ["A", "B"], "categorical"),
            Factor("Time", [30, 60], "continuous")
        ]
    
    def test_factorial_design_creation(self):
        """Test creation of factorial design."""
        design = FactorialDesign(self.factors_2level, replicates=1)
        self.assertEqual(design.name, "Full Factorial Design")
        self.assertEqual(len(design.factors), 3)
        self.assertEqual(design.replicates, 1)
        self.assertEqual(design.center_points, 0)
    
    def test_invalid_parameters(self):
        """Test invalid parameter handling."""
        with self.assertRaises(ValueError):
            FactorialDesign(self.factors_2level, replicates=0)
            
        with self.assertRaises(ValueError):
            FactorialDesign(self.factors_2level, center_points=-1)
    
    def test_design_generation_2_level(self):
        """Test generation of 2-level factorial design."""
        design = FactorialDesign(self.factors_2level, replicates=2)
        design_matrix = design.generate_design()
        
        # Check dimensions
        expected_runs = 2**3 * 2  # 2^3 combinations * 2 replicates
        self.assertEqual(len(design_matrix), expected_runs)
        
        # Check columns
        expected_columns = ['RunOrder', 'RunID', 'Replicate', 'DesignPoint', 'A', 'B', 'C']
        for col in expected_columns:
            self.assertIn(col, design_matrix.columns)
        
        # Check factor levels
        for factor in self.factors_2level:
            unique_levels = set(design_matrix[factor.name].unique())
            expected_levels = set(factor.levels)
            self.assertEqual(unique_levels, expected_levels)
        
        # Check replicates
        self.assertEqual(design_matrix['Replicate'].max(), 2)
        self.assertEqual(design_matrix['Replicate'].min(), 1)
    
    def test_design_generation_3_level(self):
        """Test generation of 3-level factorial design."""
        design = FactorialDesign(self.factors_3level, replicates=1)
        design_matrix = design.generate_design()
        
        # Check dimensions
        expected_runs = 3**2 * 1  # 3^2 combinations * 1 replicate
        self.assertEqual(len(design_matrix), expected_runs)
        
        # Check all combinations are present
        combinations = []
        for _, row in design_matrix.iterrows():
            combinations.append((row['Temp'], row['Pressure']))
        
        expected_combinations = [
            (100, 10), (100, 20), (100, 30),
            (150, 10), (150, 20), (150, 30),
            (200, 10), (200, 20), (200, 30)
        ]
        
        self.assertEqual(set(combinations), set(expected_combinations))
    
    def test_center_points(self):
        """Test addition of center points."""
        design = FactorialDesign(self.factors_mixed, replicates=1, center_points=3)
        design_matrix = design.generate_design()
        
        # Check total runs
        factorial_runs = 2**3 * 1
        center_runs = 3
        expected_total = factorial_runs + center_runs
        self.assertEqual(len(design_matrix), expected_total)
        
        # Check center points exist
        center_rows = design_matrix[design_matrix['DesignPoint'] == 'Center']
        self.assertEqual(len(center_rows), 3)
        
        # Check center point values
        expected_temp_center = (180 + 220) / 2
        expected_time_center = (30 + 60) / 2
        
        for _, row in center_rows.iterrows():
            self.assertEqual(row['Temperature'], expected_temp_center)
            self.assertEqual(row['Time'], expected_time_center)
            # Material should be middle category (index 1)
            self.assertIn(row['Material'], ['A', 'B'])
    
    def test_validation(self):
        """Test design validation."""
        # Valid design
        design = FactorialDesign(self.factors_2level, replicates=1)
        self.assertTrue(design.validate_design())
        
        # Invalid: single level factor
        invalid_factors = [Factor("A", [1], "categorical")]
        invalid_design = FactorialDesign(invalid_factors, replicates=1)
        self.assertFalse(invalid_design.validate_design())
        
        # Invalid: zero replicates
        zero_rep_design = FactorialDesign(self.factors_2level, replicates=0)
        self.assertFalse(zero_rep_design.validate_design())
    
    def test_n_runs_calculation(self):
        """Test calculation of number of runs."""
        design = FactorialDesign(self.factors_2level, replicates=3)
        expected_runs = 2**3 * 3  # 8 combinations * 3 replicates
        self.assertEqual(design.n_runs(), expected_runs)
        
        # Test with center points
        design_with_center = FactorialDesign(self.factors_2level, replicates=2, center_points=4)
        expected_runs_with_center = (2**3 * 2) + 4  # factorial + center points
        self.assertEqual(design_with_center.n_runs(), expected_runs_with_center)
        
        # Test 3-level design
        design_3level = FactorialDesign(self.factors_3level, replicates=2)
        expected_runs_3level = 3**2 * 2  # 9 combinations * 2 replicates
        self.assertEqual(design_3level.n_runs(), expected_runs_3level)
    
    def test_factorial_runs_calculation(self):
        """Test calculation of factorial runs only."""
        design = FactorialDesign(self.factors_2level, replicates=2, center_points=5)
        expected_factorial = 2**3 * 2  # 8 combinations * 2 replicates
        self.assertEqual(design.n_factorial_runs(), expected_factorial)
    
    def test_degrees_of_freedom(self):
        """Test degrees of freedom calculation."""
        design = FactorialDesign(self.factors_2level, replicates=2)
        dof = design.degrees_of_freedom()
        
        # Check main effects (2-level factors have 1 df each)
        for factor in self.factors_2level:
            self.assertEqual(dof[factor.name], 1)
        
        # Check two-factor interactions
        self.assertEqual(dof['A*B'], 1)  # 1*1 = 1
        self.assertEqual(dof['A*C'], 1)
        self.assertEqual(dof['B*C'], 1)
        
        # Check three-factor interaction
        self.assertEqual(dof['A*B*C'], 1)  # 1*1*1 = 1
        
        # Check error degrees of freedom
        total_runs = 2**3 * 2  # 16 total runs
        model_terms = 3 + 3 + 1 + 1  # 3 main + 3 two-way + 1 three-way + intercept
        expected_error_dof = total_runs - model_terms
        self.assertEqual(dof['Error'], expected_error_dof)
        
        # Check total degrees of freedom
        self.assertEqual(dof['Total'], total_runs - 1)
    
    def test_effect_calculation(self):
        """Test calculation of factorial effects."""
        design = FactorialDesign(self.factors_2level, replicates=1, randomize=False)
        design_matrix = design.generate_design()
        
        # Create mock response data with known effects
        # A has effect of +10, B has effect of +6, C has effect of +2
        # A*B interaction has effect of +4
        response_data = []
        for _, row in design_matrix.iterrows():
            response = 50  # baseline
            response += 5 if row['A'] == 1 else -5      # A effect = 10
            response += 3 if row['B'] == 1 else -3      # B effect = 6
            response += 1 if row['C'] == 1 else -1      # C effect = 2
            response += 2 if (row['A'] == 1 and row['B'] == 1) else -2  # AB interaction = 4
            response_data.append(response)
        
        effects = design.calculate_effects(response_data)
        
        # Check calculated effects
        self.assertAlmostEqual(effects['A'], 10, places=1)
        self.assertAlmostEqual(effects['B'], 6, places=1)
        self.assertAlmostEqual(effects['C'], 2, places=1)
        self.assertAlmostEqual(effects['A*B'], 4, places=1)
    
    def test_effect_calculation_validation(self):
        """Test effect calculation input validation."""
        design = FactorialDesign(self.factors_3level, replicates=1)  # 3-level design
        design_matrix = design.generate_design()
        
        # Should raise error for non-2-level design
        with self.assertRaises(ValueError):
            design.calculate_effects([1, 2, 3, 4, 5, 6, 7, 8, 9])
        
        # Test with 2-level design but wrong response length
        design_2level = FactorialDesign(self.factors_2level, replicates=1)
        design_2level.generate_design()
        
        with self.assertRaises(ValueError):
            design_2level.calculate_effects([1, 2, 3])  # Wrong length
    
    def test_coded_matrix_conversion(self):
        """Test conversion to coded matrix."""
        design = FactorialDesign(self.factors_2level, replicates=1, randomize=False)
        design_matrix = design.generate_design()
        coded_matrix = design._get_coded_matrix()
        
        # Check dimensions
        self.assertEqual(coded_matrix.shape[0], design_matrix.shape[0])
        self.assertEqual(coded_matrix.shape[1], len(self.factors_2level))
        
        # Check coding (-1, +1)
        for factor in self.factors_2level:
            unique_coded = set(coded_matrix[factor.name].unique())
            self.assertEqual(unique_coded, {-1, 1})
        
        # Check specific coding
        for i, row in design_matrix.iterrows():
            for factor in self.factors_2level:
                expected_code = -1 if row[factor.name] == factor.levels[0] else 1
                self.assertEqual(coded_matrix.loc[i, factor.name], expected_code)
    
    def test_two_level_design_check(self):
        """Test two-level design identification."""
        design_2level = FactorialDesign(self.factors_2level, replicates=1)
        self.assertTrue(design_2level._is_two_level_design())
        
        design_3level = FactorialDesign(self.factors_3level, replicates=1)
        self.assertFalse(design_3level._is_two_level_design())
        
        design_mixed = FactorialDesign(self.factors_mixed, replicates=1)
        self.assertTrue(design_mixed._is_two_level_design())  # All factors have 2 levels
    
    def test_randomization(self):
        """Test design randomization."""
        np.random.seed(42)  # For reproducible test
        
        design = FactorialDesign(self.factors_2level, replicates=1, randomize=False)
        design_matrix = design.generate_design()
        
        # Get original order (should not be randomized initially)
        original_order = design_matrix['RunID'].tolist()
        
        # Manually randomize
        design.randomize(seed=42)
        randomized_matrix = design.design_matrix
        
        # Check that RunOrder column was added
        self.assertIn('RunOrder', randomized_matrix.columns)
        
        # Check that all original runs are still present
        self.assertEqual(len(randomized_matrix), len(design_matrix))
        self.assertEqual(set(randomized_matrix['RunID']), set(original_order))
        
        # Check that randomization flag is set
        self.assertTrue(design.randomized)
        
        # Check that seed was stored
        self.assertEqual(design.seed, 42)
    
    def test_power_analysis(self):
        """Test power analysis calculation."""
        design = FactorialDesign(self.factors_2level, replicates=3)
        power_result = design.power_analysis(effect_size=1.0, alpha=0.05, power=0.8)
        
        # Check that all required keys are present
        required_keys = ['effect_size', 'alpha', 'target_power', 'calculated_power', 
                        'df_treatment', 'df_error', 'n_total', 'f_critical', 'lambda_nc']
        for key in required_keys:
            self.assertIn(key, power_result)
        
        # Check input values are preserved
        self.assertEqual(power_result['effect_size'], 1.0)
        self.assertEqual(power_result['alpha'], 0.05)
        self.assertEqual(power_result['target_power'], 0.8)
        
        # Check calculated power is reasonable
        self.assertGreater(power_result['calculated_power'], 0)
        self.assertLess(power_result['calculated_power'], 1)
        
        # Check degrees of freedom
        expected_df_treatment = 2**3 - 1  # 8-1 = 7
        expected_df_error = (2**3 * 3) - 2**3  # 24-8 = 16
        self.assertEqual(power_result['df_treatment'], expected_df_treatment)
        self.assertEqual(power_result['df_error'], expected_df_error)
        
        # Check total sample size
        expected_n_total = 2**3 * 3  # 24
        self.assertEqual(power_result['n_total'], expected_n_total)
    
    def test_power_analysis_no_factors(self):
        """Test power analysis with no factors."""
        design = FactorialDesign([], replicates=1)
        
        with self.assertRaises(ValueError):
            design.power_analysis(effect_size=1.0)
    
    def test_summary_method(self):
        """Test design summary method."""
        design = FactorialDesign(self.factors_2level, replicates=2, center_points=3)
        
        # Summary before generation
        summary_before = design.summary()
        self.assertEqual(summary_before['status'], 'Design not generated')
        
        # Generate design and get summary
        design.generate_design()
        summary = design.summary()
        
        # Check summary contents
        self.assertEqual(summary['design_name'], 'Full Factorial Design')
        self.assertEqual(summary['n_factors'], 3)
        self.assertEqual(summary['n_runs'], (2**3 * 2) + 3)  # factorial + center
        self.assertTrue(summary['randomized'])  # Should be randomized by default
        self.assertEqual(set(summary['factors']), {'A', 'B', 'C'})
        self.assertEqual(summary['design_matrix_shape'], (19, 8))  # 19 runs, 8 columns
        
        # Check factor levels
        self.assertEqual(summary['factor_levels']['A'], [0, 1])
        self.assertEqual(summary['factor_levels']['B'], [0, 1])
        self.assertEqual(summary['factor_levels']['C'], [0, 1])
    
    def test_string_representations(self):
        """Test string representations of design."""
        design = FactorialDesign(self.factors_2level, replicates=2)
        
        # Before generation
        str_before = str(design)
        self.assertIn('not generated', str_before)
        
        # After generation
        design.generate_design()
        str_after = str(design)
        self.assertIn('Full Factorial Design', str_after)
        self.assertIn('Factors: 3', str_after)
        self.assertIn('Runs: 16', str_after)
        self.assertIn('Randomized: True', str_after)
        
        # Test repr
        repr_str = repr(design)
        self.assertIn('ExperimentalDesign', repr_str)
        self.assertIn('factors=3', repr_str)
    
    def test_export_methods(self):
        """Test CSV and Excel export methods."""
        design = FactorialDesign(self.factors_2level, replicates=1)
        design.generate_design()
        
        # Test that methods exist and don't raise errors with valid design
        try:
            # These would normally write files, but we just test the method calls
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
                design.to_csv(f.name)
                self.assertTrue(os.path.exists(f.name))
                os.unlink(f.name)
                
        except Exception as e:
            self.fail(f"CSV export failed: {e}")
        
        # Test error when no design matrix
        empty_design = FactorialDesign(self.factors_2level, replicates=1)
        with self.assertRaises(ValueError):
            empty_design.to_csv('test.csv')


if __name__ == '__main__':
    unittest.main()
