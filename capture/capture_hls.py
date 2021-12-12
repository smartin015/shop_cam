#!/usr/bin/python3
import threading
import os
import time
import sys
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
import paho.mqtt.client as mqtt

STALL_COUNT = 2

def parseurl(name: str, url: str, outfile: str, already_parsed: list, client):
  try:
    response = [r.strip() for r in urlopen(url).read().decode("utf-8").split("\n")]
  except URLError: # No response
    return (already_parsed, False)
  except HTTPError:
    return (already_parsed, False)
  parsed = [r for r in response if not r.startswith('#') and r != '']
  new = False
  for line in parsed:
    if line in already_parsed:
      continue
    with open(outfile, 'ab') as f:
      try:
        f.write(urlopen(line).read())
      except HTTPError:
        continue
    client.publish("/av/status/capture/" + name, line)
    sys.stderr.write(f"{line} DONE\n")
    new = True
  return (parsed, new)

def record(base_dir, url, client):
    # Extract file name prefix from URL domain
    name = urlparse(url).netloc.split(":")[0]
    sys.stderr.write(f"Listening on {url} ({name})\n")
    last_parsed = set()
    t = threading.current_thread()
    lastnewdata = STALL_COUNT+1
    while t.alive:
      if lastnewdata > STALL_COUNT:
        outfile = os.path.join(base_dir, f"{name}_{int(time.time())}.ts")
      (last_parsed, newdata) = parseurl(name, url, outfile, last_parsed, client)
      if newdata and lastnewdata > STALL_COUNT:
        sys.stderr.write(f"new stream: {outfile}")
      lastnewdata = 0 if newdata else lastnewdata + 1
      if lastnewdata > STALL_COUNT: # Treat stalled pipeline as offline
        client.publish("/av/status/capture/" + name, "offline")
      time.sleep(5.0)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    sys.stderr.write("Connected to MQTT with result code "+str(rc))

if __name__ == "__main__":
  sys.stderr.write("Starting telemetry...\n")
  client = mqtt.Client()
  client.on_connect = on_connect
  client.connect("mqtt", 1883, 60)

  base_dir = "/mnt/usb1/l2/vlog/"
  threads = [
    threading.Thread(target=record, args=[base_dir, 'http://l2:8080/playlist.m3u8', client]),
    threading.Thread(target=record, args=[base_dir, 'http://picam1:8080/playlist.m3u8', client]),
    threading.Thread(target=record, args=[base_dir, 'http://jetson1:8080/playlist.m3u8', client]),
    threading.Thread(target=record, args=[base_dir, 'http://jetson2:8080/playlist.m3u8', client]),
  ]
  sys.stderr.write("Starting threads...\n")
  for t in threads:
    t.alive = True
    t.daemon = True
    t.start()

  sys.stderr.write("Running (Ctrl+C to stop)\n")
  try:
    client.loop_forever()
  except KeyboardInterrupt:
    pass
  sys.stderr.write("Stopping threads...\n")
  for t in threads:
    t.alive = False
  for t in threads:
    t.join()
  sys.stderr.write("Done\n")
