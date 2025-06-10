# Watchdog
## Installation

```
python3 -m pip install -U watchdog --break-system-packages
python3 -m pip install -U websockets --break-system-packages
python3 -m pip install -r requirements.txt --break-system-packages
```

## Execution
```
tshark -i ens3 -b duration:2 -b files:100 -w output/capture.pcap -f "udp port 5000"
```
(in the testing environment execute)

```
tshark -i enp3s0 -b duration:2 -b files:100 -w output/capture.pcap -f "udp port 5000"
```

And then in another terminal

```
python3 monitor.py
```

From another terminal run

```
python3 -m http.server 9000
 ```

 Then visit 192.168.154.10:9000/operator.html

 (in the testing environment 192.168.1.18:9000/operator-testing.html)

From another terminal execute
```
relay.sh
```

(from the testing environment relay testing)

From another terminal execute mediamtx