import config
import hivemq
import wifi
import tidtag
import gc
from machine import Pin

gc.collect()
gc.mem_free()
laser = Pin(22, Pin.OUT)
start_flag = False
MQTT_TOPIC_WALLFOLLOW = "pico/tidtagning"
MQTT_TOPIC_START = "pico/start"




while True:
    try:
        if not wifi.initialize_wifi(config.wifi_ssid, config.wifi_password):
            print("Afslutter program – kunne ikke forbinde til Wi-Fi")
            
        else:
            print("Prøver at forbinde til MQTT...")
            client = hivemq.connect_mqtt()
            client.subscribe(MQTT_TOPIC_START)
            

        print("Venter på 'start' besked...")
        while not start_flag:
            client.wait_msg()
            laser.value(1)
            samlet_tid = None
            lab = 0
            sensor = tidtag.PicoWallfollow()
            while lab != 4:
                tid = sensor.read_tid()
                              
                if tid:
                    hivemq.publish_mqtt(client, MQTT_TOPIC_WALLFOLLOW, tid)
                    lab += 1
            if lab == 4:
                
                hivemq.publish_mqtt(client, MQTT_TOPIC_WALLFOLLOW, "stop")
                start_flag = False
                laser.value(0)
                lab -= 4
    except Exception as e:
        print(f"Fejl: {e}")

