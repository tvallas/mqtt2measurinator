import paho.mqtt.client as mqtt
import time
import json
import hashlib
from datetime import datetime
import requests
from argparse import ArgumentParser
import os
import logging
import sys
from requests.exceptions import HTTPError

def create_parser():
    """
    Cli module argument parser
    """
    parser = ArgumentParser(description="""
    MTR transmitter readings from MQTT topic to measurinator api. 
    Most options can be also configured using environment variables.
    """)

    parser.add_argument(
        "--mqtt-host", '-m',
        help="MQTT host address (ENV: MQTT_HOST)",
        default=os.environ.get('MQTT_HOST'),
        required=False)
    parser.add_argument(
        "--mqtt-port", '-p',
        help="MQTT host port (ENV: MQTT_PORT)",
        default=int(os.environ.get('MQTT_PORT', 1883)),
        required=False)
    parser.add_argument(
        "--mqtt-topic", '-t',
        help="MQTT topic (ENV: MQTT_TOPIC)",
        default=os.environ.get('MQTT_TOPIC', "measurements/#"),
        required=False)
    parser.add_argument(
        "--client_id", '-c',
        help="Measurinator client id (ENV: MEASURINATOR_CLIENT_ID)",
        default=os.environ.get('MEASURINATOR_CLIENT_ID'),
        required=False)
    parser.add_argument(
        "--key", '-k',
        help="Measurinator secret key (ENV: MEASURINATOR_KEY)",
        default=os.environ.get('MEASURINATOR_KEY'),
        required=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--debug", '-d',
        help="Enable pringing debug messages (ENV: DEBUG)",
        required=False,
        default=os.environ.get('DEBUG', 'False').lower() in ['true', '1'],
        action='store_true'
        )
    group.add_argument(
        "--quiet", '-q',
        help="Print only error messages (ENV: QUIET)",
        required=False,
        default=os.environ.get('QUIET', 'False').lower() in ['true', '1'],
        action='store_true'
        )
    group.add_argument(
        "--version", "-v",
        help="Print the mqtt2measurinator version number and exit",
        required=False,
        default=False,
        action='store_true'
    )

    return parser

def _open_mqtt_connection(args):
    """
    Get MQTT client
    """

    mqtt.Client.connected_flag = False #create flag in class
    client = mqtt.Client('mqtt2measurinator')
    client.enable_logger()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    mqtt_host = 'localhost'
    mqtt_port = 1883
    if args.mqtt_host:
        mqtt_host = args.mqtt_host

    if args.mqtt_port:
        mqtt_port = int(args.mqtt_port)

    client.loop_start()
    logging.info(f"Connecting to MQTT host: {mqtt_host}:{mqtt_port}")
    try:
        client.connect(mqtt_host,mqtt_port)
        while not client.connected_flag: #wait in loop
            logging.debug("Waiting for MQTT connection")
            time.sleep(1)
    except mqtt.socket.timeout:
        logging.exception("MQTT server connection timeout")
        sys.exit(-1)
    except mqtt.socket.error:
        logging.exception("Unable to connect to MQTT host")
        sys.exit(-1)
    return client

def on_connect(client, userdata, flags, connection_result):
    """"
    Handles actions on MQTT connect
    """
    logging.debug("userdata: %s, flags: %s", userdata, flags)
    if connection_result==0:
        client.connected_flag = True #set flag
        logging.info("MQTT server connected OK")
    else:
        logging.warning("Bad connection Returned code=%s",str(connection_result))

def on_disconnect(client, userdata, connection_result):
    """"
    Handles actions on MQTT disconnect
    """
    logging.warning(
        "MQTT server disconnected with reason: %s, userdata: %s",
        str(connection_result), userdata
        )
    client.connected_flag=False
    client.disconnect_flag=True

client_id = ""
key = ""
version = 3

def get_checksum(version, timestamp, voltage, signal_strength, client_id, sensor_id, measurement, key):
    src = f'{version}&{timestamp}&{voltage}&{signal_strength}&{client_id}&{sensor_id}&{measurement}&{key}'
    return hashlib.sha1(src.encode()).hexdigest()  

def on_message(client, userdata, message):
    logging.debug("mqtt message: %s" ,str(message.payload.decode("utf-8")))
    json_message = json.loads(str(message.payload.decode("utf-8")))
    if( json_message["type"] != "UTILITY" ):
        measurement = str(json_message["reading"])
        sensor_id = json_message["id"]
        voltage = str(json_message["battery"])
        signal_strength = str(json_message["rsl"])
        timestring = json_message["timestamp"]
        timestamp = str(int(datetime.timestamp(datetime.fromisoformat(timestring))*1000000000))
        checksum = get_checksum(version, timestamp, voltage, signal_strength, client_id, sensor_id, measurement, key)

        body = {"checksum": checksum, "client_id": client_id, "measurement": measurement, "sensor_id": sensor_id, "signal_strength": signal_strength, "timestamp": timestamp, "version": version, "voltage": voltage }

        r = requests.post('https://api.measurinator.com/measurements', json=body)
        if ( (int(r.status_code) >= 200) & int(r.status_code) < 300 ):
            logging.debug("Successfully posted: %s", json.dumps(body))
        if (int(r.status_code) >= 400):
            response = r.json()
            logging.warning("Failed to post %s, status code: %s, reason: %s, error_msg: %s", json.dumps(body), r.status_code, r.reason, response["error_msg"])


def main():
    """
    Main function
    """

    args = create_parser().parse_args()


    # Configure logging
    log_format ='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format=log_format)
        print("Debug logging enabled")
    elif args.quiet:
        logging.basicConfig(level=logging.WARNING)
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
        sys.tracebacklimit=0

    global client_id
    global key
    client_id = args.client_id
    logging.info("Using client id: %s", client_id)
    key = args.key

    client = _open_mqtt_connection(args)

    logging.info("Subscribing to MQTT topic \"%s\"", args.mqtt_topic)
    client.subscribe(args.mqtt_topic)


    while True:
        time.sleep(60)



if __name__ == "__main__":
    main()