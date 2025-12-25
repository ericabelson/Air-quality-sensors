
from getmac import get_mac_address
import serial.tools.list_ports

def findPort(find):
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        currentPort = str(p)
        if(currentPort.endswith(find)):
            return(currentPort.split(" ")[0])


def findDuePort():
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        currentPort = str(p[2])
        if(currentPort.find("PID=2341")>=0):
            return(p[0])

def findNanoPorts():
    ports = list(serial.tools.list_ports.comports())
    outPorts = []
    for p in ports:
        currentPort = str(p)
        if(currentPort.endswith("FT232R USB UART")):
            outPorts.append(currentPort.split(" ")[0])

    return outPorts

def findSabrentPorts():
    ports = list(serial.tools.list_ports.comports())
    outPorts = []
    for p in ports:
        currentPort = str(p[2])
        if(currentPort.find("PID=067B")>=0):
            outPorts.append(str(p[0]).split(" ")[0])
    return outPorts

def findOzonePort():
    ports = list(serial.tools.list_ports.comports())
    ozonePort = []
    for p in ports:
        currentPort = str(p[2])
        if(currentPort.find("PID=067B")>=0):
            ozonePort.append(str(p[0]).split(" ")[0])
    return ozonePort


def findMacAddress():
    macAddress= get_mac_address(interface="eth0")
    if (macAddress!= None):
        return macAddress.replace(":","")

    macAddress= get_mac_address(interface="docker0")
    if (macAddress!= None):
        return macAddress.replace(":","")

    macAddress= get_mac_address(interface="enp1s0")
    if (macAddress!= None):
        return macAddress.replace(":","")

    macAddress= get_mac_address(interface="wlan0")
    if (macAddress!= None):
        return macAddress.replace(":","")

    return "xxxxxxxx"



dataFolderReference       = "/home/utsensing/utData/reference"
dataFolderMQTTReference   = "/home/utsensing/utData/referenceMQTT"
dataFolder                = "/home/utsensing/utData/raw"
dataFolderMQTT            = "/home/utsensing/utData/rawMQTT"

duePort               = findDuePort()
nanoPorts             = findNanoPorts()
ozonePort             = findOzonePort()
show2Port             = findPort("CP2104 USB to UART Bridge Controller")
macAddress            = findMacAddress()
latestDisplayOn       = True
latestOn              = True

# MQTT Configuration
# By default, MQTT is disabled for local-only operation.
# If you want to use MQTT, install a local broker (e.g., Mosquitto)
# and update the settings below.
#
# For local Mosquitto broker:
#   mqttBroker = "localhost"
#   mqttPort = 1883
#
# SECURITY NOTE: External MQTT brokers have been removed.
# All sensor data stays local on your network.

mqttOn                   = False          # Set True to enable MQTT
mqttCredentialsFile      = 'mintsXU4/credentials.yml'
mqttBroker               = "localhost"    # Local MQTT broker only
mqttPort                 = 1883           # Standard MQTT port (no TLS for local)


gpsPort               = findPort("GPS/GNSS Receiver")


if __name__ == "__main__":
    # the following code is for debugging
    # to make sure everything is working run python3 mintsDefinitions.py 
    print("Mac Address          : {0}".format(macAddress))
    print("Data Folder Reference: {0}".format(dataFolderReference))
    print("Data Folder Raw      : {0}".format(dataFolder))
    print("Due Port             : {0}".format(duePort))
    print("Ozone Port           : {0}".format(ozonePort))
    print("GPS Port             : {0}".format(gpsPort))
    print("Latest On                  : {0}".format(latestOn))
    print("MQTT On                    : {0}".format(mqttOn))
    print("MQTT Credentials File      : {0}".format(mqttCredentialsFile))
    print("MQTT Broker and Port       : {0}, {1}".format(mqttOn,mqttPort))

    #-------------------------------------------#
    print("Nano Ports :")
    for dev in nanoPorts:
        print("\t{0}".format(dev))
