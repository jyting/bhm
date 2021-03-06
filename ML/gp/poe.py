from ML.gp.gp import GaussianProcess
from ML.helpers import partition_indexes
# from ML.gp.gp_ensemble_estimators import GP_ensembles
from ML.gp.gpy_ensemble_estimators import GP_ensembles

import numpy as np
import math
import pdb

class PoGPE(GP_ensembles):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def predict(self, x, parallel=True):
        gaussian_means, gaussian_variances = self.gp_means_vars(x, parallel=parallel)

        # -1 : 8.4768 (100 iter), 9.3239 (100 iter), 8.42110 (100 iter), 8.3598 (100 iter)
        # -2 : 6.3987 (100 iter), 4.2984 (100 iter), 10.7466 (100 iter)
        gaussian_precisions = gaussian_variances**(-1)

        # These contain a row for each binary class case (OvR)
        #   AFTER summing along axis 0 (each of the local experts)
        poe_precisions = np.sum(gaussian_precisions, axis=0)  # vars
        poe_variances = poe_precisions**(-1)
        poe_means = poe_variances * np.sum(gaussian_precisions * gaussian_means, axis=0)  # means

        return poe_means, poe_variances
