#importing libraries
import sys
import os
import glob
import urllib.request as urllib2
from time import sleep
import Adafruit_DHT as dht
import board
import busio
import digitalio
import adafruit_bmp280
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import math

#Write API Key of Thingspeak channel
myapi = '52W81CQR59GONMEW'
#Accessing the Thingspeak channel to upload data 
base_url = 'https://api.thingspeak.com/update?api_key=%s' %myapi

#**************************************************************************************************************
#Codes for interfacing DS18B20 sensor with Raspberry Pi
#1-wire modules for DS18B20
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

#Declaring three different variables that points to the location of DS18B20 sensor data
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

#In the read_temp_raw function, the file that contains DS18B20 temperature output is opened.
#All the lines from the file is read and returned.
#The read_temp function calls this function.
def read_temp_raw():
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines

#In the read_temp function, the data is processed from the read_temp_raw function.
def read_temp():
	lines = read_temp_raw()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(.2)
		lines = read_temp_raw()
	equalpos = lines[1].find('t=')
	if equalpos != -1:
		temp_string = lines[1][equalpos+2:]
		temp_c = float(temp_string) / 1000.0
		temp_f = temp_c * 9.0 / 5.0 + 32.0
		return temp_c, temp_f
#****************************************************************************************************************


#****************************************************************************************************************
#codes for interfacing BMP280 sensor with Raspberry Pi
#Initializing the SPI connection with BMP280 sensor
spi = busio.SPI(board.SCK, MOSI= board.MOSI, MISO = board.MISO)
cs = digitalio.DigitalInOut(board.D5)
sensor = adafruit_bmp280.Adafruit_BMP280_SPI(spi, cs)
#*****************************************************************************************************************


#*****************************************************************************************************************
#codes for interfacing ADS1115 ADC with Raspberry Pi
#Initializing the I2C connection with ADS1115 Analog-to-Digital Converter
i2c = busio.I2C(board.SCL, board.SDA)
#Creating an ADC object
ads = ADS.ADS1115(i2c)
ads.gain = 1
#*****************************************************************************************************************


#*****************************************************************************************************************
#Codes for interfacing MQ135 Gas sensor with Raspberry Pi
#Intializing the parameters for calibration of sensor output values
m = -0.3376
b = 0.7165
R0 = 37

#In the gas_calib funcion, the raw output from sensor is converted into PPM values
def gas_calib():
    sensor_value = chan0.value
    RS_gas = ((5*10)/chan0.voltage)-10
    ratio = RS_gas/R0
    ppm_log = (math.log10(ratio)-b)/m
    ppm = pow(10,ppm_log)
    return ppm

#Read the MQ135 Gas sensor output values using ADS1115 through Pin 0
chan0 = AnalogIn(ads, ADS.P0)
#******************************************************************************************************************


#******************************************************************************************************************
#codes for interfacing Capacitive soil moisture sensor wiht Raspberry Pi
#In the value_perc function, the Capacitive soil moisture sensor output value is mapped to the percentage range
def value_perc(x, in_min, in_max, out_min, out_max):
	return int((x-in_min) * (out_max-out_min) / (in_max-in_min) + out_min)

#Read the Capacitive Soil Moisture sensor output values using ADS1115 through Pin 1
chan1 = AnalogIn(ads, ADS.P1)
#******************************************************************************************************************


#******************************************************************************************************************
#codes for interfacing GUVAS12-SD UV sensor with Raspberry Pi
#In the uv_calc function, the output sensor voltage is mapped to UV-INDEX (0-11)
def uv_calc(mv_volt):
	if mv_volt < 50:
		uv_index = '0'
	elif mv_volt < 227:
		uv_index = '1'
	elif mv_volt < 318:
		uv_index = '2'
	elif mv_volt < 408:
		uv_index = '3'
	elif mv_volt < 503:
		uv_index = '4'
	elif mv_volt < 606:
		uv_index = '5'
	elif mv_volt < 696:
		uv_index = '6'
	elif mv_volt < 795:
		uv_index = '7'
	elif mv_volt < 881:
		uv_index = '8'
	elif mv_volt < 976:
		uv_index = '9'
	elif mv_volt < 1079:
		uv_index = '10'
	else:
		uv_index = '11'
	return uv_index

#Read the GUVAS12-SD UV sensor output values using ADS1115 through Pin 2
chan2 = AnalogIn(ads, ADS.P2)
#*******************************************************************************************************************


#******************************************************************************************************************
#codes for calculating Heat Index 
#Initializing the parameters
c1 = -42.379
c2 = 2.04901523
c3 = 10.14333127
c4 = -0.22475541
c5 = -6.83783e-3
c6 = -5.481717e-2
c7 = 1.22874e-3
c8 = 8.5282e-4
c9 = -1.99e-6

#In the heat_index_calc function, the Heat Index value is calculated using humidity and temperature values
def Heatindex_calc(T,R):
    T2 = T*T
    R2 = R*R
    TR = T*R
    HI = c1 + c2*T + c3*R + c4*TR + c5*T2 + c6*R2 + c7*T2*R + c8*T*R2 + c9*T2*R2
    HI_c = (HI - 32.0) * (5.0 / 9.0)
    return HI_c
#*******************************************************************************************************************

#******************************************************************************************************************
#codes for calculating Dew Point
#In the Dewpoint_calc function, the Dew Point value is calculated using humidity and temperature values
def Dewpoint_calc(temp, hum): 
  k = math.log(hum/100) + (17.62 * temp) / (243.12 + temp)
  return 243.12 * k / (17.62 - k)
#*******************************************************************************************************************

while 1:
	try:
        #Read the DHT22 Humidity sensor 
		hum,temp_1 = dht.read_retry(dht.DHT22,17)

        #Read the DS18B20 Temperature sensor
		temp_c, temp_f =  read_temp()

		#Read the BMP280 Pressure sensor
		pressure_value = sensor.pressure

        #Read the MQ135 sensor
		ppm = gas_calib()
		
        #Read the Capacitive soil moisture sensor
		perc = value_perc(chan1.value, 23000, 7000, 0, 100)
		if perc > 100:
			perc = 100
		if perc < 0:
			perc = 0

        #Read the UV sensor
		mv_volt = chan2.voltage * 1000
		uv_index = uv_calc(mv_volt)
		
		#Calculate the Heat Index value
		HI = Heatindex_calc(temp_f,hum)
		
		#Calculate the Dew Point value
		dew_point = Dewpoint_calc(temp_c,hum)
		
		#Rounded of to 3 decimal places
		hum = '%.3f' %hum
		temp_c = '%.3f' %temp_c
		pressure_value = '%.3f' %pressure_value
		ppm = '%3f' %ppm
		heat_index = '%.3f' %HI
		dew_point = '%.3f' %dew_point

        #Uploading the sensor data to Thingspeak channel
		conn = urllib2.urlopen(base_url + '&field1=%s&field2=%s&field3=%s&field4=%s&field5=%s&field6=%s&field7=%s&field8=%s' %(temp_c,hum,pressure_value,perc,uv_index,ppm,heat_index,dew_point))
		print(conn.read())
		conn.close()
		sleep(120)
	except:
		break


