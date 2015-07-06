import smbus
import time
import requests
import json
import sys
import string
sys.path.append("../lcd_berepi/lib")
from lcd import *

SHT20_ADDR = 0x40       # SHT20 register address
SHT20_CMD_R_T = 0xF3    # no hold Master Mode (Tmeperature)
SHT20_CMD_R_RH = 0xF5   # no hold Master Mode (Humidity)
SHT20_CMD_RESET = 0xFE  # soft reset

bus = smbus.SMBus(1)    # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

def reading(v) :        # read sht20 sensor
    bus.write_quick(SHT20_ADDR)
    if v == 1:
        bus.write_byte(SHT20_ADDR, SHT20_CMD_R_T)
    elif v == 2:
        bus.write_byte(SHT20_ADDR, SHT20_CMD_R_RH)
    else :
        return False

    time.sleep(.1)

    b = (bus.read_byte(SHT20_ADDR) <<8)
    b += bus.read_byte(SHT20_ADDR)

    return b

def calc(temp, humi) :
    tmp_temp = -46.85 + 175.72 * float(temp) / pow(2,16)
    tmp_humi = -6 + 125 * float(humi) / pow(2,16)

    return tmp_temp, tmp_humi

def main() :    
    lcd_init()          # when program start, init lcd
    while True:
        temp = reading(1)
        humi = reading(2)
        if not temp or not humi :
            print( "register error" )
            break
        value = calc(temp, humi)
        tempVal = ('%.5s' %value[0])
        humiVal = ('%.5s' %value[1])
        lcd_string('Temp : %s' % tempVal, LCD_LINE_1, 1)
        lcd_string('Humi : %s' % humiVal, LCD_LINE_2, 1)
        if float(tempVal) < 22 :
            backlight_func(0)
        elif float(tempVal) < 28 :
            backlight_func(1)
        else :
            backlight_func(2)
        print "temp : %s \t humi : %s" % (tempVal, humiVal)

        send_data(value[0], value[1])
        time.sleep(5)

def send_data(temp, humi) :
    url = "http://127.0.0.1:4242/api/put"
    data = {
            "metric": "sht20.temp",
            "timestamp" : time.time(),
            "value" : float(temp),
            "tags":{
                "host": "mgpark"
            }
    }
    ret = requests.post(url, data=json.dumps(data))

    print ret.text

    data = {
            "metric": "sht20.humi",
            "timestamp" : time.time(),
            "value" : float(humi),
            "tags":{
                "host": "mgpark"
            }
    }
    ret = requests.post(url, data=json.dumps(data))

    print ret.text


def backlight_func(i) :
    if i == 0 :
        blue_backlight(False)
    elif i == 1 :
        green_backlight(False)
    else :
        red_backlight(False)

if __name__ == '__main__' :
    try :
        main()
    except KeyboardInterrupt:
        pass
    finally:
        lcd_byte(0x01, LCD_CMD)
        lcd_string("Goodbye!", LCD_LINE_1, 2)
        GPIO.cleanup()

