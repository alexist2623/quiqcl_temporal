# -*- coding: utf-8 -*-
"""
Created on Fri Mar 18 08:40:04 2022

@author: QCP32
"""
################ Importing GUI Dependencies #####################
import os, time, sys
from PyQt5 import uic
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QFileDialog, QVBoxLayout, QPushButton
from PyQt5.QtCore    import pyqtSignal, QThread, QObject

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import configparser, pathlib

filename = os.path.abspath(__file__)
dirname = os.path.dirname(filename)
uifile = dirname + '/Micromotion_Minimizer.ui'
widgetdir = dirname + '/widgets/'

Ui_Form, QtBaseClass = uic.loadUiType(uifile)
version = "2.01"

from micromotion_minimizer_theme import micromotion_minimizer_theme_base

sys.path.append("C:/Users/QCP32/Documents/GitHub/QtDevice_Server/Client/gui/applications/m_minimizer/Libs")
from Micromotion_minimizer_runner import MicromotionRunner as MMR

#%%
class MicromotionMinimizer(QtWidgets.QMainWindow, Ui_Form, micromotion_minimizer_theme_base):
    
    _opened_module = False
    
    def __init__(self, device_dict=None, parent=None, theme="black"):
        QtWidgets.QMainWindow.__init__(self)
                
        # self.ccd = device_dict["ccd"]
        # self.sequencer = device_dict["sequencer"]
        
        self.parent = parent
        self._theme = theme
        
        self.runner = MMR(device_dict, self)
        # self.cp = self.parent.cp
        
        self.setupUi(self)
        self._initUi()
        self.setWindowTitle("Micromotion Minimizer v.%s" % version)
    #     self._initUi()
    #     self._connectSignals()
        
    #     self.scanner.readStagePosition()
    #     self.setWindowTitle("PMT Aligner v%s" % version)
    
    
    # def show(self):
    #     if not self._opened_module:
    #         self.openOpener()
        
    #     else:
    #         self.pmt_aligner_gui.show()
    
    # def initiateUi(self):
    #     try:
    #         self.pmt_aligner_gui = PMTAlginerGUI(self.device_dict, self, self._theme)
    #         self.pmt_aligner_gui.changeTheme(self._theme)
    #         self._opened_module = True
    #         self.show()
    #     except Exception as err:
    #         print(err)
        self.changeTheme(self._theme)
        
    def _initUi(self):
        self.canvas_weak, [self.im_weak_raw, self.im_weak_fit] = self._create_im_canvas(self.GBOX_RF_weak, 2)
        self.canvas_strong, [self.im_strong_raw, self.im_strong_fit] = self._create_im_canvas(self.GBOX_RF_strong, 2)
        
        self.canvas_rf, [self.rf_bar] = self._create_plot_canvas(self.GBOX_RF_photon, 1)
        self.canvas_hist, [self.hist_plot] = self._create_plot_canvas(self.GBOX_history, 1)
        
        
    def _create_im_canvas(self, frame, im_num=1):
        fig = plt.Figure(tight_layout=True)
        canvas = FigureCanvas(fig)
        
        layout = QVBoxLayout()
        layout.addWidget(canvas)
        frame.setLayout(layout)
        
        
        ax_list = []
        im_list = []
        
        for im_idx in range(im_num):
            ax = fig.add_subplot(1, im_num, im_idx+1)
            ax.set_xticks([])
            ax.set_yticks([])
            
            ax_list.append(ax)
      
        spine_list = ['bottom', 'top', 'right', 'left']
        
        if self._theme == "black":
            plt.style.use('dark_background')
            plt.rcParams.update({"savefig.facecolor": [0.157, 0.157, 0.157],
                                "savefig.edgecolor": [0.157, 0.157, 0.157]})
            
            fig.set_facecolor([0.157, 0.157, 0.157])
            
            for ax in ax_list:
                ax.set_facecolor([0.157, 0.157, 0.157])
                ax.tick_params(axis='x', colors=[0.7, 0.7, 0.7], length=0)
                ax.tick_params(axis='y', colors=[0.7, 0.7, 0.7], length=0)
            
                im = ax.imshow(np.zeros((3,3)), cmap="inferno")
                

                for spine in spine_list:
                    ax.spines[spine].set_color([0.7, 0.7, 0.7])
                    
                im_list.append(im)

        elif self._theme == "white":
            plt.style.use('default')
            plt.rcParams.update({"savefig.facecolor": [1, 1, 1],
                                "savefig.edgecolor": [1, 1, 1]})
            fig.set_facecolor([1, 1, 1])
            
            for ax in ax_list:
                ax.set_facecolor([1, 1, 1])
                ax.tick_params(axis='x', colors='k', length=0)
                ax.tick_params(axis='y', colors='k', length=0)
                
                im = ax.imshow(np.zeros((3,3)), cmap="viridis")
                
                for spine in spine_list:
                    ax.spines[spine].set_color('k')
                    
                im_list.append(im)
            
        return canvas, im_list
    
    def _create_plot_canvas(self, frame, num_axis=1):
        fig = plt.Figure(tight_layout=True)
        canvas = FigureCanvas(fig)
        
        layout = QVBoxLayout()
        layout.addWidget(canvas)
        frame.setLayout(layout)
        
        spine_list = ['bottom', 'top', 'right', 'left']

        ax_list = []
        
        # for idx_
        for idx_axis in range(num_axis):
            
            if idx_axis:
                ax = ax_list[0].twinx()
            else:
                ax = fig.add_subplot(1,1,1)

            if self._theme == "black":
                plt.style.use('dark_background')
                plt.rcParams.update({"savefig.facecolor": [0.157, 0.157, 0.157],
                                    "savefig.edgecolor": [0.157, 0.157, 0.157]})
                
                fig.set_facecolor([0.157, 0.157, 0.157])
                ax.set_facecolor([0.157, 0.157, 0.157])
                ax.tick_params(axis='x', colors=[0.7, 0.7, 0.7], length=0)
                ax.tick_params(axis='y', colors=[0.7, 0.7, 0.7], length=0)
                
                for spine in spine_list:
                    ax.spines[spine].set_color([0.7, 0.7, 0.7])
    
            elif self._theme == "white":
                plt.style.use('default')
                plt.rcParams.update({"savefig.facecolor": [1, 1, 1],
                                    "savefig.edgecolor": [1, 1, 1]})
                fig.set_facecolor([1, 1, 1])
                ax.set_facecolor([1, 1, 1])
                ax.tick_params(axis='x', colors='k', length=0)
                ax.tick_params(axis='y', colors='k', length=0)
                
                for spine in spine_list:
                    ax.spines[spine].set_color('k')
                
            ax_list.append(ax)
                
        return canvas, ax_list
        
    def setStyleSheet(self, stylesheet):
        self.styleSheetString = stylesheet
        # exec( "self.application_dict['%s'].setStyleSheet(self._theme_base[self._theme])" % (app))
        # exec( "self.application_dict['%s'].show()" % app)
        
    def toStatusBar(self, msg):
        self.statusbar.showMessage(msg)
        
    #%% slots
    def loadAgentTriggered(self):
        print(self.sender().objectName())
    
    def loadEnvironmentTriggered(self):
        print(self.sender().objectName())
    
    def saveButtonPressed(self):
        print(self.sender().objectName())
    
    def runButtonPressed(self):
        print(self.sender().objectName())
    
    def resetButtonPressed(self):
        print(self.sender().objectName())
    
    def loadButtonPressed(self):
        print(self.sender().objectName())