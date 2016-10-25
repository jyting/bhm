from ML.gp.gp import GaussianProcess
from ML.helpers import partition_indexes
# from ML.gp.gp_ensemble_estimators import GP_ensembles
from ML.gp.gp_ensemble_estimators import GP_ensembles

import numpy as np
import math
import pdb

class GPoGPE(GP_ensembles):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def predict(self, x, parallel=True, keep_probs=False):
        gaussian_means, gaussian_variances = self.gp_means_vars(x, parallel=parallel)

        # Expert contributions 
        expert_count = self.gp_experts.shape[0]
        betas = np.full(x.shape[0], 1/expert_count)

        gaussian_precisions = gaussian_variances ** (-1)

        # These contain a row for each binary class case (OvR)
        # NOTE betas can only be factored out as it is consistent throughout

        gpoe_precisions = np.sum(betas * gaussian_precisions, axis=0)
        gpoe_variances = gpoe_precisions ** (-1)
        gpoe_means = gpoe_variances * np.sum(betas * gaussian_precisions * gaussian_means, axis=0)

        if keep_probs == True:
            return gpoe_means, gpoe_variances

        if self.gp_type == 'classification':
            return np.argmax(means_poe, axis=0)
        elif self.gp_type == 'regression':
            return gpoe_means, gpoe_variances
