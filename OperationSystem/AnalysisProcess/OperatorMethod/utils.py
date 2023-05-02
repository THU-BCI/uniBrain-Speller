import math

def ITR(N,P,winBIN):

    winBIN = winBIN+0.5

    if   P == 1:
        ITR = math.log2(N)*60/winBIN
    elif P == 0:
        ITR = (math.log2(N)+ 0 +(1-P)*math.log2((1-P)/(N-1)))*60/winBIN
        ITR = 0
    else:
        ITR = (math.log2(N)+P*math.log2(P)+(1-P)*math.log2((1-P)/(N-1)))*60/winBIN

    return ITR

