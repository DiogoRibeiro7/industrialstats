"""Advanced model fitting and selection for experimental data."""

import logging
import warnings
from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class ModelFitting:
    """
    Advanced model fitting with automatic term selection and validation.
    """

    def __init__(self, data: pd.DataFrame, response_column: str):
        """Initialize model fitting.

        Parameters
        ----------
        data : pandas.DataFrame
            Experimental data.
        response_column : str
            Name of the response variable.
        """
        if response_column not in data.columns:
            raise ValueError(f"Response column '{response_column}' not found")

        self.data = data.copy()
        self.response = response_column
        self.factor_columns = [
            col
            for col in data.columns
            if col
            not in [response_column, "RunID", "RunOrder", "Replicate", "DesignPoint"]
        ]

        # Remove missing values
        self.data = self.data.dropna(subset=[response_column])

        if len(self.data) == 0:
            raise ValueError("No valid data after removing missing values")

        self.fitted_models: Dict[str, Any] = {}
        self.model_comparison: Optional[pd.DataFrame] = None

    def stepwise_selection(
        self,
        entry_threshold: float = 0.05,
        removal_threshold: float = 0.10,
        max_terms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Perform stepwise model selection.

        Parameters
        ----------
        entry_threshold : float, optional
            P-value threshold for entering terms, by default ``0.05``.
        removal_threshold : float, optional
            P-value threshold for removing terms, by default ``0.10``.
        max_terms : int, optional
            Maximum number of terms in the model.

        Returns
        -------
        dict
            Stepwise selection results.
        """
        # Generate candidate terms
        candidate_terms = self._generate_candidate_terms()

        if max_terms is None:
            max_terms = min(len(candidate_terms), len(self.data) // 3)

        # Start with intercept-only model
        current_terms = ["Intercept"]
        selection_history = []

        while True:
            improved = False

            # Forward step: try adding terms
            best_addition = None
            best_p_value = float("inf")

            for term in candidate_terms:
                if term not in current_terms and len(current_terms) < max_terms:
                    trial_terms = current_terms + [term]
                    try:
                        model_result = self._fit_terms(trial_terms)

                        # Get p-value for the new term
                        if term in model_result["p_values"]:
                            p_value = model_result["p_values"][term]
                            if p_value < entry_threshold and p_value < best_p_value:
                                best_addition = term
                                best_p_value = p_value
                    except Exception as e:
                        logger.debug("Failed to fit trial terms %s: %s", trial_terms, e)
                        continue

            # Add best term if found
            if best_addition is not None:
                current_terms.append(best_addition)
                selection_history.append(
                    {
                        "action": "add",
                        "term": best_addition,
                        "p_value": best_p_value,
                        "current_terms": current_terms.copy(),
                    }
                )
                improved = True

            # Backward step: try removing terms
            worst_removal = None
            worst_p_value = 0

            for term in current_terms[1:]:  # Skip intercept
                trial_terms = [t for t in current_terms if t != term]
                try:
                    model_result = self._fit_terms(current_terms)

                    if term in model_result["p_values"]:
                        p_value = model_result["p_values"][term]
                        if p_value > removal_threshold and p_value > worst_p_value:
                            worst_removal = term
                            worst_p_value = p_value
                except Exception as e:
                    logger.debug("Failed to evaluate term %s: %s", term, e)
                    continue

            # Remove worst term if found
            if worst_removal is not None:
                current_terms.remove(worst_removal)
                selection_history.append(
                    {
                        "action": "remove",
                        "term": worst_removal,
                        "p_value": worst_p_value,
                        "current_terms": current_terms.copy(),
                    }
                )
                improved = True

            # Stop if no improvement
            if not improved:
                break

        # Fit final model
        final_model = self._fit_terms(current_terms)

        return {
            "selected_terms": current_terms,
            "selection_history": selection_history,
            "final_model": final_model,
            "entry_threshold": entry_threshold,
            "removal_threshold": removal_threshold,
        }

    def hierarchical_fitting(
        self, max_order: int = 3, significance_level: float = 0.05
    ) -> Dict[str, Any]:
        """Fit hierarchical models respecting effect hierarchy.

        Parameters
        ----------
        max_order : int, optional
            Maximum interaction order, by default 3.
        significance_level : float, optional
            Significance level for term inclusion, by default 0.05.

        Returns
        -------
        dict
            Hierarchical fitting results.
        """
        # Generate terms by hierarchy level
        terms_by_order = self._generate_hierarchical_terms(max_order)

        selected_terms = ["Intercept"]
        hierarchy_results = {}

        # Fit each hierarchy level
        for order in sorted(terms_by_order.keys()):
            logger.debug("Testing %s-order terms...", order)

            significant_terms = []

            for term in terms_by_order[order]:
                # Check if parent terms are included (hierarchy principle)
                if self._hierarchy_satisfied(term, selected_terms):
                    trial_terms = selected_terms + [term]

                    try:
                        model_result = self._fit_terms(trial_terms)

                        if term in model_result["p_values"]:
                            p_value = model_result["p_values"][term]
                            if p_value < significance_level:
                                significant_terms.append(
                                    {
                                        "term": term,
                                        "p_value": p_value,
                                        "coefficient": model_result["coefficients"][
                                            term
                                        ],
                                    }
                                )
                    except Exception as e:
                        logger.debug("Error fitting term %s: %s", term, e)
                        continue

            # Add significant terms
            if significant_terms:
                # Sort by p-value and add
                significant_terms.sort(key=lambda x: x["p_value"])
                for term_info in significant_terms:
                    selected_terms.append(term_info["term"])

                hierarchy_results[f"order_{order}"] = significant_terms

        # Fit final hierarchical model
        final_model = self._fit_terms(selected_terms)

        return {
            "selected_terms": selected_terms,
            "hierarchy_results": hierarchy_results,
            "final_model": final_model,
            "max_order": max_order,
            "significance_level": significance_level,
        }

    def all_subsets_selection(self, criterion: str = "AIC") -> Dict[str, Any]:
        """Perform all possible subsets selection.

        Parameters
        ----------
        criterion : str, default="AIC"
            Selection criterion: ``'AIC'``, ``'BIC'``, ``'R2'``, ``'R2_adj'``.

        Returns
        -------
        Dict[str, Any]
            All subsets results.
        """
        candidate_terms = self._generate_candidate_terms()
        max_terms = min(len(candidate_terms), len(self.data) // 4)  # Conservative limit

        if len(candidate_terms) > 20:
            warnings.warn(
                "Large number of candidate terms. Consider using stepwise selection."
            )

        best_models_by_size = {}
        all_models = []

        # Try all subset sizes
        for subset_size in range(1, max_terms + 1):
            best_criterion = (
                float("inf") if criterion in ["AIC", "BIC"] else float("-inf")
            )
            best_model = None
            best_terms = None

            # Try all combinations of this size
            for term_combination in combinations(candidate_terms, subset_size):
                terms = ["Intercept"] + list(term_combination)

                try:
                    model_result = self._fit_terms(terms)
                    criterion_value = model_result["model_metrics"][criterion]

                    all_models.append(
                        {
                            "terms": terms,
                            "n_terms": len(terms),
                            "criterion_value": criterion_value,
                            "r_squared": model_result["model_metrics"]["R2"],
                            "model_result": model_result,
                        }
                    )

                    # Check if best for this size
                    if criterion in ["AIC", "BIC"]:
                        is_better = criterion_value < best_criterion
                    else:
                        is_better = criterion_value > best_criterion

                    if is_better:
                        best_criterion = criterion_value
                        best_model = model_result
                        best_terms = terms

                except Exception as e:
                    logger.debug("Failed to fit subset %s: %s", terms, e)
                    continue

            if best_model is not None:
                best_models_by_size[subset_size] = {
                    "terms": best_terms,
                    "model": best_model,
                    "criterion_value": best_criterion,
                }

        # Find overall best model
        overall_best = None
        overall_best_criterion = (
            float("inf") if criterion in ["AIC", "BIC"] else float("-inf")
        )

        for size, model_info in best_models_by_size.items():
            criterion_value = model_info["criterion_value"]

            if criterion in ["AIC", "BIC"]:
                is_better = criterion_value < overall_best_criterion
            else:
                is_better = criterion_value > overall_best_criterion

            if is_better:
                overall_best = model_info
                overall_best_criterion = criterion_value

        return {
            "best_models_by_size": best_models_by_size,
            "overall_best": overall_best,
            "all_models": sorted(all_models, key=lambda x: x["criterion_value"]),
            "criterion": criterion,
        }

    def cross_validation(
        self,
        model_terms: List[str],
        k_folds: int = 5,
        random_state: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Perform k-fold cross-validation.

        Parameters
        ----------
        model_terms : list of str
            Model terms to validate.
        k_folds : int, optional
            Number of folds, by default 5.
        random_state : int, optional
            Seed for reproducible splitting.

        Returns
        -------
        dict
            Cross-validation results.
        """
        from sklearn.model_selection import KFold

        kf = KFold(n_splits=k_folds, shuffle=True, random_state=random_state)

        cv_results = {"fold_results": [], "predictions": [], "actuals": []}

        for fold, (train_idx, test_idx) in enumerate(kf.split(self.data)):
            train_data = self.data.iloc[train_idx]
            test_data = self.data.iloc[test_idx]

            # Fit model on training data
            try:
                # Create temporary ModelFitting object for training data
                train_fitter = ModelFitting(train_data, self.response)
                train_model = train_fitter._fit_terms(model_terms)

                # Predict on test data
                test_predictions = self._predict_with_model(
                    train_model, test_data, model_terms
                )
                test_actuals = test_data[self.response].values

                # Calculate fold metrics
                fold_rmse = np.sqrt(np.mean((test_predictions - test_actuals) ** 2))
                fold_mae = np.mean(np.abs(test_predictions - test_actuals))
                fold_r2 = 1 - np.sum((test_actuals - test_predictions) ** 2) / np.sum(
                    (test_actuals - np.mean(test_actuals)) ** 2
                )

                cv_results["fold_results"].append(
                    {
                        "fold": fold + 1,
                        "rmse": fold_rmse,
                        "mae": fold_mae,
                        "r2": fold_r2,
                        "n_train": len(train_data),
                        "n_test": len(test_data),
                    }
                )

                cv_results["predictions"].extend(test_predictions)
                cv_results["actuals"].extend(test_actuals)

            except Exception as e:
                logger.debug("Cross-validation fold %s failed: %s", fold + 1, e)
                cv_results["fold_results"].append({"fold": fold + 1, "error": str(e)})

        # Calculate overall CV metrics
        if cv_results["predictions"]:
            all_predictions = np.array(cv_results["predictions"])
            all_actuals = np.array(cv_results["actuals"])

            cv_results["overall_rmse"] = np.sqrt(
                np.mean((all_predictions - all_actuals) ** 2)
            )
            cv_results["overall_mae"] = np.mean(np.abs(all_predictions - all_actuals))
            cv_results["overall_r2"] = 1 - np.sum(
                (all_actuals - all_predictions) ** 2
            ) / np.sum((all_actuals - np.mean(all_actuals)) ** 2)

            # Calculate mean and std of fold metrics
            valid_folds = [f for f in cv_results["fold_results"] if "error" not in f]
            if valid_folds:
                cv_results["mean_rmse"] = np.mean([f["rmse"] for f in valid_folds])
                cv_results["std_rmse"] = np.std([f["rmse"] for f in valid_folds])
                cv_results["mean_r2"] = np.mean([f["r2"] for f in valid_folds])
                cv_results["std_r2"] = np.std([f["r2"] for f in valid_folds])

        return cv_results

    def bootstrap_validation(
        self,
        model_terms: List[str],
        n_bootstrap: int = 100,
        random_state: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Perform bootstrap validation.

        Parameters
        ----------
        model_terms : list of str
            Model terms to validate.
        n_bootstrap : int, optional
            Number of bootstrap samples, by default 100.
        random_state : int, optional
            Seed for reproducible resampling.

        Returns
        -------
        dict
            Bootstrap validation results.
        """
        rng = np.random.default_rng(random_state)
        n_samples = len(self.data)
        bootstrap_results = {
            "coefficients": {term: [] for term in model_terms},
            "r_squared": [],
            "rmse": [],
            "predictions": [],
        }

        # Original model for comparison
        original_model = self._fit_terms(model_terms)

        for bootstrap_idx in range(n_bootstrap):
            # Create bootstrap sample
            bootstrap_indices = rng.integers(0, n_samples, size=n_samples)
            bootstrap_data = self.data.iloc[bootstrap_indices].reset_index(drop=True)

            try:
                # Fit model on bootstrap sample
                bootstrap_fitter = ModelFitting(bootstrap_data, self.response)
                bootstrap_model = bootstrap_fitter._fit_terms(model_terms)

                # Store coefficients
                for term in model_terms:
                    if term in bootstrap_model["coefficients"]:
                        bootstrap_results["coefficients"][term].append(
                            bootstrap_model["coefficients"][term]
                        )
                    else:
                        bootstrap_results["coefficients"][term].append(np.nan)

                # Store model metrics
                bootstrap_results["r_squared"].append(
                    bootstrap_model["model_metrics"]["R2"]
                )
                bootstrap_results["rmse"].append(
                    bootstrap_model["model_metrics"]["RMSE"]
                )

                # Predict on original data
                predictions = self._predict_with_model(
                    bootstrap_model, self.data, model_terms
                )
                bootstrap_results["predictions"].append(predictions)

            except Exception as e:
                logger.debug("Bootstrap iteration failed: %s", e)
                for term in model_terms:
                    bootstrap_results["coefficients"][term].append(np.nan)
                bootstrap_results["r_squared"].append(np.nan)
                bootstrap_results["rmse"].append(np.nan)
                bootstrap_results["predictions"].append(np.full(n_samples, np.nan))

        # Calculate bootstrap statistics
        bootstrap_stats = {}

        # Coefficient statistics
        for term in model_terms:
            coeff_values = [
                c for c in bootstrap_results["coefficients"][term] if not np.isnan(c)
            ]
            if coeff_values:
                bootstrap_stats[f"{term}_mean"] = np.mean(coeff_values)
                bootstrap_stats[f"{term}_std"] = np.std(coeff_values)
                bootstrap_stats[f"{term}_ci_lower"] = np.percentile(coeff_values, 2.5)
                bootstrap_stats[f"{term}_ci_upper"] = np.percentile(coeff_values, 97.5)

                # Bias calculation
                original_coeff = original_model["coefficients"].get(term, 0)
                bootstrap_stats[f"{term}_bias"] = np.mean(coeff_values) - original_coeff

        # Model performance statistics
        valid_r2 = [r2 for r2 in bootstrap_results["r_squared"] if not np.isnan(r2)]
        valid_rmse = [rmse for rmse in bootstrap_results["rmse"] if not np.isnan(rmse)]

        if valid_r2:
            bootstrap_stats["r2_mean"] = np.mean(valid_r2)
            bootstrap_stats["r2_std"] = np.std(valid_r2)
            bootstrap_stats["r2_ci_lower"] = np.percentile(valid_r2, 2.5)
            bootstrap_stats["r2_ci_upper"] = np.percentile(valid_r2, 97.5)

        if valid_rmse:
            bootstrap_stats["rmse_mean"] = np.mean(valid_rmse)
            bootstrap_stats["rmse_std"] = np.std(valid_rmse)
            bootstrap_stats["rmse_ci_lower"] = np.percentile(valid_rmse, 2.5)
            bootstrap_stats["rmse_ci_upper"] = np.percentile(valid_rmse, 97.5)

        return {
            "bootstrap_results": bootstrap_results,
            "bootstrap_stats": bootstrap_stats,
            "original_model": original_model,
            "n_bootstrap": n_bootstrap,
            "success_rate": len(valid_r2) / n_bootstrap,
        }

    def model_comparison(self, model_list: List[List[str]]) -> pd.DataFrame:
        """Compare multiple models using various criteria.

        Parameters
        ----------
        model_list : list of list of str
            List of model term lists to compare.

        Returns
        -------
        pandas.DataFrame
            Model comparison table.
        """
        comparison_results = []

        for i, model_terms in enumerate(model_list):
            try:
                model_result = self._fit_terms(model_terms)

                comparison_results.append(
                    {
                        "Model": f"Model_{i+1}",
                        "Terms": " + ".join(model_terms),
                        "N_Terms": len(model_terms),
                        "R2": model_result["model_metrics"]["R2"],
                        "R2_Adj": model_result["model_metrics"]["R2_adj"],
                        "AIC": model_result["model_metrics"]["AIC"],
                        "BIC": model_result["model_metrics"]["BIC"],
                        "RMSE": model_result["model_metrics"]["RMSE"],
                        "F_Statistic": model_result["model_metrics"].get(
                            "F_statistic", np.nan
                        ),
                        "F_P_Value": model_result["model_metrics"].get(
                            "F_p_value", np.nan
                        ),
                    }
                )

                # Store fitted model
                self.fitted_models[f"Model_{i+1}"] = model_result

            except Exception as e:
                logger.debug("Model comparison failed for model %s: %s", i + 1, e)
                comparison_results.append(
                    {
                        "Model": f"Model_{i+1}",
                        "Terms": " + ".join(model_terms),
                        "N_Terms": len(model_terms),
                        "Error": str(e),
                    }
                )

        self.model_comparison = pd.DataFrame(comparison_results)
        return self.model_comparison

    def _generate_candidate_terms(self) -> List[str]:
        """Generate candidate model terms."""
        terms = []

        # Main effects
        for factor in self.factor_columns:
            terms.append(factor)

        # Two-factor interactions
        for i, factor1 in enumerate(self.factor_columns):
            for factor2 in self.factor_columns[i + 1 :]:
                terms.append(f"{factor1}*{factor2}")

        # Three-factor interactions (if not too many factors)
        if len(self.factor_columns) <= 5:
            for i, factor1 in enumerate(self.factor_columns):
                for j, factor2 in enumerate(self.factor_columns[i + 1 :], i + 1):
                    for factor3 in self.factor_columns[j + 1 :]:
                        terms.append(f"{factor1}*{factor2}*{factor3}")

        return terms

    def _generate_hierarchical_terms(self, max_order: int) -> Dict[int, List[str]]:
        """Generate terms organized by hierarchy order."""
        terms_by_order = {}

        # Order 1: Main effects
        terms_by_order[1] = self.factor_columns.copy()

        # Order 2: Two-factor interactions
        if max_order >= 2:
            terms_by_order[2] = []
            for i, factor1 in enumerate(self.factor_columns):
                for factor2 in self.factor_columns[i + 1 :]:
                    terms_by_order[2].append(f"{factor1}*{factor2}")

        # Order 3: Three-factor interactions
        if max_order >= 3:
            terms_by_order[3] = []
            for i, factor1 in enumerate(self.factor_columns):
                for j, factor2 in enumerate(self.factor_columns[i + 1 :], i + 1):
                    for factor3 in self.factor_columns[j + 1 :]:
                        terms_by_order[3].append(f"{factor1}*{factor2}*{factor3}")

        return terms_by_order

    def _hierarchy_satisfied(self, term: str, included_terms: List[str]) -> bool:
        """Check if hierarchy principle is satisfied for a term."""
        if "*" not in term:
            return True  # Main effects always satisfy hierarchy

        # For interaction terms, all parent terms must be included
        factors_in_term = term.split("*")

        # Check all lower-order combinations
        for order in range(1, len(factors_in_term)):
            for parent_combination in combinations(factors_in_term, order):
                if order == 1:
                    parent_term = parent_combination[0]
                else:
                    parent_term = "*".join(parent_combination)

                if parent_term not in included_terms:
                    return False

        return True

    def _fit_terms(self, terms: List[str]) -> Dict[str, Any]:
        """Fit model with specified terms."""
        import statsmodels.api as sm
        from statsmodels.formula.api import ols

        # Build model formula
        if "Intercept" in terms:
            formula_terms = [t for t in terms if t != "Intercept"]
        else:
            formula_terms = terms

        if not formula_terms:
            formula = f"{self.response} ~ 1"  # Intercept only
        else:
            # Convert terms to statsmodels format
            formula_parts = []
            for term in formula_terms:
                if "*" in term:
                    # Interaction term
                    factors = term.split("*")
                    formula_parts.append(" * ".join([f"C({f})" for f in factors]))
                else:
                    # Main effect
                    formula_parts.append(f"C({term})")

            formula = f"{self.response} ~ " + " + ".join(formula_parts)

        # Fit model
        model = ols(formula, data=self.data).fit()

        # Extract results
        coefficients = dict(zip(model.params.index, model.params.values))
        std_errors = dict(zip(model.params.index, model.bse.values))
        t_stats = dict(zip(model.params.index, model.tvalues.values))
        p_values = dict(zip(model.params.index, model.pvalues.values))

        # Calculate model metrics
        n = len(self.data)
        p = len(model.params)

        model_metrics = {
            "R2": model.rsquared,
            "R2_adj": model.rsquared_adj,
            "AIC": model.aic,
            "BIC": model.bic,
            "RMSE": np.sqrt(model.mse_resid),
            "F_statistic": model.fvalue,
            "F_p_value": model.f_pvalue,
            "Log_likelihood": model.llf,
            "N_observations": n,
            "N_parameters": p,
        }

        return {
            "coefficients": coefficients,
            "std_errors": std_errors,
            "t_statistics": t_stats,
            "p_values": p_values,
            "model_metrics": model_metrics,
            "fitted_values": model.fittedvalues.values,
            "residuals": model.resid.values,
            "model_object": model,
            "formula": formula,
        }

    def _predict_with_model(
        self,
        model_result: Dict[str, Any],
        new_data: pd.DataFrame,
        model_terms: List[str],
    ) -> np.ndarray:
        """Make predictions with a fitted model."""
        # Use the statsmodels model object for prediction
        model_obj = model_result["model_object"]
        predictions = model_obj.predict(new_data)
        return predictions.values

    def residual_diagnostics(self, model_terms: List[str]) -> Dict[str, Any]:
        """Perform comprehensive residual diagnostics.

        Parameters
        ----------
        model_terms : List[str]
            Model terms to diagnose.

        Returns
        -------
        Dict[str, Any]
            Diagnostic results.
        """
        model_result = self._fit_terms(model_terms)

        residuals = model_result["residuals"]
        fitted_values = model_result["fitted_values"]

        diagnostics = {}

        # Basic residual statistics
        diagnostics["residual_stats"] = {
            "mean": np.mean(residuals),
            "std": np.std(residuals),
            "min": np.min(residuals),
            "max": np.max(residuals),
            "range": np.max(residuals) - np.min(residuals),
        }

        # Normality tests
        try:
            shapiro_stat, shapiro_p = stats.shapiro(residuals)
            diagnostics["normality_test"] = {
                "shapiro_wilk_statistic": shapiro_stat,
                "shapiro_wilk_p_value": shapiro_p,
                "normal_assumption": shapiro_p > 0.05,
            }
        except Exception as e:
            logger.debug("Normality test failed: %s", e)
            diagnostics["normality_test"] = {
                "error": f"Unable to perform normality test: {e}"
            }

        # Homoscedasticity tests
        try:
            # Breusch-Pagan test
            from statsmodels.stats.diagnostic import het_breuschpagan

            bp_stat, bp_p, bp_f_stat, bp_f_p = het_breuschpagan(
                residuals, model_result["model_object"].model.exog
            )

            diagnostics["homoscedasticity_test"] = {
                "breusch_pagan_statistic": bp_stat,
                "breusch_pagan_p_value": bp_p,
                "homoscedastic_assumption": bp_p > 0.05,
            }
        except Exception as e:
            logger.debug("Homoscedasticity test failed: %s", e)
            diagnostics["homoscedasticity_test"] = {
                "error": f"Unable to perform homoscedasticity test: {e}"
            }

        # Independence test
        try:
            from statsmodels.stats.diagnostic import durbin_watson

            dw_stat = durbin_watson(residuals)

            diagnostics["independence_test"] = {
                "durbin_watson_statistic": dw_stat,
                "independent_assumption": 1.5 <= dw_stat <= 2.5,
            }
        except Exception as e:
            logger.debug("Independence test failed: %s", e)
            diagnostics["independence_test"] = {
                "error": f"Unable to perform independence test: {e}"
            }

        # Outlier detection
        standardized_residuals = residuals / np.std(residuals)
        outliers = np.abs(standardized_residuals) > 2.5

        diagnostics["outlier_analysis"] = {
            "n_outliers": np.sum(outliers),
            "outlier_indices": np.where(outliers)[0].tolist(),
            "max_standardized_residual": np.max(np.abs(standardized_residuals)),
        }

        # Leverage and influence
        try:
            influence = model_result["model_object"].get_influence()
            leverage = influence.hat_matrix_diag
            cooks_d = influence.cooks_distance[0]

            high_leverage = leverage > 2 * len(model_terms) / len(self.data)
            high_influence = cooks_d > 4 / len(self.data)

            diagnostics["leverage_influence"] = {
                "max_leverage": np.max(leverage),
                "n_high_leverage": np.sum(high_leverage),
                "high_leverage_indices": np.where(high_leverage)[0].tolist(),
                "max_cooks_d": np.max(cooks_d),
                "n_high_influence": np.sum(high_influence),
                "high_influence_indices": np.where(high_influence)[0].tolist(),
            }
        except Exception as e:
            logger.debug("Leverage and influence calculation failed: %s", e)
            diagnostics["leverage_influence"] = {
                "error": f"Unable to calculate leverage and influence: {e}"
            }

        return diagnostics

    def lack_of_fit_test(self, model_terms: List[str]) -> Dict[str, Any]:
        """Perform lack-of-fit test for models with replicates.

        Parameters
        ----------
        model_terms : List[str]
            Model terms to test.

        Returns
        -------
        Dict[str, Any]
            Lack-of-fit test results.
        """
        # Check if we have replicates
        factor_combinations = self.data[self.factor_columns].drop_duplicates()

        if len(factor_combinations) == len(self.data):
            return {"error": "No replicates found for lack-of-fit test"}

        # Fit the model
        model_result = self._fit_terms(model_terms)

        # Calculate pure error and lack-of-fit
        pure_error_ss = 0
        pure_error_df = 0

        for _, combination in factor_combinations.iterrows():
            # Find all replicates for this combination
            mask = True
            for factor in self.factor_columns:
                mask &= self.data[factor] == combination[factor]

            replicates = self.data[mask]

            if len(replicates) > 1:
                # Calculate pure error for this combination
                replicate_responses = replicates[self.response].values
                replicate_mean = np.mean(replicate_responses)

                pure_error_ss += np.sum((replicate_responses - replicate_mean) ** 2)
                pure_error_df += len(replicates) - 1

        if pure_error_df == 0:
            return {"error": "Insufficient replicates for lack-of-fit test"}

        # Calculate lack-of-fit
        total_error_ss = np.sum(model_result["residuals"] ** 2)
        total_error_df = len(self.data) - len(model_terms)

        lof_ss = total_error_ss - pure_error_ss
        lof_df = total_error_df - pure_error_df

        if lof_df <= 0:
            return {"error": "Model is saturated - cannot test lack-of-fit"}

        # Calculate F-statistic
        lof_ms = lof_ss / lof_df
        pure_error_ms = pure_error_ss / pure_error_df

        f_statistic = lof_ms / pure_error_ms
        p_value = 1 - stats.f.cdf(f_statistic, lof_df, pure_error_df)

        return {
            "lack_of_fit_ss": lof_ss,
            "lack_of_fit_df": lof_df,
            "lack_of_fit_ms": lof_ms,
            "pure_error_ss": pure_error_ss,
            "pure_error_df": pure_error_df,
            "pure_error_ms": pure_error_ms,
            "f_statistic": f_statistic,
            "p_value": p_value,
            "adequate_fit": p_value > 0.05,
            "n_unique_combinations": len(factor_combinations),
            "total_observations": len(self.data),
        }
