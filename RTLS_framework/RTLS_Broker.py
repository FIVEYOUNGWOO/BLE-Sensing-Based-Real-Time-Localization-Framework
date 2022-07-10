
######################################################## NOTE #######################################################
# Date : 2022-05-27 to 2022-06-30                                                                                   #
#                                                                                                                   #
# Execute the server broker                                                                                         #
#####################################################################################################################

import time
from threading import Thread
from multiprocessing import *

from RTLS_UI import *
from RTLS_Utils import *
from RTLS_Server import *
from RTLS_Filter import *
from RTLS_Constants import *

# Class for sharing estimated position values.
class SharedMemory(): x, y = [], []

# Description of Broker function as below:
# [Acquire] the pre-processed beacon packets from each gateway.
# [Calculate] distance by using filtered-RSSI, transmit power, and path-loss.
# [Copy] the calculated distance between each gateway and beacons.
# [Estimate] a number of beacon positions based on the Quadrilateration algorithm.
# [Share] the estimated positions based on SharedMemory class.

def broker(beacon_sample, token_with_port, area_size):
  while True:
    # Acquire of beacon packet from each gateway.
    GW1 = func_read_JSON(token = token_with_port[0][0], port = token_with_port[0][1])
    GW2 = func_read_JSON(token = token_with_port[1][0], port = token_with_port[1][1])
    GW3 = func_read_JSON(token = token_with_port[2][0], port = token_with_port[2][1])
    GW4 = func_read_JSON(token = token_with_port[3][0], port = token_with_port[3][1])
      
    # Check the lenght of received dictonary.
    if (func_condition_GW(GW1, GW2, GW3, GW4)):
      for i in range(beacon_sample):
        try:
          # Estimate distance between gateway and each target beacons.
          d0 = func_cal_distance(GW1[i].get('RSSI'), GW1[i].get('POWER'))
          d1 = func_cal_distance(GW2[i].get('RSSI'), GW2[i].get('POWER'))
          d2 = func_cal_distance(GW3[i].get('RSSI'), GW3[i].get('POWER'))
          d3 = func_cal_distance(GW4[i].get('RSSI'), GW4[i].get('POWER'))
        
          # Quadrilateration algorithm-based estimated beacon positions.
          est_x, est_y = func_cal_quad(area_size, d0, d1, d2, d3)
        
          # Performance check_point : estimated beacon positions.
          # print('estimated X_{} = {}, estimated Y_{} = {}'.format(i, est_x, i, est_y))
        
          # Copy the estimated beacon positions.
          SharedMemory.x.extend(est_x)
          SharedMemory.y.extend(est_y)
          
        # Gateway has not acq. or sent yet... wait for a few seconds.
        except IndexError:
          pass
          
      # Delete the stack of global-list memory.
      if len(SharedMemory.x) % beacon_sample == 0 and len(SharedMemory.y) % beacon_sample == 0:
        del SharedMemory.x[:-beacon_sample]
        del SharedMemory.y[:-beacon_sample]
      
      # For wait print() because the values updated fast. Only using performance check_opint
      # time.sleep(2)


# Description of Broker_run function as below:
# [Read] the gateway, and beacon configuration files from CSV.
# [Generate] the webhook server token with the port number.
# [Run] the defined webhook server services from RTLS_Server.py.
# [Run] the RTLS.Ui.py after server processing conditions.

def broker_run():
  # Loading each configulation files.
  load_area = func_gateway_config("configs\config_gateway.csv")
  load_number = func_beacon_config("configs\config_beacon.csv")

  # Setting indoor size and number of beacons.
  area_size = (load_area[0][4],load_area[1][4])
  beacon_sample = len(load_number)

  # Configuration of delimiter and port number.
  token_with_port = [('GW1', 2998), ('GW2', 2999), ('GW3', 3000), ('GW4', 3001)]
  
  # Asynchronous server based on multi-process.
  for token, port in token_with_port:
    proc = Process(target = RunFlaskApp, args = (token, port))
    proc.start()

    # Checking your multi-processor. <boolen to number of list>
    PROCESSOR_BOL.append(proc.is_alive())
  
  # Checking your multi-processor equals to defined 'token_with_port'.
  if len(PROCESSOR_BOL) == len(token_with_port):
    
    application = QApplication(sys.argv)
    application.setFont(QFont("나눔스퀘어_ac", 8))
    
    broker_thread = Thread(target = broker, args = ((beacon_sample, token_with_port, area_size)))
    broker_thread.start()
    
    interface = UserInterface([SharedMemory.x, SharedMemory.y])
    interface.show()
    application.exec_()