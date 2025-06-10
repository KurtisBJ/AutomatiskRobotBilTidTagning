import config
from umqtt.simple import MQTTClient
import time


MQTT_SERVER = config.mqtt_server
MQTT_PORT = 0
MQTT_USER = config.mqtt_username
MQTT_PASSWORD = config.mqtt_password
MQTT_CLIENT_ID = b"raspberrypi_picow"
MQTT_KEEPALIVE = 7200
MQTT_SSL = True
MQTT_SSL_PARAMS = {"server_hostname": MQTT_SERVER}

forskel = 0

def connect_mqtt():
    client = MQTTClient(client_id=MQTT_CLIENT_ID,
                        server=MQTT_SERVER,
                        port=MQTT_PORT,
                        user=MQTT_USER,
                        password=MQTT_PASSWORD,
                        keepalive=MQTT_KEEPALIVE,
                        ssl=MQTT_SSL,
                        ssl_params=MQTT_SSL_PARAMS)
    client.set_callback(handle_message)
    client.connect()
    return client

def publish_mqtt(client, topic, value):
    client.publish(topic, value)
    print(f"Publiceret til {topic}: {value}")
    
def handle_message(topic, msg):
    global start_flag, forskel
    msg_str = msg.decode()  
    print(f"Modtaget: {topic.decode()} {msg_str}")

    try:
        command, timestamp = msg_str.split("|")
        timestamp = float(timestamp)  
        if topic == b"pico/start" and command == "start":
            pico_now = time.time()
            forskel = (pico_now - timestamp) / 10000
            start_flag = True
    except ValueError:
        print("Ugyldig besked – kunne ikke splitte besked korrekt.")
    
