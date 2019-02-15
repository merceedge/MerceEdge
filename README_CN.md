# MerceEdge

[English](https://github.com/merceedge/MerceEdge/blob/master/README.md)


MerceEdge是一个边缘异构协议组件连接服务，可以运行在PC、RaspberryPi上以及服务器上，可以应用在多种场合，比如：SmartHome，SmartFactroy等，目前计划支持的协议包括：mqtt、ZigBee、BLE、REST API

MerceEdge可以：
* 在云计算边缘连接组合异构协议的IOT组件；
* 连接可以加入边缘计算模块，比如：数据过滤、数据分析、AI算法

## 什么是边缘异构协议组件连接服务

“边缘”是指工作在用户本地，处于云计算的边缘（可参考wiki边缘计算概念）；“异构协议连接”是指连接不同的物联网通信协议与接口，如：REST API、mqtt、BLE、2.4GHz、Zigbee等等；


## 我们为什么要做MerceEdge

围绕在我们身边的不同协议的物联网（IOT）设备越来越多，但不同协议类型的、遗留的、不同厂家的设备经常无法兼容，我们希望能够提供一种运行在用户本地，具有快速反应的、安全的、易用的连接服务，让用户能够根据自己的需要，灵活组织不同的设备交互，完成特定的功能。

## 抽象模型
</a>
<p align="center">
    <img src="https://github.com/merceedge/resources/blob/master/MerceEdge_models.png?raw=true", width="600px">
</p>


    * 组件（component）
    * 接口（interface）
    * 连线（wire）
    * 连线负载（wire load）
    * 方案（formula）


## 安装和运行
  ### 从源代码安装和运行
  1. git clone源代码

    git clone https://github.com/merceedge/MerceEdge.git
    git submodule init
    git submodule update

  2. 安装python3.6环境, 最好使用virtualenv或者pipenv, 具体情况请根据你的操作系统环境进行安装

在本地安装一个mqtt服务端（由于MerceEdge使用了MQTT服务，所以我们需要一个MQTT服务器，在MerceEdge中也可以指定一个已有的MQTT服务，在后面的文档中会介绍。这里我们直接安装一个MQTT服务就好）。本例使用mosquitto服务,  你可以参考[这里](https://mosquitto.org/download/)来下载安装， 安装好后默认运行：


    mosquitto -c /usr/local/etc/mosquitto/mosquitto.conf


  3. 安装MerceEdge

    (MerceEdge) / # cd MerceEdge
    (MerceEdge) MerceEdge # python setup.py develop




  4. 验证一下是否安装成功
   
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



  5. 运行一个边缘计算的例子
   
    （先Ctrl + c 停止上面的edge运行）

    （然后修改rtmp组件的配置文件）
     (MerceEdge) MerceEdge # vim merceedge/tests/formula/rtmp_demo_formula.yaml
     (修改第24行，然后保存并退出vim)
      rtmp_url: "rtmp://change_your_rtmp_path_here" 或者 rtmp_url: "/local_path/test_video.mp4"

     (运行)
     (MerceEdge) MerceEdge # edge -f ./merceedge/tests/formula/rtmp_demo_formula.yaml

打开另一个终端窗口, 同样使用前面设置好的MerceEdge virtualenv, 运行以下命令：

    (MerceEdge)  MerceEdge # cd merceedge/tests/demo 
    (MerceEdge)  demo # python object_detector_ui.py

  可以看到输出显示结果
  
</a>
<p align="center">
    <img src="https://github.com/merceedge/resources/blob/master/object_detection_demo_record.gif?raw=true", width="360px">
</p>


### 从docker运行
  1. 安装[docker](https://docs.docker.com/install/overview/)和[docker-compose](https://docs.docker.com/compose/install/)
  2.   git clone源代码

    git clone https://github.com/merceedge/MerceEdge.git .
    cd MerceEdge

  3. Build docker merceedge镜像

    docker-compose build

  4.  运行

    docker-compose up


## 例子
  * 边缘计算的例子

  本例从rtmp服务接收视频流，并使用基于Tensorflow目标识别的“连线负载”，对视频流进行目标识别分析，最后使用MQTT服务把视频分析结果发到显示终端组件上。


    (MerceEdge) MerceEdge # edge -f ./merceedge/tests/formula/rtmp_demo_formula.yaml

打开另一个终端窗口, 同样使用前面设置好的MerceEdge virtualenv, 运行以下命令：

    (MerceEdge)  MerceEdge # cd merceedge/tests/demo 
    (MerceEdge)  demo # python object_detector_ui.py

  * 使用不同协议button和light的连接例子(TODO)
  * 过滤接口数据的例子(TODO)
  


## 特性
1. Edge设备出厂默认使用yaml对一些Merce Group认证的组件支持，用户也可以根据自己需要自己扩展组件
2. 提供组件类型CURD操作（组件类型的 REST API）
3. 提供根据组件类型对组件实例CURD的操作（REST API ）
4. 提供连线的CURD操作
5. 连接异构组件



## 异构组件模版yaml schema格式（TODO）
## 设计 (TODO)

组件、接口、连线、协议Provider

* 图示
## 已知问题
## 开源协议（Apache License 2.0）
## 相关讨论区
* [Telegram](https://t.me/joinchat/AC9xSxWoAgXjLnBuQPFDqw)
* [Slack](https://merceedgecommunity.slack.com/archives/CFNQ62K6Y)

#MerceEdge#

