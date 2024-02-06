# -*- coding: utf-8 -*-
"""
Created on Fri Mar 25 16:57:27 2022

@author: QCP32
"""
import numpy as np
from scipy.optimize import curve_fit

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

