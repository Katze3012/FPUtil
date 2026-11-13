import tkinter as tk
from tkinter import messagebox
import numpy as np
from fontTools.varLib import plot
from uncertainties import ufloat

from FPUtilGUI import GUI
import FPUtil
import uncertainties
import re

def paramFromName(name):
    m = re.search(r"L=(\d+(?:[.,]\d+)?)\s*cm", name)
    return float(m.group(1).replace(",", ".")) if m else None

def fitGaussianCurve(app,parent):
    data=app.get_data().T
    if data is None:
        messagebox.showinfo("Error", "Please select a data file")
        return
    xaxis = np.linspace(0, stop=len(data[0]), num=len(data[0]))
    popt1, perr1 = FPUtil.gaussianBeamIntensityFit([xaxis,data[0]],400000,np.argmax(data[0]),20,0)
    popt2, perr2 = FPUtil.gaussianBeamIntensityFit([xaxis,data[1]],400000,np.argmax(data[1]),20,0)
    ax1 = app.fig.axes[0]
    ax2 = app.fig.axes[1]
    ax1.plot(xaxis,FPUtil.gaussianBeamIntensityCurve(xaxis,*popt1),"red")
    ax2.plot(xaxis,FPUtil.gaussianBeamIntensityCurve(xaxis,*popt2), "blue")
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
    tk.Button(parent, text="Fit Gaussian Curve", command=lambda: fitGaussianCurve(app,parent)).pack(side=tk.LEFT, padx=10,pady=5)

def beamWidth(axes,datasets):
    ax = axes[0]
    names,valuesX,valuesXerr,valuesY,valuesYerr,params = [],[],[],[],[],[]
    #lengthErr = 0.1/np.sqrt(3)

    for key,name,path,data in datasets:
        data = data.T
        xaxis= np.linspace(0, stop=len(data[0]), num=len(data[0]))
        try:
            popt1, perr1 = FPUtil.gaussianBeamIntensityFit([xaxis, data[0]], 400000, np.argmax(data[0]), 20, 0)
            popt2, perr2 = FPUtil.gaussianBeamIntensityFit([xaxis, data[1]], 400000, np.argmax(data[1]), 20, 0)
            valuesX.append(np.abs(popt1[2]))
            valuesXerr.append(np.abs(perr1[2]))
            valuesY.append(np.abs(popt2[2]))
            valuesYerr.append(np.abs(perr2[2]))
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
        ax.plot(np.array(params)[order], np.array(valuesX)[order],"o-",color="blue")
        ax.plot(np.array(params)[order], np.array(valuesY)[order],"o-",color="red")
        ax.errorbar(params, valuesX, yerr=valuesXerr, xerr=lengthErr, fmt="o", capsize=2, label="Messdaten",color="blue")
        ax.errorbar(params, valuesY, yerr=valuesYerr, xerr=lengthErr, fmt="o", capsize=2, label="Messdaten",color="red")
        ax.set_xlabel("Resonatorlänge in cm")
        ax.set_ylabel("Strahlbreite in Pixel")
    else:
        ax.plot(range(len(valuesX)), valuesX, "o-")
        ax.plot(range(len(valuesY)), valuesY,"o-")
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels(names, rotation=45, ha="right")
        ax.set_xlabel("Datensatz")

    text = ([f"w_x={valuesX[i]:.4g}±{valuesXerr[i]:.4g}  " + f"w_y={valuesY[i]:.4g}±{valuesYerr[i]:.4g}  \n" for i in range(len(valuesX))])
    app.set_results(text)

if __name__ == "__main__":
    root = tk.Tk()
    app = GUI(root)
    app.registerPlot("Single Gaussian Beam",singleGaussianView,n_plots=2,controls=singleGaussianControls)
    app.registerPlot("Beam Width",beamWidth,n_plots=1,allData=True)
    root.mainloop()