#! /usr/bin/env python2.6
# -*- coding: utf-8 -*-

"""
Sipura VOIP
Authors: GlennNZ

Sipura Linksys Cisco VOIP Indigodomo Plugin

"""

import datetime
import time as t
import urllib2
import os
import shutil
import socket
import logging
import requests

from ghpu import GitHubPluginUpdater

try:
    import indigo
except:
    pass

# Establish default plugin prefs; create them if they don't already exist.
kDefaultPluginPrefs = {
    u'configMenuPollInterval': "300",  # Frequency of refreshes.
    u'configMenuServerTimeout': "15",  # Server timeout limit.
    # u'refreshFreq': 300,  # Device-specific update frequency
    u'configUpdaterForceUpdate': False,
    u'configUpdaterInterval': 24,
    u'updaterEmail': "",  # Email to notify of plugin updates.
    u'updaterEmailsEnabled': False  # Notification of plugin updates wanted.
}


class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        pfmt = logging.Formatter('%(asctime)s.%(msecs)03d\t[%(levelname)8s] %(name)20s.%(funcName)-25s%(msg)s', datefmt='%Y-%m-%d %H:%M:%S')
        self.plugin_file_handler.setFormatter(pfmt)

        try:
            self.logLevel = int(self.pluginPrefs[u"logLevel"])
        except:
            self.logLevel = logging.INFO

        self.indigo_log_handler.setLevel(self.logLevel)
        self.logger.debug(u"logLevel = " + str(self.logLevel))

        self.debugLog(u"Initializing Cisco/Sipura VOIP plugin.")

        self.timeOutCount = 0

        self.deviceNeedsUpdated = ''
        self.prefServerTimeout = int(self.pluginPrefs.get('configMenuServerTimeout', "15"))
        self.updater = GitHubPluginUpdater(self)
        self.configUpdaterInterval = self.pluginPrefs.get('configUpdaterInterval', 24)
        self.configUpdaterForceUpdate = self.pluginPrefs.get('configUpdaterForceUpdate', False)

        self.useNumberConversion = self.pluginPrefs.get('useNumberConversion',False)
        self.folderLocation = self.pluginPrefs.get('folderLocation','')
        #self.sipServer = self.pluginPrefs.get('configUpdaterForceUpdate', False)
        self.deviceId = 0
        self.ringing = False
        self.connected = False
        self.callType =''
        self.connectTime = ''
        self.kill = True
        self.checkTime = t.time()
        self.triggers = { }
        self.currentNumber =''

        self.numberstoConvert = []



    def __del__(self):

        self.debugLog(u"__del__ method called.")
        indigo.PluginBase.__del__(self)

    def closedPrefsConfigUi(self, valuesDict, userCancelled):

        self.debugLog(u"closedPrefsConfigUi() method called.")

        if userCancelled:
            self.debugLog(u"User prefs dialog cancelled.")

        if not userCancelled:

            self.debugLog(u"User prefs saved.")
            indigo.server.log(u"Debugging Level: {0}".format(self.logLevel))

        self.useNumberConversion = self.pluginPrefs.get('useNumberConversion',False)
        self.folderLocation = self.pluginPrefs.get('folderLocation','')

        if self.useNumberConversion:
            self.loadFileNumbers()
        else:
            self.numberstoConvert = []
            self.logger.debug(u'Numbers to Convert Removed:' +str(self.numberstoConvert))

        return True

    def loadFileNumbers(self):

        self.logger.debug(u'loadFile of Number Conversions called')

        self.folderLocation = self.pluginPrefs.get('folderLocation', '')

        if self.folderLocation == '':
            self.logger.info(u'Folder Name cannot be empty')
            return
        self.numberstoConvert = []
        try:
            folder = self.folderLocation
            filename = 'numbersConvert.txt'
            #f = open(folder+'/'+filename, 'r')
            with open(folder+'/'+filename, 'rb') as fp:
                for i in fp.readlines():
                    tmp = i.split(',')
                    try:
                        self.numberstoConvert.append((str(tmp[0].strip()), str(tmp[1].strip())))
                    except Exception as error:
                        self.logger.error(u'Error with numbersConvert.txt file Data Format File: are they comma seperated with each on new line?')
                        self.logger.debug(error)
                        pass
            self.logger.debug(self.numberstoConvert)


        except Exception as error:
            self.logger.info(u'Exception within loadFileNumbers:'+str(error))


        return

    def calltoLoadFile(self, valuesDict):
        self.logger.debug(u'LoadFile Config Button Pressed')
        self.loadFileNumbers()
        return

    # Start 'em up.
    def deviceStartComm(self, dev):

        self.debugLog(u"deviceStartComm() method called.")
        self.debugLog(u'deviceID equals:'+str(dev.id))


        self.debugLog(u"Starting Device:  {0}:".format(dev.name))
        dev.updateStateOnServer("currentNumber", '')
        dev.updateStateOnServer("deviceStatus", '')
        dev.updateStateOnServer("callType", '')
        update_time = t.strftime("%m/%d/%Y at %H:%M")
        #dev.updateStateOnServer('deviceLastUpdated', value=update_time)
        dev.updateStateOnServer('callTime', value='')
        self.deviceId = dev.id
        dev.updateStateOnServer('deviceOnline', False)
        self.kill = False
        if self.useNumberConversion:
            self.loadFileNumbers()





    # Shut 'em down.
    def deviceStopComm(self, dev):

        self.debugLog(u"deviceStopComm() method called.")
        indigo.server.log(u"Stopping SIPURA device: " + dev.name)
        dev.updateStateOnServer('deviceOnline', False)
        self.kill = True

    def forceUpdate(self):
        self.updater.update(currentVersion='0.0.0')

    def checkForUpdates(self):
        if self.updater.checkForUpdate() == False:
            indigo.server.log(u"No Updates are Available")

    def updatePlugin(self):
        self.updater.update()

    def runConcurrentThread(self):
            # Gra
            # b the first device (don' want to multithread0

            while self.stopThread == False:

                for dev in indigo.devices.itervalues('self'):

                    if dev.configured and dev.enabled:
                        dev.updateStateOnServer('deviceOnline', True)

                        porttouse = dev.pluginProps['sourcePort']
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s.settimeout(1)

                        self.logger.info(u"Socket Connection Opened on port:"+str(porttouse))

                        try:
                            s.bind(('', int(porttouse)))

                        except socket.error, msg:

                            self.errorLog(u'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + str(msg[1]) )
                            dev.updateStateOnServer('deviceOnline', False)
                            dev.setErrorStateOnServer(u'Offline')
                            self.sleep(5)



                        try:
                            while True and dev.enabled and dev.configured and self.kill == False:


                                # Only support one VOIP device
                                # very likely easier way to do it


                                #self.debugLog(u"MainLoop running:  {0}:".format(dev.name))
                                    #How to limit indigo that only one device is allowed?


                                try:

                                    self.updateStates(dev)

                                    data, addr = s.recvfrom(9024)



                                    self.parseData(dev,data,addr)



                                except socket.timeout:

                                    # or no data received.
                                    #self.debugLog(u"SOCKET Error  {0}:".format(e))
                                    pass

                                if self.connected or self.ringing:
                                    self.sleep(0.2)
                                else:
                                    self.sleep(1)

                        except self.stopThread:
                            self.debugLog(u'Restarting/or error. Stopping SpiruaVOIP thread.')
                            s.close()
                            pass


                self.debugLog(u' No Configured & Enabled Device:')
                    # How to limit indigo that only one device is allowed?
                self.sleep(60)

    def updateStates(self,dev):


        timeDifference = int(t.time() - self.checkTime)

        if timeDifference <= 10:

               # self.debugLog(u' Update States: Time Difference <30 returned: '+unicode(timeDifference))
            return


        self.debugLog(u'Update States Run: for Device: '+str(dev.name))

        if self.connected:
            lengthcall = t.time() - self.connectTime
            m, s = divmod(lengthcall, 60)
            h, m = divmod(m, 60)
            formatedlength = "%d:%02d:%02d" % (h, m, s)

            dev.updateStateOnServer('durationCall', value=formatedlength)
        self.checkTime = t.time()
        return

    def convertNumbers(self, dev,number):

        self.debugLog(u' Convert Numbers States Run:')

        oldnumber = number

        for k,v in self.numberstoConvert:
            number = number.replace(k,v)

            self.debugLog(u' Old Number: ' +unicode(oldnumber)+'  New Number:'+unicode(number))

        return number

    def parseData(self,dev, data,addr):

        self.debugLog(u"parseData Called:  {0}:".format(data))
        sipserver = dev.pluginProps['sipServer']
        if data.startswith('INVITE'):


            self.debugLog(u"parseData Called: Contains INVITE")


            #if data.find(sipserver) > 0:
            # change to below five times faster
            if sipserver in data:
                # sipserver found - must be ongoing call  (hopefully logic holds)
                self.callType = "Outgoing"
            else:
                self.callType = "Incoming"


            self.debugLog(u"parseData: CallType {0}".format(self.callType))

            #if data.find("Contact: <sip:") > 0 and self.callType == "Incoming":
            if 'Contact: <sip:' in data and self.callType=='Incoming' and dev.states['deviceStatus']!='Incoming Ringing':
                pos = data.find("Contact: <sip:") + 14
                dataedit = data[pos:].split('\n', 1)[0]
                end = dataedit.find("@")
                number = str(dataedit[0:end])
                if end <= 0:
                    number = "No Caller ID"
                update_time = t.strftime("%m/%d/%Y at %H:%M")
                self.ringing = True

                self.currentNumber = self.convertNumbers(dev,number)

                self.triggerCheck(dev)

                dev.updateStateOnServer('lastNumber', dev.states['currentNumber'])
                self.debugLog("Incoming call:  Number:  {0}".format(self.currentNumber))
                dev.updateStateOnServer("currentNumber", str(self.currentNumber))
                dev.updateStateOnServer("deviceStatus", "Incoming Ringing")
                dev.updateStateOnServer('deviceLastUpdated', value=update_time)
                dev.updateStateOnServer('callTime', value=update_time)
                dev.updateStateOnServer('callType', value='Incoming')

                self.updateVar('SPAIncomingCallerId', str(self.currentNumber))
                self.callType = ''


            if self.callType == "Outgoing" and dev.states['deviceStatus']!='Outgoing Ringing':

                pos = data.find("INVITE sip:") + 11
                dataedit = data[pos:].split('\n', 1)[0]
                end = dataedit.find("@")
                number = str(dataedit[0:end])
                if end <= 0:
                    number = "No Caller ID"
                update_time = t.strftime("%m/%d/%Y at %H:%M")
                self.ringing = True
                self.currentNumber = self.convertNumbers(dev,number)
                self.debugLog(u"Outgoing call:  Number:  {0}".format(self.currentNumber))
                dev.updateStateOnServer('lastNumber', dev.states['currentNumber'])
                dev.updateStateOnServer("currentNumber", str(self.currentNumber))
                dev.updateStateOnServer("deviceStatus", "Outgoing Ringing")
                dev.updateStateOnServer('deviceLastUpdated', value=update_time)
                dev.updateStateOnServer('callTime', value=update_time)
                dev.updateStateOnServer('callType', value='Incoming')
                self.updateVar('SPAOutgoingCallerId', str(self.currentNumber))
                self.callType = ''

        if data.startswith('SIP/2.0 200 OK') and self.ringing == True:
            self.connected = True
            self.ringing = False
            self.debugLog(u"Connected call:  Number:  {0}".format(dev.states['currentNumber']))
            dev.updateStateOnServer("deviceStatus", "Connected")
            formatedlength = "%d:%02d:%02d" % (0, 0, 0)
            dev.updateStateOnServer('durationCall', value=formatedlength)
            self.connectTime = t.time()

        if data.startswith('CANCEL') and self.ringing == True:
            self.connected = False
            self.ringing = False
            self.debugLog(u"Disconnected call:  Number:  {0}".format(dev.states['currentNumber']))
            self.callType = ""
            dev.updateStateOnServer("deviceStatus", "Off Hook")


        if data.startswith('BYE') and self.connected == True:
            self.connected = False
            self.debugLog(u"Disconnected call:  Number:  {0}".format(dev.states['currentNumber']))
            self.callType = ""
            dev.updateStateOnServer("deviceStatus", "Off Hook")


        return

    def speakCallerNumber(self,pluginAction, dev):


        indigo.server.speak(self.currentNumber)

        return

    def rebootSPA(self,pluginAction, dev):

        try:
            url = 'http://' + dev.pluginProps['sourceXML'] + '/admin/reboot'
            r = requests.get(url, timeout=5)


            self.debugLog(U'Rebooting Device:'+str(r.status_code))


        except Exception as error:

            self.logger.debug(u'Error with Reboot'+str(error))

        return

    def updateVar(self, name, value):
        if name not in indigo.variables:
            indigo.variable.create(name, value=value)

            self.debugLog(u"updateVar Called: Create Variable")
        else:
            indigo.variable.updateValue(name, value)

            self.debugLog(u"updateVar Called: Update Variable")

    def shutdown(self):

        self.debugLog(u"shutdown() method called.")

    def startup(self):

        self.debugLog(u"Starting Spirua VOIP Plugin. startup() method called.")

        # See if there is a plugin update and whether the user wants to be notified.
        try:
            if self.configUpdaterForceUpdate:
                self.updatePlugin()

            else:
                self.checkForUpdates()
            self.sleep(1)
        except Exception as error:
            self.errorLog(u"Update checker error: {0}".format(error))

    def validatePrefsConfigUi(self, valuesDict):

        return True, valuesDict

    def validateDeviceConfigUi(self, valuesDict, typeId, devId):

        self.debugLog(u"validateDeviceConfigUi() method called.")

        if valuesDict[u'sourcePort'] == '':
            errorMsgDict = indigo.Dict()
            errorMsgDict[u'sourcePort']= u'Port Cannot be blank and must be number 1024-65535.'
            return (False,valuesDict, errorMsgDict)

        try:
            port = int(valuesDict[u'sourcePort'])

            if (port <= 1024 or port > 65535):
                errorMsgDict = indigo.Dict()
                errorMsgDict[u'sourcePort'] = u"Port number needs to be a valid MacOS UDP port (1024-65535)."
                return (False, valuesDict, errorMsgDict)
        except ValueError:
            errorMsgDict = indigo.Dict()
            errorMsgDict[u'sourcePort'] = u"Port number needs to be a valid MacOS UDP port Number! (1024-65535)."
            return (False, valuesDict, errorMsgDict)
        # self.errorLog(u"Plugin configuration error: ")
        sipserver = valuesDict[u'sipServer']
        if sipserver.find('.') < 0:
            errorMsgDict = indigo.Dict()
            errorMsgDict[u'sipServer'] = u'Sip Server Details Need to be entered.'
            return (False, valuesDict, errorMsgDict)
        return True, valuesDict

    def setStatestonil(self, dev):

        self.debugLog(u'setStates to nil run')


    def refreshDataAction(self, valuesDict):
        """
        The refreshDataAction() method refreshes data for all devices based on
        a plugin menu call.
        """

        self.debugLog(u"refreshDataAction() method called.")
        self.refreshData()
        return True

    def refreshData(self):
        """
        The refreshData() method controls the updating of all plugin
        devices.
        """

        self.debugLog(u"refreshData() method called.")

        try:
            # Check to see if there have been any devices created.
            if indigo.devices.itervalues(filter="self"):

                self.debugLog(u"Updating data...")

                for dev in indigo.devices.itervalues(filter="self"):
                    self.refreshDataForDev(dev)

            else:
                indigo.server.log(u"No Enphase Client devices have been created.")

            return True

        except Exception as error:
            self.errorLog(u"Error refreshing devices. Please check settings.")
            self.errorLog(unicode(error.message))
            return False

    def refreshDataForDev(self, dev):

        if dev.configured:

            self.debugLog(u"Found configured device: {0}".format(dev.name))

            if dev.enabled:

                self.debugLog(u"   {0} is enabled.".format(dev.name))
                timeDifference = int(t.time() - t.mktime(dev.lastChanged.timetuple()))

            else:

                self.debugLog(u"    Disabled: {0}".format(dev.name))


    def refreshDataForDevAction(self, valuesDict):
        """
        The refreshDataForDevAction() method refreshes data for a selected device based on
        a plugin menu call.
        """

        self.debugLog(u"refreshDataForDevAction() method called.")

        dev = indigo.devices[valuesDict.deviceId]

        self.refreshDataForDev(dev)
        return True

    def stopSleep(self, start_sleep):
        """
        The stopSleep() method accounts for changes to the user upload interval
        preference. The plugin checks every 2 seconds to see if the sleep
        interval should be updated.
        """
        try:
            total_sleep = float(self.pluginPrefs.get('configMenuUploadInterval', 300))
        except:
            total_sleep = iTimer  # TODO: Note variable iTimer is an unresolved reference.
        if t.time() - start_sleep > total_sleep:
            return True
        return False

    def toggleDebugEnabled(self):
        """
        Toggle debug on/off.
        """

        self.debugLog(u"toggleDebugEnabled() method called.")
        if self.logLevel == logging.INFO:
             self.logLevel = logging.DEBUG

             self.indigo_log_handler.setLevel(self.logLevel)
             indigo.server.log(u'Set Logging to DEBUG')
        else:
            self.logLevel = logging.INFO
            indigo.server.log(u'Set Logging to INFO')
            self.indigo_log_handler.setLevel(self.logLevel)

        self.pluginPrefs[u"logLevel"] = self.logLevel
        return









    def triggerStartProcessing(self, trigger):
        self.logger.debug("Adding Trigger %s (%d) - %s" % (trigger.name, trigger.id, trigger.pluginTypeId))
        assert trigger.id not in self.triggers
        self.triggers[trigger.id] = trigger

    def triggerStopProcessing(self, trigger):
        self.logger.debug("Removing Trigger %s (%d)" % (trigger.name, trigger.id))
        assert trigger.id in self.triggers
        del self.triggers[trigger.id]

    def triggerCheck(self, device):

        for triggerId, trigger in sorted(self.triggers.iteritems()):
            self.logger.debug("Checking Trigger %s (%s), Type: %s" % (trigger.name, trigger.id, trigger.pluginTypeId))

            if trigger.pluginProps["deviceID"] != str(device.id):
                self.logger.debug("\t\tSkipping Trigger %s (%s), wrong device: %s" % (trigger.name, trigger.id, device.id))
            else:
                if trigger.pluginTypeId == "call":
                    if device.states["deviceStatus"] != "0":
                        self.logger.debug("\tExecuting Trigger %s (%d)" % (trigger.name, trigger.id))
                        indigo.trigger.execute(trigger)

                else:
                    self.logger.debug("\tUnknown Trigger Type %s (%d), %s" % (trigger.name, trigger.id, trigger.pluginTypeId))
        return