import GPy
import numpy as np
from helpers import roc_auc_score_multi
from helpers import binarised_labels_copy

def gpy_bin_predict(features, labels):
    m = GPy.models.GPClassification(features[train_idx], labels_simple[train_idx])
    probs = m.predict(features_sn[test_idx])[0].T[0,:]

def gpy_bench(features, labels, train_idx):
    test_idx = np.array(list(set(np.arange(16502)) - set(train_idx)))
    # labels_simple = labels_simple.reshape(labels_simple.shape[0], 1)

    pred_probs = []
    uniq_labels = np.unique(labels)
    for c in uniq_labels:
        cur_bin_labels = binarised_labels_copy(labels, c)
        m = GPy.models.GPClassification(features[train_idx], labels_simple[train_idx])
        probs = m.predict(features_sn[test_idx])[0].T[0,:]
        pred_probs.append(probs)

    pred_probs = np.array(pred_probs).reshape(uniq_labels.shape[0], test_idx.shape[0])
