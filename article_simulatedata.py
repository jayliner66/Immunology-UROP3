'''
Created on Aug 10, 2014

@author: jonaswallin

BayesFlow is available at https://github.com/JonasWallin/BayesFlow/.

'''
from __future__ import print_function, division
import sys
import numpy as np
import numpy.random as npr
import pandas as pd
import random

from BayesFlow.src.PurePython import GMM
from BayesFlow.src.PurePython.distribution import wishart
from BayesFlow.src import utils as util


def simulate_data_v2(n_cells, n_persons, seed=None, silent=True):
    """
        simulating a larger data sets for article
    """

    sigmas = np.load('covs_.npy')
    thetas = np.load('means_.npy')
    weights = np.load('weights_.npy')
    weights /= np.sum(weights)

    df = pd.DataFrame(data=thetas)
    # print(df)
    # print(sigmas.shape)
    df_sig = pd.DataFrame(data=sigmas[:,:,0])
    # print(df_sig)

    if not silent:
        print("preprocsseing sigma:", end='')
        sys.stdout.flush()
    sigma_theta = []
    for sigma in sigmas:
        var_ = np.sort(np.linalg.eig(sigma)[0])
        z_sigma = var_[0] * npr.randn(*sigma.shape)
        sigma_theta.append(0.1*(sigma + np.dot(z_sigma.T, z_sigma)))

    if not silent:
        print("done")
        sys.stdout.flush()

    nu = 100
    ratio_act = np.array([1.,  0.5,  0.5,  0.5,  0.5,  1,  1,
                          1,  1,  1,  1,  1])
    ratio_act = np.ones(ratio_act.shape)  # warning warning test
    Y, act_Class, mus, x = simulate_data_(thetas=thetas,
                                          sigma_theta=sigma_theta,
                                          sigmas=sigmas,
                                          weights=weights,
                                          nu=nu,
                                          ratio_act=ratio_act,
                                          n_cells=n_cells,
                                          n_persons=n_persons,
                                          seed=seed,
                                          silent=silent)

    return Y, act_Class, mus, thetas, sigmas, weights, x


def simulate_data_(thetas, sigma_theta, sigmas, weights, nu=100, ratio_act=None, n_cells=5*10**4, n_persons=40,
                   seed=None, silent=True):
    """
        simulating data given:
        *thetas*      list of latent means
        *sigma_theta* variation between the means
        *sigmas*      list of latent covariances
        *weights*     list of probabilites
        *nu*          inverse wishart parameter
        *ratio_act*     probabilility that the cluster is active at a person
        *n_cells*     number of cells at a person
        *n_persons*   number of persons
        *seed*        random number generator
    """

    if seed is None:
        npr.seed(seed)

    K = len(weights)
    dim = thetas[0].shape[0]
    if ratio_act is None:
        ratio_act = np.ones(K)

    act_class = np.zeros((n_persons, K))
    for i in range(K):
        act_class[:np.int(np.ceil(n_persons * ratio_act[i])), i] = 1.
    # print(act_class)
    Y = []
    x = []
    nu = 100
    mus = []

    for i in range(n_persons):

        if not silent:
            print("setting up person_{i}: ".format(i=i), end='')
            sys.stdout.flush()

        mix_obj = GMM.mixture(K=np.int(np.sum(act_class[i, :])))
        theta_temp = []
        sigma_temp = []
        for j in range(K):
            if act_class[i, j] == 1:
                theta_temp.append(thetas[j] + util.rmvn(np.zeros((dim, 1)), sigma_theta[j]))
                sigma_temp.append(wishart.invwishartrand(nu, (nu - dim - 1) * sigmas[j]))
            else:
                theta_temp.append(np.ones(dim) * np.NAN)
                sigma_temp.append(np.ones((dim, dim)) * np.NAN)
        theta_temp_ = [theta_temp[aC] for aC in np.where(act_class[i, :] == 1)[0]]
        sigma_temp_ = [sigma_temp[aC] for aC in np.where(act_class[i, :] == 1)[0]]

        mix_obj.mu = theta_temp_
        mus.append(theta_temp)
        mix_obj.sigma = sigma_temp_

        p_ = np.array([(0.2*np.random.rand() + 0.9) * weights[aC] for aC in np.where(act_class[i, :] == 1)[0]])
        p_ /= np.sum(p_)
        mix_obj.p = p_
        mix_obj.d = dim
        #Y_, x_ =  mix_obj.simulate_data2(np.int(np.floor(0.99*n_cells)))
        Y_, x_ = mix_obj.simulate_data2(n_cells)

        noise_variance = np.eye(mix_obj.d)
        np.fill_diagonal(noise_variance, np.var(Y_, 0))
        #Y_noise = npr.multivariate_normal(np.mean(Y_, 0), noise_variance, size = np.int(np.ceil(0.01*n_cells)))
        #Y_ = np.vstack((Y_, Y_noise))
        #np.random.shuffle(Y_)
        Y.append(Y_)
        x.append(x_)

        if not silent:
            print("done")
            sys.stdout.flush()

    mus = np.array(mus)

    return Y, act_class, mus.T, x

if __name__ == "__main__":

    import matplotlib.pyplot as plt
    n_persons = 20
    seed = 123456
    n_cells = 10**4
    Y, act_Class, mus, thetas, sigmas, weights, x = simulate_data_v2(n_cells=n_cells, n_persons=n_persons, seed=seed)
    K = len(thetas[:, 0])
    color = plt.cm.rainbow(np.linspace(0, 1, K))
    for k in range(4):
        plt.figure()
        for j in range(mus.shape[1]):
            plt.text(thetas[j, 2*k], thetas[j, 2*k + 1], str(j), color=color[j],  fontsize=14)
        for i in range(n_persons):
            for j in range(mus.shape[1]):
                plt.scatter(mus[2*k, j, i], mus[2*k + 1, j, i], color=color[j], s=4)
    # plt.show()
    for i in range(n_persons):
        weights = np.load('weights_.npy')
        weights /= np.sum(weights)
        print(random.choices([0,1,2,3,4,5,6,7,8,9,10], weights=weights, k=1))
