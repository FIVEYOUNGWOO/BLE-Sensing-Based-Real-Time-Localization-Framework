######################################################## NOTE #######################################################
# Date : 2022-05-27 to 2022-06-30                                                                                   #
#                                                                                                                   #
# RTLS_run.py as Main file                                                                                          #
#                                                                                                                   #
# Overview of RTLS_Run.py below:                                                                                    # 
# [Call] the necessary values, and functions from RTLS_Constants.py and RTLS_Utils.py                               #
# [Read] the scenario environment and H/W configurations such as area, number of beacons and gateways from CSV file # 
# [Ready] the gateway dedicated webhook server token and port number for executing the RTLS_Server.py               #
# [Run] the webhook server services based on the allocated parameters                                               #
#       -> where the 'services' is including the pre-processing of the received beacon packets, and filtering       #
# [Write] pre-processed and filtered beacon packets in each defined URL address by using the webhook server         # 
# [Read] the written beacon information <JSON> from each different URL address in RTLS Broker.broker() function     #
#                                                                                                                   #
# Our RTLS goals:                                                                                                   #
# First, to estimate the positions of the livestock.                                                                #
# Second, to handle the RTLS processing automatically.                                                              #
#####################################################################################################################

import os 
import RTLS_Broker

if __name__ == '__main__':
  os.environ["WERKZEUG_RUN_MAIN"] = 'true'
  RTLS_Broker.broker_run()