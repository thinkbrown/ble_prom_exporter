#!/usr/bin/env python3
import configparser
import bluepy
import time
import socketserver
import http.server
import threading
import sys
import signal
import datetime
config = configparser.ConfigParser()
config.read('/etc/ble_exporter.conf')
dataPoints = {}
server = None
scanner = None

def logger(message):
    print(f"[{datetime.datetime.now().ctime()}] {message}", flush=True)

class updateData(bluepy.btle.DefaultDelegate):
    def __init__(self):
        bluepy.btle.DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if dev.addr in config.sections():
            dev_name = config[dev.addr]['name']
            logger(f"Received new data from {dev_name}")
            data = dev.getValueText(22)
            temperature = int(data[16:20], 16)/10
            humidity = int(data[20:22], 16)
            battery = int(data[22:24], 16)
            battery_mv = int(data[24:28], 16)
            dataPoints[dev.addr] = {'name': dev_name,
                              'temperature': temperature,
                              'humidity': humidity,
                              'battery': battery,
                              'battery_mv': battery_mv}


class metricHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        buffer = ""
        for point, value in dataPoints.items():
            buffer += f"ble_temperature{{address=\"{point}\", name=\"{value['name']}\"}} {value['temperature']}\n"
            buffer += f"ble_humidity{{address=\"{point}\", name=\"{value['name']}\"}} {value['humidity']}\n"
            buffer += f"ble_battery_percent{{address=\"{point}\", name=\"{value['name']}\"}} {value['battery']}\n"
            buffer += f"ble_battery_millivolts{{address=\"{point}\", name=\"{value['name']}\"}} {value['battery_mv']}\n"
        self.wfile.write(bytes(buffer, "utf8"))
        return


class metricServer(threading.Thread):
    def run(self):
        global dataPoints
        self.httpd = socketserver.TCPServer(("", int(config['global']['port'])), metricHandler)
        logger(f"Server started at localhost:{config['global']['port']}")
        self.httpd.serve_forever()
    def stop(self):
        self.httpd.server_close
        logger("metricServer closed")




def main():
    global server
    global scanner
    shutdownEvent = threading.Event()
    server = metricServer()
    server.start()
    scanner = bluepy.btle.Scanner().withDelegate(updateData())
    scanner.start()
    while True:
        scanner.process(timeout = 3)


def shutdownHandler(sig, frame):
    logger('Signal received, shutting down...')
    global server
    global scanner
    server.stop()
    scanner.stop()
    logger("scanner stopped, we're done here")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdownHandler)
    signal.signal(signal.SIGTERM, shutdownHandler)
    main()
