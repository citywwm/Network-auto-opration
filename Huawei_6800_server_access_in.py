#!/usr/bin/env python3
# -*- coding:UTF-8 -*-
import os,sys

#运行此脚本时，需要在后面跟上需要输入的列表名称，例如：python3 XXX.py AAA.csv ,否则程序报错。
#输入的CSV文件，格式应该符合规定格式。
#Read the CSV per line as a dictionary named RowDict
#将CSV文件读入，每行作为一个字典存储，字典的键名为表头名称，键值为表格内容，字典名为RowDict。
#DEVICENAME,sys,phyhostname,interface,isAbideUP,ip,port-channel,portCMode,mode,vlan,isLacpTimeoutFast
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

#开始创建配置，为每个输入列表中的设备名称（DEVICENAME）创建一个配置。
#

#Create vlan command for every Device.
#创建配置中的vlan部分，
#注意，vlan部分只能有3中写法：
#1、单独一个数字，如100； 
#2、多个不连续的vlan需要用"."隔开，如100.200.300;
#3、多个连续的vlan可以用"-"进行连接，如100-110
for i in range(0,len(InputList)):
	ConfigFile=open(InputList[i]['DEVICENAME']+'.cfg','a')
	if '.' in InputList[i]['vlan']:
		ConfigFile.write('vlan batch '+InputList[i]['vlan'].replace('.',' ')+'\n')
	elif '-' in InputList[i]['vlan']:
		ConfigFile.write('vlan batch '+InputList[i]['vlan'].replace('-',' to ')+'\n')
	else:
		ConfigFile.write('vlan '+InputList[i]['vlan']+'\n')
	ConfigFile.close()
#vlan创建完成，但是配置有些冗余，下一版本将去除重复命令。

#Create eth-trunk and interface command for every Device.
#为每个设备创建Eth-trunk配置。所有ConfigFile.write后面都是输入的命令，\n 是换行。
for i in range(0,len(InputList)):
	ConfigFile=open(InputList[i]['DEVICENAME']+'.cfg','a')
	if InputList[i]['port-channel'] != '':
		#Eth-trunk基础配置，编号，模式，描述等。
		ConfigFile.write('interface Eth-Trunk %s \n' %InputList[i]['port-channel'])
		ConfigFile.write(' description '+InputList[i]['sys']+'_'+InputList[i]['phyhostname']+'_'+InputList[i]['ip']+'\n')
		ConfigFile.write(' mode %s \n' %InputList[i]['portCMode'])
		if InputList[i]['isLacpTimeoutFast'] == 'y':
			ConfigFile.write(' lacp timeout fast \n')
		else:pass
		#Eth-trunk交换模式配置，access或trunk等，暂时无hybrid需求。
		if InputList[i]['mode'] == 'access' and '.' not in InputList[i]['vlan'] and '-' not in InputList[i]['vlan']:
			ConfigFile.write(' port link-type %s \n' %InputList[i]['mode'])
			ConfigFile.write(' port default vlan %s \n' %InputList[i]['vlan'])
			ConfigFile.write(' undo shutdown \n \n')
		elif InputList[i]['mode'] == 'trunk':
			ConfigFile.write(' port link-type %s \n' %InputList[i]['mode'])
			ConfigFile.write(' port trunk allow-pass vlan %s \n' %InputList[i]['vlan'].replace('.',' ').replace('-',' to '))			
			ConfigFile.write(' port trunk pvid vlan 1 \n')
			ConfigFile.write(' undo shutdown \n \n')
		else:
			print('port mode or vlan is not correct')
			ConfigFile.write(' port mode or vlan is not correct')
			ConfigFile.write(' undo shutdown \n \n')
		#物理端口与创建的Eth-trunk绑定配置。
		ConfigFile.write('interface %s \n' %InputList[i]['interface'])
		ConfigFile.write(' eth-trunk %s \n' %InputList[i]['port-channel'])	
		ConfigFile.write(' undo shutdown \n \n')
	else:
	#不需要Eth-trunk的单独物理端口配置
		ConfigFile.write('interface %s \n' %InputList[i]['interface'])
		ConfigFile.write(' description '+InputList[i]['sys']+'_'+InputList[i]['phyhostname']+'_'+InputList[i]['ip']+'\n')
		if InputList[i]['mode'] == 'access' and '.' not in InputList[i]['vlan'] and '-' not in InputList[i]['vlan']:
			ConfigFile.write(' port link-type %s \n' %InputList[i]['mode'])
			ConfigFile.write(' port default vlan %s \n' %InputList[i]['vlan'])
		elif InputList[i]['mode'] == 'trunk':
			ConfigFile.write(' port link-type %s \n' %InputList[i]['mode'])
			ConfigFile.write(' port trunk allow-pass vlan %s \n' %InputList[i]['vlan'].replace('.',' ').replace('-',' to '))			
			ConfigFile.write(' port trunk pvid vlan 1 \n')
		else:
			print('port mode or vlan is not correct')
			ConfigFile.write(' port mode or vlan is not correct')
		ConfigFile.write(' undo shutdown \n \n')
	ConfigFile.close()
	print(InputList[i]['DEVICENAME']+InputList[i]['interface']+' config created ')
#目前Eth-trunk端口配置有可能重复生成，下一版本可去除重复。
#由于华为6800交换机的配置命令中不支持 port trunk allow-pass vlan XXX add（最后加一个add）的命令，
#此脚本最好适用于端口新开，端口如果已经有配置，此脚本生成的配置需要慎重审核！！！

