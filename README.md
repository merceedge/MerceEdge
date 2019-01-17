# Merce Edge

[English（TODO）](http://google.com)


MerceEdge是一个边缘异构协议组件连接服务，可以运行在PC、RaspberryPi上以及服务器上，可以应用在多种场合，比如：Smarthome，SmartFactroy等，目前计划支持的协议包括：mqtt、2.4GHz、BLE、REST API

* Edge可以：
    * 在云计算边缘连接组合异构协议的IOT组件；
    * 连接可以加入边缘计算模块，比如：数据过滤、数据分析、AI算法

* 什么是边缘异构协议组件连接服务 (TODO）

“边缘”是指工作在用户本地，处于云计算的边缘（可参考wiki边缘计算概念）；“异构协议连接”是指连接不同的物联网通信协议与接口，如：REST API、mqtt、BLE、2.4GHz、Zigbee等等；


* 我们为什么要做MerceEdge

围绕在我们身边的不同协议的物联网（IOT）设备越来越多，但不同协议类型的、遗留的、不同厂家的设备经常无法兼容，我们希望能够提供一种运行在用户本地，具有快速反应的、安全的、易用的连接服务，让用户能够根据自己的需要，灵活组织不同的设备交互，完成特定的功能。

* 术语表 (TODO)

    * 组件（component）
    * 接口（interface）
    * 连线（wire）
    * 连线负载（wire Load）
    * 方案（formula）


* 运行
  TODO
  * 从源代码运行
  * 从docker运行

* Demo 
  * 准备的硬件、软件、操作步骤等，链接app例子项目
  * 举一个使用不同协议button和light的连接例子
  * 过滤接口数据的例子
  * 边缘计算的例子


* 特性
1. Edge设备出厂默认使用yaml对一些Merce Group认证的组件支持，用户也可以根据自己需要自己扩展组件
2. 提供组件类型CURD操作（组件类型的 REST API）
3. 提供根据组件类型对组件实例CURD的操作（REST API ）
4. 提供连线的CURD操作
5. 连接异构组件



* 异构组件模版yaml schema格式（TODO）
* 设计 (TODO)

组件、接口、连线、协议Provider


* 每个组件实例硬件设备出厂后自带UUID，作为虚拟组件映射的id, 如果没有分配，edge会分配一个给该组件

问题：如何让Client知道Edge分配给这个组件的id？定位？Client根据Edge API返回记录下？

* 图示
  
* 开源协议（Apache License 2.0）

#MerceEdge#

