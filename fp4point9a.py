import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import numpy as np
from scipy.stats import rayleigh

from FPUtilGUI import GUI
import FPUtil
import re

def main(app):

    hermiteOrderX = tk.StringVar(value="1")
    hermiteOrderY = tk.StringVar(value="1")

    def getHermiteOrderX():
        try:
            return int(hermiteOrderX.get())
        except ValueError:
            return 1

    def getHermiteOrderY():
        try:
            return int(hermiteOrderY.get())
        except ValueError:
            return 1

    def paramFromName(name):
        m = re.search(r"L=(\d+(?:[.,]\d+)?)\s*cm", name)
        return float(m.group(1).replace(",", ".")) if m else None

    def fitGaussianCurve(parent):
        data=app.get_data().T
        if data is None:
            messagebox.showinfo("Error", "Please select a data file")
            return
        xaxis = np.linspace(0, stop=len(data[0]), num=len(data[0]))
        popt1, perr1 = FPUtil.gaussianBeamIntensityFit([xaxis, data[0]], 400000, np.argmax(data[0]), 20, 0)
        popt2, perr2 = FPUtil.gaussianBeamIntensityFit([xaxis, data[1]], 400000, np.argmax(data[1]), 20, 0)
        ax1 = app.fig.axes[0]
        ax2 = app.fig.axes[1]
        ax1.plot(xaxis, FPUtil.gaussianBeamIntensityCurve(xaxis, *popt1), "red")
        ax2.plot(xaxis, FPUtil.gaussianBeamIntensityCurve(xaxis, *popt2), "blue")
        app.fig.canvas.draw()
        app.set_results(
            f"Fitting results: \n"
            f"A_x = {popt1[0]} ± {perr1[0]}; A_y = {popt2[0]} ± {perr2[0]} \n"
            f"mu_x ={popt1[1]} ± {perr1[1]}; mu_y = {popt2[1]} ± {perr2[1]} \n"
            f"w_x ={popt1[2]} ± {perr1[2]}; w_y = {popt2[2]} ± {perr2[2]} \n"
            f"c_x ={popt1[3]} ± {perr1[3]}; c_y = {popt2[3]} ± {perr2[3]}"
        )
        return

    def singleGaussianView(axes,data):
        data=data.T
        ax1, ax2 = axes
        ax1.plot(data[0],'b')
        ax2.plot(data[1],'r')
        ax1.grid()
        ax1.title.set_text("Zeilen")
        ax2.title.set_text("Spalten")
        ax1.set_xlabel("Pixel")
        ax2.set_xlabel("Pixel")
        ax1.set_ylabel("Intensität")
        ax2.set_ylabel("Intensität")
        ax2.grid()

    def singleGaussianControls(parent,app):
        tk.Button(parent, text="Fit Gaussian Curve", command=lambda: fitGaussianCurve(parent)).pack(side=tk.LEFT, padx=10,pady=5)

    def beamWidth(axes,datasets):
        ax = axes[0]
        names,valuesX,valuesXerr,valuesY,valuesYerr,params = [],[],[],[],[],[]
        pixelSize = 6.3
        #lengthErr = 0.1/np.sqrt(3)

        for key,name,path,data in datasets:
            data = data.T
            xaxis= np.linspace(0, stop=len(data[0]), num=len(data[0]))
            try:
                popt1, perr1 = FPUtil.gaussianBeamIntensityFit([xaxis, data[0]], 400000, np.argmax(data[0]), 20, 0)
                popt2, perr2 = FPUtil.gaussianBeamIntensityFit([xaxis, data[1]], 400000, np.argmax(data[1]), 20, 0)
                valuesX.append(np.abs(popt1[2])*pixelSize)
                valuesXerr.append(np.abs(perr1[2])*pixelSize)
                valuesY.append(np.abs(popt2[2])*pixelSize)
                valuesYerr.append(np.abs(perr2[2])*pixelSize)
            except Exception:
                valuesX.append(np.nan)
                valuesXerr.append(np.nan)
                valuesY.append(np.nan)
                valuesYerr.append(np.nan)
            names.append(name)
            params.append(paramFromName(name))

        lengthErr = [0.1/np.sqrt(3) for i in valuesXerr]

        if all(p is not None for p in params):
            order = np.argsort(np.array(params))
            ax.scatter(np.array(params)[order], np.array(valuesX)[order],marker="o",color="blue")
            ax.scatter(np.array(params)[order], np.array(valuesY)[order],marker="o",color="red")
            ax.scatter(np.array(params)[order],(np.array(valuesX)[order]+np.array(valuesY)[order])/2,marker="o",color="green")
            ax.errorbar(np.array(params)[order], np.array(valuesX)[order], yerr=np.array(valuesXerr)[order], xerr=lengthErr, fmt="o", capsize=2, label="Messdaten",color="blue")
            ax.errorbar(np.array(params)[order], np.array(valuesY)[order], yerr=np.array(valuesYerr)[order], xerr=lengthErr, fmt="o", capsize=2, label="Messdaten",color="red")
            ax.errorbar(np.array(params)[order], (np.array(valuesX)[order]+np.array(valuesY)[order])/2, yerr=np.sqrt(np.array(valuesXerr)[order]**2+np.array(valuesYerr)[order]**2), xerr=lengthErr, fmt="o", capsize=2, label="Messdaten", color="green")
            ax.set_xlabel("Resonatorlänge in cm")
            ax.set_ylabel("Strahlbreite in μm")
        else:
            ax.plot(range(len(valuesX)), valuesX, "o-")
            ax.plot(range(len(valuesY)), valuesY,"o-")
            ax.set_xticks(range(len(names)))
            ax.set_xticklabels(names, rotation=45, ha="right")
            ax.set_xlabel("Datensatz")

        text = ([f"w_x={valuesX[i]:.4g}±{valuesXerr[i]:.4g}  " + f"w_y={valuesY[i]:.4g}±{valuesYerr[i]:.4g}"+  f" w_mean={((valuesX[i]+valuesY[i])/2):.4g}±{(np.sqrt(valuesXerr[i]**2+valuesYerr[i]**2)):.2g} \n" for i in range(len(valuesX))])
        app.set_results(text)

    def beamWidthControls(parent,app):
        tk.Button(parent, text="Show theoretical line", command=lambda: theoreticalLine(parent)).pack(side=tk.LEFT, padx=10, pady=5)

    def theoreticalLine(parent):
        ax = app.fig.axes[0]
        xaxis = np.linspace(0.3, 0.89, num=1000)
        beamWidthAtResonator = np.sqrt(632.8e-9/(2*np.pi)*np.sqrt((2*0.45-xaxis)*xaxis))
        rayleighLength=np.sqrt( ((2*0.45-xaxis) *xaxis) /4)
        oldBeamWidth = beamWidthAtResonator*np.sqrt((1+(xaxis/2)**2/(rayleighLength**2)))
        newBeamWidth = oldBeamWidth*np.sqrt(1+0.08**2/(np.pi*oldBeamWidth**2/632.8e-9)**2)
        ax.plot(xaxis*100, newBeamWidth*1e6, color="tab:orange")
        app.fig.canvas.draw()

    def higherModes(axes,data):
        data =data.T
        ax1, ax2 = axes
        ax1.plot(data[0], 'b')
        ax2.plot(data[1], 'r')
        ax1.grid()
        ax1.title.set_text("Zeilen")
        ax2.title.set_text("Spalten")
        ax1.set_xlabel("Pixel")
        ax2.set_xlabel("Pixel")
        ax1.set_ylabel("Intensität")
        ax2.set_ylabel("Intensität")
        ax2.grid()

    def higherModesFit(parent):
        data=app.get_data().T
        if data is None:
            messagebox.showinfo("Error", "Please select a data file")
            return
        xaxis = np.linspace(0, stop=len(data[0]), num=len(data[0]))
        print(getHermiteOrderX())
        popt1, perr1 = FPUtil.higherModeGaussianBeamIntensityFit([xaxis,data[0]],getHermiteOrderX())
        popt2, perr2 = FPUtil.higherModeGaussianBeamIntensityFit([xaxis, data[1]],getHermiteOrderY())
        ax1 = app.fig.axes[0]
        ax2 = app.fig.axes[1]
        ax1.plot(xaxis, FPUtil.higherModeGaussianBeamIntensityCurve(xaxis, *popt1,getHermiteOrderX()), "red")
        ax2.plot(xaxis, FPUtil.higherModeGaussianBeamIntensityCurve(xaxis, *popt2,getHermiteOrderY()), "blue")
        app.fig.canvas.draw()
        app.set_results(
            f"Fitting results: \n"
            f"A_x = {popt1[0]} ± {perr1[0]}; A_y = {popt2[0]} ± {perr2[0]} \n"
            f"mu_x ={popt1[1]} ± {perr1[1]}; mu_y = {popt2[1]} ± {perr2[1]} \n"
            f"w_x ={popt1[2]} ± {perr1[2]}; w_y = {popt2[2]} ± {perr2[2]} \n"
            f"c_x ={popt1[3]} ± {perr1[3]}; c_y = {popt2[3]} ± {perr2[3]}"
        )
        return


    def higherModesControls(parent,app):
        tk.Button(parent, text="Fit Gaussian Curve", command=lambda: higherModesFit(parent)).pack(side=tk.LEFT, padx=10,pady=5)
        ttk.Label(parent, text="Order of Hermite polynomials(mn):").pack(side=tk.LEFT,padx=(10,5))
        entryX = ttk.Entry(parent, width=8, textvariable=hermiteOrderX)
        entryY = ttk.Entry(parent, width=8, textvariable=hermiteOrderY)
        entryX.pack(side=tk.LEFT)
        entryY.pack(side=tk.LEFT)
        entryX.bind("<Return>",lambda e: app.redraw())
        entryY.bind("<Return>",lambda e: app.redraw())
        entryX.bind("<FocusOut>",lambda e: app.redraw())
        entryY.bind("<FocusOut>",lambda e: app.redraw())

    app.registerPlot("Single Gaussian Beam",singleGaussianView,n_plots=2,controls=singleGaussianControls)
    app.registerPlot("Beam Width",beamWidth,n_plots=1,allData=True,controls=beamWidthControls)
    app.registerPlot("Higher Modes",higherModes,n_plots=2,controls=higherModesControls)