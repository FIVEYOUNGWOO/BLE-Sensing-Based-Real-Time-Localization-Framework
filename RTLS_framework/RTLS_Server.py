######################################################## NOTE #######################################################
# Date : 2022-05-27 to 2022-06-30                                                                                   #
#                                                                                                                   #
# If triggered 'GET', or 'POST' events, then we can receive the beacon information from localhost webhook server.   #
# We received the ibeacon information as below:                                                                     #
# 1) dict.get('timestamp')      | '2022-05-26T03:03:32.970Z'                                                        #
# 2) dict.get('type')           | 'iBeacon'                                                                         #
# 3) dict.get('mac')            | 'AC233FAA45E5'                                                                    #
# 4) dict.get('bleName')        | ''                                                                                #
# 5) dict.get('ibeaconUuid')    | 'E2C56DB5DFFB48D2B060D0F5A71096E0'                                                #
# 6) dict.get('ibeaconMajor')   | '0'                                                                               #
# 7) dict.get('ibeaconMinor')   | '0'                                                                               #
# 8) dict.get('rssi')           | '-29'                                                                             #
# 9) dict.get('ibeaconTxPower') | '-59'                                                                             #
# 10) dict.get('battery')       | ''                                                                                #
#####################################################################################################################

import re
import os
import sys
import signal
import logging
import threading

from RTLS_Utils import *
from RTLS_Filter import *
from RTLS_Constants import *
from multiprocessing import *
from flask import Flask, request, jsonify

# Get number of beacons.
beacon_list = func_beacon_config('configs\config_beacon.csv')

# Remove the some symbol ":".
for i in range(len(beacon_list)):
    beacon_list[i] = re.sub(":","",beacon_list[i])

# Remove warning nofitications.
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)

# Parent class for running HookServer (with some preprocessing).
class HookServer(threading.Thread):
    def __init__ (self, token, port):
        
        self.save_info = []
        self.value = []
        self.beacon_dict = []
        self.dict = {}

        self.token = token
        self.port = port
        
        # Setup for a Flask application instants.
        self.server_app = Flask(__name__, static_folder='./media')
        self.server_app.debug = False

        # Ignore web-hook server tracking information.
        log = logging.getLogger('werkzeug')
        log.disabled = True

        @self.server_app.route('/' + self.token, methods=['GET', 'POST'])
        def index1():
            # If 'GET' request.
            if request.method == 'GET':
                
                # JSON LONG convert to the dictionary.
                content = request.args.to_dict()
                
            # If 'POST' request.
            elif request.method == 'POST':

                # Read the JSON-LONG data.
                content = request.get_json()

                # Received beacon information (dict) per time slot (1 sec).
                MAX_EXTRACT_LOOP = len(content)
                
                # Unwrapping of i-beacon dictionary <dict>.
                for i in range(0, MAX_EXTRACT_LOOP):

                    # Acquired the raw beacon packets <list of [str], [str], [str]>.
                    self.save_info = list(func_combine(content[i].get('mac'), content[i].get('rssi'), content[i].get('ibeaconTxPower')))
                                                                    
                    # Copy the received beacon JSON data.
                    self.value = self.save_info
                    
                    # Get received beacon packet length.
                    Pkt = len(self.value[0])
                    save_Pkt = len(self.save_info[0])
                    
                    # Checking the received beacon addresses.
                    if (list(set(beacon_list) & set(self.value[0]))):
                        
                        # Pre-allocate rssi, txpower list space.
                        self.dict = {i:{'rssi':[], 'txpower':[]} for i in beacon_list} 
                        
                        for i in range (Pkt):                            
                            # Applied the Kalman filtering for equalizing the outlier RSSI data.
                            self.value[1][i] = func_kalman_filter(self.value[1][i],i)

                            # Get received beacon packets.
                            mac_address = self.value[0][i]
                            self.dict[mac_address]['rssi'].append(self.value[1][i])
                            self.dict[mac_address]['txpower'].append(self.value[2][i])
                        
                        # Automatically creates a dictionary and parses each beacon information.
                        self.beacon_dict = [{'MAC': Mac, 'RSSI': values['rssi'], 'POWER': values['txpower']} for Mac, values in self.dict.items()]

                    # List management for return values.
                    if (Pkt % 10 == 0):
                        del self.value[0][0:]
                        del self.value[1][0:]
                        del self.value[2][0:]

                    # Export acquired beacon information from each gateway.
                    if (EXPORT_ACTIVE and save_Pkt % MAX_PKT == 0):
                        
                        # Save the received beacon information every MAX_Pkt '5000'.
                        func_export(self.token, self.save_info[0], self.save_info[1], self.save_info[2])
                        
                        del self.save_info[0][0:]
                        del self.save_info[1][0:]
                        del self.save_info[2][0:]
                        
            # Somtimes HTML rendering causes a huge delay, so we just returning the extrected values, and HTML status code.
            # If you need rendering on HTML, add return render_dictlate("index.html")
            return jsonify(self.beacon_dict), 200
        
# A child class that inherits and executes HookServer.
class RunFlaskApp(HookServer):
    def __init__(self, token, port):
        
        # Inherit variables from parent class.
        super().__init__(token, port)
        
        # Handling of the HookServer execution.
        try:
            # Where host IP 0.0.0.0 that grants external access.
            self.server_app.run(host='0.0.0.0', port=self.port, use_reloader=False, threaded=True)
            
        except:
            print('[{}] Server occured error !!'.format(self.token))
            os.kill(os.getpid(), signal.SIGTERM)
            
