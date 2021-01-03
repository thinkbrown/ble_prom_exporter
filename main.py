#!/usr/bin/env python3
import configparser
import bluepy
import time
import socketserver
import http.server
import threading
import sys

config = configparser.ConfigParser()
config.read('/etc/ble_exporter.conf')
dataPoints = {}


class updateData(bluepy.btle.DefaultDelegate):
    def __init__(self):
        bluepy.btle.DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if dev.addr in config.sections():
            dev_name = config[dev.addr]['name']
            print(f"Received new data from {dev_name}")
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

def runServer():
    global dataPoints
    with socketserver.TCPServer(("", int(config['global']['port'])), metricHandler) as httpd:
        httpd.allow_reuse_address = True
        try:
            print(f"Server started at localhost:{config['global']['port']}")
            httpd.serve_forever()
        except:
            httpd.server_close()

daemon = threading.Thread(name="metricServer", target=runServer)
daemon.setDaemon(True)
daemon.start()
scanner = bluepy.btle.Scanner().withDelegate(updateData())
scanner.scan(timeout = 0)
