from subprocess import check_output
from subprocess import call
import re
import time
import thread
from support import interface as spoof, random_mac_address
from splinter import Browser
import random
import socket

class InterfaceInformationLoader:
    def __init__(self):
        self.adapters = None  # List of adapter information

    def refresh(self):
        rawNetsh = check_output(["netsh", "wlan","show", "interfaces"])
        r = []
        reg = re.compile("Name \s* : ")
        reg1 = re.compile("Description \s* : ")
        reg2 = re.compile("Physical address \s* : ")
        reg3 = re.compile("State \s* : ")
        reg4 = re.compile("SSID \s* : ")

        split = reg.split(rawNetsh)[1:]
        for s in split:
            name = s.split("\n")[0].strip()
            hardware = reg1.split(s)[1].split("\n")[0].strip()
            mac = reg2.split(s)[1].split("\n")[0].strip()
            state = reg3.split(s)[1].split("\n")[0].strip()
            SSID = ""
            if state == "connected":
                SSID = reg4.split(s)[1].split("\n")[0].strip()
            r += [[name, hardware,mac,state, SSID]]
        self.adapters = r

interfaceInformation = InterfaceInformationLoader()

class Bssid:
    def __init__(self, mac, signal, connectionType):
        self.mac = mac
        self.signal = signal
        self.connectionType = connectionType

class Network:
    """
    Container for a wireless network
    """
    def __init__(self, ssid, strength, bssids):
        self.ssid =ssid # network name
        self.strength = strength # Strength of network
        self.bssids=bssids #list of access point mac addresses

    def __str__(self):
        return self.ssid+" has strength "+str(self.strength)+"% and "+str(len(self.bssids))+" access points in range"

class NetworkAdapter:
    """
    Container for a wifi adapter.
    Can query networks, mac address, hardware id, connect/disconnect, etc
    """
    def __init__(self, osName, hardwareName):
        self.osName = osName
        self.hardwareName = hardwareName

    def __str__(self):
        return self.hardwareName +" - "+self.osName

    def getConnectionState(self): # Returns connection state & SSID (if connected)
        # Get hardware name & mac
        interfaceInformation.refresh()
        for x in interfaceInformation.adapters:
            if x[0] == self.osName:
                 return x[3], x[4]

    def getAvailableNetworks(self):
        rawNetsh = check_output("netsh wlan show networks interface=\""+self.osName+"\" mode=Bssid")
        ssidsRE = re.compile("SSID [0-9]* :")
        bssidsRE = re.compile("BSSID *[0-9]*\s*: ")
        signalRE = re.compile("Signal \s* : ")
        radioRE = re.compile("Radio type \s* : ")
        authRE = re.compile("Authentication \s* : ")
        networks = []
        for ssid in ssidsRE.split(rawNetsh)[1:]: # For each SSID
            ssidName = ssid.split("\n")[0].strip()
            auth = authRE.split(ssid)[1].split("\n")[0].strip()
            bssids = []
            for bssid in bssidsRE.split(ssid)[1:]: # Each bssid - Record mac, strength, signal type
                signal = signalRE.split(bssid)[1].split("\n")[0].strip().strip("%")
                radio = radioRE.split(bssid)[1].split("\n")[0].strip()
                mac = bssid.split("\n")[0].strip()
                bssids += [Bssid(mac=mac, signal=signal, connectionType=radio)]
            signal_strength = max(int(p.signal) for p in bssids)
            if auth == "Open" and ssidName != '':
                networks += [Network(ssid=ssidName, strength=signal_strength, bssids=bssids)]
        return networks

    def getMacAddress(self):
        interfaceInformation.refresh()
        for x in interfaceInformation.adapters:
            if x[0] == self.osName:
                return x[2]
        return None

    def setMacAddress(self, mac): # Note Resets Adapter
        spoofer = spoof.get_os_spoofer()
        spoofer.set_interface_mac(self.osName, mac)
        return None

    def connectToNetwork(self, network):
        try:
            out = check_output("netsh wlan connect "+network.ssid.strip(" ")+" ssid="+network.ssid+" interface=\""+self.osName+"\"")
        except Exception, err:
            out = call("netsh wlan connect "+network.ssid.strip(" ")+" ssid="+network.ssid+" interface=\""+self.osName+"\"")
        # print out
        return None

    def disconnect(self):
        out = check_output("netsh wlan disconnect interface=\""+self.osName+"\"")
        return None

    def reset(self):
        """
        resets adapter and reconnects to the network it's currently connected to
        :return:
        """
        return None


def register_mac_with_xfinity(mac,output, count = 0,time_out = 30):
    if(count >= 2):
        return False
    if count > 0:
        output.append("Uncertain if successful, trying again")

    b = Browser('phantomjs') #'phantomjs' #webdriver.PhantomJS()
    output.append("Browser Launched")
    success = False
    try:
        url = "https://xfinity.nnu.com/xfinitywifi/?client-mac="+mac.lower()
        socket.setdefaulttimeout(60)
        b.visit(url)
        if b.is_text_present("Your complimentary session has expired."):
            # b.quit()
            output.append("Mac has already been registered")
            success = True

        if(success==False):
            b.select("rateplanid","spn")
            # print b.url
            email = str(random.randrange(10000000,99999999))+'@comcast.com'
            zip_code = random.randrange(10000,99999)
            try:
                b.fill('spn_postal', zip_code)
                b.fill('spn_email', email)
            except:
                pass

            try:
                b.check('spn_terms')
            except:
                pass

            url = b.url

            b.find_by_value('submit').first.click()
            b.find_by_value('submit').first.click()
            output.append("Submitting Mac Request, Waiting for result")
            waitTime = 0
            while(b.url == url and waitTime < time_out): #total shit...
                time.sleep(1)
                waitTime += 1
                if waitTime>0 and waitTime%15 == 0:
                    output.append("Waiting for request to complete ... ["+str(waitTime)+"s]")


            #TODO validate..... ie did webpage load/etc
            if(b.is_text_present("Your complimentary session is now active!")):
                success = True

            if(waitTime >= time_out and not success):
                success = register_mac_with_xfinity(mac,output,count=count+1, time_out=time_out)


    except Exception, err:
        print err.message
        print b.url
        print b.html
        success = register_mac_with_xfinity(mac, output, count=count+1, time_out=time_out)
        pass
    finally:
        b.quit()
        return success

def resetNetwork(adapter,network,statusOut):
    def run():
        macRegistered = False
        newMac = "02" + random_mac_address()[2:]

        statusOut.append("Newly generated mac is \""+newMac+"\"")
        adapterState = adapter.getConnectionState()
        print "\""+adapterState[0]+"\""
        print "\""+adapterState[1]+"\""
        if(adapterState[0] == 'connected' and adapterState[1] == network.ssid):
            statusOut.append("Adapter is connected to the network, attempting to register mac early..")
            macRegistered = register_mac_with_xfinity(newMac,statusOut,time_out=3) # Fails when internet is not active
            if macRegistered:
                statusOut.append("Mac registered successfully")
            else:
                statusOut.append("Mac registration failed...")

        statusOut.append("Changing mac address...")
        adapter.setMacAddress(newMac)
        statusOut.append("Mac address is now "+adapter.getMacAddress())
        time.sleep(3)
        statusOut.append("Connecting to "+network.ssid)
        adapter.connectToNetwork(network)

        time.sleep(3)
        adapterState = adapter.getConnectionState()
        statusOut.append("adapter connected to "+adapterState[1])

        if not macRegistered:
            statusOut.append("Registering mac ....")
            if not register_mac_with_xfinity(newMac,statusOut,count=-1,time_out=45):
                statusOut.append("Mac registration failed...")
    thread.start_new_thread(run, ())
    return None

def is_internet(host="8.8.8.8", port=53,time_out=5):
    r = False
    try:
        s = socket.create_connection((host, port),timeout=time_out)
        s.close()
        r = True
    except Exception as ex:
        print ex.message
        pass

    return r

