from ML.gp.gp import GaussianProcess
from ML.helpers import partition_indexes
from ML.gp.gp_ensemble_estimators import GP_ensembles

import numpy as np
import math

class rBCM(GP_ensembles):
    def __init__(self, args):
        super().__init__(args)

    def predict(self, x, keep_probs=False):
        gaussian_means, vars_gp = self.gp_means_vars(x)

        # These contain a row for each binary class case (OvR)
        #   AFTER summing along axis 0 (each of the local experts)
        M = vars_gp.shape[0]
        gaussian_variance = vars_gp
        gaussian_precisions = gaussian_variance**(-1)

        # TODO prior precision - squared element-wise inverse of diagonal along covariance matrix
        # prior_precision = vars_gp**(-2) # NOTE WRONG - prior precision is diag of elementwise inverse of cov matrix
        prior_variances = np.empty_like(gaussian_precisions)
        for idx, gp_expert in enumerate(self.gp_experts):
            prior_variance = gp_expert.prior_variance(x)
            prior_variances[idx] = prior_variance
        prior_precisions = prior_variances**(-1)

        betas = 0.5 * (np.log(prior_variances) - np.log(gaussian_variance))

        rbcm_precisions = np.sum(betas * gaussian_precisions + (1-np.sum(betas)) * prior_precisions, axis=0)
        rbcm_variances = rbcm_precisions**(-1)
        rbcm_means = rbcm_variances * np.sum(betas * gaussian_precisions * gaussian_means, axis=0) # means

        if self.gp_type == 'classification':
            rbcm_precisions = np.sum(rbcm_precisions, axis=0)
            rbcm_means = np.sum(rbcm_means, axis=0)
            if keep_probs == True:
                return rbcm_means, rbcm_variances
            return np.argmax(rbcm_means, axis=0)
        elif self.gp_type == 'regression':
            return rbcm_means, rbcm_variances
