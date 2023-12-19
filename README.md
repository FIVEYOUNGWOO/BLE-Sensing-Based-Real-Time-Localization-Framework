## BLE-WiFi-Based Real-Time Localization Framework

This code supports a real-time location estimation system (RTLS) framework, utilizing multiple gateways and beacons for detecting and tracking various objects indoors.

Within this RTLS framework, BLE packets broadcast by several beacons are collected by each gateway. The collected data is logged over HTTP in JSON format.

The RSSI values measured by the gateways are processed in real-time using Flask, enabling the parsing and recording of each beacon's information. Furthermore, The estimated location is automatically calculated from quadrilateral methods in the local server, it displays the estimated coordinates of each beacon on a graphical map in PyQt.

We have ascertained that the positioning accuracy of the RTLS framework achieved a precision of 94% in a 3X7 m indoor scenario.

## Requirements
- (HW) MINEW IoT G1 gateway
- (HW) MINEW E5, E7, E8 beacons
- (SW) Flask
- (SW) Python
- (SW) PyQt
