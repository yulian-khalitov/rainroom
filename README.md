# Rainroom

Software for entertainment attraction [Rainroom](https://www.mechanismus.pro/komnata-dozhdya)

# Applied equipment

* 4 [lidar](https://www.slamtec.com/en/Lidar/A1) sensors for determining the position of people

* **RS-485** controllers network communicating via **Modbus** protocol for on / off the rain
* **TCP/IP** to  **RS-485** adapter to send **Modbus** packages from server (PC) to controllers

# Run program
```
pip install numpy rplidar-roboticia modbus_tk pysimplegui
./source.py
```

# Demonstration (old version)

![alt text](https://github.com/yulian-khalitov/rainroom/blob/master/screenshots/screenshot1.jpg)
