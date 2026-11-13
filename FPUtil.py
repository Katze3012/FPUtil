import numpy as np
from scipy.optimize import curve_fit
from scipy.special import eval_hermite
import matplotlib.pyplot as plt
import csv
from functools import partial

def csvImporterAndParser(filename,delimiter='\t',decimal='.',skiprows=0):
    data = []
    with open(filename) as f:
        lines = f.readlines()[skiprows:]

    if delimiter==' ':
        parsed = (line.split() for line in lines)
    else:
        parsed = csv.reader(lines,delimiter=delimiter)

    for l in parsed:
        values=[x.strip() for x in l]
        if not values:
            continue
        if decimal==',':
            values = [v.replace(decimal,'.') for v in values]
        data.append([float(i) for i in values])
    return np.array(data, dtype=float)

def gaussCurve(x, a, mu, sigma, c):
    return a * np.exp(-(x - mu)**2 / (2 * sigma**2))+c

def doubleGaussianCurve(x, a1, mu1, sigma1, a2, mu2, sigma2, c):
    return a1 * np.exp(-(x - mu1)**2 / (2 * sigma1**2)) + a2 * np.exp(-(x - mu2)**2 / (2 * sigma2**2)) + c

def linearCurve(x, a, b):
    return a * x + b

def specialFunctionSternGerlachCurve(x, a,q,z,c):
    return 2*a*np.exp(-q/(np.abs(x+z)))*1/((np.abs(x+z))**3)+c

def gaussianBeamIntensityCurve(x,a, mu, sigma, c):
    return a/(sigma**2)*np.exp(-2*(x - mu)**2 / (sigma**2))+c

def higherModeGaussianBeamIntensityCurve(x,A, x0, w, offset,n):
    u = np.sqrt(2) * (x - x0) / w
    return A * eval_hermite(n, u) ** 2 * np.exp(-2 * (x - x0) ** 2 / w ** 2) + offset

def temModel(n):
    def model(x,A, x0, w, offset):
        u = np.sqrt(2) * (x - x0) / w
        return A * eval_hermite(n, u) ** 2 * np.exp(-2 * (x - x0) ** 2 / w ** 2) + offset
        #return A/(sigma**2)*np.exp(-2*(x - mu)**2 / (sigma**2))*(eval_hermite(n,np.sqrt(2)*(x-mu)/sigma))**2+offset
    return model

def gaussianFit(data, a, mean, sigma, c):
    if not len(data)==2:
        data= np.transpose(data)
    popt,pcov = curve_fit(gaussCurve, data[0],data[1],p0=[a, mean, sigma, c])
    perr = np.sqrt(np.diag(pcov))
    return [popt,perr]

def doubleGaussianFit(data, a1, mean1, sigma1, a2, mean2, sigma2, c):
    if not len(data)==2:
        data= np.transpose(data)
    popt,pcov = curve_fit(doubleGaussianCurve,data[0],data[1],p0=[a1, mean1, sigma1, a2, mean2, sigma2, c])
    perr = np.sqrt(np.diag(pcov))
    return [popt,perr]

def linearFit(data, a, b):
    if not len(data)==2:
        data= np.transpose(data)
    popt,pcov = curve_fit(linearCurve,data[0],data[1],p0=[a, b])
    perr = np.sqrt(np.diag(pcov))
    return [popt,perr]

def specialFunctionSternGerlachFit(data, a,q,z,c,cLow,cHigh):
    if not len(data)==2:
        data= np.transpose(data)
    popt,pcov = curve_fit(specialFunctionSternGerlachCurve,data[0],data[1],p0=[a,q,z,c],bounds=([-np.inf,-np.inf,-np.inf,cLow],[np.inf,np.inf,np.inf,cHigh]))
    perr = np.sqrt(np.diag(pcov))
    return [popt,perr]

def gaussianBeamIntensityFit(data, a, mean, sigma, c):
    if not len(data)==2:
        data= np.transpose(data)
    popt,pcov = curve_fit(gaussianBeamIntensityCurve, data[0],data[1],p0=[a, mean, sigma, c])
    perr = np.sqrt(np.diag(pcov))
    return [popt,perr]

def higherModeGaussianBeamIntensityFit(data,n):
    offset0 = np.percentile(data[1],5)
    yc = np.clip(data[1]-offset0,0,None)

    x0 = np.sum(data[0]*yc)/np.sum(data[0])
    var = np.sum(yc*(data[0]-x0)**2)/np.sum(yc)
    w0 = 2* np.sqrt(var)/ np.sqrt(2*n+1)

    model = temModel(n)
    A0 = yc.max()/max(eval_hermite(n,0.0)**2,1)
    p0 = [A0,x0,w0,offset0]

    popt, pcov = curve_fit(model, data[0],data[1],p0=p0,maxfev=50000,bounds=([0,0,0,0],[np.inf,np.inf,np.inf,np.inf]))
    perr = np.sqrt(np.diag(pcov))
    return [popt,perr]

def createSimplePlot(data):
    plt.figure()
    plt.plot(data[0],data[1],label="Messdaten")
    plt.show()

def createPlotWithFitAndError(data,xAxis,fitcurve,title,xlabel:str,ylabel:str,dataErr,path,name):
    plt.figure()
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.plot(data[0],data[1])
    plt.errorbar(data[0],data[1],yerr=dataErr[1],xerr=dataErr[0],fmt="o",capsize=2,label="Messdaten",color="tab:blue")
    plt.plot(xAxis,fitcurve,label="Fit")
    plt.legend()
    plt.savefig(path+"\\"+name+".pdf")
    plt.clf()