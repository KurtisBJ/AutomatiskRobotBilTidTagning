import cv2 as cv
import cv2.aruco as aruco
import numpy as np
import paho.mqtt.client as mqtt

# === Konstanter ===
TAG_SIZE = 0.13  # i meter
SQUARE_TAGS = [0, 5, 6, 7]
MOVING_TAGS = [1, 2, 3, 4]
CALIBRATION_FILE = "calibration_data.npz"

# === MQTT Parametre ===
MQTT_SERVER = "0cf7151b3a114f89baefcd26973c2d45.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "kris789"
MQTT_PASSWORD = "Dsx82yzv"
MQTT_TOPIC = "pico/sumo_stop"

# === MQTT Setup ===
def on_connect(client, userdata, flags, rc):
    print(f"Forbundet til MQTT-server med kode {rc}")

def connect_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.tls_set()  # SSL til HiveMQ
    client.on_connect = on_connect
    client.connect(MQTT_SERVER, MQTT_PORT, 60)
    return client

def publish_mqtt(client, topic, message):
    client.publish(topic, message)
    print(f"MQTT → {topic}: {message}")

def load_calibration(file_path):
    with np.load(file_path) as data:
        return data["mtx"], data["dist"]

def create_detector():
    dictionary = aruco.getPredefinedDictionary(aruco.DICT_APRILTAG_36h11)
    parameters = aruco.DetectorParameters()
    return aruco.ArucoDetector(dictionary, parameters)

def is_point_inside_square(tag_pos, square_points):
    tag_xy = tuple(tag_pos[:2])
    square_xy = np.array([pt[:2] for pt in square_points], dtype=np.float32)
    return cv.pointPolygonTest(square_xy, tag_xy, False) >= 0

def draw_tag_info(frame, rvec, tvec, corner, tag_id, mtx, dist):
    cv.drawFrameAxes(frame, mtx, dist, rvec, tvec, TAG_SIZE * 0.5)
    x, y, z = tvec[0]
    corner_avg = np.mean(corner[0], axis=0).astype(int)
    text = f"ID:{tag_id} XYZ:[{x:.2f} {y:.2f} {z:.2f}]"
    cv.putText(frame, text, (corner_avg[0], corner_avg[1] - 10),
               cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

def process_frame(frame, detector, mtx, dist, prev_inside_states, all_outside_reported, mqtt_client):
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    corners, ids, _ = detector.detectMarkers(gray)

    if ids is None:
        return frame, prev_inside_states, all_outside_reported

    rvecs, tvecs, _ = aruco.estimatePoseSingleMarkers(corners, TAG_SIZE, mtx, dist)
    tag_dict = {id[0]: tvec[0] for id, tvec in zip(ids, tvecs)}

    for i, tag_id in enumerate(ids.flatten()):
        draw_tag_info(frame, rvecs[i], tvecs[i], corners[i], tag_id, mtx, dist)

    if all(tag in tag_dict for tag in SQUARE_TAGS):
        square_points_3d = [tag_dict[tag] for tag in SQUARE_TAGS]
        square_corners_2d, _ = cv.projectPoints(np.array(square_points_3d),
                                                np.zeros(3), np.zeros(3),
                                                mtx, dist)
        square_corners_2d = square_corners_2d.reshape(-1, 2).astype(int)
        cv.polylines(frame, [square_corners_2d], isClosed=True, color=(255, 0, 0), thickness=2)

        current_inside_states = {}

        for tag_id in MOVING_TAGS:
            if tag_id in tag_dict:
                moving_pos = tag_dict[tag_id]
                inside = is_point_inside_square(moving_pos, square_points_3d)
                current_inside_states[tag_id] = inside

                if prev_inside_states[tag_id] is None:
                    prev_inside_states[tag_id] = inside
                elif inside != prev_inside_states[tag_id]:
                    action = "entered" if inside else "exited"
                    print(f"Tag {tag_id} has {action} the square.")
                    prev_inside_states[tag_id] = inside

        if current_inside_states:
            all_outside = all(not inside for inside in current_inside_states.values())
            if all_outside and not all_outside_reported:
                print("Alle bevægelige tags er uden for kvadratet.")
                publish_mqtt(mqtt_client, MQTT_TOPIC, "stop")
                all_outside_reported = True
            elif not all_outside:
                all_outside_reported = False

    return frame, prev_inside_states, all_outside_reported

# === Main loop ===
def main():
    mtx, dist = load_calibration(CALIBRATION_FILE)
    detector = create_detector()

    cap = cv.VideoCapture(0)
    if not cap.isOpened():
        raise IOError("Kan ikke åbne webcam")

    mqtt_client = connect_mqtt()
    mqtt_client.loop_start()  # Kør som baggrundstråd

    prev_inside_states = {tag_id: None for tag_id in MOVING_TAGS}
    all_outside_reported = False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame, prev_inside_states, all_outside_reported = process_frame(
            frame, detector, mtx, dist, prev_inside_states, all_outside_reported, mqtt_client
        )

        cv.imshow("AprilTag Overvågning", frame)
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv.destroyAllWindows()
    mqtt_client.loop_stop()
    mqtt_client.disconnect()

if __name__ == "__main__":
    main()