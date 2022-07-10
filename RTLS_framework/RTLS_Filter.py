######################################################## NOTE #######################################################
# Date : 2022-05-27 to 2022-06-30                                                                                   #
#                                                                                                                   #
# 1D Kalman filtering method.                                                                                       #
#####################################################################################################################

import numpy as np

from RTLS_Utils import *
from RTLS_Constants import *


# Y. Shen, B. Hwang, and J. P. Jeong, ‘Particle filtering-based indoor positioning system for beacon tag tracking,’ IEEE Access.
def func_kalman_filter(measured_rssi,idx):
    KF_RSSI = []
    KF_RSSI.append(measured_rssi)
      
    # from the reference paper.
    processNoise = 0.05
    measurementNoise = np.var(KF_RSSI)
    predictedRSSI, errorCovariance = 0, 0
    
    # Start 2nd applied the kalman filtering case.
    if idx != 0:
        priorRSSI = KF_RSSI[idx-1]
        priorErrorCovariance = 1
        
    # Start 1st applied the kalman filtering case.
    else:
        priorRSSI = KF_RSSI[idx]
        
        # Error covariance.
        priorErrorCovariance = errorCovariance + processNoise
    
    # KalmanGain formula.
    kalmanGain = priorErrorCovariance / (priorErrorCovariance + measurementNoise)
    
    # K = P / P + R (P: error covariance, R: measurement noise).
    predictedRSSI = priorRSSI + (kalmanGain * (measured_rssi - priorRSSI))
        
    # RSSI Estimation Expression RSSI = Previous RSSI + (KalmanGain*(Current RSSI - Previous RSSI)).
    errorCovariance = (1 - kalmanGain) * priorErrorCovariance

    # Save the predicted RSSI values.
    KF_RSSI[idx] = predictedRSSI

    # After finding the RSSI, the newly calibrated error covariance equation P = (1 - KalmanGain)previous error covariance.
    return int(predictedRSSI)