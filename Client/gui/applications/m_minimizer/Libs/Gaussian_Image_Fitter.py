# -*- coding: utf-8 -*-
"""
Created on Mon Aug  9 20:41:47 2021

@author: QCP32
"""

import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import numpy as np


# Gaussian 2D elliptical fitting. the coupling (or rotating) coefficient(b) is usually small.
# To fit, the function returns a vector.
def Gaussian_2D_elliptic(idx_arr, x_0, y_0, A, B, a, b, c):
    x, y = idx_arr
    result = A*np.exp(-(a*(x-x_0)**2 + 2*b*(x-x_0)*(y-y_0) + c*(y-y_0)**2)) + B
    return result.flatten()


def Gaussian_fitter(im_array, guess_a = 0.3, guess_b = 0.001, guess_c = 0.3):
    
    guess_y, guess_x = np.unravel_index(np.argmax(im_array), im_array.shape)
    
    guess_B = np.min(im_array)
    guess_A = np.max(im_array) - guess_B
        
    arr_x = np.arange(im_array.shape[0])
    arr_y = np.arange(im_array.shape[1])
    
    
    popt, pcov = curve_fit(Gaussian_2D_elliptic, 
                           np.meshgrid(arr_x, arr_y),
                           im_array.flatten(),
                           p0 = [guess_x, guess_y, guess_A, guess_B, guess_a, guess_b, guess_c])
    
    
    return popt, pcov

def figure_savor(ccd_im, fit_im, save_file, figure_view = False):        
    if figure_view: plt.ioff() # plt figure will not be shown. interaction off.
    else:           plt.ion()  # plt figure will be shown.
    
    fig = plt.figure()
    org_ax = fig.add_subplot(121)
    fit_ax = fig.add_subplot(122)
    
    # original image.
    org_ax.set_title("CCD image")
    org_ax.contourf(ccd_im)
    
    ccd_y, ccd_x = np.unravel_index(np.argmax(ccd_im), ccd_im.shape).astype(np.int16)
    org_ax.set_xlim(ccd_x - 6, ccd_x + 6)
    org_ax.set_ylim(ccd_y - 6, ccd_y + 6)


    # fitted image.
    fit_ax.set_title("Fitted image")
    fit_ax.contourf(fit_im)
    
    fit_y, fit_x = np.unravel_index(np.argmax(fit_im), fit_im.shape).astype(np.int16)
    fit_ax.set_xlim(fit_x - 6, fit_x + 6)
    fit_ax.set_ylim(fit_y - 6, fit_y + 6)

    try:
        fig.save_fig(save_file, dpi=150)
        print("Save done.")
    except Exception as e:
        print("Save failed with following exception: %s" % e)
    
    return
    

    
    