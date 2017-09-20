# zzagent操作说明v1
一． 安装环境
1. CentOS 7/Debian 8
2. Python 2.7.6+（但2.7.9除外）

二． 配置启动（案例以192.168.163.101初始化）
1. 执行python命令
导入库文件： from zzagent.inits import *
创建server配置文件： create_server_ini('192.168.163.101')
创建client配置文件： create_client_ini('192.168.163.101')
Client端可以不用创建server配置文件

2. 修改server/client配置文件
默认在用户家目录创建.zzserver.ini和.zzclient.ini文件


修改相应的host，port值


启动服务
服务端：zzsrv start
客户端：zzcli start
可用命令zzmgr list查看当前连接


三． 调用说明（提供两种调用方式，RPC/9998端口与REST/9988端口）
1. RPC方式
批量执行命令


项目初始化


配置变更


推送文件（将server端配置文件所设定目录中的文件推送到client端）


2. REST方式（需安装requests库）
推送文件