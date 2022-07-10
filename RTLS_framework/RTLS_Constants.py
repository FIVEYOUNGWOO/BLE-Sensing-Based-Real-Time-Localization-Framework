######################################################## NOTE #######################################################
# Date : 2022-05-27 to 2022-06-30                                                                                   #
#                                                                                                                   #
# A collection of constants and coefficients                                                                        #
#####################################################################################################################

import socket

############################################################################################
# For ServerHandler.py 
PROCESSOR_BOL = []                                # Number of running multi-processes [list].
EXPORT_ACTIVE = True                              # Export csv file per each gateway devices [boolean].
MAX_PKT = 5000                                    # Maximum number of packet.
AT_LEAST_INFO = 10                                # Minimum number of beacon information for calculating after flush.

############################################################################################
# For filter, calculation, and algorithms.
ENV_FACTOR = 1.7

# Indoors coefficient when there is line of sight to the router.
# 1.6 to 1.8 for indoors when there is line of sight to the router.
# 2.7 to 3.5 for urban areas;
# 3.0 to 5.0 in suburban areas;

############################################################################################
# For read JSON function.
PREFIX_HTTP = 'http://'                          # Prefix of http address.
DELIMITER_PORT = ':'                             # Delimiter of port number.
DELIMITER_TOKEN = '/'                            # Delimiter of gateway token.
URL= socket.gethostbyname(socket.gethostname())  # Find your localhost IP address automatically.