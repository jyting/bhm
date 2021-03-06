import numpy as np
from datetime import datetime
from ML.gp.poe import PoGPE
from ML.gp.gpoe import GPoGPE

from progressbar import ProgressBar
try:
    import matplotlib as mpl
    from matplotlib import pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    from matplotlib.patches import Rectangle
    # from utils.benchmarks import dm_test_data
    import matplotlib.cm as cm
    import matplotlib as mpl
    from matplotlib import colors
except:
    print("Failed to import matplotlib stuff. Check relevant libraries are installed if working from a headless server.")
import math
import pdb
from ML.gp import gp
from ML.gp import gp_gpy
from scipy.interpolate import spline
from scipy.stats import gaussian_kde
from utils import load_data

from utils.downsample import fixed_grid_blocksize

def plot_confidence(x, y, xnew, y_pred, sigma, title=None, filename='gp_with_variance_plot.pdf'):
    # Plot function, prediction, and 95% confidence interval based on MSE
    confidence = 1.9600
    # plt.plot(x, y, 'r:', label=u'$f(x) = x\, \sin(x)$')
    plt.scatter(x, y)
    plt.plot(xnew, y_pred, 'b-', label=u'Prediction')
    plt.fill(np.concatenate([xnew, xnew[::-1]]),
            np.concatenate([y_pred - confidence * sigma,
                (y_pred + confidence * sigma)[::-1]]),
            alpha=.3, fc='b', ec='None', label='95% confidence interval (1 standard deviation)')
    plt.xlabel('$x$ (inputs)')
    plt.ylabel('$y$ (outputs)')

    # plt.legend()
    if title != None:
        plt.title(title)

    plt.savefig(filename)
    clear_plt()

def plot_dm_stats(points, display=False, filename='dm_stats.pdf'):
    axes = points.shape[1]
    length = points.shape[0]
    colors = ['b', 'r', 'g', 'c']
    for col, c in zip(range(axes), colors):
        print('Scattering points for axis {}/{}...'.format(col+1, axes))
        plt.scatter(np.arange(length), points[:,col], color=c)

    print('Image generated, ', end='', flush=True)
    if display == False:
        print('saving...')
        plt.savefig(filename)
    else:
        print('displaying...')
        plt.display()

    clear_plt()

def plot_gp_stats(points, display=False, filename='gp_stats.pdf'):
    length = points.shape[1]
    colors = ['b', 'r', 'g', 'c']
    for row, c in zip(points, colors):
        plt.scatter(np.arange(length), row, color=c)

    if display == False:
        plt.savefig(filename)
    else:
        plt.display()

    clear_plt()

def scatter_arrays(points, display=False, filename='scatterplot.pdf', marker='x', c='b', labels=None):
    fig, ax = plt.subplots()
    if points.shape[1] == 4:
        ax.set_ylim(-0.1, 1.19)
        x = np.arange(1, points.shape[1]+1)
        ax.set_xticks(x)
    elif points.shape[1] > 4:
        ax.set_xlim(0, 25)
        x = np.concatenate((np.arange(1, 21), [22, 23, 24]))
        ax.set_xticks(x)
    ax.set_xlabel('label no.')
    ax.set_ylabel('f-score')
    
    colors = ['b', 'r', 'c', 'g']
    # for row, label, c in enumerate(points, labels, colors):

    print(x.shape)
    print(points[0].shape)

    # ax.plot(x, points, label=labels)
    # ax.scatter(np.repeat(x.T, 4, axis=0), points, s=20, lw=2, c=colors)
    for i in range(len(points)):
        ax.plot(x, points[i], label=labels[i], c=colors[i])
        ax.scatter(x, points[i], s=20, lw=2, marker=marker, c=colors[i])

    plt.legend(fontsize=11)
    # ax.set_ylim((points.min(), points.max()))
    if display == False:
        plt.savefig(filename)
    else:
        plt.display()

    clear_plt()

def plot_gp_with_variance(X, Y, x, y, y_pred, sigma, filename='gp_with_variance.pdf'):

    # Plot function, prediction, and 95% confidence interval based on MSE
    # confidence = 1.9600
    fig = plt.figure(figsize=(12,8))

    # plt.plot(x, y, 'r:', label=u'$f(x) = x\, \sin(x)$')

    # Training
    plt.plot(X, Y, 'bo', markersize=5, label=u'Observations')

    # Test actuals
    plt.plot(x, y, 'rx', markersize=5, label=u'Test', mew=2.0)

    # Predictions and variance
    plt.plot(x, y_pred, 'g-', label=u'Prediction', mew=2.0)
    plt.fill(np.concatenate([x, x[::-1]]),
            np.concatenate([y_pred - sigma,
                (y_pred + sigma)[::-1]]),
            alpha=0.2, fc='b', ec='None', label='95% confidence interval')

    # Axes labels
    plt.xlabel('$x$')
    plt.ylabel('$y$')

    # Handle logic of bounding graph on min/max of x/y coordinates
    y_mins = 1.1*np.array([np.min(Y), np.min(y), np.min(y_pred)])
    y_maxs = 1.1*np.array([np.max(Y), np.max(y), np.max(y_pred)])
    x_mins = 1.05*np.array([np.min(X), np.min(x)])
    x_maxs = 1.05*np.array([np.max(X), np.max(x)])
    plt.ylim(np.min(y_mins), np.max(y_maxs))
    plt.xlim(np.min(x_mins), np.max(x_maxs))

    # plt.legend(loc='upper left')
    plt.savefig(filename)
    clear_plt()
    # plt.show()

def show_all():
    # In a display backend
    backend = mpl.get_backend()
    print("Using backend {}".format(backend))
    if backend != 'agg':
        plt.show()
    # No display backend
    else:
        date = datetime.now()

    plt.savefig('images/{}.pdf'.format(date))

def generate_subplots(rows=1, columns=1, actual_count=1, title_list=None, with_fig=False, with_big_ax=False):
    fig = plt.figure()
    if with_big_ax == True:
        big_ax = fig.add_subplot(111)
    axs = [fig.add_subplot(rows, columns, i) for i in range(1, actual_count+1)]
    # fig, axs = plt.subplots(nrows=rows, ncols=columns, sharex=True, sharey=True)

    if title_list != None:
        for title, ax in zip(title_list, axs):
            ax.set_title(title)
            # ax.set_xlim(-2, 3)
            # ax.set_ylim(-2, 2)

    ret = axs

    if with_fig == True:
        ret = [ret]
        ret.append(fig)

    if with_big_ax == True:
        ret.append(big_ax)

    return ret 

def plot_test_graph():
    f_output1 = lambda x: 4. * np.cos(x/5.) - .4*x - 35. + np.random.rand(x.size)[:,None] * 2
    X1 = np.random.rand(100)[:,None]; X1=X1*75
    Y1 = f_output1(X1)
    fig = plt.figure(1)
    ax1 = fig.add_subplot(211)
    ax1.scatter(X1, Y1)
    # ax1.set_xlim(2, 3)
    # ax1.set_ylim(-5, 5)
    plt.show()

def plot_continuous(X, Y):
    if X.shape[1] == 2:
        x, y, z = X[:,0], X[:,1], Y

        fig = plt.figure()
        ax1 = fig.add_subplot(111, projection='3d')

        collection = ax1.scatter(x, y, z)
        plt.show()

    elif X.shape[1] == 1:
        x, y = X, Y

        fig = plt.figure()
        ax1 = fig.add_subplot(111)

        collection = ax1.scatter(x, y)
        plt.show()

def plot_classes(X, Y, Y_pred):
    if X.shape[1] == 3:
        x, y, z = X[:,0], X[:,1], X[:,2]

        # fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, projection='3d')
        fig = plt.figure()
        ax1 = fig.add_subplot(111, projection='3d')
        ax2 = fig.add_subplot(121, projection='3d')

        # ax3D_pred = fig.add_subplot(111, projection='3d')
        collection_p = ax1.scatter(x, y, z, c=Y_pred, cmap = cm.Spectral)

        # ax3D_r = fig.add_subplot(121, projection='3d', sharex=ax3D_pred)
        collection_r = ax2.scatter(x, y, z, c=Y, cmap=cm.Spectral)

        plt.colorbar(collection_p)
        plt.show()

    elif X.shape[1] == 2:
        x, y, = X[:,0], X[:,1]
        fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)

        # Predictions
        # Preds Plots
        pos_idx = np.nonzero(Y_pred==1)[0]
        neg_idx = np.array(list(set(list(np.arange(len(Y)))) - set(list(pos_idx))))
        x_pos = x[pos_idx]
        y_pos = y[pos_idx]
        x_neg = x[neg_idx]
        y_neg = y[neg_idx]

        Y_pred_pos = Y_pred[pos_idx]
        Y_pred_neg = Y_pred[neg_idx]
        # ax1.scatter(x, y, c=Y_pred)

        ax1.plot(x_pos, y_pos, 'o', color='y')
        ax1.plot(x_neg, y_neg, 'x', color='r')
        ax1.set_title('Predictions')

        # Actuals Plots
        pos_idx = np.nonzero(Y==1)[0]
        neg_idx = np.array(list(set(list(np.arange(len(Y)))) - set(list(pos_idx))))
        x_pos = x[pos_idx]
        y_pos = y[pos_idx]
        x_neg = x[neg_idx]
        y_neg = y[neg_idx]

        Y_pos = Y[pos_idx]
        Y_neg = Y[neg_idx]
        # ax2.scatter(x, y, c=Y)
        ax2.plot(x_pos, y_pos, 'o', color='y')
        ax2.plot(x_neg, y_neg, 'x', color='r')
        ax2.set_title('Observations')

        plt.show()

def scatter_map(locations, labels, filename='scattermap'):
    x_min = locations[:,0].min()
    x_max = locations[:,0].max()
    y_min = locations[:,0].min()
    y_max = locations[:,0].max()

    fig, ax = plt.subplots()
    if np.unique(labels).shape[0] == 1:
        im = ax.scatter(locations[:,0], locations[:,1], c='black', s=8, lw=0)
    else:
        im = ax.scatter(locations[:,0], locations[:,1], c=labels, cmap=cm.viridis, s=8, lw=0)
    ax.set_xlabel('$x$ coordinates')
    ax.set_ylabel('$y$ coordinates')

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    plt.savefig(filename+'.pdf')
    clear_plt()
    return im

def plot_toy_data(*args, **kwargs):
    print('Function removed. Use utils/visualisation.scatter_map_clusters')

def scatter_toymap_clusters(locations, title='Illustrative example plots', filename='tmp.pdf', display=False):
    """
    Plot the toy DM vs GP data to show clusters
    """
    x = locations[:,0]
    y = locations[:,1]

    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.scatter(x, y, c='grey', lw=0, s=8)
    ax.set_title(title)
    ax.annotate('cluster A', xy=(-4.5, 2.2), xytext=(-7.4, 0),
            arrowprops=dict(facecolor='black', shrink=0.05),
            )
    ax.annotate('cluster B', xy=(4.0, 2), xytext=(2, -1),
            arrowprops=dict(facecolor='black', shrink=0.05),
            )

    ax.annotate('cluster C', xy=(-2, -5), xytext=(0, -6),
            arrowprops=dict(facecolor='black', shrink=0.05),
            )

    ax.set_xlabel('$x$ coordinates')
    ax.set_ylabel('$y$ coordinates')

    # Show image
    if display == False:
        plt.savefig(filename)
    else:
        plt.show()
    clear_plt()

def scatter_multi_maps(locations, labels, filename='scattermap'):
    for i in range(labels.shape[1]):
        im = scatter_map(locations, labels[:,i], '{}_{}'.format(filename, i))
    
    standalone_colorbar(im, filename=filename+'_horz', orientation='horizontal', label='Label distributions')
    # standalone_colorbar(im, filename=filename+'_vert', orientation='vertical', label='Label distributions')
    clear_plt()

def show_map(locations, labels, x_bins=None, y_bins=None, display=False, filename='map', vmin=None, vmax=None, ax=None, hide_y=False, title=None, save_im=False, norm=None, show_cbar=True):
    """
    Given the x, y coord locations and corresponding labels, plot this on imshow (null points
    will be shown as blank in the background).
    """

    if (x_bins == None and y_bins == None):
        x_bins = np.unique(locations[:,0])
        y_bins = np.unique(locations[:,1])

    x_bins.sort()
    y_bins.sort()

    x_min = min(x_bins)
    x_max = max(x_bins)
    y_min = min(y_bins)
    y_max = max(y_bins)

    print('Prepating to plot {} points...'.format(locations.shape[0]))
    print("Creating x, y index map to determine where to plot...")
    x_bin_coord_map = dict( zip( x_bins, range(len(x_bins)) ) )
    y_bin_coord_map = dict( zip( y_bins, range(len(y_bins)) ) )

    print("Building coordinate matrix with NaNs except where actual measurements exist...")
    # X, Y = np.meshgrid(x_bins, y_bins)
    Z = np.zeros((y_bins.shape[0], x_bins.shape[0]))

    print("Assigning labels...")
    Z[:] = None
    x_locations = [x_bin_coord_map[x] for x, y in locations]
    y_locations = [y_bin_coord_map[y] for x, y in locations]
    Z[(y_locations, x_locations)] = labels

    cur_fig = plt if ax == None else ax
    in_ax = False if ax == None else True

    print("Setting colourbar (legend)...")
    cmap = cm.viridis
    # cmaplist = [cmap(i) for i in range(cmap.N)]
    # cmap = cmap.from_list('custom cmap', cmaplist, cmap.N)

    print("Bulding image...")
    # plt.imshow(Z, extent=[x_min, x_max, y_min, y_max], origin='lower', cmap=cmap, vmin=vmin, vmax=vmax)

    ###############
    # uniq_C = np.unique(labels)
    # # Can also take an Nx3 or Nx4 array of rgb/rgba values - will need for 24 case hmmm
    # # cmap = colors.ListedColormap(['blue', 'cyan', 'yellow', 'red'])
    # if uniq_C.shape[0] > 4:
    #     bounds=np.linspace(0,23,24)
    # else:
    #     bounds=np.linspace(0,3,4)
    # norm = colors.BoundaryNorm(bounds, cmap.N)
    ###############

    # norm = colors.LogNorm(Z.mean() + 0.5 * Z.std(), Z.max(), clip='True')

    # Adjust lower bound (0 is invalid) when using LogNorm for imshow
    if norm == mpl.colors.LogNorm:
        if vmin == 0:
            vmin += 1e-5
        norm = colors.LogNorm(vmin=vmin, vmax=vmax)

    # Display image
    im = cur_fig.imshow(Z, extent=[x_min, x_max, y_min, y_max], origin='lower', vmin=vmin, vmax=vmax, cmap=cmap, norm=norm)

    # Slightly hacky - unfortunately neeeded for 0-count argmaxs of 24 labels
    if np.unique(labels).shape[0] < 5:
        uniq_labels = np.arange(5)
    else:
        uniq_labels = np.arange(25)


    # plt.colorbar(cmap=cmap, norm=norm, spacing='Proportional', boundaries=bounds, format='%li')
    # mpl.colorbar.colorbar_factory(cur_fig, habitat_map)
    if in_ax == False:
        uniq = np.unique(labels).shape[0]
        if uniq > 4 and uniq <= 24:
            plt.colorbar(ticks=range(uniq))
        elif uniq == 4:
            bounds = np.linspace(uniq_labels.min()+1, uniq_labels.max(), uniq_labels.shape[0])
            norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
            plt.colorbar(im, ticks=bounds, cmap=cmap, norm=norm)
        elif show_cbar == True:
            plt.colorbar()

    # Setting axis labels
    xlabel = 'UTM x-coordinate, zone 51S'
    ylabel = 'UTM y-coordinate, zone 51S'
    axis_fontsize = 10
    if in_ax == True:
        ax.tick_params(axis='both', which='both', labelsize=8)
        ax.yaxis.tick_right()
        # print('Setting axis labels for subfig...')
        # cur_fig.set_xlabel(xlabel, fontsize=axis_fontsize)
        # cur_fig.set_ylabel(ylabel, fontsize=axis_fontsize)
    else:
        print('Setting axis labels...')
        cur_fig.xlabel(xlabel, fontsize=axis_fontsize)
        cur_fig.ylabel(ylabel, fontsize=axis_fontsize)
        if title != None:
            cur_fig.title(title, fontsize=12)
            print('Title set as: {}'.format(title))

    if hide_y == True:
        ax.get_yaxis().set_visible(False)

    print("Image generated!")
    if in_ax == True :
        return im
    elif display == True:
        cur_fig.show()
    elif save_im == True:
        cur_fig.savefig(filename + '.pdf')
        return im
    else:
        cur_fig.savefig(filename + '.pdf')

    clear_plt()

    # Create colourbar here if single (integer) labels are being predicted
    # if type(labels[0]) == np.int64:
    #     print('Creating colour bar...')
    #     standalone_colorbar(im, '{}_colourbar.pdf'.format(filename))

def multi_label_histogram(multi_labels):
    """
    Plots a histogram of how many classifications are contained within each label set
    """

    non_zero_labels = np.array([np.sum(labels != 0) for labels in multi_labels])
    bins = np.bincount(non_zero_labels)
    # plt.hist(bins[1:], bins.shape[0]-1)
    plt.hist(non_zero_labels, bins=range(1,bins.shape[0]), bottom=1)
    for i, txt in enumerate(bins):
        plt.annotate(str(txt), (i, 0), xytext=(i,-300), va='top', ha='center')
    plt.savefig('label_occurrences_full24classes.pdf')

def histogram(freqs, title=None, filename='freqs.pdf', offset=0):
    """
    Plots a histogram 
    """
    bins = np.arange(offset, freqs.shape[0]+offset)
    fig, ax = plt.subplots()
    ax.hist(bins, bins=bins - .5, weights=freqs, lw=0, color=['blue'])
    ax.set_xticks(bins[:-1])
    ax.set_xlim(1, freqs.shape[0])
    ax.set_xlabel('label number')
    ax.set_ylabel('no. of occurrences')

    if title != None:
        plt.title(title)
    # for i, txt in enumerate(freqs):
    #     plt.annotate(str(txt), (i, 0), xytext=(i,-300), va='top', ha='center')
    plt.savefig(filename)
    clear_plt()

def clear_plt(fig=None):
    """
    Clears pyplot caches/etc.
    """
    plt.cla()
    plt.clf()
    if fig != None:
        del(fig)

def plot_coords(locations, filename='tmp.pdf', display=True, lims=None):
    """
    Plots a given set of x,y coordinates.
    Locations are given as a list of (x,y) tuples
    """
    x = locations[:,0]
    y = locations[:,1]
    plt.scatter(x, y)
    if lims != None:
        plt.xlim(lims['x_min'], lims['x_max'])
        plt.ylim(lims['y_min'], lims['y_max'])
    if display == False:
        plt.savefig(filename)
    else:
        plt.show()

def plot_training_with_grid(locations, filename='training_map.pdf', display=True, reduction_factor=2):
    """
    Plots the training datapoints with fixed downsampling grid overlaid on top
    """
    _, _, _, _, _, _, reduced_x_coords, reduced_y_coords = fixed_grid_blocksize(locations, reduction_factor)
    fig = plt.figure()
    ax = fig.gca()
    # ax.set_xticks(reduced_x_coords)
    # ax.set_yticks(reduced_y_coords)
    # ax.set_yticks([])
    # ax.set_xticks([375000])
    plt.scatter(locations[:,0], locations[:,1])
    plt.grid(linestyle='dashed')
    plt.savefig(filename)

def plot_multilabel_distribution(labels, title='Multi-label distribution', filename='multilabel_distr.pdf', display=True):
    """
    Plot a histogram of the distribution of multi-labels (a single set)
    """
    x = np.arange(labels.shape[0]) # x-axis
    y1 = labels[:,0] # first label
    y2 = labels[:,1] # second label

    # fig = plt.figure() 
    # ax = fig.add_subplot(111)

    # ax.scatter(x, y1, c='b')
    # ax.scatter(x, y2, c='r')

    p1 = plt.bar(x, y1, color='r',  lw=0)
    p2 = plt.bar(x, y2, bottom=y1, color='b', lw=0)

    plt.title(title)

    # Show image
    if display == False:
        plt.savefig(filename)
    else:
        plt.show()

    clear_plt()

def plot_map(locations, labels, filename='map.pdf'):
    colours = ['b', 'g', 'r', 'c']
    for i, c in enumerate(colours):
        cur_idxs = np.where(labels == i)[0]
        plt.scatter(locations[:,0][cur_idxs], locations[:,1][cur_idxs], color=c)
    plt.savefig(filename)
    clear_plt()

def dm_pred_vs_actual(preds, actuals, title='DM predictions vs actuals', filename='dm_pred_plot', display=False):
    """
    Plots all the DM predictions vs actual for the distribution of labels at each point
    """
    x = np.arange(1, preds.shape[0]+1)
    colours = ['b', 'g', 'r', 'c', 'm', 'y', 'b', 'w']
    # cmap = cm.viridis
    # colours = [cmap(i) for i in range(cmap.N)]

    for i in range(preds.shape[1]):
        cur_preds = preds[:,i]
        cur_actuals = actuals[:,i]
        pred_scat = plt.scatter(x, cur_preds, marker='x', c=colours[i])
        actual_scat = plt.scatter(x, cur_actuals, marker='o', c=colours[i])
        plt.legend([pred_scat, actual_scat], ['Predictions', 'Actuals'])
        plt.title(title + str(i))

        if display == False:
            plt.savefig(filename+str(i)+'.pdf')
        clear_plt()

def gp_pred_vs_actual(y_distr, y_pred, sigma, display=False, filename='toy_gp_pred_plot_'):
    """
    Plots the predictions of a GP for a particular class (binary/OvA) with the variance highlighted
    """
    x = np.arange(1, y_distr.shape[0]+1)
    for i in range(y_pred.shape[0]):
        # Create y where positive is the 'current' label
        y = [1 if max(row) == row[i] else 0 for row in y_distr]

        # Test actuals
        test_actuals = plt.plot(x, y, 'rx', markersize=2, label=u'Test', mew=2.0)
    
        # Predictions and variance
        predictions = plt.plot(x, y_pred[i], 'g-', label=u'Prediction', mew=2.0)
        predictions = plt.plot(x, y_pred[i], 'g-', label=u'Prediction', mew=2.0)
        variance = plt.fill(np.concatenate([x, x[::-1]]),
                np.concatenate([y_pred[i] - sigma[i],
                    (y_pred[i] + sigma[i])[::-1]]),
                alpha=0.2, fc='b', ec='None', label='95% confidence interval')
    
        # Axes labels
        plt.xlabel('$x$')
        plt.ylabel('$y$')
        plt.legend([test_actuals[0], predictions[0], variance[0]], ['Test', 'Raw Predictions', 'Variance'])
    
        # plt.legend(loc='upper left')
        if display == False:
            plt.savefig(filename+str(i)+'.pdf')
        else:
            plt.show()
        clear_plt()

def standalone_toyplot_hist_legend(filename='toyplot_hist_distr_legend.pdf'):
    """
    Generates a standalone legend describing the histogram of the toy plots 
    """
    fig = plt.figure()
    figlegend = plt.figure(figsize=(4,3))
    ax = fig.add_subplot(111)
    bar1 = ax.bar(range(10), np.random.randn(10), color='r')
    bar2 = ax.bar(range(10), np.random.randn(10), color='b')
    x_descript = Rectangle((0, 0), 1, 1, fc="w", fill=False, edgecolor='none', linewidth=0)
    y_descript = Rectangle((0, 0), 1, 1, fc="w", fill=False, edgecolor='none', linewidth=0)
    figlegend.legend([x_descript, y_descript, bar1, bar2], ('x-axis - normalised ratio of label', 'y-axis - data point number', 'Label 0', 'Label 1'), 'center')

    figlegend.savefig(filename, bbox_inches='tight', pad_inches = 0)

def standalone_DM_colorbar_legend(filename='dm_plot_colorbar.pdf'):
    """
    Generates a standalone colorbar for the DM heatmaps
    """
    # TODO 
    fig = plt.figure()
    figlegend = plt.figure(figsize=(4,3))
    ax = fig.add_subplot(111)
    bar1 = ax.bar(range(10), np.random.randn(10), color='r')
    bar2 = ax.bar(range(10), np.random.randn(10), color='b')
    x_descript = Rectangle((0, 0), 1, 1, fc="w", fill=False, edgecolor='none', linewidth=0)
    y_descript = Rectangle((0, 0), 1, 1, fc="w", fill=False, edgecolor='none', linewidth=0)
    figlegend.legend([x_descript, y_descript, bar1, bar2], ('x-axis - normalised ratio of label', 'y-axis - data point number', 'Label 0', 'Label 1'), 'center')

    figlegend.savefig(filename, bbox_inches='tight', pad_inches = 0)

def plot_dm_chains(chains, filename='dm_mcmc_weights'):
    weight_count = chains.shape[1]
    x = np.arange(1, chains.shape[0]+1)
    rows = math.ceil(math.sqrt(chains.shape[1]))
    # axs = generate_subplots(rows=rows, columns=rows, actual_count=weight_count, title_list=None)
    for idx in range(weight_count):
        plt.plot(x, chains[:,idx])
        plt.savefig(filename+'_'+str(idx)+'.pdf')
        clear_plt()

def plot_dm_hists(chains, filename='dm_mcmc_weight_hist', cols=None, rows=None, xlims=None, ylims=None):
    """
    Plots histograms of each MCMC weight to visualise their distribution
    """
    # Determine layout of graphs on page
    if cols == None or rows == None:
        cols = np.round(math.sqrt(chains.shape[1]/2.51))
        rows = math.ceil(chains.shape[1]/cols)
        print(cols, rows)

    weight_count = chains.shape[1]

    axs, fig, big_ax = generate_subplots(rows=rows, columns=cols, actual_count=weight_count, with_fig=True, with_big_ax=True)
    # axs = generate_subplots(rows=rows, columns=cols, actual_count=weight_count, title_list=None)
    xlabel = 'weight values'
    ylabel = 'weight counts per x-axis value'
    big_ax.spines['top'].set_color('none')
    big_ax.spines['bottom'].set_color('none')
    big_ax.spines['left'].set_color('none')
    big_ax.spines['right'].set_color('none')
    big_ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
    big_ax.set_xlabel(xlabel, fontsize=14)
    big_ax.set_ylabel(ylabel, fontsize=14)

    # Generate necessary axes
    font = {'family' : 'normal',
            'weight' : 'normal',
            'size'   : 7}
    mpl.rc('font', **font)

    # Plot all graphs
    bar = ProgressBar(maxval=len(axs))
    bar.start()
    for i, ax in enumerate(axs):
        bar.update(i)
        n, bins, patches = ax.hist(chains[:,i], bins=50)

        # Only show x-axis for last plot in each *column*
        if i < weight_count - cols:
            ax.get_xaxis().set_visible(False)

        # Only show y-axis for left-most plots
        if (i+1) % cols != 0:
            ax.get_yaxis().set_visible(False)
        else:
            ax.yaxis.tick_right()

        if xlims != None:
            ax.set_xlim(xlims)
        if ylims != None:
            ax.set_ylim(ylims)
    bar.finish()

    # Save graphs
    # plt.tight_layout()
    plt.savefig(filename+'.pdf')
    mpl.rcdefaults()

    clear_plt()

def plot_dm_hists_multi(chains, filename='dm_mcmc_weight_hist', ylims=None):
    """
    Plot a large number of MCMC chains on a series of images each containing (c x r) MC chains
    """
    # 5x16 = 5x8 x 2
    # Convert chains to numpy array if not already to allow easier axis access
    # if type(chains) != np.ndarray:
    #     print('Converting chains to numpy array...')
    #     chains = np.array(chains)

    # Flatten each chain from a matrix of chains to access slices easily
    if len(chains) >= 3:
        print('Flattening chains with more than 2 dimensions...')
        chains = chains.reshape(len(chains), chains.shape[1] * chains.shape[2])

    # Organise MCMC chains into rows of 5 (up to 8 columns)
    h_max = 5
    v_max = 8

    # Calculate chain axes boundaries to plot per multi-histogram image
    bounds = np.arange(0, chains.shape[1], h_max * v_max)
    if bounds[-1] < chains.shape[1]:
        bounds = np.concatenate((bounds, [chains.shape[1]]))
    print('Full list of chains broken up into segments to print per multi-hist image: {}'.format(bounds))

    xlims = (chains.min(), chains.max())

    # Print each of the mcmc segments
    for i in np.arange(1, bounds.shape[0]):
        print('Now plotting hist plots {}/{}...'.format(i, bounds.shape[0]-1))
        plot_dm_hists(chains[:,bounds[i-1]:bounds[i]], '{}_{}'.format(filename, i), cols=h_max, rows=v_max, xlims=xlims, ylims=ylims)

def plot_multi_maps(q_locations, q_preds, filename='dm_simplelabel_heatmap', across=2, down=2, offset=None, title_list=None, vmin=None, vmax=None, norm=None, xticks=None, include_map=False, orientation='vertical'):
    """
    Plots heatmap for each label in data
    """
    dims = q_preds.shape[1]
    axs, fig, big_ax = generate_subplots(rows=down, columns=across, actual_count=dims, title_list=title_list, with_fig=True, with_big_ax=True)
    xlabel = 'UTM x-coordinates, zone 51S'
    ylabel = 'UTM y-coordinates, zone 51S'
    big_ax.spines['top'].set_color('none')
    big_ax.spines['bottom'].set_color('none')
    big_ax.spines['left'].set_color('none')
    big_ax.spines['right'].set_color('none')
    big_ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
    big_ax.set_xlabel(xlabel)
    big_ax.set_ylabel(ylabel)

    # fig.text(0.5, 0, xlabel, ha='center')
    # fig.text(0, 0.5, ylabel, va='center', rotation='vertical')
    # plt.tick_params(labelcolor='none', top='off', bottom='off', left='off', right='off')
    # plt.xlabel(xlabel)
    # plt.ylabel(ylabel)

    if vmin == None and vmax == None:
        vmin = q_preds.min()
        vmax = q_preds.max()
    bounds = {
        'vmin': vmin,
        'vmax': vmax
    }

    for i, ax in enumerate(axs):
        hide_y_labels = True if i%2 == 0 else False
        im = show_map(q_locations, q_preds[:,i], ax=ax, hide_y = hide_y_labels, norm=norm, **bounds)
        if offset != None:
            ax.set_title('label {}'.format(offset+i))
        elif title_list != None:
            ax.set_title(title_list[i])
        else:
            raise ValueError('plot_multi_maps function needs either an offset or title list!')

    fig.tight_layout()
    plt.savefig(filename+'.pdf')

    if (title_list == None and q_preds.shape[1] <= 4) or include_map == True:
        print('Also creating colour bar...')
        standalone_colorbar(im, filename=filename, xticks=xticks, orientation=orientation)
        clear_plt()
    # elif include_map == True:
    #     fig.colorbar(big_ax)
    #     clear_plt()
    else:
        clear_plt()

    return im

def plot_dm_per_label_maps_multi(q_locations, q_preds, filename='dm_alllabels_heatmap'):
    """
    Creates multiple multi-heatmap images for the 24-label case
    """
    label_map={1:0,2:0,3:1,4:3,5:1,6:3,7:3,8:3,9:3,10:1,11:3,12:3,13:2,14:2,15:2,16:1,17:1,18:0,19:1,20:0,21:0,22:1,23:0,24:0}

    vmin = q_preds.min()
    vmax = q_preds.max()
    # vmin=0
    # vmax=1

    multimap_kwargs = {'vmin': vmin, 'vmax': vmax, 'norm': mpl.colors.LogNorm}

    step = 4
    if 24 % step != 0:
        raise ValueError('step size needs to divide into 24 perfectly!')
    across = 2
    down = int(step/across)
    step_locs = np.arange(0,24,step)
    for idx, i in enumerate(step_locs):
        title_set = ['label {} ({})'.format(i, label_map[i+1]) for i in range(i, i+step)]
        cur_filename = '{}_{}-{}'.format(filename, i, i+step-1)
        print(cur_filename)
        im = plot_multi_maps(q_locations, q_preds[:,i:i+step], cur_filename, 
                across=across, down=down, title_list=title_set, **multimap_kwargs)

    # plot_multi_maps(q_locations, q_preds[:,:6],       '{}_1-6'.format(filename), across=2, down=3, title_list=title_set1, **bounds)
    # plot_multi_maps(q_locations, q_preds[:,6:12],     '{}_7-12'.format(filename), across=2, down=3, title_list=title_set2, **bounds)
    # plot_multi_maps(q_locations, q_preds[:,12:18],    '{}_13-18'.format(filename), across=2, down=3, title_list=title_set3, **bounds)
    # im = plot_multi_maps(q_locations, q_preds[:,18:], '{}_19-24'.format(filename), across=2, down=3, title_list=title_set4, **bounds)
    clear_plt()

    standalone_colorbar(im, filename)
    clear_plt()

def standalone_multioutput_colorbar(vmin=0, vmax=1, filename='dm_standalone_colorbar.pdf', title='Dirichlet Multinomial Regression Colour Bar'):
    """
    Standalone colorbar for multi-output distributions (scale from 0 to 1)
    """
    fig = plt.figure(figsize=(8, 1))
    # fig.subplots_adjust(left=0, right=0.2, bottom=0, top=0.2)
    ax = fig.add_axes([0.05, 0.50, 0.9, 0.15])
    cmap = cm.viridis
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
    cb1 = mpl.colorbar.ColorbarBase(ax, cmap=cmap, norm=norm, orientation='horizontal')
    ax.set_title(title)
    plt.savefig(filename)
    clear_plt()

def standalone_label_colorbar(label_count=24, filename='label_standalone_colorbar.pdf', title='Label Colourbar'):
    """
    Standalone colorbar for discrete labels
    """
    fig = plt.figure(figsize=(8, 1))
    ax = fig.add_axes([0.05, 0.50, 0.9, 0.15])

    cmap = cm.viridis
    cmaplist = [cmap(i) for i in range(cmap.N)]
    cmap = cmap.from_list('custom cmap', cmaplist, cmap.N)
    bounds = np.linspace(1, label_count, label_count)
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    cb1 = mpl.colorbar.ColorbarBase(ax, cmap=cmap, norm=norm, spacing='Uniform', format='%li', orientation='horizontal')
    ax.set_title(title)
    plt.savefig(filename)

    clear_plt()

def standalone_colorbar(im, filename, orientation='horizontal', label=None, xticks=None):
    if orientation=='horizontal':
        fig = plt.figure(figsize=(8, 1))
        cax = fig.add_axes([0.05, 0.50, 0.9, 0.15])
    else:
        fig = plt.figure(figsize=(1, 8))
        cax = fig.add_axes([0.03, 0.03, 0.3, 0.95])

    cb = fig.colorbar(im, cax=cax, orientation=orientation)
    if xticks != None:
        cb.set_ticks(xticks)

    if label != None:
        cb.set_label(label)
    # font = {'family' : 'normal',
    #         'weight' : 'normal',
    #         'size'   : 7}
    # mpl.rc('font', **font)
    plt.savefig('{}_colourbar.pdf'.format(filename))
    print('colour bar for {} created!'.format(filename))
    clear_plt()
    mpl.rcdefaults()

def plot_multiple_axes(points, labels = None, filename='multi_plots.pdf'):
    """
    Takes arguments (points, filename<optional>).
    Scatter plots data points in the shape (N, K), where N is the number of points.
    """
    if labels != None and labels[0][0] == np.int64:
        # need to make discrete colour bar
        pass

    colors = ['c', 'b', 'r', 'y', 'g']
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.ticklabel_format(useOffset=False)
    for i in range(points.shape[1]):
        print('Plotting axis {} of {}...'.format(i+1, points.shape[1]))
        x = points.shape[0]
        y = points[:,i]
        ax.scatter(np.arange(x), y, c=colors[i], s=3, lw=0)
    plt.savefig(filename)
    clear_plt(fig)

def plot_training_with_colours(locations, labels, filename='training_plots.pdf'):
    """
    Plots a given set of x,y coordinates with corresponding labels.
    Locations are given as a list of (x,y) tuples
    """
    x_min = locations[:,0].min()
    x_max = locations[:,0].max()
    y_min = locations[:,1].min()
    y_max = locations[:,1].max()
    plt.xlim(x_min, x_max)
    plt.ylim(y_min, y_max)

    colours4 = ['b', 'c', 'y', 'r']
    colours = np.full(labels.shape[0], None, str)
    # for c, cur_label in zip(colours4, np.unique(labels)):
    #     cur_idxs = np.where(labels == cur_label)[0]
    #     colours[cur_idxs] = c
    plt.scatter(locations[:,0], locations[:,1], s=1, lw=0, c=labels, cmap=discrete_cmap(4, 'jet'))
    
    plt.colorbar(ticks=[2,8,4,9], spacing='Proportional')
    plt.xlabel('UTM x-coordinate, zone 51S')
    plt.ylabel('UTM y-coordinate, zone 51S')

    plt.tight_layout()
    plt.savefig(filename)
    clear_plt()

def discrete_cmap(N, base_cmap=None):
    """Create an N-bin discrete colormap from the specified input map"""

    # Note that if base_cmap is a string or None, you can simply do
    #    return plt.cm.get_cmap(base_cmap, N)
    # The following works for string, None, or a colormap instance:

    base = plt.cm.get_cmap(base_cmap)
    color_list = base(np.linspace(0, 1, N))
    cmap_name = base.name + str(N)
    return base.from_list(cmap_name, color_list, N)

def bathymetry_survey_example():
    pass

def MAP_example(filename='MAP_example.pdf'):
    """
    Plots a basic example of what Maximum a Posteriori estimation does
    """
    data = [1.3]*3 + [2.5]*2 + [3.5]*8 + [4.5]*3 + [5.5]*1 + [6.5]*2
    density = gaussian_kde(data)
    xs = np.linspace(0,8,200)
    density.covariance_factor = lambda : .25
    density._compute_covariance()
    xs_densities = density(xs)

    max_freq_point = xs[xs_densities.argmax()]

    fig, ax = plt.subplots()

    ax.set_xlabel('$x$-values')
    ax.set_ylabel('Posterior distrubtion')

    ax.plot(xs,xs_densities)
    ax.plot((max_freq_point, max_freq_point), (0, 0.5), 'k--')
    ax.annotate('MAP for x', xy=(max_freq_point, 0.3), xytext=(max_freq_point+1, 0.295),
            arrowprops=dict(facecolor='black', shrink=0.05),
            )

    plt.savefig(filename)
    clear_plt()
    
    return xs_densities

def ova_example(filename='ova_example.pdf'):
    """
    Plots a simple set of data to show how one-vs-all approaches would segragate data. Due
    to the clear separation of each cluster, it resembles an example of the boundaries of a
    2D SVM.
    """
    X1, X2, X3 = load_data.generate_toy_clusters()

    fig, ax = plt.subplots()
    ax.scatter(X3[:,0], X3[:,1], c='g', cmap=cm.viridis, label='class 1')
    ax.scatter(X2[:,0], X2[:,1], c='b', cmap=cm.viridis, label='class 2')
    ax.scatter(X1[:,0], X1[:,1], c='r', cmap=cm.viridis, label='class 3')
    ax.set_xlim(-10, 10)
    ax.set_ylim(-10, 10)
    ax.plot((-6, 2), (-10,10), 'g-')
    ax.plot((6, -2), (-10,10), 'b-')
    ax.plot((-10, 10), (0, 0), 'r-')
    ax.set_xlabel('$x$-coordinate')
    ax.set_ylabel('$y$-coordinate')

    plt.legend(loc='lower right')

    plt.savefig(filename)
    clear_plt()

def smooth_pred(x, y_pred, v_pred):
    """
    Uses splining to smooth a sequence of data (to make non-jittery plots)
    """
    xnew = np.linspace(x.min(), x.max(), 300)
    yp_smooth = spline(x.flatten(), y_pred, xnew)
    vp_smooth = spline(x.flatten(), v_pred, xnew)
    return yp_smooth, np.abs(vp_smooth)

def plot_illustrative_gp_hparams(x=None, filename='gp_sample_plot.pdf'):
    """
    Multiple plots of a GP on some hard-coded data with varying hyper parameters (signal variance,
    length scales, noise variance) to show their effect on the model and predictions
    """
    def f(x):
        return 5*np.sin(x) + np.random.normal(scale=0.4, size=len(x))[:,np.newaxis]**2

    if x == None:
        x = np.linspace(1, 10, 30).reshape(-1, 1)
    y = f(x)

    x = np.array([-7, -6, -5.5, -4.9, -2.5, -2.4, -2.0, -1.5, -0.5, 0.3, 0.4, 0.5, 2.3, 2.5, 4.0, 4.1, 5.0, 6.0, 6.5]).reshape(-1, 1)
    y = np.array([-1.8, 0, 0.3, -0.9, -1.3, -1.2, 0.4, 1.6, 1.9, 0.0, -0.9, -1.1, -2.7, -2.2, -1.2, -1.0, -1.5, -1.0, -0.8]).reshape(-1, 1)
    xnew = np.linspace(x.min(), x.max(), 300).reshape(-1, 1)

    gp_model = gp.GaussianProcess
    # gp_model = gp_gpy.GPR

    # gpr1 = gp_model()
    gpr1 = PoGPE(15)
    gpr1.fit(x, y)
    y1, v1 = gpr1.predict(xnew)
    y1 = np.average(y1, axis=1); v1 = np.average(v1, axis=1)
    # y1, v1 = smooth_pred(x, y1, v1)
    # print("The fitted GP's stats were: ferr:{} l_scale:{} nerr:{}".format(gpr1.f_err, gpr1.l_scales, gpr1.n_err))
    print(gpr1)
    # 2.435308763334455 l_scale:[ 0.81049339] nerr:0.0

    # gpr2 = gp_model()
    gpr2 = GPoGPE(15)
    gpr2.fit(x, y, False)
    # gpr2.set_hps(ferr=2, lscales=2.7, nerr=0.5)
    y2, v2 = gpr2.predict(xnew)
    y2 = np.average(y2, axis=1); v2 = np.average(v2, axis=1)
    # y2, v2 = smooth_pred(x, y2, v2)

    gpr3 = gp_model()
    gpr3.fit(x, y, False)
    gpr3.set_hps(ferr=1, lscales=0.3, nerr=0.001)
    y3, v3 = gpr3.predict(xnew)
    # y3, v3 = smooth_pred(x, y3, v3)

    # gpr4 = gp.GaussianProcess()
    # gpr4.fit(x, y)
    # gpr4.f_err = 3
    # gpr4.l_scales = 1
    # gpr4.n_err = 0.1
    # y4, v4 = gpr4.predict_regression(xnew)
    
    plot_confidence(x, y, xnew, y1, np.sqrt(v1), title=None, filename='gp_with_variance_plot1.pdf')
    plot_confidence(x, y, xnew, y2, np.sqrt(v2), title=None, filename='gp_with_variance_plot2.pdf')
    plot_confidence(x, y, xnew, y3, np.sqrt(v3), title=None, filename='gp_with_variance_plot3.pdf')

    return (y1, v1), (y2, v2), (y3, v3)

def plot_multiple_arrays(data, filename='multi_plot.pdf', datatype='variance'):
    fig, ax = plt.subplots()
    colors = [cm.viridis.colors[0], cm.viridis.colors[90], cm.viridis.colors[180]]
    clust_dict = {0: 'A', 1: 'B', 2: 'C'}
    for i in range(data.shape[1]):
        ax.plot(range(data.shape[0]), data[:,i], c=colors[i], label='Cluster {}'.format(clust_dict[i]))

    ax.set_ylabel(datatype)
    ax.set_xlabel('n-th data point in cluster')

    #TODO legend
    plt.legend(loc='upper right')

    plt.savefig(filename)
    clear_plt()
