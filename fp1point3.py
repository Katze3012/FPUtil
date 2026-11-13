import FPUtil as fp
import numpy as np
from uncertainties import ufloat

def approxMagnField(x):
    return np.round(0.9043*x-0.0257,2)

magnField = []
magnFieldUncert = []
temps = []
scalingParam = 1.8*1e-3
uncert1V = 0.02/np.sqrt(3)
uncert3V = 0.1/np.sqrt(3)
uncertPosition = scalingParam*0.01/np.sqrt(3)
uncertMagnField = 0.02/np.sqrt(3)
xerr = []
yerr = []
offsets = []
offsetsUncert = []
offsetsSpecial = []
offsetsSpecialUncert = []
realMagneton=9.274010e-24

with open("../1.3/data.csv", "r") as f:
    data = f.readlines()
    data = [x.split(",") for x in data]
    data = [[float(x) for x in y] for y in data]

for i in range(0,len(data),2):
    magnField.append(data[i][0])
    temps.append(data[i+1][0]+273.15)
    del data[i][0]
    del(data[i+1][0])
    yerr.append([])
    xerr.append([])
    for j in range(0, len(data[i])):
        xerr[int(i / 2)].append(uncertPosition)
        if float(data[i + 1][j]) >= 1:
            yerr[int(i / 2)].append(uncert3V)
        elif float(data[i + 1][j]) < 1:
            yerr[int(i / 2)].append(uncert1V)

for i in range(0,len(data),2):
    for j in range(0,len(data[i])):
        data[i][j] = data[i][j]*1.8

del magnField[0]

for i in range(0,len(magnField)):
    magnFieldUncert.append(uncertMagnField)

magnFieldGrad=np.array(approxMagnField(np.array(magnField)))*0.9661/2.5e-3

data1FitGaussParam=fp.gaussianFit([np.array(data[0]),np.array(data[1])],2,16.6,1,0.3)
data2FitGaussParam=fp.doubleGaussianFit([np.array(data[2]),np.array(data[3])],1.45,15.9,0.5,1.4,17.5,0.5,0.6)
data3FitGaussParam=fp.doubleGaussianFit([np.array(data[4]),np.array(data[5])],1.3,16,0.5,1.4,17.5,0.5,0.7)
data4FitGaussParam=fp.doubleGaussianFit([np.array(data[6]),np.array(data[7])],1.15,16,0.5,1.15,17.5,0.5,0.55)
data5FitGaussParam=fp.doubleGaussianFit([np.array(data[8]),np.array(data[9])],1.3,16,0.5,1.3,17.5,0.5,0.55)

FitGaussParams=[data1FitGaussParam,data2FitGaussParam,data3FitGaussParam,data4FitGaussParam,data5FitGaussParam]

for i in range(1,len(FitGaussParams)):
    offsets.append(FitGaussParams[i][0][4]-FitGaussParams[i][0][1])
    offsetsUncert.append(np.sqrt(FitGaussParams[i][1][4]**2 + FitGaussParams[i][1][1]**2))

offsetsFitGaussParam=fp.linearFit([magnFieldGrad,offsets],1,1)

magnetonGauss=ufloat(offsetsFitGaussParam[0][0],offsetsFitGaussParam[1][0])*1e-3*3*1.3806203e-23*ufloat(np.mean(temps),np.std(temps))/(455e-3*7e-2*(1-7e-2/(2*455e-3)))


data2FitSpecialParam=fp.specialFunctionSternGerlachFit([np.array(data[2]),np.array(data[3])],9.1,2,-16.5,0.6,0.59,0.61)
data3FitSpecialParam=fp.specialFunctionSternGerlachFit([np.array(data[4]),np.array(data[5])],9.1,2,-16.5,0.72,0.71,0.73)
data4FitSpecialParam=fp.specialFunctionSternGerlachFit([np.array(data[6]),np.array(data[7])],9.1,2,-16.5,0.54,0.53,0.55)
data5FitSpecialParam=fp.specialFunctionSternGerlachFit([np.array(data[8]),np.array(data[9])],9.1,2,-16.5,0.54,0.53,0.55)

FitSpecialParams=[[],data2FitSpecialParam,data3FitSpecialParam,data4FitSpecialParam,data5FitSpecialParam]

for i in range(1,len(FitSpecialParams)):
    offsetsSpecial.append(2*FitSpecialParams[i][0][1]/3)
    offsetsSpecialUncert.append(2*FitSpecialParams[i][1][1]/3)

offsetsFitSpecialParam=fp.linearFit([magnFieldGrad,offsetsSpecial],1,1)

magnetonSpecial = ufloat(offsetsFitSpecialParam[0][0],offsetsFitSpecialParam[1][0])*1e-3*3*1.3806203e-23*ufloat(np.mean(temps),np.std(temps))/(455e-3*7e-2*(1-7e-2/(2*455e-3)))

def main():
    fp.createPlotWithFitAndError([np.array(data[0]),data[1]],
                                 np.linspace(min(data[0]),max(data[0]),1000),
                                 fp.gaussCurve(np.linspace(min(data[0]),max(data[0]),1000),
                                       *FitGaussParams[0][0]),
                         "Intensitätsverteilung bei ausgeschaltetem Magnetfeld",
                         "Position [mm]",
                         "Intensität [V]",
                                 [xerr[0],yerr[0]],
                                 "../1.3",
                                 "ohneBFeld"
                                 )
    print(FitGaussParams[0])
    for i in range(1,len(FitGaussParams)):
        fp.createPlotWithFitAndError([np.array(data[2*i]), data[2*i+1]],
                                     np.linspace(min(data[2*i]),max(data[2*i]),1000),
                                     fp.doubleGaussianCurve(np.linspace(min(data[2*i]),max(data[2*i]),1000), *FitGaussParams[i][0]),
                                     f"Intensitätsverteilung bei einer Magnetfeldstärke von " + str(approxMagnField(magnField[i-1])) +"T",
                                     "Position [mm]",
                                     "Intensität [V]",
                                     [xerr[i],yerr[i]],
                                     "../1.3",
                                     "gaussMitBFeld" + str(magnField[i-1])
                                     )
        print(FitGaussParams[i])
    fp.createPlotWithFitAndError([magnFieldGrad,offsets],
                                 np.linspace(min(magnFieldGrad),max(magnFieldGrad),1000),
                                 fp.linearCurve(np.linspace(min(magnFieldGrad),max(magnFieldGrad),1000),*offsetsFitGaussParam[0]),
                                 f"Versatz der beiden Peaks abhängig vom Magnetfeldgradienten",
                                 "Magnetfeldgradient [T/m]",
                                 "Versatz [mm]",
                                 [magnFieldUncert,offsetsUncert],
                                 "../1.3",
                                 "linearfitgauss")
    print("Versatz [mm]")
    print(offsets,offsetsUncert)
    print("Magneton")
    print(magnetonGauss)
    for i in range(1,len(FitSpecialParams)):
       fp.createPlotWithFitAndError([np.array(data[2*i]), data[2*i+1]],
                                    np.linspace(min(data[2*i]),max(data[2*i]),1000),
                                    fp.specialFunctionSternGerlachCurve(np.linspace(min(data[2*i]),max(data[2*i]),1000), *FitSpecialParams[i][0]),
                                    f"Intensitätsverteilung bei einer Magnetfeldstärke von " + str(approxMagnField(magnField[i-1])) +"T",
                                    "Position [mm]",
                                    "Intensität [V]",
                                    [xerr[i],yerr[i]],
                                    "../1.3",
                                    "specialMitBFeld" + str(magnField[i - 1])
                                    )
       print(FitSpecialParams[i])
    fp.createPlotWithFitAndError([magnFieldGrad,offsetsSpecial],
                                 np.linspace(min(magnFieldGrad),max(magnFieldGrad),1000),
                                 fp.linearCurve(np.linspace(min(magnFieldGrad),max(magnFieldGrad),1000),*offsetsFitSpecialParam[0]),
                                f"Versatz der beiden Peaks abhängig vom Magnetfeldgradienten",
                                "Magnetfeldgradient [T/m]",
                                "Versatz [mm]",
                                 [magnFieldUncert,offsetsUncert],
                                 "../1.3",
                                 "linearspecialfit")
    print("Versatz [mm]")
    print(offsetsSpecial,offsetsUncert)
    print("Magneton")
    print(magnetonSpecial)