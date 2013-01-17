#!/usr/bin/env python

'''
D0 = DECAY   = X
D1 = MODE0   = X
D2 = MODE1   = X
D3 = MODE2 	 = X
D4 = nRESET  = 1
D5 = nSLEEP  = 1
D6 = nENABLE = 0
D7 = 		 = 0
'''
from spi import SPI
from bbio import *

# init the SPI for the DAC
spi2_0 = SPI(2, 0)
spi2_0.bpw = 8
spi2_0.mode = 1
# Init the SPI for the serial to parallel
spi2_1 = SPI(2, 1)
spi2_1.bpw = 8
spi2_1.mode = 0

class SMD:

    all_smds = list()

    @staticmethod
    def commit():
        # First, update the serial to parallel reg
        for smd in SMD.all_smds:
	        #print "comitting to SMD: "+hex(smd.getState())
	        spi2_1.writebytes([smd.getState()])

    ''' Init'''
    def __init__(self, stepPin, dirPin, faultPin, dac_channel, name):
        self.dac_channel     = dac_channel  # Which channel on the dac is connected to this SMD
        self.stepPin         = stepPin
        self.dirPin          = dirPin
        self.faultPin        = faultPin
        self.name            = name
        self.state 		     = 0x70   	    # The state of the inputs
        self.dacvalue 	     = 0x00   	    # The voltage value on the VREF		
        self.enabled 	     = False	    # Start disabled
        self.currentPosition = 0.0 	        # Starts in pos 0
        self.stepDelay       = 1.0          # Delay between each step (will be set by feed rate)
        self.debug = 1

        SMD.all_smds.append(self) 	        # Add to list of smds

        pinMode(stepPin,   0, 0) 	        # Output, no pull up
        pinMode(dirPin,    0, 0) 	        # Output, no pull up
        pinMode(faultPin,  1, 0) 	        # Input, no pull up
 						
    ''' Sets the SMD enabled '''
    def setEnabled(self):
        if not self.enabled:
            self.state &= ~(1<<6)
            self.update()
            self.enabled = True
	
    ''' Sets the SMD disabled '''
    def setDisabled(self):
        if self.enabled:
            self.state |= (1<<6)
            self.update()
            self.enabled = False

    ''' Move a certain distance, relative movement '''
    def move(self, mm):
        if mm > 0:
            digitalWrite(self.dirPin, 1)
        else:
            digitalWrite(self.dirPin, 0)

        self.step(int(abs(mm)/self.mmPrStep))
        self.currentPosition += mm

    ''' Move to an absolute position '''
    def moveTo(self, pos):
        self.move(pos-self.currentPosition)

    ''' Set the current position of this stepper '''
    def setCurrentPosition(self, pos):
        self.currentPosition = pos
	
    '''Logic high to enable device, logic low to enter
    low-power sleep mode. Internal pulldown.'''
    def enableSleepmode(self):
        self.state &= ~(1<<5)		
        self.update()

    ''' Disables sleepmode (awake) '''
    def disableSleepmode(self):
        self.state |= (1<<5)		
        self.update()

    '''nReset - Active-low reset input initializes the indexer
    logic and disables the H-bridge outputs.
    Internal pulldown.'''
    def reset(self):
        self.state |= (1<<4)
        self.update()
        self.state &= ~(1<<4)
        self.update()

    ''' Microstepping (default = 0) '''
    def setMicrostepping(self, value):
        pass   #TODO

    ''' Current chopping limit (This is the value you can change) '''
    def setCurrentValue(self, iChop):
        # Calculate the value for the DAC
        vRef = 3.3 # Voltage reference on the DAC
        rSense = 0.1 # Resistance for the 
        vOut = iChop*5.0*rSense # Calculated voltage out from the DAC (See page 9 in the datasheet for the DAC)

        self.dacval = int((vOut*256.0)/vRef)
        byte1 = ((self.dacval & 0xF0)>>4) + (self.dac_channel<<4)
        byte2 = (self.dacval & 0x0F)<<4
        spi2_0.writebytes([byte1, byte2])
        # Update all channels
        spi2_0.writebytes([0xA0, 0xFF]) # TODO: Change to only this channel (1<<dac_channel) ?

    ''' Set the feed rate in mm/min '''
    def setFeedRate(self, feed_rate):		
        print "SetFeedRate"
        minutes_pr_mm = 1.0/float(feed_rate)
        seconds_pr_mm = minutes_pr_mm*60.0
        seconds_pr_step = self.mmPrStep*seconds_pr_mm
        self.stepDelay = seconds_pr_step*1000.0
        if self.debug > 0:
            print "feed rate: %f, sec.pr.mm: %f, sec.pr.step: %f"%(feed_rate, seconds_pr_mm, seconds_pr_step)

    ''' Toggle the "step" pin n times. '''
    def step(self, steps):
        print self.name+"Stepping %d times "%steps 
        for i in range(steps):
	        toggle(self.stepPin)
	        delay(self.stepDelay)

    ''' Returns the current state '''
    def getState(self):
        return self.state

    ''' Commits the changes	'''
    def update(self):
        # Commit the serial to parallel
        SMD.commit()
			
    ''' Sets the number of mm the stepper moves pr step. 
	    This must be measured and calibrated '''
    def setMMPrstep(self, mmPrStep):
        self.mmPrStep = mmPrStep
			

	
	
