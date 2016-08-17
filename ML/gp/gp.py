import sys
import math
import pdb
from datetime import datetime

from collections import OrderedDict
from progress.bar import Bar

import multiprocessing as mp
from multiprocessing import Pool

from itertools import combinations

# Project-internals
from ML.helpers import partition_indexes
from ML.helpers import sigmoid

# Numpy
import numpy as np
from numpy import linalg

# Sympy 
from sympy import KroneckerDelta

# Scipy
from scipy.optimize import minimize
from scipy.spatial.distance import cdist
from scipy.stats import norm

# TODO when doing K(X, X), simply use (n_err^2)I instead of KroneckerDelta

# using http://www.robots.ox.ac.uk/~mebden/reports/GPtutorial.pdf

# Example
# a = np.array([1,2,3,4,5])
# a = a.reshape(5,1) # 5 rows, 1 column
# b = np.array([6,7,8])
# b = np.reshape(1,3) # 1 row, 3 columns

class GaussianProcess:
    def __init__(self, classification_type='OvR'):
        if classification_type == 'OvO':
            self.fit_all_classes = self.fit_classes_OvO
            self.predict_probs = self.predict_probs_OvO
        elif classification_type == 'OvR':
            self.fit_all_classes = self.fit_classes_OvR
            self.predict_probs = self.predict_probs_OvR

    # Overrite to print class details
    def __str__(self):
        try:
            class_print = "f_err: {}\nl_scales: {}\nn_err: {}".format(self.f_err, self.l_scales, self.n_err)
            return class_print
        except:
            return "GP hasn't been trained yet."

    ####################################################
    #################### Regression ####################
    ####################################################

    # Regression fit
    def fit_regression(self, X, y):

        # Set basic data
        self.X = X  # Inputs
        self.y = y
        self.size = len(X)

        # Determine optimal GP hyperparameters
        # x0 = np.random.rand(2 + X.shape[1])
        # f_err, l_scales, n_err
        x0 = [100] + [50] * X.shape[1] + [0.1]
        # gp_hp_guess = [1.0] * 3 # initial guess

        # res = minimize(self.SE_NLL, x0, method='bfgs')
        res = minimize(self.SE_NLL, x0, method='bfgs', jac=self.SE_der)

        # res['x'] = np.array([3076.7471, 100.58150154, 0.304933902061]) # NOTE hardcoded sample values 
        # res['x'] = np.array([3000, 100, 0.3])
        self.f_err, self.l_scales, self.n_err = self.unpack_GP_args(res['x'])

        # S et a few 'fixed' variables once GP HPs are determined for later use (with classifier)
        self.L = self.L_create(self.X, self.f_err, self.l_scales, self.n_err)
        self.K_inv = np.linalg.inv(self.L.T).dot(np.linalg.inv(self.L))
        self.alpha = linalg.solve(self.L.T, (linalg.solve(self.L, self.y)))

    def predict_regression(self, x, L=None, alpha=None, f_err=None, l_scales=None, n_err=None):

        # Assign hyperparameters and other calculated variables
        if L==None and alpha==None and f_err==None and l_scales==None:
            L = self.L
            alpha = self.alpha
            f_err = self.f_err
            l_scales = self.l_scales
            n_err = self.n_err

        # # Initialise data structure for means, variances
        # means = np.zeros(x.shape[0])
        # variances = np.zeros(x.shape[0])
        
        # # Predict for all points
        # for i, row in enumerate(x):
        #     ks = self.K_se(self.X, [row], f_err, l_scales)              # 2.25 
        #     mean = ks.T.dot(alpha)                                      # 2.25 line 4
        #     v = linalg.solve(L, ks)                                     # 2.26 line 5
        #     variance = self.dist([row], [row], l_scales) - v.T.dot(v)   # 2.26 line 6

        #     # Assign mean, variance for current point
        #     means[i] = mean
        #     variances[i] = variance

        # # if len(means.shape) == 2 and means.shape[1] == 1:
        # #     means = means.reshape(means.shape[0])
        # return means, variances

        # TODO fix - mean and var need to be calculated per point
        k_star = self.K_se(self.X, x, f_err, l_scales)
        f_star = k_star.T.dot(alpha)
        v = np.linalg.solve(L, k_star)
        var = self.K_se(x, x, f_err, l_scales) - v.T.dot(v)

        # Corner case with only one dimension 
        if len(f_star.shape) == 2 and f_star.shape[1] == 1:
            f_star = f_star.reshape(f_star.shape[0])

        pdb.set_trace()

        return f_star, var


    def SE_der(self, args):
        # TODO fix - get around apparent bug
        # if len(args.shape) != 1:
        #     # print(args)
        #     args = args[0]

        f_err, l_scales, n_err = self.unpack_GP_args(args)
        # TODO use alpha calculated from SE_NLL

        L = self.L_create(self.X, f_err, l_scales, n_err)
        alpha = linalg.solve(L.T, (linalg.solve(L, self.y))) # save for use with derivative func
        aaT = alpha.dot(alpha.T)
        K_inv = np.linalg.inv(L.T).dot(np.linalg.inv(L))

        # Calculate dK/dtheta over each hyperparameter
        eval_dK_dthetas = self.eval_dK_dthetas(f_err, l_scales, n_err)

        # Incorporate each dK/dt into gradient
        derivatives = [float(-0.5 * np.matrix.trace((aaT - K_inv).dot(dK_dtheta))) for dK_dtheta in eval_dK_dthetas]
        return np.array(derivatives)

    # Args is an array to allow for scipy.optimize
    def SE_NLL(self, args):
        # TODO fix - get around apparent bug
        if len(args.shape) != 1:
            args = args[0]

        f_err, l_scales, n_err = self.unpack_GP_args(args)
        L = self.L_create(self.X, f_err, l_scales, n_err)
        
        alpha = linalg.solve(L.T, (linalg.solve(L, self.y))) # save for use with derivative func
        nll = (
            0.5 * self.y.T.dot(alpha) + 
            np.matrix.trace(np.log(L)) + # sum of diagonal
            0.5 * self.size * math.log(2*math.pi)
        )

        return nll

    ####################################################
    ####################### PLSC #######################
    ####################################################

    def prior_variance(self, x):

        if self.gp_type == 'classification':
            params = np.array(list(self.classifier_params.values()))
            averaged_params = np.average(params, axis=0)
            f_errs = averaged_params[0]
            n_errs = averaged_params[-1]
        elif self.gp_type == 'regression':
            f_errs = self.f_err
            n_errs = self.n_err

        # for foo in self.classifier_params.values():
        #     print(foo)
        # all_params = np.array(.unpack_GP_args(class_params) for class_params in self.classifier_params.values()])
        # all_params.reshape(self.class_count, len(self.classifier_params[0]))

        prior_var = f_errs**2 * np.exp([0] * x.shape[0]) + np.full(x.shape[0], n_errs**2)
        return prior_var

    #################### Negative LOO log predictive probability ####################

    # Unpacks arguments to deal with list of length scales in list of arguments
    def unpack_LLOO_args(self, args):
        f_err = float(args[0])
        l_scales = args[1:self.X.shape[1]+1]
        n_err = args[self.X.shape[1]+1]
        a = float(args[self.X.shape[1]+2])
        b = float(args[self.X.shape[1]+3])
        return f_err, l_scales, n_err, a, b

    def LLOO(self, args):
        f_err, l_scales, n_err, a, b = self.unpack_LLOO_args(args)

        L = self.L_create(self.X, f_err, l_scales, n_err)
        alpha = linalg.solve(L.T, (linalg.solve(L, self.y))) # save for use with derivative func
        K_inv = np.linalg.inv(L.T).dot(np.linalg.inv(L))
        mu = self.y - alpha/np.diag(K_inv)
        sigma_sq = 1/np.diag(K_inv)

        LLOO = -sum(norm.cdf(
            self.y * (a * mu + b) /
            np.sqrt(1 + a**2 * sigma_sq)
        ))

        return LLOO

    # NOTE likely incorrect - currently doesn't recalculate K per datapoint
    def LLOO_der(self, args):
        d1 = datetime.now()
        
        f_err, l_scales, n_err, a, b = self.unpack_LLOO_args(args)

        # This block is common to both LLOO and LLOO_der
        L = self.L_create(self.X, f_err, l_scales, n_err)
        alpha = linalg.solve(L.T, (linalg.solve(L, self.y))) # save for use with derivative func
        K_inv = np.linalg.inv(L.T).dot(np.linalg.inv(L))
        mu = self.y - alpha/np.diag(K_inv)
        sigma_sq = 1/np.diag(K_inv)

        r = a * mu + b

        K_i_diag = np.diag(K_inv)
        dK_dthetas = self.eval_dK_dthetas(f_err, l_scales, n_err) 
        Zs = np.array([K_inv.dot(dK_dtheta) for dK_dtheta in dK_dthetas])
        dvar_dthetas = [np.diag(Z.dot(K_inv))/K_i_diag**2 for Z in Zs] 
        dmu_dthetas = [Z.dot(alpha) / K_i_diag - alpha * dvar_dtheta for Z, dvar_dtheta in zip(Zs, dvar_dthetas)]

        pdf_on_cdf = norm.pdf(r) / norm.cdf(self.y * r)

        # Dervative over LLOO for each of the hyperparameters
        dLLOO_dthetas = [
                -sum(pdf_on_cdf * 
                    (self.y * a / np.sqrt(1 + a**2 * sigma_sq)) * 
                    (dmu_dtheta - 0.5 * a * (a * mu + b) / (1 + a**2 * sigma_sq) * dvar_dtheta))
                    for dmu_dtheta, dvar_dtheta in zip(dmu_dthetas, dvar_dthetas)
        ]

        # Derivative of LLOO w.r.t b
        dLLOO_db_arr = (
            pdf_on_cdf *
            self.y / np.sqrt(1 + a**2 * sigma_sq)
        )
        dLLOO_db = -sum(dLLOO_db_arr)

        # Derivative of LLOO w.r.t a, utilising dLLOO/db
        dLLOO_da = -sum(dLLOO_db_arr *
                        (mu - b * a * sigma_sq) /
                        (1 + a**2 * sigma_sq)
                       )
        
        gradients = dLLOO_dthetas + [dLLOO_da] + [dLLOO_db]

        return np.array(gradients, dtype=np.float64)

    def fit_classes_OvO(self, X, y):
        uniq_y = np.unique(y)
        ovos = combinations(uniq_y, 2)
        self.ovo_pairs = [pair for pair in ovos]
        for class_pair in self.ovo_pairs:
            # Get the two classes involved in this OvO
            pos_class, neg_class = class_pair

            # f_err, l_scales (for each dimension), n_err, alpha, beta
            x0 = [1] + [1] * X.shape[1] + [1,1,1]

            # Set binary labels for each OvO classifier
            cur_idxs = np.where((y != pos_class) & (y != neg_class))
            self.y = y[cur_idxs]
            self.y[np.where(self.y == neg_class)] = -1
            self.y[np.where(self.y == pos_class)] = 1
            self.X = X[cur_idxs]

            # Optimise
            res = minimize(self.LLOO, x0, method='bfgs', jac=self.LLOO_der)

            # Set params for the ibnary OvO
            self.classifier_params[class_pair] = res['x']

            # Reset ys
            self.y = y
            self.X = X

    def fit_classes_OvR(self, X, y):
        uniq_y = np.unique(y)
        prog_bar = Bar('Classes fitted', max=uniq_y.shape[0])
        for c in uniq_y:

            # f_err, l_scales (for each dimension), n_err, alpha, beta
            x0 = [1] + [1] * X.shape[1] + [1, 1, 1]

            # Set binary labels for OvA classifier
            self.y = np.array([1 if label == c else 0 for label in y])

            # Optimise and save hyper/parameters for current binary class pair
            # res = minimize(self.LLOO, x0, method='bfgs')
            res = minimize(self.LLOO, x0, method='bfgs', jac=self.LLOO_der)

            # Set params for current binary regressor (classifier)
            # for param, val in zip(params, res['x']):
            #     self.classifier_params[c][param] = val
            self.classifier_params[c] = res['x']

            # Reset ys
            self.y = y
            prog_bar.next()
        prog_bar.finish()

    # Classification
    def fit_classification(self, X, y):

        self.size = len(y)
        self.X = X
        self.classifier_params = OrderedDict()
        self.class_count = np.unique(y).shape[0]
        # self.class_count = 4
        params = ['f_err', 'l_scales', 'n_err', 'a', 'b']

        # Build OvA classifier for each unique class in y
        # OvR here - also TODO an OvO!
        self.fit_all_classes(X, y)


    # The 'extra' y_ parameter is to allow restriction of y for parallelisation
    def predict_class(self, x, keep_probs=False):

        # TODO vectorize 
        # Vectorize calculation of predictions
        # vec_pred_class_single = np.vectorize(self.predict_class_single)

        # Generate squashed y precidtions in steps
        if x.shape[0] > 5000:
            y_preds = np.zeros((len(self.classifier_params), 2, x.shape[0]))
            step = 2000

            # Step through data and predict in chunks
            for start in range(0, x.shape[0], step):
                next_idx = start + 2000
                end = next_idx if next_idx <= x.shape[0] else x.shape[0]
                cur_preds = np.array([self.predict_class_single(x[start:end], label, params)
                             for label, params in self.classifier_params.items()])
                y_preds[:,:,start:end] = cur_preds

        # Predict smaller datasets all at once
        else:
            y_preds = np.array([
                self.predict_class_single(x, label, params)
                for label, params in self.classifier_params.items()
            ])

        # Unpack means, variances
        y_means, y_vars = y_preds[:,0], y_preds[:,1]

        # Return raw OvA squashed probabilities per class 
        #   (for AUROC scores and GP ensemble methods - PoE, BCM, etc.)
        if keep_probs == True:
            return y_means, y_vars

        y_means_squashed = sigmoid(y_means)

        # Return max squashed value for each data point representing class prediction
        return self.predict_probs(y_means)

    def predict_probs_OvR(self, y_preds):
        return np.argmax(y_preds, axis=0)

    def predict_probs_OvO(self, y_preds):

        # Round each row off to 1s and 0s
        y_rnd = np.abs(np.rint(y_preds).astype(np.int))

        # Convert each row into actual predicted class labels based on OvO pairs
        for row_idx in range(y_rnd.shape[0]):
            # idxs have to be cached first as inlining them will overlap - 
            #    e.g. set to 0, then detected as 0 again
            yes_idxs = np.where(y_rnd[row_idx] == 1)
            no_idxs = np.where(y_rnd[row_idx] == 0)

            y_rnd[row_idx][yes_idxs] = self.ovo_pairs[row_idx][0]
            y_rnd[row_idx][no_idxs] = self.ovo_pairs[row_idx][1]

        # TODO take the max count for each column as class predictions
        return np.apply_along_axis(lambda x: np.argmax(np.bincount(x)), axis=0, arr=y_rnd)

    # Predict regression values in the binary class case
    def predict_class_single(self, x, label, params):
        # Set parameters
        f_err, l_scales, n_err = self.unpack_GP_args(params)

        # Set y to binary one vs. all labels
        y_ = np.copy(self.y)
        y_[np.where(y_ != label)[0]] = -1
        y_[np.where(y_ != -1)[0]] = 1

        # Set L and alpha matrices
        L = self.L_create(self.X, f_err, l_scales, n_err)
        alpha = linalg.solve(L.T, (linalg.solve(L, y_)))

        # Get predictions of resulting mean and variances
        y_pred, y_var = self.predict_regression(x, L, alpha, f_err, l_scales)

        return y_pred, y_var

    ############################### Derivatives ################################

    def L_create(self, X, f_err, l_scales, n_err):

        m = self.K_se(X, X, f_err, l_scales) + n_err**2 * np.identity(X.shape[0]).astype(np.float64)
        return linalg.cholesky(m)

    def dist(self, x1, x2, l_scales):
        # Dividing by length scale first before passing into cdist to
        #   accounts for different length scale for each dimension
        return cdist(x1/l_scales, x2/l_scales, 'sqeuclidean')

    def K_se(self, x1, x2, f_err, l_scales):
        m = self.dist(x1, x2, l_scales)
        return f_err**2 * np.exp(-0.5 * m)
        # return np.exp(-0.5 * m)

    def dK_df_eval(self, m, f_err, l_scales):
        return 2*f_err * m

    def dK_dls_eval(self, k, f_err, l_scales):

        k_ = np.copy(k)
        k_ = f_err**2 * k_

        # Repeats each row along axis=1
        M = np.repeat(self.X[:,None,:], len(self.X), axis=1) 

        # Separates Ms into every dimension of original dataset
        M_ds = np.array([[M[:,:,i], M[:,:,i].T] for i in range(self.X.shape[1])]) 

        # Derivative over length scale for each dimension
        dK_dls = [l_scale**(-3) * (m-mt)**2 * k_ for l_scale, (m, mt) in zip(l_scales, M_ds)]

        return dK_dls

    def dK_dn_eval(self, n_err):
        dK_dn = np.diag(np.array([2*n_err]*self.X.shape[0]))
        return dK_dn

    # Evaluates each dK_dtheta pre-calculated symbolic lambda with current iteration's hyperparameters
    def eval_dK_dthetas(self, f_err, l_scales, n_err):
        # Reshape length scales into a 1x matrix
        l_scales = np.array(l_scales)

        # exp(...) block of squared exponential function
        m = np.exp(-0.5 * self.dist(self.X, self.X, l_scales))

        # Evaluate all the partial derivatives
        dK_df = self.dK_df_eval(m, f_err, l_scales)
        dK_dls = self.dK_dls_eval(m, f_err, l_scales)
        dK_dn = self.dK_dn_eval(n_err)

        return np.array([dK_df] + dK_dls + [dK_dn], dtype=np.float64)


    #############################################################################
    ################################## Generic ##################################
    #############################################################################

    def unpack_GP_args(self, args):
        if len(args.shape) == 2:
            args = args[0]

        f_err = float(args[0])
        l_scales = args[1:self.X.shape[1]+1]
        n_err = args[self.X.shape[1]+1]
        return f_err, l_scales, n_err

    def fit(self, X, y):
        # Class labels TODO account for more integer types properly
        if type(y[0]) == np.int64:
            self.gp_type = 'classification'
            return self.fit_classification(X, y)
    
        # Continuous outputs
        else:
            self.gp_type = 'regression'
            return self.fit_regression(X, y)

    def predict(self, x, keep_probs=False, parallel=False):

        # Split predict job over number of cores available-1!
        if parallel == True:
            return self.predict_parallel(x, keep_probs)

        if self.gp_type == 'classification':
            return self.predict_class(x, keep_probs)

        if self.gp_type == 'regression':
            return self.predict_regression(x)

    # Parallelise class prediction across available cores
    def predict_parallel(self, x, keep_probs):

        # Set up the parallel jobs on separate processes, to overcome 
        # Python's GIL for proper parallelisation
        nprocs = mp.cpu_count() - 1
        jobs = partition_indexes(x.shape[0], nprocs)
        args = [(x[start:end], keep_probs, False) for start, end in jobs]
        pool = Pool(processes=nprocs)
        print("Distributing predictions across {} processes...".format(nprocs))
        predict_results = pool.starmap(self.predict, args)
        # for results in predict_results:
        #     print("This round")
        #     print(results.shape)

        if keep_probs == True:
            # Concat along data points axis
            return np.concatenate(predict_results, axis=2)

        # Concat along class list axis
        return np.concatenate(predict_results, axis=0)

    ################################################################################
    ############################ Multi-Task Stuff ##################################
    ################################################################################

    # def fit_multi_task(self, X, y):
    #     self.N = self.X.shape[0]
    #     self.M = np.unique(y).shape[0]

    # def predict_multi_task(self, x):
    #     Kf
    #     Kx
    #     task_variances
    #     D = np.diag(task_variances)
    #     I = np.identity(Kf.shape[0]) # Not sure about shape of identity matrix here
    #     sigma = np.kron(Kf, Kx) + np.kron(D, I)

    #     means = np.kron(Kf, Kx).T.dot(np.inv(sigma)).dot(y)
    #     return means

    # # Returns lower triangular Cholesky decomposition for complete-data log-likelihood
    # def multi_task_L_ll(self):
    #     N = self.N
    #     M = self.M
    #     Kf = self.Kf_update()
    #     Kx = self.Kx()
    #     F = self.F()
    #     Y = self.Y()
    #     task_variances
    #     D = np.diag(task_variances)
    #     task_variances
    #     L_comp_ll = -N/2 * np.log(Kf) - M/2 * log(Kx) - 0.5 * np.trace(np.inv(Kf).dot(F.T).dot(np.inv(Kx).dot(F))) \
    #                         - N/2 np.sum(np.log(task_variances) - 0.5 * np.trace((Y-F).dot(np.inv(D)).dot((Y-F).T)) - M*N/2 * np.log(2*np.pi)) 
    #     return L_comp_ll

    # # Returns updated hyperparameters by finding argmin of the log likelihood
    # def multi_task_update_theta(self, thetas):
    #     res = minimize(self.multi_task_theta_ll, thetas, method='bfgs')
    #     return res['x']

    # # Returns updated hyperparams
    # def thetas(self):
    #     hyperparams
    #     Kx
    #     N = self.N
    #     F
    #     M = self.M
    #     theta_xs = N * np.abs(np.log(F.T.dot(np.inv(Kx)).dot(F))) + M * np.log(Kx)
    #     return theta_xs

    # # Returns updated K^f matrix
    # def Kf(self):
    #     hyperparams
    #     Kx
    #     N = self.N
    #     F
    #     Kf = 1/N * F.T.dot(np.inv(Kx)).dot(F)
    #     return Kf

    # # Returns updated noise over tasks
    # def task_noise(self):
    #     N = self.N
    #     Y
    #     F
    #     task_variances = 1/N * (Y-F).T.dot(Y-F)
    #     return task_variances

    # # Covariance functions over inputs
    # # NOTE stationary covariance functions as K^f explains variance
    # #   unit variance, (zero mean?)
    # def Kx(self, f_err, l_scales, n_err):
    #     # TODO follow NOTE from comment above function
    #     return self.K_se(f_err, l_scales, n_err)
    # 
    # # NxM matrix Y such that y = vecY
    # # y_il is response for l-th task on i-th input x_i
    # def Y(self):
    #     pass

    # # Vector of function values corresponding to Y
    # def F(self):
    #     pass
