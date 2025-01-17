#!/usr/bin/python
import RPi.GPIO as GPIO
import math

class MAX6675(object):
    '''Python driver for [MAX6675 Cold-Junction Compensated Thermocouple-to-Digital Converter]
     Requires:
     - The [GPIO Library](https://code.google.com/p/raspberry-gpio-python/) (Already on most Raspberry Pi OS builds)
     - A [Raspberry Pi](http://www.raspberrypi.org/)
    '''
    def __init__(self, cs_pin, clock_pin, data_pin, units = "c", power_pin = 0, board = GPIO.BCM):
        '''Initialize Soft (Bitbang) SPI bus
        Parameters:
        - cs_pin:    Chip Select (CS) / Slave Select (SS) pin (Any GPIO)
        - clock_pin: Clock (SCLK / SCK) pin (Any GPIO)
        - data_pin:  Data input (SO / MOSI) pin (Any GPIO)
        - units:     (optional) unit of measurement to return. ("c" (default) | "k" | "f")
        - power_pin (optional) allows thermocouple chip to be powered from gpio
        - board:     (optional) pin numbering method as per RPi.GPIO library (GPIO.BCM (default) | GPIO.BOARD)
        '''
        self.cs_pin = cs_pin
        self.clock_pin = clock_pin
        self.data_pin = data_pin
        self.units = units
        self.power_pin = power_pin
        self.data = None
        self.board = board
        self.noConnection = self.shortToGround = self.shortToVCC = self.unknownError = False
        
        #set board type
        GPIO.setmode(self.board)
        #if using thermocouple power pin, initialise and set high
        if (self.power_pin > 0):
            GPIO.setup(self.power_pin, GPIO.OUT)
            GPIO.output(self.power_pin, GPIO.HIGH)
        # Initialize needed GPIO
        GPIO.setup(self.cs_pin, GPIO.OUT)
        GPIO.setup(self.clock_pin, GPIO.OUT)
        GPIO.setup(self.data_pin, GPIO.IN)
       

        # Pull chip select high to make chip inactive
        GPIO.output(self.cs_pin, GPIO.HIGH)

    def get(self):
        '''Reads SPI bus and returns current value of thermocouple.'''
        self.read()
        self.checkErrors()
        return getattr(self, "to_" + self.units)(self.data_to_tc_temperature())

    def read(self):
        '''Reads 16 bits of the SPI bus & stores as an integer in self.data.'''
        bytesin = 0
        # Select the chip
        GPIO.output(self.cs_pin, GPIO.LOW)
        # Read in 16 bits
        for i in range(16):
            GPIO.output(self.clock_pin, GPIO.LOW)
            bytesin = bytesin << 1
            if (GPIO.input(self.data_pin)):
                bytesin = bytesin | 1
            GPIO.output(self.clock_pin, GPIO.HIGH)
        # Unselect the chip
        GPIO.output(self.cs_pin, GPIO.HIGH)
        # Save data
        self.data = bytesin

    def checkErrors(self, data_16 = None):
        '''Checks error bit'''
        if data_16 is None:
            data_16 = self.data
        anyErrors = (data_16 & 0x4) != 0    # Fault bit, D3
        if anyErrors:
            self.noConnection = True       
           
        else:
            self.noConnection = False

    def data_to_tc_temperature(self, data_16 = None):
        '''Takes an integer and returns a thermocouple temperature in celsius.'''
        if data_16 is None:
            data_16 = self.data
        tc_data = data_16 >> 3
        return self.convert_tc_data(tc_data)

    

    def convert_tc_data(self, tc_data):
        '''Convert thermocouple data to a useful number (celsius).'''
        return tc_data * 0.25

    def to_c(self, celsius):
        '''Celsius passthrough for generic to_* method.'''
        return celsius

    def to_k(self, celsius):
        '''Convert celsius to kelvin.'''
        return celsius + 273.15

    def to_f(self, celsius):
        '''Convert celsius to fahrenheit.'''
        return celsius * 9.0/5.0 + 32

    def cleanup(self):
        '''Selective GPIO cleanup'''
        GPIO.setup(self.cs_pin, GPIO.IN)
        GPIO.setup(self.clock_pin, GPIO.IN)

    

class MAX6675Error(Exception):
     def __init__(self, value):
         self.value = value
     def __str__(self):
         return repr(self.value)

if __name__ == "__main__":

    # Multi-chip example ( copied from max31855 lib. Has not been tested)
    import time
    cs_pins = [4, 17, 18, 24]
    clock_pin = 23
    data_pin = 22
    units = "f"
    thermocouples = []
    for cs_pin in cs_pins:
        thermocouples.append(MAX6675(cs_pin, clock_pin, data_pin, units))
    running = True
    while(running):
        try:
            for thermocouple in thermocouples:
                rj = thermocouple.get_rj()
                try:
                    tc = thermocouple.get()
                except MAX6675Error as e:
                    tc = "Error: "+ e.value
                    running = False
                print("tc: {} and rj: {}".format(tc, rj))
            time.sleep(1)
        except KeyboardInterrupt:
            running = False
    for thermocouple in thermocouples:
        thermocouple.cleanup()
