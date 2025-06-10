from time import sleep
import network




def initialize_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    timeout = 10
    while timeout > 0:
        if wlan.status() >= 3:
            break
        timeout -= 1
        print("Forbinder til Wi-Fi...")
        sleep(1)

    if wlan.status() != 3:
        
        return False
    print("Wi-Fi tilsluttet:", wlan.ifconfig()[0])
    
    return True
