# written by grey@christoforo.net
# on 21 Feb 2018

from picoscope import ps4000
import numpy as np

class ps4262:
    """
    picotech PS4262 library
    """
    currentScaleFactor = 1/10000000 # amps per volt through our LPM7721 eval board
    def __init__(self, VRange = 5, requestedSamplingInterval = 1e-6, tCapture = 0.3, triggersPerMinute = 30):
        """
        picotech PS4262 library constructor
        """
        # this opens the device
        self.ps = ps4000.PS4000()

        # setup sampling interval
        self.setTimeBase(requestedSamplingInterval = requestedSamplingInterval, tCapture = 0.3)

        # setup current collection channel (A)
        self.setChannel(VRange = VRange)

        # turn on the function generator
        self.setFGen(enabled = True, triggersPerMinute = triggersPerMinute)

        # setup triggering
        self.ps._lowLevelSetExtTriggerRange(VRange = 5)
        trigDelay = round(1000 / self.triggerFrequency) # in ms
        trigDelay = 0 # in ms
        self.ps.setSimpleTrigger('EXT', 0.1, 'Rising', delay=0, timeout_ms = trigDelay, enabled=True)

        # start the collection
        self.run()

    def __del__(self):
        try:
            self.ps.stop()
            self.ps.close()
        except:
            print("")
            pass

    def setFGen(self, enabled = True, triggersPerMinute = 10):
        frequency = triggersPerMinute / 60
        self.triggerFrequency = frequency
        if enabled is True:
            self.ps.setSigGenBuiltInSimple(offsetVoltage=0.5,pkToPk=1,waveType="Square", frequency=frequency, shots=0, stopFreq=frequency)
        else:
            self.ps.setSigGenBuiltInSimple(offsetVoltage=0,pkToPk=0,WaveType="DC", frequency=1, shots=1, stopFreq=1)

    def setChannel(self, VRange = 2):
        self.VRange = VRange
        channelRange = self.ps.setChannel(channel='A', coupling='DC', VRange=VRange, VOffset=0.0, enabled=True, BWLimited=0, probeAttenuation=1.0)

    def setTimeBase(self, requestedSamplingInterval=1e-6, tCapture=0.3):
        self.requestedSamplingInterval = requestedSamplingInterval
        self.tCapture = tCapture

        self.ps.oversample = 0
        self.ps.timebase = self.ps.getTimeBaseNum4262(requestedSamplingInterval)
        self.actualSampleInterval = self.ps.getTimestepFromTimebase4262(self.ps.timebase)
        self.ps.noSamples = round(tCapture/self.actualSampleInterval)
        (self.ps.sampleInterval, self.ps.maxSamples) = self.ps._lowLevelGetTimebase(tb = self.ps.timebase, noSamples = self.ps.noSamples, oversample = self.ps.oversample, segmentIndex = 0)
        self.actualSamplingInterval = self.ps.sampleInterval
        self.nSamples = self.ps.noSamples
        if self.ps.maxSamples < self.ps.noSamples :
            print("Error: Can't collect that many samples!", self.ps.noSamples)

    def getMetadata(self):
        """
        Returns metadata struct
        """
        metaData = {"Voltage Range" : self.VRange,
        "Trigger Frequency": self.triggerFrequency,
        "Requested Sampling Interval": self.requestedSamplingInterval,
        "Capture Time": self.tCapture}
        return metaData

    def getData(self):
        """
        Returns two np arrays:
        time in seconds since trigger (can be negative)
        current in amps
        """
        self.ps.waitReady() # hang here until data is ready
        voltageData = self.ps.getDataV('A', self.nSamples, returnOverflow=False)

        resultStruct = {"time": self.timeVector, "current": voltageData * self.currentScaleFactor}
        self.run() # arm the trigger for next capture
        return resultStruct

    def run(self):
        """
        This arms the trigger
        """
        pretrig = 0.1
        self.ps.runBlock(pretrig = pretrig, segmentIndex = 0)
        self.timeVector = (np.arange(self.ps.noSamples) - int(round(self.ps.noSamples * pretrig))) * self.actualSamplingInterval

    def isReady(self):
        """Send command to sourcemeter
        """
        return self.ps.isReady()
