import socket
import ubinascii
import network
import json
import os
import usocket
import internal_hotspot
import machine
import sys
import utime
import NFC_PN532 as nfc
import gc
from picozero import pico_led, Button
from camera import *
from time import sleep

# SETTINGS
SETTINGS = dict()
CONFIG = dict()
PORT = 25961
PORT_INC = 25962

with open("settings.json") as f:
    SETTINGS = json.load(f)
with open("config.json") as f:
    CONFIG = json.load(f)

# SPI
if CONFIG['nfc_conn']:
    spi_dev = machine.SPI(1, baudrate=1000000, polarity=0, phase=0, sck=machine.Pin(10), mosi=machine.Pin(11), miso=machine.Pin(8))
    cs = machine.Pin(9, machine.Pin.OUT)
    cs.on()
    pn532 = nfc.PN532(spi_dev,cs)
    ic, ver, rev, support = pn532.get_firmware_version()
    print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))
    pn532.SAM_configuration()
if CONFIG['cam_conn']:
    spi_cam = machine.SPI(0,sck=machine.Pin(2), miso=machine.Pin(4), mosi=machine.Pin(3), baudrate=8000000)
    cs_cam = machine.Pin(7, machine.Pin.OUT)
    cam = Camera(spi_cam, cs_cam, debug_information=True)
    cam.resolution = '640x480'
    cam.capture_jpg()
    base_length = cam.received_length
    print('Base length will be '+str(base_length))


# RELAY
relay = machine.Pin(CONFIG['relay'],machine.Pin.OUT)
relay.value(1)

# SIPOL
beeper = machine.Pin(CONFIG['chime'],machine.Pin.OUT)
beeper.value(0)

def exception_led(period, maxtime):
    if maxtime is None:
        while True:
            pico_led.toggle()
            utime.sleep(period)
    for x in range(0,maxtime):
        pico_led.toggle()
        utime.sleep(period)
    pico_led.on()
    return
        
def beep(times, pulse, pulse2=0.1):
    for _ in range(0,times):
        beeper.value(1)
        utime.sleep(pulse)
        beeper.value(0)
        utime.sleep(pulse2)
    beeper.value(0)

def out_button():
    relay.value(0)
    print('out_button')
    beep(1,0.1)
    utime.sleep(CONFIG['button_time'])
    relay.value(1)

def read_nfc(tout):
    try:
        uid = pn532.read_passive_target(timeout=tout)
    except Exception as e:
        print("failed to read - "+str(e))
        
    if uid is None:
        print('CARD NOT FOUND')
    else:
        numbers = [i for i in uid]
        string_ID = '{}-{}-{}-{}'.format(*numbers)
        print('Found card with UID:', [hex(i) for i in uid])
        print('Number_id: {}'.format(string_ID))
        gc.collect()
        print("collected")
        return string_ID
    return None

def key_register():
    print("key_register")
    beep(5,0.1)
    string_ID = read_nfc(5000)
    beep(5,0.5) if string_ID == None else beep(1,0.5)
    return string_ID

def main_loop(host):
    global PORT, pn532, cam, base_length
    '''
        MainLoop:
        - healthcheck on 25961
        - check for incomming message on 25962
        - try reading NFC
        - try reading QR
    '''
    print("MainLoop started!")
    btn = Button(13)
    btn.when_pressed = out_button
    while True:
        try:
            try:
                print("listen")
                sock_listen = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
                sock_listen.setsockopt(usocket.SOL_SOCKET, usocket.SO_REUSEADDR, 1)
                sock_listen.bind(('', PORT_INC))
                sock_listen.listen(5)
                sock_listen.setblocking(False)
                utime.sleep(0.5)
                
                try:
                    conn, addr = sock_listen.accept()
                    print("Connection from", addr)
                    conn.settimeout(1)
                    incomming = conn.recv(1024).decode()
                    print("  | "+str(incomming))

                    if incomming == 'REGUSER':
                        key = key_register()
                        if key:
                            conn.send(('OK#' + key).encode())
                        else:
                            conn.send('ERR'.encode())
                        utime.sleep(5)
                    elif incomming == 'OPEN':
                        conn.send(('OK').encode())
                        relay.value(0)
                        print('access_granted')
                        beeper.value(1)
                        utime.sleep(0.5)
                        beeper.value(0)
                        utime.sleep(CONFIG['auth_time']-0.5)
                        relay.value(1)
                    gc.collect()

                except OSError as e:
                    pass 
                finally:
                    if 'conn' in locals():
                        conn.close()
            except Exception as e:
                print(str(e))
            finally:
                sock_listen.close()
            
            if CONFIG['nfc_conn']:
                print("NFC")
                string_ID = read_nfc(500)
                if string_ID != None:
                    try:
                        sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
                        sock.connect((SETTINGS['host'], PORT))
                        print("ready to send")
                        sock.sendall(('INC#'+SETTINGS['correlation_id']+'#'+string_ID).encode())
                        print("awaiting response")
                        response = sock.recv(1024).decode()
                        resp = response.split('#')
                        if(resp[0] == 'OK'):
                            relay.value(0)
                            print('access_granted')
                            beeper.value(1)
                            utime.sleep(0.5)
                            beeper.value(0)
                            utime.sleep(CONFIG['auth_time']-0.5)
                            relay.value(1)
                        elif(resp[0] == 'NOTAUTHORIZED'):
                            SETTINGS['setup'] = 1
                            print("We're no longer authorized, restarting from setup stage 1...")
                            with open("settings.json", "w") as f:
                                json.dump(SETTINGS, f)
                            print("Reset data saved.")
                            machine.reset()
                        else:
                            beep(3,0.2,0.2)
                            print('not_found_beep')
                    except Exception as e:
                        print(e)
                        exception_led(0.5,3)
                    finally:
                        sock.close()
            
            if CONFIG['cam_conn']:
                print("QR")
                cam.capture_jpg()
                print(str((abs((cam.received_length - base_length) / base_length) * 100)))
                if((abs((cam.received_length - base_length) / base_length) * 100) >=5):
                    beep(1,0.1)
                    print('waiting a bit for steady image')
                    utime.sleep(1.5)
                    gc.collect()

                    chunk_counter = 0
                    
                    ## for testing - this is where we start our timer
                    #start_time = utime.ticks_ms()
                    
                    sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
                    sock.connect((SETTINGS['host'], PORT))

                    cam.capture_jpg()
                    beep(1,0.1)
                    
                    try:
                        cam.chunked_prev_int = 0x00
                        while True:
                            chunk = cam.chunkedJPG(chunk_size=512)
                            ## chunk = (bytes, is_eof?)
                            print("chunk "+str(chunk_counter))
                            if chunk[1]:
                                sock.sendall(chunk[0])
                                break
                            sock.sendall(chunk[0])
                            chunk_counter += 1
                        sock.sendall(b'_EOF')
                        print('bytes sent')
                        
                        utime.sleep(2)
                        
                        sock.sendall(SETTINGS['correlation_id'].encode())
                        print('ID sent')
                        
                        print("waiting for answer")
                        
                        resp = sock.recv(1024).decode()
                        
                        if(resp == 'OK'):
                            relay.value(0)
                            print('access_granted')
                            ## this is where the timer ends
                            #end_time = utime.ticks_ms()
                            #elapsed_time = utime.ticks_diff(end_time, start_time) / 1000
                            #print("This took us:")
                            #print(elapsed_time)
                            beeper.value(1)
                            utime.sleep(0.5)
                            beeper.value(0)
                            utime.sleep(CONFIG['auth_time']-0.5)
                            relay.value(1)
                        elif(resp == 'NOTAUTHORIZED'):
                            SETTINGS['setup'] = 1
                            print("We're no longer authorized, restarting from setup stage 1...")
                            with open("settings.json", "w") as f:
                                json.dump(SETTINGS, f)
                            print("Reset data saved.")
                            machine.reset()
                        else:
                            beep(3,0.2,0.2)
                            print('not_found_beep')
                        cam.capture_jpg()
                        base_length = cam.received_length
                    except Exception as e:
                        print(e)
                    finally:
                        sock.close()
        except Exception as e:
            print(e)
            print("exception happened")
            break
        finally:
            print("final")
        utime.sleep(1)
    exception_led(0.5, None)

    
def port_test(local_ip, port):
    global pico_led
    print("Port test started, searching for service")
    for rx in range(1,256):
        gc.collect()
        hostr = '.'.join(str(local_ip).split(".")[0:3])+'.'+str(rx)
        print(" > "+str(hostr))
        pico_led.toggle()
        try:
            s = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((hostr, port))
            s.close()
            return hostr
        except Exception as e:
            exception_led(0.5, 3)
            print(e)
        finally:
            s.close()
    pico_led.on()
    return None

## if setup is 1, we need to open the captive portal, to allow users to enter the correct WIFI credentials.
if(SETTINGS['setup'] == 0):
    pico_led.on()
    cf_details = internal_hotspot.start('DD_wizard','password12')
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(cf_details[0],cf_details[1])
    while wlan.isconnected() == False:
        pico_led.toggle()
        print('Waiting for connection...')
        sleep(1)
    pico_led.on()
    print(wlan.ifconfig())
    print(f'Initial connection established, searching for the local DD server')
    dd_local_ip = port_test(wlan.ifconfig()[0], PORT)
    if dd_local_ip == None:
        print("Couldn't find doda server")
    else:
        print("Found doda server at "+str(dd_local_ip))
        SETTINGS['ssid'] = cf_details[0]
        SETTINGS['pass'] = cf_details[1]
        SETTINGS['setup'] = 1
        SETTINGS['host'] = dd_local_ip
        with open("settings.json", "w") as f:
            json.dump(SETTINGS, f)
        print("Server data saved to settings")
        print("\n\n")
        print("Connection completed, DoorController will now fully restart...")
        # this should be used in PROD
        machine.reset()
        # this is for dev only
        #sys.exit()
elif(SETTINGS['setup'] == 1):
    print("(setup in progress, already have an IP)")
    print("(reafy check completed)")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print(SETTINGS['ssid']+" - "+SETTINGS['pass'])
    wlan.connect(SETTINGS['ssid'],SETTINGS['pass'])
    while wlan.isconnected() == False:
        pico_led.toggle()
        print('Waiting for connection...')
        sleep(1)
    pico_led.on()
    print(wlan.ifconfig())
    print(f'Initial connection established, starting registration progress...')
    ## registering ourselves, if we don't already have a correlation_id
    if(SETTINGS['correlation_id'] == ''):
        try:
            sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((SETTINGS['host'], PORT))
            messg = 'REGISTER#'+str(wlan.ifconfig()[0])
            print(messg)
            sock.sendall(messg.encode())
            response = sock.recv(1024).decode()
            resp = response.split('#')
            print(str(resp))
            if(resp[0] == 'OK'):
                SETTINGS['correlation_id'] = resp[1]
                with open("settings.json", "w") as f:
                    json.dump(SETTINGS, f)
                print("Server correlation id data saved to settings")
            else:
                raise Exception('Exception in reg response from DODA server')
        except Exception as e:
            print(e)
        finally:
            sock.close()
    ## await authentication
    while True:
        try:
            sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
            sock.connect((SETTINGS['host'], PORT))
            messg = 'HEALTHCHECK#'+SETTINGS['correlation_id']+'#'+str(wlan.ifconfig()[0])
            sock.sendall(messg.encode())
            response = sock.recv(1024).decode()
            resp = response.split('#')
            if(resp[0] == 'OK'):
                SETTINGS['setup'] = 2
                break
        except Exception as e:
            print(e)
        finally:
            sock.close()
        sleep(10)
    ## save settings
    with open("settings.json", "w") as f:
        json.dump(SETTINGS, f)
    print("New server data saved to settings")
    print("\n\n")
    print("Setup completed, DoorController will now fully restart...")
    machine.reset()
else:
    print("(ready check completed)")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    print(SETTINGS['ssid']+" - "+SETTINGS['pass'])
    wlan.connect(SETTINGS['ssid'],SETTINGS['pass'])
    tryi = 0
    while wlan.isconnected() == False or tryi <= 30:
        pico_led.toggle()
        print('Waiting for connection...')
        sleep(1)
        tryi += 1
    if wlan.isconnected() == False:
        exception_led(0.25,None)
    pico_led.on()
    print(wlan.ifconfig())
    print(f'Initial connection established, searching for the local DD server & getting settings')
    main_loop(SETTINGS['host'])