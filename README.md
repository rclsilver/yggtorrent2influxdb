# yggtorrent2influxdb
Import YggTorrent ratio to InfluxDB

## Run it with docker

```
docker run \
    -d \
    -e YGGTORRENT_DOMAIN='<main_yggtorrent_domain>' \
    -e YGGTORRENT_USER='<your_yggtorrent_username>' \
    -e YGGTORRENT_PASS='<your_yggtorrent_password>' \
    -e INFLUXDB_HOST='<your_influxdb_host>' \
    -e INFLUXDB_PORT='<your_influxdb_port>' \
    -e INFLUXDB_USER='<your_influxdb_user>' \
    -e INFLUXDB_PASS='<your_influxdb_pass>' \
    -e INFLUXDB_BASE='<your_influxdb_base>' \
    rclsilver/yggtorrent2influxdb:v1.0.0
```

## Run it with kubernetes

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: yggtorrent2influxdb
  labels:
    name: yggtorrent2influxdb
    app: yggtorrent2influxdb
spec:
  replicas: 1
  selector:
    matchLabels:
      app: yggtorrent2influxdb
  template:
    metadata:
      name: yggtorrent2influxdb
      labels:
        app: yggtorrent2influxdb
        name: yggtorrent2influxdb
    spec:
      restartPolicy: Always
      containers:
      - name: yggtorrent2influxdb
        image: rclsilver/yggtorrent2influxdb:v1.0.0
        imagePullPolicy: IfNotPresent
        env:
          - name: YGGTORRENT_DOMAIN
            value: "<main_yggtorrent_domain>"
          - name: YGGTORRENT_USER
            value: "<your_yggtorrent_username>"
          - name: YGGTORRENT_PASS
            value: "<your_yggtorrent_password>"
          - name: INFLUXDB_HOST
            value: "<your_influxdb_host>"
          - name: INFLUXDB_PORT
            value: "<your_influxdb_port>"
          - name: INFLUXDB_USER
            value: "<your_influxdb_user>"
          - name: INFLUXDB_PASS
            value: "<your_influxdb_pass>"
          - name: INFLUXDB_BASE
            value: "<your_influxdb_base>"
```
