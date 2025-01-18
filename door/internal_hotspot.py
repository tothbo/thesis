import network
import time
import socket
import ubinascii

def urldecode(str):
    dic = {"%21":"!","%22":'"',"%23":"#","%24":"$","%26":"&","%27":"'","%28":"(","%29":")","%2A":"*","%2B":"+","%2C":",","%2F":"/","%3A":":","%3B":";","%3D":"=","%3F":"?","%40":"@","%5B":"[","%5D":"]","%7B":"{","%7D":"}"}
    for k,v in dic.items(): str=str.replace(k,v)
    return str

def index_page():
    html = """
        <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
            </head>
            <body>
                <h1>Setup</h1>
                <p>Enter your WiFi credentials bellow, so the DoorController can access the local server. After entering the details, the DoorController will restart.</p>
                <form method='get'>
                    <label for="ssid">ssid (wifi name)</label>
                    <input type="text" id="ssid" name="ssid" /><br/><br/>
                    <label for="password">password</label>
                    <input type="password" id="password" name="password" /><br/><br/>
                    <input type="submit" name="connect" value="connect" />
                </form>
            </body>
        </html>
    """
    return html
def fallback_page():
    html = """
        <html>
            <head>
                <meta name="viewport" content="width=device-width, initial-scale=1">
            </head>
            <body>
                <h1>Setup completed!</h1>
                <p>Please wait about 5 minutes. The DoorController should now restart, connect to the WiFi with the password, and search for the local DD server.<br/><br/>If the password was incorrect (or it can't find the server in the default network), DoorController will reopen the setup hotspot.</p>
            </body>
        </html>
    """
    return html

# if you do not see the network you may have to power cycle
# unplug your pico w for 10 seconds and plug it in again
def start(ssid, password):
    """
        Description: This is a function to activate AP mode
        
        Parameters:
        
        ssid[str]: The name of your internet connection
        password[str]: Password for your internet connection
        
        Returns: None
    """
    # Just making our internet connection
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=ssid, password=password)
    ap.active(True)
    
    while ap.active() == False:
        pass
    print('AP Mode Is Active, You can Now Connect')
    print('IP Address To Connect to:: ' + ap.ifconfig()[0])
    
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   #creating socket object
    s.bind(('', 80))
    s.listen(5)

    while True:
        conn, addr = s.accept()
        print('Got a connection from %s' % str(addr))
        request = conn.recv(1024)
        print('Content = %s' % str(request))
        if('GET / HTTP' in request):
            response = index_page()
            conn.send(response)
        elif('GET /?ssid=' in request):
            print('\n\n got ssid\n')
            ssid = urldecode(request.decode().split("ssid=")[1].split("&")[0])
            passw = urldecode(request.decode().split("password=")[1].split("&")[0])
            print(ssid+'>'+passw)
            response = fallback_page()
            conn.send(response)
            conn.close()
            ap.active(False)
            ap = None
            return (ssid,passw)
        else:
            response = fallback_page()
            conn.send(response)
        conn.close()