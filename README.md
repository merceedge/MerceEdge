# MerceEdge

[中文](https://github.com/merceedge/MerceEdge/blob/master/README_CN.md)


MerceEdge is an edge heterogeneous protocol component connection service that can run on PC, RaspberryPi, and server. It can be used in a variety of applications, such as SmartHome, SmartFactroy, etc. Currently, the protocols currently planned include: mqtt, ZigBee, BLE, REST API.

MerceEdge can:
* Connect the IOT components of the combined heterogeneous protocol at the edge of the cloud computing
* Connections can be added to the edge calculation module, such as: data filtering, data analysis, AI algorithm

## What is the Edge Heterogeneous Protocol Component Connection Service?

"Edge" refers to working locally on the user's edge, at the edge of cloud computing (refer to the wiki edge computing concept); "heterogeneous protocol connection" refers to connecting different IoT communication protocols and interfaces, such as: REST API, mqtt, BLE , 2.4GHz, Zigbee, etc.


## Why do we want to develop MerceEdge

There are more and more Internet of Things (IOT) devices around different protocols around us, but different protocol types, legacy, and different vendors' devices are often incompatible. We hope to provide a kind of operation that is local to the user and has a quick response. The secure, easy-to-use connection service allows users to flexibly organize different device interactions and perform specific functions according to their needs.

## Glossary (TODO)

    * Component
    * Interface
    * Wire
    * Wire Load
    * Formula


## Installation and run
  ### Install and run from source code
  1. git clone source code

    git clone https://github.com/merceedge/MerceEdge.git
    git submodule init
    git submodule update

  2. Install python3.6 environment, it is best to use virtualenv or pipenv, please install according to your operating system environment.

Install a mqtt server locally (because MerceEdge uses the MQTT service, we need an MQTT server. We can also specify an existing MQTT service in MerceEdge, which will be introduced in the following document. Here we install an MQTT service directly. Just fine). This example uses the mosquitto service. You can download it by referring to [here] (https://mosquitto.org/download/). After installation, it will run by default:


    mosquitto -c /usr/local/etc/mosquitto/mosquitto.conf


  3. Install MerceEdge

    (MerceEdge) / # cd MerceEdge
    (MerceEdge) MerceEdge # python setup.py develop




  4. Verify that the installation was successful
   
    (MerceEdge) MerceEdge # edge

     __  __                   _____    _            
    |  \/  | ___ _ __ ___ ___| ____|__| | __ _  ___ 
    | |\/| |/ _ \ '__/ __/ _ \  _| / _` |/ _` |/ _ \
    | |  | |  __/ | | (_|  __/ |__| (_| | (_| |  __/
    |_|  |_|\___|_|  \___\___|_____\__,_|\__, |\___|
                                        |___/      

    Load user config file: 
    ...

    * Serving Flask app "merceedge.api_server.app" (lazy loading)
    * Environment: production
    WARNING: Do not use the development server in a production environment.
    Use a production WSGI server instead.
    * Debug mode: on



  5. Run an example of edge calculation
   
    （First Ctrl + c stop the above edge run）

    （Then modify the configuration file of the rtmp component）
     (MerceEdge) MerceEdge # vim merceedge/tests/formula/rtmp_demo_formula.yaml
     (Modify line 24, then save and exit vim)
      rtmp_url: "rtmp://change_your_rtmp_path_here" or rtmp_url: "/local_path/test_video.mp4"

     (Let's run)
     (MerceEdge) MerceEdge # edge -f ./merceedge/tests/formula/rtmp_demo_formula.yaml

Open another terminal window, and also use the MerceEdge virtualenv set up earlier, run the following command:

    (MerceEdge)  MerceEdge # cd merceedge/tests/demo 
    (MerceEdge)  demo # python object_detector_ui.py


 ![object detector](https://merceedge.oss-cn-hongkong.aliyuncs.com/object_detection_demo_record.gif)

### Run from docker (TODO)

## Demo
  * Demo of edge calculation

  This demo receives a video stream from the rtmp service and uses the object-detection "wired load" to perform target recognition analysis on the video stream, and then uses the MQTT service to send the video analysis result to the display terminal component.

    (MerceEdge) MerceEdge # edge -f ./merceedge/tests/formula/rtmp_demo_formula.yaml

Open another terminal window, and also use the MerceEdge virtualenv set up earlier, run the following command:

    (MerceEdge)  MerceEdge # cd merceedge/tests/demo 
    (MerceEdge)  demo # python object_detector_ui.py

  *  Use different protocol button and light connection examples (TODO)
  *  Example of filtering interface data (TODO)
  


## Feature
1. The Edge device defaults use yaml for some Merce Group certified components, and users can extend the components themselves according to their needs.
2. Provide component type CURD operations (component type REST API)
3. Provide operations on component instance CURD based on component type (REST API)
4. Provide wired CURD operation
5. Connect heterogeneous components



## Heterogeneous component template yaml schema format (TODO)
## Desgin (TODO)

Component, interface, connection, protocol provider


## Known issues(TODO)
## Open Source Agreement (Apache License 2.0)
## Related Discussion
* [Telegram](https://t.me/joinchat/AC9xSxWoAgXjLnBuQPFDqw)
* [Slack](https://merceedgecommunity.slack.com/archives/CFNQ62K6Y)

#MerceEdge#

