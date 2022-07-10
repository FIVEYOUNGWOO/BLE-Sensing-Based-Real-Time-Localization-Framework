######################################################## NOTE #######################################################
# Date : 2022-05-27 to 2022-06-30                                                                                   #
#                                                                                                                   #
# Defined the functions collections.                                                                                #
#####################################################################################################################

import os
import sys
import csv
import json
import requests
import numpy as np
import pandas as pd
from sympy import Symbol
from datetime import datetime

from RTLS_Filter import *
from RTLS_Constants import *
    
# Define the exporting csv function.
def func_export(token, mac_info, rssi_info, txpower_info):
    
  # Define file path (write your specific path).
  FILE_PATH = 'C:\\Users\\duddn\\Desktop\\SNL_project\\dataset\\'
    
  # Define timestap.
  TIME_STAMP = str(datetime.now().strftime('%Y%m%d%H%M%S'))
    
  # '/' replace.
  GW_NUMBER = token.replace('/', '_')
    
  # Define file type <.csv>.
  FILE_TYPE = '.csv'
    
  # Getting the beacon datas (list to dictionary).
  dict_test = dict(MAC = mac_info, RSSI = rssi_info, POWER = txpower_info)
    
  try:
    # Generate timestamp_gateway.csv.
    with open(FILE_PATH + TIME_STAMP + GW_NUMBER + FILE_TYPE, 'w') as outfile:
      # Creating a csv writer object.
      writerfile = csv.writer(outfile)
      
      # Writing dictionary keys as headings of csv.
      writerfile.writerow(dict_test.keys())
      
      # Writing list of dictionary.
      writerfile.writerows(zip(*dict_test.values()))
            
  except IOError:
    print("I/O error")
    
  print('[{}] CSV export successful!'.format(GW_NUMBER.strip('_')))
  return

# Define the finding file path function.
def func_find_file(wanted_file_string):
  if type(wanted_file_string) != str:
    print('Your input is not a string. Fllow the example :: configs/config_beacon.csv')
    sys.exit()
  else:
    pass
  return os.path.abspath(wanted_file_string)

# Read the beacon default information
# Define the reading beacon information function.
def func_beacon_config(BC_CONFIG_PATH):
  path = func_find_file(BC_CONFIG_PATH)
  csv_loader = pd.read_csv(path, names =['Address'], header = None)
  beacon_address = csv_loader['Address'].values.tolist()
    
  # Return beacon_address
  return beacon_address

# Read the gateway default information
def func_gateway_config(gw_config_path):
  # If we have gateway configuration ?
  if (gw_config_path != None):
    path = gw_config_path
    csv_loader = pd.read_csv(path, names =['Type', 'Numbering', 'Address', 'X', 'Y','Color'], header = None)
        
    # convert column to list [Numbering]
    gateway_numbering = csv_loader['Numbering'].values.tolist()
    gateway_address = csv_loader['Address'].values.tolist()
    gateway_X = csv_loader['X'].values.tolist()
    gateway_Y = csv_loader['Y'].values.tolist()
    gateway_Color = csv_loader['Color'].values.tolist()
        
  # If we don't have gateway configuration ?
  else:
    sys.exit('Could not find the configuration file')
    
  # Return gateway_numbering for UI client panel
  return gateway_numbering, gateway_address, gateway_X, gateway_Y, gateway_Color

# Define the read JSON function.
def func_read_JSON(token, port):    
  # Concat your webhook server address automatically.
  url_connector = (PREFIX_HTTP + URL + DELIMITER_PORT + str(port) + DELIMITER_TOKEN + token)
    
  try:
      # Try to connect your defined server.
      connect = requests.get(url_connector)
        
      if connect.status_code == 200:
        # Return <class 'list'>.
        return json.loads(connect.text)
        
  except requests.exceptions.Timeout:
    pass
  except requests.exceptions.ConnectionError:
    pass
  except requests.exceptions.HTTPError:
    pass
  except requests.exceptions.RequestException:
    pass

# Check multiple gateay accesses.
def func_condition_GW(G1, G2, G3, G4):
  condition = (G1 and G2 and G3 and G4 is not None)
  return condition


# Local-based
def func_combine(mac, rssi, tx):
  mac_info = []
  rssi_info = []
  power_info = []
  
  mac_info.append(mac)
  rssi_info.append(rssi)
  power_info.append(tx)
  return mac_info, rssi_info, power_info


# Calcuate of the env_factor for distance equation.
# We have to chaning if-elif structure to switch-dict.
def func_cal_ENV():
  
  # Get Area size from configulation CSV file.
  gateway_value = func_gateway_config("configs\config_gateway.csv")
  
  # Less than 100m.
  if int(gateway_value[0][4]) * int(gateway_value[1][4]) < 100:
    ENV_FACTOR = 1.7
      
  # Less than 500m.
  elif int(gateway_value[0][4]) * int(gateway_value[1][4]) < 500:
    ENV_FACTOR = 2.1
      
  # Less than 1km.
  elif int(gateway_value[0][4]) * int(gateway_value[1][4]) < 1000:
    ENV_FACTOR = 2.4
      
  # Less than 1.5km.
  elif int(gateway_value[0][4]) * int(gateway_value[1][4]) < 1500:
    ENV_FACTOR = 2.9
      
  # Less than 2.0km.
  elif int(gateway_value[0][4]) * int(gateway_value[1][4]) < 2000:
    ENV_FACTOR = 3.4
      
  # Over 2.5Km.
  else:
    ENV_FACTOR = 4.4
      
  return ENV_FACTOR


# RSSI signal-based estimating distance(m) between gateway and target beacon.
def func_cal_distance(rssi, tx_power):
  
  # Calculates the distance through path-loss propagation model.
  path_loss = func_cal_ENV()
    
  est_distance = []
    
  for i in range(0, len(rssi)):
    est_distance.append(10 **((tx_power[i] - rssi[i]) / (10 * path_loss)))
   
  # We calculate the distance average at every second.
  # In this approach can be reducing Outliers in a second.
  return np.mean(est_distance)


# Quadrilateration algorithm. <Simple version> : for debugging integrated IPS software.
# We will improve accuracy based on the hybrid algorithm such as combining fingerprinting and quadrilateration.
# In this algorithm function, we can generate the estimated beacon position automatically.
def func_cal_quad(area_size, d0, d1, d2, d3):
  list_x = []
  list_y = []
  
  # Getting indoor size.
  indoor_size = area_size
  
  # Generate gateway position automatically.
  gateway_pos=[(0,0),(indoor_size[0],0),(indoor_size[0],indoor_size[1]),(0,indoor_size[1])]
  
  est_x = Symbol('x')
  est_y = Symbol('y')
  
  # Gateway 1 position.
  GW0_X = int(gateway_pos[0][0])
  GW0_Y = int(gateway_pos[0][1])
  
  # Gateway 2 position.
  GW1_X = int(gateway_pos[1][0])
  GW1_Y = int(gateway_pos[1][1])
  
  # Gateway 3 position.
  GW2_X = int(gateway_pos[2][0])
  GW2_Y = int(gateway_pos[2][1])
  
  # Gateway 4 position.
  GW3_X = int(gateway_pos[3][0])
  GW3_Y = int(gateway_pos[3][1])
    
  # [NOTE] Equation of a circle with radius as distance obtained by RSSI.
  # pow((est_x - GW0_X),2) + pow((est_y - GW0_Y),2) == pow(d0,2)
  # pow((est_x - GW1_X),2) + pow((est_y - GW1_Y),2) == pow(d1,2)
  # pow((est_x - GW2_X),2) + pow((est_y - GW2_Y),2) == pow(d2,2)
  # pow((est_x - GW3_X),2) + pow((est_y - GW3_Y),2) == pow(d3,2)
  
  # [NOTE] Equation passing through the intersection of GW0 and GW1 .. GW2 and GW3.
  # 2 * (GW1_X - GW0_X) * est_x + 2 * (GW1_Y - GW0_Y) == d0 - d1 - pow(GW0_X,2) + pow(GW1_X,2) - pow(GW0_Y,2) + pow(GW1_Y,2)
  # 2 * (GW2_X - GW1_X) * est_x + 2 * (GW2_Y - GW1_Y) == d1 - d2 - pow(GW1_X,2) + pow(GW2_X,2) - pow(GW1_Y,2) + pow(GW2_Y,2)
  # 2 * (GW3_X - GW2_X) * est_x + 2 * (GW3_Y - GW2_Y) == d2 - d3 - pow(GW2_X,2) + pow(GW3_X,2) - pow(GW2_Y,2) + pow(GW3_Y,2) 
  
  # Replace each polynomial with the letters A .. I to improve the complexity of the operation.
  A = 2 * (GW1_X - GW0_X)
  B = 2 * (GW1_Y - GW0_Y)

  C = pow(d0, 2) - pow(d1, 2) - pow(GW0_X,2) + pow(GW1_X,2) - pow(GW0_Y,2) + pow(GW1_Y,2)

  D = 2 * (GW2_X - GW1_X)
  E = 2 * (GW2_Y - GW1_Y)
  F = pow(d1, 2) - pow(d2, 2) - pow(GW1_X,2) + pow(GW2_X,2) - pow(GW1_Y,2) + pow(GW2_Y,2)
  
  G = 2 * (GW3_X - GW2_X)
  H = 2 * (GW3_Y - GW2_Y)
  I = pow(d2 ,2) - pow(d3, 2) - pow(GW2_X,2) + pow(GW3_X,2) - pow(GW2_Y,2) + pow(GW3_Y,2)

  # Coordinates obtained by trilateration. <3>
  est_x = ((F * B) - (E * C)) / ((B * D) - (E * A))
  est_y = ((F * A) - (D * C)) / ((A * E) - (D * B))
  
  # Coordinates obtained by quadrilateration. <4>
  if (((G*est_x) + (H*est_y)) == I):
    est_x = ((I * E) - (H * F)) / ((E * G) - (H * D))
    est_y = ((I * D) - (G * F)) / ((D * H) - (G * E))
  
  # Copy the estimated beacon positions each (x, y).
  list_x.append(est_x)
  list_y.append(est_y)

  return list_x, list_y