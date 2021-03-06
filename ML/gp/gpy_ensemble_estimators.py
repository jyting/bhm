from ML.gp import gp_gpy
from ML.gp import gp
from ML.helpers import partition_indexes
from progressbar import Bar, Percentage, Counter, ProgressBar, ETA
from ML.helpers import sigmoid

import numpy as np
import math
import pdb

class GP_ensembles():
    def __init__(self, expert_size=200):
        print(expert_size)
        self.expert_size = expert_size
    
    def fit(self, X, y, parallel=False):
        if type(y[0]) != np.int64:
            print('Performing ensemble GP regression')
            # self.gp_type = 'regression'
            self.model = gp_gpy.GPR
        else:
            print('Performing ensemble GP classification')
            self.model = gp_gpy.GPyC
            # self.gp_type = 'classification'

        self.labels_count = np.unique(y).shape[0]

        # NOTE hacky fix here
        if self.labels_count > 4:
            self.labels_count = 24

        # self.num_classes = np.unique(y).shape[0]
    
        # Shuffle the data in a separate copy
        # TODO need to 'organise' these into 
        shuf_idxs = np.arange(y.shape[0])
        np.random.shuffle(shuf_idxs)
        X_s = X[shuf_idxs]
        y_s = y[shuf_idxs]
        # 200 data points per expert classifier
        expert_count = math.ceil(X_s.shape[0]/self.expert_size)
    
        # Create and train all local GP experts
        gp_experts = np.full(expert_count, self.model(), dtype='object')
        idxs = partition_indexes(X_s.shape[0], expert_count)
        widgets=['Fitting: ', Bar(), ' ', Counter(), ' ', Percentage(), ' ', ETA()]
        bar = ProgressBar(widgets=widgets, maxval=gp_experts.shape[0])
        bar.start()
        for i, gp_expert, (start, end) in zip(range(gp_experts.shape[0]), gp_experts, idxs):
            bar.update(i)
            gp_expert.fit(X_s[start:end], y_s[start:end], parallel=parallel)
        bar.finish()
        self.gp_experts = gp_experts

        return self
    
    # Returns the means and variances for each GP expert
    def gp_means_vars(self, x, parallel=False):
    
        # Means, variances for each binary class case for each GP regressor (classifier)
        # Shape - (experts, 2, classes, data points)
        #   2 - 0-axis for means, 1-axis for variances

        y_preds = np.zeros((self.gp_experts.shape[0], 2, x.shape[0], self.labels_count ))
        widgets=['Predicting: ', Bar(), ' ', Counter(), ' ', Percentage(), ' ', ETA()]
        bar = ProgressBar(widgets=widgets, maxval=self.gp_experts.shape[0])
        bar.start()
        for i in range(self.gp_experts.shape[0]):
            bar.update(i)
            y_preds[i] = self.gp_experts[i].predict(x, parallel=parallel)
        bar.finish()

        # y_preds = np.array([gp_expert.predict(x, parallel=parallel) for gp_expert in self.gp_experts])
    
        # Extract means and variances
        means_gp = y_preds[:,0]
        vars_gp = y_preds[:,1]
    
        return means_gp, vars_gp

