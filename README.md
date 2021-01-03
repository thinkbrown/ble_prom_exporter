# README

This is a simple exporter for listening to bluetooth low energy beacons and exporting their reported temperature/humidity to Prometheus

## Running

You should be able to build and run the container like this, but starting it with docker-compose is just easier.

See `example_service/` for an example

```
docker build . -t ble_exporter:latest
docker run -d -v "ble_exporter.conf:/etc/ble_exporter.conf" \
  --cap-add=CAP_NET_RAW --cap-add=CAP_NET_ADMIN \
  --network=host \
  ble_exporter:latest
```

