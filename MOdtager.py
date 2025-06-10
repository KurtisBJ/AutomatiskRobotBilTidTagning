import paho.mqtt.client as mqtt
import ssl
from database import dbconnect


last_command = "none"
lab_times = []  # Buffer til lab tider



def on_message(client, userdata, msg):
    global last_command, lab_times
    message = msg.payload.decode().strip().strip("'").strip('"')
    print(f"Modtog MQTT-besked: {message}")
    last_command = message

    if message.lower() == "stop":
        print("STOP modtaget – venter på upload fra bruger")
        return  # Vi gemmer ikke i databasen her!

    try:
        lab_times.append(float(message))
    except ValueError:
        print(f"Modtog ugyldigt tal: {repr(message)}")



def mqtt_thread():
    client = mqtt.Client()
    client.username_pw_set("kris789", "Dsx82yzv")
    client.tls_set_context(ssl.create_default_context())
    client.connect("0cf7151b3a114f89baefcd26973c2d45.s1.eu.hivemq.cloud", 8883)
    client.subscribe("pico/tidtagning")
    client.subscribe("pico/sumo_stop")
    client.on_message = on_message
    client.loop_forever()

def get_last_command():
    global last_command
    current = last_command
    last_command = "none"  # reset efter læsning
    return current

def pop_lab_times():
    global lab_times
    if len(lab_times) < 3:
        return None
    result = lab_times[-3:]
    lab_times = lab_times[:-3]  # de 3 sidste
    return result