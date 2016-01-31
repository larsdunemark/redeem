#!/usr/bin/env python
"""
An alarm can be executed when an error condition occurs

Author: Elias Bakken

 Redeem is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Redeem is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Redeem.  If not, see <http://www.gnu.org/licenses/>.
"""
from threading import Thread
import time
import logging

from multiprocessing import JoinableQueue
import Queue

class Alarm:
    THERMISTOR_ERROR    = 0 # Thermistor error. 
    HEATER_TOO_COLD     = 1 # Temperature has fallen below the limit
    HEATER_TOO_HOT      = 2 # Temperature has gone too high
    HEATER_RISING_FAST  = 3 # Temperture is rising too fast
    HEATER_FALLING_FAST = 4 # Temperature is faling too fast
    FILAMENT_JAM        = 5 # If filamet sensor is installed
    WATCHDOG_ERROR      = 6 # Can this be detected?
    ENDSTOP_HIT         = 7 # During print. 
    ALARM_TEST          = 8 # Testsignal, used during start-up

    printer = None
    executor = None

    def __init__(self, alarm_type, message):
        self.type = alarm_type
        self.message = message
        if Alarm.executor:
            Alarm.executor.queue.put(self)
        else:
            logging.error("Enable to enqueue alarm!")
        
    def execute(self):
        """ Execute the alarm """
        if self.type == Alarm.THERMISTOR_ERROR:
            logging.error(self.message)
            self.stop_print()
            self.inform_listeners(self.message)
        elif self.type == Alarm.HEATER_TOO_COLD:
            logging.error(self.message)
            self.stop_print()
            self.inform_listeners(self.message)
        elif self.type == Alarm.HEATER_TOO_HOT:
            logging.error(self.message)
            self.stop_print()
            self.inform_listeners(self.message)
        elif self.type == Alarm.HEATER_RISING_FAST:
            logging.error(self.message)
            self.stop_print()
            self.inform_listeners(self.message)
        elif self.type == Alarm.HEATER_FALLING_FAST:
            logging.error(self.message)
            self.disable_heaters()
            self.inform_listeners(self.message)
        elif self.type == Alarm.ALARM_TEST:
            logging.info(self.message)
            self.inform_listeners(self.message)
        else:
            logging.warning("An Alarm of unknown type was sounded!")

    # These are the different actions that can be 
    # done once an alarm is sounded. 
    def stop_print(self):
        """ Stop the print """
        logging.warning("Stopping print")
        self.printer.path_planner.emergency_interrupt()
        self.disable_heaters()

    def disable_heaters(self):
        logging.warning("Disabling heaters")
        for _, heater in self.printer.heaters.iteritems():
            heater.extruder_error = True

    def inform_listeners(self, message):
        """ Inform all listeners (comm channels) of the occured error """
        logging.debug("Informing listeners")
        if Alarm.printer and hasattr(Alarm.printer, "comms"):
            for _, comm in Alarm.printer.comms.iteritems():
                comm.send_message("Alarm: "+message)

    def make_sound(self):
        """ If a speaker is connected, sound it """        
        pass

    def send_email(self):
        """ Send an e-mail to a predefined address """
        pass
    
    def send_sms(self):
        pass

    def record_position(self):
        """ Save last completed segment to file """
        pass
    
    


class AlarmExecutor:
    def __init__(self):
        self.queue = JoinableQueue(10)
        self.running = True
        self.t = Thread(target=self._run)
        self.t.start()

    def _run(self):
        while self.running:
            try:
                alarm = self.queue.get(block=True, timeout=1)
                alarm.execute() 
                logging.debug("Alarm executed")
                self.queue.task_done()       
            except Queue.Empty:
                continue
            
    def stop(self):
        logging.debug("Stoppping executor")
        self.running = False
        self.t.join()
    

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')


    class FooPrinter:
        pass
    
    p = FooPrinter()
    alarm_executor = AlarmExecutor()
    Alarm.printer = p
    Alarm.executor = alarm_executor
    alarm = Alarm(Alarm.ALARM_TEST, {}, "Test")
    time.sleep(1)
    alarm_executor.stop()
    
    


