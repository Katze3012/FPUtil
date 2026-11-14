import numpy as np
from scipy.optimize import curve_fit
from scipy.special import eval_hermite, eval_hermitenorm
import matplotlib.pyplot as plt
import csv
from PIL import Image
from scipy.ndimage import uniform_filter

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

def bmpImporterAndParser(bmp_path):
    img = Image.open(bmp_path).convert("L")
    arr = np.asarray(img)
    return arr

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

def higherModeGaussianBeamIntensity3DCurve(coords, A, x0, y0 , wx,wy, offset,theta,n,m):
    x,y = coords
    xr = (x - x0) * np.cos(theta) + (y - y0) * np.sin(theta)
    yr = -(x - x0) * np.sin(theta) + (y - y0) * np.cos(theta)
    u = np.sqrt(2) * (xr - x0) / wx
    v = np.sqrt(2) * (yr - y0) / wy
    return A * eval_hermite(n, u) ** 2 * eval_hermite(m, v)**2 * np.exp(
        -2 / wx ** 2 * xr ** 2 + -2 / wy ** 2 * yr ** 2) + offset

def temModel(n):
    def model(x,A, x0, w, offset):
        u = np.sqrt(2) * (x - x0) / w
        return A * eval_hermite(n, u) ** 2 * np.exp(-2 * (x - x0) ** 2 / w ** 2) + offset
        #return A/(sigma**2)*np.exp(-2*(x - mu)**2 / (sigma**2))*(eval_hermite(n,np.sqrt(2)*(x-mu)/sigma))**2+offset
    return model

def temModel3D(n,m):
    def model3D(coords, A, x0, y0 , wx,wy, offset,theta):
        x,y = coords
        xr = (x - x0) * np.cos(theta) + (y - y0) * np.sin(theta)
        yr = -(x - x0) * np.sin(theta) + (y - y0) * np.cos(theta)
        u = np.sqrt(2) * xr / wx
        v = np.sqrt(2) * yr / wy
        return (A * eval_hermite(n, u) ** 2 * eval_hermite(m, v)**2 * np.exp(
            -2 / wx ** 2 * xr ** 2 + -2 / wy ** 2 * yr ** 2) + offset).ravel()
    return model3D


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

# Letzte Version bevor ich aufgegeben habe und Claude den Rest fixen lassen hab
#def higherModeGaussianBeamIntensity3DFit(data,n,m):
#    data = np.asarray(data,dtype=float)
#    print(n,m,type(n), type(m))
#    model3D = temModel3D(n,m)
#    yy,xx = np.mgrid[0:data.shape[0],0:data.shape[1]]
#
#    offset0 = np.percentile(data,5)
#    zc = np.clip(data-offset0,0,None)
#    s=data.sum()
#    x0 = (xx * zc).sum() / s
#    y0 = (yy * zc).sum() / s
#    wx0 = 2/np.sqrt(2*n+1)*np.sqrt((zc * (xx - x0) ** 2).sum() / s)
#    wy0 = 2/np.sqrt(2*m+1) * np.sqrt((zc * (yy - y0) ** 2).sum() / s)
#    p0 = [zc.max(), 350, 350, wx0, wy0, offset0,0]
#    print(p0)
#    popt,pcov = curve_fit(model3D,(xx,yy),data.ravel(),p0=p0,maxfev=20000,bounds=([0,0,1,1,0,0,-np.pi],[np.inf,np.inf,1e4,1e4,np.inf,np.inf,np.pi]))
#    perr = np.sqrt(np.diag(pcov))
#    return [popt,perr,p0]

def higherModeGaussianBeamIntensity3DFit(data, n, m, step=4):
    data = np.asarray(data, dtype=float)
    H, W = data.shape
    model3D = temModel3D(n, m)

    yy, xx = np.mgrid[0:H, 0:W]

    # Untergrund und Zentrum robust bestimmen (geglättet, Schwelle gegen Rauschen)
    offset0 = np.percentile(data, 5)
    sm = uniform_filter(data, 15) - offset0
    zc = np.clip(sm - 0.2 * sm.max(), 0, None)
    s = zc.sum()
    x0 = (xx * zc).sum() / s
    y0 = (yy * zc).sum() / s

    # Breite aus dem zweiten Moment (Momente ohne Schwelle, aber offsetbereinigt)
    zm = np.clip(data - offset0, 0, None)
    sm_ = zm.sum()
    wx0 = 2 / np.sqrt(2*n + 1) * np.sqrt((zm * (xx - x0)**2).sum() / sm_)
    wy0 = 2 / np.sqrt(2*m + 1) * np.sqrt((zm * (yy - y0)**2).sum() / sm_)

    # Downsampling für den Fit (echte Pixelkoordinaten behalten)
    xs, ys, zs = xx[::step, ::step], yy[::step, ::step], data[::step, ::step]

    # Amplitude über das Einheitsmodell
    unit = model3D((xs, ys), 1, x0, y0, wx0, wy0, 0, np.pi/4)
    A0 = (zs.max() - offset0) / unit.max()

    lower = [0,      0, 0,      5,    5,    0,      -np.pi]
    upper = [np.inf, W, H, W,    H,    np.inf,  np.pi]

    best = None
    for theta0 in (np.pi/4, 0.0):            # beide Orientierungen probieren
        p0 = [A0, x0, y0, wx0, wy0, offset0, theta0]
        try:
            popt, pcov = curve_fit(model3D, (xs, ys), zs.ravel(), p0=p0, bounds=(lower, upper), maxfev=20000)
        except RuntimeError:
            continue
        rss = np.sum((zs.ravel() - model3D((xs, ys), *popt))**2)
        if best is None or rss < best[0]:
            best = (rss, popt, pcov, p0)

    if best is None:
        raise RuntimeError("Fit nicht konvergiert")
    _, popt, pcov, p0 = best
    return popt, np.sqrt(np.diag(pcov)), p0

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