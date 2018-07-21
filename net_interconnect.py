#!/usr/bin/env python3
# -*- coding:UTF-8 -*-
import os,sys

#运行此脚本时，需要在后面跟上需要输入的列表名称，例如：python3 XXX.py AAA.csv ,否则程序报错。
#输入的CSV文件，格式应该符合规定格式。
#Read the CSV per line as a dictionary named RowDict
#将CSV文件读入，每行作为一个字典存储，字典的键名为表头名称，键值为表格内容，字典名为RowDict。
#LocalDevName,LocalVendor,LocalInterface,LocalUP,Channeled,LocalChannelMode,LocalChannelNumber,LocalIP,LocalMask,
#RemoteDevName,RemoteVendor,RemoteInterface,RemoteUP,RemoteChannelNumber,RemoteIP,RemoteMask,LacpTimeoutFast
#表头（键名）如上
InCSV = open(sys.argv[1],'r')
InputList=[]
DictNum = 0
#Created the dict key name , input a list.
#通过表头创建字典的键，并且将所有键名写入一个列表。 
CsvHeader = InCSV.readlines(1)[0].replace('\n','').split(',')
#This for loop change the CSV to a list , the list is [{name:aa,age:x},{{name:bb,age:y}},{{name:cc,age:z}}]
#每一行创建为一个字典，将所有的字典的组成一个列表，名称是InputList，格式[{name:aa,age:x},{{name:bb,age:y}},{{name:cc,age:z}}]
for i in InCSV.readlines():
	locals()['RowDict%s'%DictNum] ={}
	for j in range (0,len(i.split(','))):
		locals()['RowDict%s'%DictNum][CsvHeader[j]] = str(i.split(',')[j].replace('\n','').replace(r'"',''))
	InputList.append(locals()['RowDict%s'%DictNum])
	del locals()['RowDict%s'%DictNum]
	DictNum+=1
InCSV.close()

#创建列表完成
#Make directory and into it , Write the configration file .
#可选，创建一个目录并且进入该目录。
#此处应该处理一下，检测要创建的目录是否存在。暂时屏蔽掉。
#os.mkdir('./HWconfig')
#os.chdir('./HWconfig')

#开始创建配置，为每个输入列表中的设备名称（Local and Remote）创建一个配置。
#

#Create eth-trunk and interface command for Source Device.
#为起始端设备创建配置，配置从ConfigTemplate文件中读取,不同厂商有不同的配置模板。
for i in range(0,len(InputList)):
	SrcConfigFile=open(InputList[i]['LocalDevName']+'.cfg','a')
	#处理需要进行Ethchannel捆绑的配置。
	if InputList[i]['Channeled'].lower() == 'y':
		if InputList[i]['LocalVendor'].lower() == 'cisco':
			pass
			#read cisco config
		elif InputList[i]['LocalVendor'].lower() == 'huawei':
			#read huawei config
			ConfigTemplate=open('huawei_channel_cfg_template.cfg','r')
			for conf in ConfigTemplate.readlines():
				if '$$Eth-Trunk$$' in conf :
					SrcConfigFile.write(conf.replace('$$Eth-Trunk$$',InputList[i]['LocalChannelNumber']))
				elif '$$description$$' in conf :
					SrcConfigFile.write(conf.replace('$$description$$','link_to_'+InputList[i]['RemoteDevName']+'_'+InputList[i]['RemoteChannelNumber']))
				elif '$$lacpmode$$' in conf :
					SrcConfigFile.write(conf.replace('$$lacpmode$$',InputList[i]['LocalChannelMode']))
				elif '$$lacpfast$$' in conf and InputList[i]['LacpTimeoutFast'].lower() == 'y':
					SrcConfigFile.write(conf.replace('$$lacpfast$$','lacp timeout fast'))
				elif '$$lacpfast$$' in conf and InputList[i]['LacpTimeoutFast'].lower() != 'y':
					pass
				elif '$$ipaddress$$' in conf :
					SrcConfigFile.write(conf.replace('$$ipaddress$$',InputList[i]['LocalIP']+' '+InputList[i]['LocalMask']))
				elif '$$interface$$' in conf :
					SrcConfigFile.write(conf.replace('$$interface$$',InputList[i]['LocalInterface']))
				else :
					SrcConfigFile.write(conf)
			ConfigTemplate.close()
		elif InputList[i]['LocalVendor'].lower() == 'h3c':
			pass
			#read h3c config
		else :
			print('请指定设备厂商，以生成相应配置')
			break
	else :
		if InputList[i]['LocalVendor'].lower() == 'cisco':
			pass
			#read cisco config
		elif InputList[i]['LocalVendor'].lower() == 'huawei':
			#read HW config
			ConfigTemplate=open('huawei_interface_cfg_template.cfg','r')
			for conf in ConfigTemplate.readlines():
				if '$$interface$$' in conf :
					SrcConfigFile.write(conf.replace('$$interface$$',InputList[i]['LocalInterface']))
				elif '$$description$$' in conf :
					SrcConfigFile.write(conf.replace('$$description$$','link_to_'+InputList[i]['RemoteDevName']+'_'+InputList[i]['RemoteInterface']))
				elif '$$ipaddress$$' in conf :
					SrcConfigFile.write(conf.replace('$$ipaddress$$',InputList[i]['LocalIP']+' '+InputList[i]['LocalMask']))
				else :
					SrcConfigFile.write(conf)
			ConfigTemplate.close()
		elif InputList[i]['LocalVendor'].lower() == 'h3c':
			pass
			#read h3c config
		else :
			print('请指定设备厂商，以生成相应配置')
			break
	SrcConfigFile.close()
	print('src %s config genarate !' %InputList[i]['LocalDevName'])

#Create eth-trunk and interface command for Destination Device.
#为目标端设备创建配置，配置从ConfigTemplate文件中读取,不同厂商有不同的配置模板。
for i in range(0,len(InputList)):
	DstConfigFile=open(InputList[i]['RemoteDevName']+'.cfg','a')
	#处理需要进行Ethchannel捆绑的配置。
	if InputList[i]['Channeled'] == 'y':
		if InputList[i]['RemoteVendor'].lower() == 'cisco':
			pass
			#read cisco config
		elif InputList[i]['RemoteVendor'].lower() == 'huawei':
			#read huawei config
			ConfigTemplate=open('huawei_channel_cfg_template.cfg','r')
			for conf in ConfigTemplate.readlines():
				if '$$Eth-Trunk$$' in conf :
					DstConfigFile.write(conf.replace('$$Eth-Trunk$$',InputList[i]['RemoteChannelNumber']))
				elif '$$description$$' in conf :
					DstConfigFile.write(conf.replace('$$description$$','link_to_'+InputList[i]['LocalDevName']+'_'+InputList[i]['LocalChannelNumber']))
				elif '$$lacpmode$$' in conf :
					DstConfigFile.write(conf.replace('$$lacpmode$$',InputList[i]['LocalChannelMode']))
				elif '$$lacpfast$$' in conf and InputList[i]['LacpTimeoutFast'].lower() == 'y':
					DstConfigFile.write(conf.replace('$$lacpfast$$','lacp timeout fast'))
				elif '$$lacpfast$$' in conf and InputList[i]['LacpTimeoutFast'].lower() != 'y':
					pass
				elif '$$ipaddress$$' in conf :
					DstConfigFile.write(conf.replace('$$ipaddress$$',InputList[i]['RemoteIP']+' '+InputList[i]['RemoteMask']))
				elif '$$interface$$' in conf :
					DstConfigFile.write(conf.replace('$$interface$$',InputList[i]['RemoteInterface']))
				else :
					DstConfigFile.write(conf)
			ConfigTemplate.close()
		elif InputList[i]['RemoteVendor'].lower() == 'h3c':
			pass
			#read h3c config
		else:
			print('请指定设备厂商，以生成相应配置')
			break
#处理不需要进行EtherChannel捆绑的配置
	else:
		if InputList[i]['RemoteVendor'].lower() == 'cisco':
			pass
			#read cisco config
		elif InputList[i]['RemoteVendor'].lower() == 'huawei':
			#read huawei config
			ConfigTemplate=open('huawei_interface_cfg_template.cfg','r')
			for conf in ConfigTemplate.readlines():
				if '$$interface$$' in conf :
					DstConfigFile.write(conf.replace('$$interface$$',InputList[i]['RemoteInterface']))
				elif '$$description$$' in conf :
					DstConfigFile.write(conf.replace('$$description$$','link_to_'+InputList[i]['LocalDevName']+'_'+InputList[i]['LocalInterface']))
				elif '$$ipaddress$$' in conf :
					DstConfigFile.write(conf.replace('$$ipaddress$$',InputList[i]['RemoteIP']+' '+InputList[i]['RemoteMask']))
				else :
					DstConfigFile.write(conf)
			ConfigTemplate.close()
		elif InputList[i]['RemoteVendor'].lower() == 'h3c':
			pass
			#read h3c config
		else:
			print('请指定设备厂商，以生成相应配置')
			break
	DstConfigFile.close()
	print('dst %s config genarate !' %InputList[i]['RemoteDevName'])
