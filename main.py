#!/usr/bin/env python3
import configparser
import bluepy
import time
import socketserver
import http.server
import threading

config = configparser.ConfigParser()
config.read('ble_exporter.conf')
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
            print(f"Temperature: {temperature}c ({temperature*9/5+32}f)")
            humidity = int(data[20:22], 16)
            print(f"Humidity: {humidity}%")
            battery = int(data[22:24], 16)
            print(f"Battery: {battery}%")
            battery_mv = int(data[24:28], 16)
            print(f"{battery_mv} mV")
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
        try:
            print(f"Server started at localhost:{config['global']['port']}")
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()

daemon = threading.Thread(name="metricServer", target=runServer)
daemon.setDaemon(True)
daemon.start()
scanner = bluepy.btle.Scanner().withDelegate(updateData())
scanner.scan(timeout = 0)
