# -*- coding: utf-8 -*

import random
import threading

import kivy
import thread

from support import random_mac_address

kivy.require('1.9.1') # replace with your current kivy version !
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.vertex_instructions import BorderImage
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.togglebutton import ToggleButton

from kivy.config import Config


import time
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.switch import Switch
import datetime




x = .05
y = 1-.1
yAdd = -.1
xAdd = .10
buttonWidth = .2
dropWidth = .2
countertimeZ = 0.0
lasttimeZ = 0.0
isOn = False
adapterSelected = None
networkSelected = None
isInternet = False

class MyLabel(Label):
    def __init__(self, **kwargs):
        super(MyLabel,self).__init__(**kwargs)
        #  color=(0, 0, 0, 1), halign="right"
        self.color = (0, 0, 0, 1)
        self.halign = "left"
        self.valign = "middle"
        if not kwargs.has_key("size_hint"):
            self.size_hint=(buttonWidth,.05)
        self.bind(size=self.setter("text_size"))

class SimpleCountDownTimer:
    def __init__(self, label, timeLeft): # time left in seconds
        self.label = label
        self.timeLeft = timeLeft
        self.startTime = int(time.time())


    def setTimeLeft(self, t): #time in seconds, resets count down
        self.timeLeft = t
        self.startTime = int(time.time())

    def addTime(self, t):
        self.timeLeft+=t

    def update(self):
        seconds=self.timeLeft - (int(time.time())- self.startTime)
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        self.label.text = "%02d:%02d:%02d" % (h, m, s)

    def left(self):
        return self.timeLeft - (int(time.time())- self.startTime)

class SimpleCountUpTimer:
    def __init__(self, label): # time left in seconds
        self.label = label
        self.startTime = int(time.time())


    def reset(self): # resets count up
        self.startTime = int(time.time())

    def addTime(self, t):
        self.startTime -= datetime.timedelta(seconds=t)

    def update(self):
        seconds=int(time.time())-self.startTime
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        self.label.text = "%02d:%02d:%02d" % (h, m, s)


class MultiLineLabel(Label):
    def __init__(self, **kwargs):
        super(MultiLineLabel, self).__init__( **kwargs)
        self.text_size = self.size
        self.bind(size= self.on_size)
        self.bind(text= self.on_text_changed)
        self.size_hint_y = None # Not needed here
        self.numLines = 18
        # self.text_size = self.size
        # # self.bind(size= self.on_size)
        # self.bind(text= self.on_text_changed)
        #
        # self.bind(size=self.setter("text_size"))
        self.halign = "center"
        self.valign = "top"
        self.markup = True
        # self.size_hint_y = None # Not needed here
        self.lines = ["\n"]*self.numLines


    def on_size(self, widget, size):
        self.text_size = size[0], None
        self.texture_update()
        if self.size_hint_y == None and self.size_hint_x != None:
            self.height = max(self.texture_size[1], self.line_height)
        elif self.size_hint_x == None and self.size_hint_y != None:
            self.width  = self.texture_size[0]

    def on_text_changed(self, widget, text):
        self.on_size(self, self.size)

    def update_status(self, status):
        if(len(status)>50):
            status = "[size="+str(int(max(15.0 - max((len(status)-50)/5.0,0.0),1.0)))+"]"+status+"[/size]"

        self.lines += [status+"\n"]
        if(len(self.lines)>self.numLines):
            self.lines = self.lines[-self.numLines:]
        self.text = "".join(self.lines)

    def clear(self):
        self.lines = ["\n"]*self.numLines
        self.update_status()


def textScaleDropDown(str):
    s = len(str)
    if(s>40):
        s = 40
        str = str[:40]
    size = max(15.0 - max((len(str)-6.0)/5.0,0.0),1.0)
    return [str, size]

def scaleButton(btn,str=None):
    if (str is not None):
        btn.text = str
    btn.text = textScaleDropDown(btn.text)[0]
    btn.font_size = textScaleDropDown(btn.text)[1]


programOutput = MultiLineLabel(pos_hint={'x':x+xAdd*4.5, 'y':y-.5},size_hint=(.45,.4),color = (1,0,0,1),valign="middle",font_size='15sp')
networks = DropDown(max_height=300, do_scroll_x=True)
networkButton = Button(text='Choose Network',  size_hint=(buttonWidth,.05),pos_hint={'x':x+xAdd, 'y':y+yAdd})
# Get adapter information
from  xfinity_connector import *

interfaceInformation = InterfaceInformationLoader()
interfaceInformation.refresh()
adapters = []
for interface in interfaceInformation.adapters:
    adapters += [NetworkAdapter(interface[0],interface[1])]

btnMap = {} # buttons to adapters
def onSelectInterface(dropDown,data):
    if(not isOn):
        adapter = btnMap.get(data[0])
        programOutput.update_status("Adapter \"" + adapter.hardwareName +"\" has been selected!")
        data[1].text = adapter.hardwareName
        scaleButton(data[1])
        global adapterSelected
        global networkSelected
        adapterSelected = adapter
        networkButton.text="Choose Network"
        networkSelected = None
        networks.clear_widgets()
        #Set Network options
        availNets = sorted(adapter.getAvailableNetworks(),key=lambda x:x.strength,reverse=True)

        for network in availNets:
            ntkbtn = Button(text=network.ssid, size_hint_y=None, height=44)
            scaleButton(ntkbtn)
            ntkbtn.text += " ["+str(network.strength)+"%]"
            btnMap[ntkbtn] = network
            ntkbtn.bind(on_release=lambda ntkbtn: networks.select(ntkbtn))
            networks.add_widget(ntkbtn)


        programOutput.update_status("Now select the Xfinity network from the list")
        programOutput.update_status("")
    else:
        programOutput.update_status("Please set to off before changing adapter")
    return None


def onSelectNetwork(dropDown,data):
    network = btnMap[data]
    programOutput.update_status("Network "+network.ssid+" has been selected! ")
    networkButton.text = network.ssid
    scaleButton(networkButton)
    networkButton.text += " ["+str(network.strength)+"%]"
    global networkSelected
    networkSelected = network
    programOutput.update_status("Now set network refresh rate & then turn on the clocks")
    return None




class MyList(list):
    def __init__(self):
        self.l = threading.Lock()

    def append(self, val):
        try:
            self.l.acquire()
            list.append(self, val)
        finally:
            if self.l.locked():
                self.l.release()
    def pop(self, index=0):
        val = ""
        try:
            self.l.acquire()
            val = list.pop(self, index)
        finally:
            if self.l.locked():
                self.l.release()
        return val



class MyApp(App):
    def build(self, **kwargs):
        Window.clearcolor = (1, 1, 1, 1)
        self.title = "Xfinity Wifi Connector"
        self.icon = "imgs/appIcon.png"
        layout = FloatLayout()
        # super(LoginScreen, self).__init__(**kwargs)


        layout.add_widget(MyLabel(text='Adapters: ', pos_hint={'x':x, 'y':y}))

        #Create adapters button
        adapterDropDown = DropDown(max_height=300,do_scroll_x=True)
        adapterButton = Button(text='Choose Adapter',  size_hint=(buttonWidth,.05),pos_hint={'x':x+xAdd, 'y':y})
        for adapter in adapters:
            btn = Button(text=adapter.hardwareName, size_hint_y=None, height=44)
            btnMap[btn]=adapter
            scaleButton(btn)
            btn.bind(on_release=lambda btn: adapterDropDown.select([btn,adapterButton]))

            # Add the button inside the dropdown
            adapterDropDown.add_widget(btn)



        adapterButton.bind(on_release=adapterDropDown.open)

        # Listen for the selection in the dropdown list and
        adapterDropDown.bind(on_select=onSelectInterface)

        downArrow  = Image(source='imgs/down-arrow2.png',pos_hint={'x':x+xAdd+buttonWidth-.04, 'y':y},size_hint=(.05,.05))
        # adapterButton.add_widget(downArrow)
        layout.add_widget(adapterButton)
        layout.add_widget(downArrow)

        # Networks button
        layout.add_widget(MyLabel(text='Networks: ', pos_hint={'x':x, 'y':y+yAdd}))
        networkButton.bind(on_release=networks.open)
        networks.bind(on_select=onSelectNetwork)



        downArrow  = Image(source='imgs/down-arrow2.png',pos_hint={'x':x+xAdd+buttonWidth-.04, 'y':y+yAdd},size_hint=(.05,.05))

        layout.add_widget(networkButton)
        layout.add_widget(downArrow)

        layout.add_widget(MyLabel(text='Refresh Rate: ', pos_hint={'x':x, 'y':y+yAdd*2}))

        timeLabel = MyLabel(text='57 mins', pos_hint={'x':x+xAdd+buttonWidth, 'y':y+yAdd*2})

        st = Slider(min=10, max=70, value=57, size_hint=(buttonWidth,.05),pos_hint={'x':x+xAdd, 'y':y+yAdd*2},step=1)
        def OnSliderValueChange(instance,value):
            timeLabel.text = str(value)+" mins"

        st.bind(value=OnSliderValueChange)

        layout.add_widget(timeLabel)
        layout.add_widget(st)

        l = MyLabel(text='Time Till Next Refresh:', pos_hint={'x':x, 'y':y+yAdd*3})
        layout.add_widget(l)

        l = MyLabel(text = "00:00:00",pos_hint={'x':x+xAdd+.045, 'y':y+yAdd*4.25},font_size='25sp',size_hint=(buttonWidth,.05))
        refreshCountDown= SimpleCountDownTimer(l,10*60)
        layout.add_widget(l)

        l = MyLabel(text='Time On Connection:', pos_hint={'x':x, 'y':y+yAdd*5})

        layout.add_widget(l)

        l = MyLabel(text = "00:00:00",pos_hint={'x':x+xAdd+.045, 'y':y+yAdd*6.20},font_size='25sp',size_hint=(buttonWidth,.05))
        connectionTimer = SimpleCountUpTimer(l)
        layout.add_widget(l)



        img = Image(source='imgs/tex.png',pos_hint={'x':x+xAdd*3.5, 'y':y-.57}, size_hint=(.65,.65), allow_stretch=True)
        layout.add_widget(img)
        # commandStream = ScrollView()

        programOutput.update_status("Waiting to be turned on!")
        programOutput.update_status("Please pick adapter and network!")
        layout.add_widget(programOutput)

        #add xfinity logo   pos_hint={'x':x+xAdd*4.5, 'y':y-.5},size_hint=(.45,.4),color = (1,0,0,1),valign="middle",font_size='15sp'
        xfinityImage = Image(source='imgs/xfinity-logo.png',pos_hint={'x':x+xAdd*5.5, 'y':y-.8},size_hint=(.25,.25))
        layout.add_widget(xfinityImage)


        global isInternet
        def holdValue(instance, value):
            global isInternet
            if(not isInternet):
                instance.state = 'normal'
            else:
                instance.state = 'down'


        internet_connected = ToggleButton(text = 'Status: Internet Connected', state='normal',pos_hint={'x':x+xAdd*5, 'y':y-.825},size_hint=(.35,.07), color = (0,1,0,1),font_size='20sp')

        global isInternet
        isInternet = is_internet()
        if(isInternet):
            internet_connected.state = 'down'
            internet_connected.text = 'Status: Internet Connected'
            internet_connected.color = (0,1,0,1)
        else:
            internet_connected.state = 'normal'
            internet_connected.text = 'Status: No Internet'
            internet_connected.color = (1,0,0,1)

        internet_connected.bind(state=holdValue)
        layout.add_widget(internet_connected)

        global isOn

        switch = ToggleButton(text = 'Off', state='normal', pos_hint={'x':x+buttonWidth*.35, 'y':y+yAdd*8},size_hint=(.25,.1), color = (1,0,0,1))

        threadSafeList = MyList() #Updates from network reset thread
        global thState
        thState = None
        def cb(dt):
            global lasttimeZ
            global countertimeZ
            global isInternet
            global thState
            if isOn:
                connectionTimer.update()
                refreshCountDown.update()
                if refreshCountDown.left() < 0 and( thState==None or not thState.locked()):
                    thState =callback(switch, 'down', True)
            while len(threadSafeList) > 0:
                programOutput.update_status(threadSafeList.pop())
            countertimeZ += dt

            # Update Internet Label
            if(countertimeZ > lasttimeZ + 20.0):
                print "Tick tock"
                # global isInternet
                isInternet = is_internet()
                if(isInternet):
                    internet_connected.state = 'down'
                    internet_connected.text = 'Status: Internet Connected'
                    internet_connected.color = (0,1,0,1)
                else:
                    internet_connected.state = 'normal'
                    internet_connected.text = 'Status: No Internet'
                    internet_connected.color = (1,0,0,1)
                lasttimeZ = countertimeZ


        Clock.schedule_interval(cb, .5)

        #create worker thread (resets connection)
        #create thread safe list
        # On/Off Button
        def callback(instance, value,auto=False):
            global isOn
            if(adapterSelected is not None and networkSelected is not None):
                if(value == 'down'):
                    instance.text="On"
                    instance.color=(0,1,0,1)
                    programOutput.update_status("")
                    programOutput.update_status("Network resetting")
                    resetNetwork(adapterSelected,networkSelected,threadSafeList)
                    refreshCountDown.setTimeLeft(st.value*60)
                    connectionTimer.reset()
                    isOn = True
                else:
                    instance.text = "Off"
                    instance.color=(1,0,0,1)
                    isOn = False
                    programOutput.update_status("Stopping timers! Network will not be automatically reset")
            elif value == 'down':
                programOutput.update_status("Please select adapter and corresponding network!")
                instance.state = 'normal'


        switch.bind(state=callback)
        layout.add_widget(switch)


        s = Screen(name='Xfinity Wifi Connector')
        s.add_widget(layout)
        sm = ScreenManager()
        sm.add_widget(s)

        return sm





if __name__ == '__main__':
    MyApp().run()

