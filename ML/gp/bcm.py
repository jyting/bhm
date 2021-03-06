from ML.gp.gp import GaussianProcess
from ML.helpers import partition_indexes
# from ML.gp.gp_ensemble_estimators import GP_ensembles
from ML.gp.gpy_ensemble_estimators import GP_ensembles

import numpy as np
import math
import pdb

class BCM(GP_ensembles):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def predict(self, x, parallel=True):
        gaussian_means, gaussian_variances = self.gp_means_vars(x, parallel=parallel)

        # These contain a row for each binary class case (OvR)
        #   AFTER summing along axis 0 (each of the local experts)
        M = gaussian_variances.shape[0]
        # gaussian_precisions = gaussian_variances**(-1)
        gaussian_precisions = 1/gaussian_variances

        # TODO prior precision - squared element-wise inverse of diagonal along covariance matrix
        # prior_precision = gaussian_variances**(-2) # NOTE WRONG - prior precision is diag of elementwise inverse of cov matrix
        prior_variances = np.empty_like(gaussian_precisions)
        for idx, gp_expert in enumerate(self.gp_experts):
            prior_variance = gp_expert.prior_variance(x)
            prior_variances[idx] = prior_variance
        # prior_precisions = prior_variances**(-1)
        prior_precisions = 1/prior_variances

        bcm_precisions = np.sum(gaussian_precisions + (1-M) * prior_precisions, axis=0) # variances
        # bcm_variances = bcm_precisions**(-1)
        bcm_variances = 1/bcm_precisions
        bcm_means = bcm_variances * np.sum(gaussian_precisions * gaussian_means, axis=0) # means

        return bcm_means, bcm_variances
