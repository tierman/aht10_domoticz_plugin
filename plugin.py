#           AHT10 Plugin
#
#           Author:     tjonczyk, 2023
#

"""
<plugin key="AHT10" name="AHT10" author="tjonczyk" version="0.0.1">
    <description>
        AHT10 Sensor Plugin.<br/><br/>
        Specify i2c address of device.<br/>
    </description>
    <params>
        <param field="Address" label="I2C Address" width="300px" required="true" default="0x38"/>
    </params>
</plugin>
"""

import smbus, time, Domoticz


class Aht10Device:
    CONFIG = [0x08, 0x00]
    MEASURE = [0x33, 0x00]

    def __init__(self, bus, i2CAddress):
        self.bus = smbus.SMBus(bus)
        self.addr = i2CAddress
        self.bus.write_i2c_block_data(self.addr, 0xE1, self.CONFIG)
        time.sleep(0.2)  # Wait for AHT to do config (0.2ms from datasheet)

    # getData - gets temperature and humidity
    # returns tuple of collected data. getData[0] is Temp, getData[1] is humidity
    def getData(self):
        byte = self.bus.read_byte(self.addr)
        self.bus.write_i2c_block_data(self.addr, 0xAC, self.MEASURE)
        time.sleep(0.5)
        data = self.bus.read_i2c_block_data(self.addr, 0x00)
        temp = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
        ctemp = ((temp * 200) / 1048576) - 50
        hum = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
        chum = int(hum * 100 / 1048576)
        return round(ctemp, 1), chum


class BasePlugin:
    i2cAddress = None

    def onStart(self):
        Domoticz.Log("Address: " + Parameters["Address"])
        # Find devices that already exist, create those that don't
        self.i2cAddress = 0x38 # //hex(literal_eval(Parameters["Address"]))
        destination = str("ATH10: " + hex(self.i2cAddress))

        Domoticz.Log("Endpoint '" + destination + "' found.")
        deviceFound = False
        for Device in Devices:
            if (("Name" in Devices[Device].Options) and (
                    Devices[Device].Options["Name"] == destination)): deviceFound = True
        if (deviceFound == False):
            Domoticz.Device(Name=destination, Unit=16, TypeName="Temp+Hum", Options={"Name": destination}).Create()

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called, with address: " + hex(self.i2cAddress))
        m = Aht10Device(1, self.i2cAddress)
        data = m.getData()
        destination = str("ATH10: " + hex(self.i2cAddress))

        for Device in Devices:
            if (("Name" in Devices[Device].Options) and (Devices[Device].Options["Name"] == destination)):
                Devices[Device].Update(1, str(data[0]) + ';' + str(data[1]) + ';0')
                Domoticz.Log("update device:" + str(data[0]) + ';' + str(data[1]))

global _plugin
_plugin = BasePlugin()


def onStart():
    global _plugin
    _plugin.onStart()


def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)


def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

