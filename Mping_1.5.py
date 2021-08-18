#!/usr/bin/env python3
# -*- coding:UTF-8 -*-
from multiprocessing import Pool
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
import subprocess
import ipaddress
import xlwt
import time,os,pprint

def CollIPRIB():#登录设备，查看路由表，并处理。只留下/24的路由。
	WL3750 = {
		'device_type': 'cisco_ios',
		'host': '1.1.1.1',
		'username': 'username',
		'password': 'password'
	}
	SWssh = ConnectHandler(**WL3750)
	IPrib = SWssh.send_command("show ip route")
	#用NTC templates处理一下获得的数据
	RibInfo = parse_output(platform='cisco_ios',command="show ip route",data=IPrib)
	TmpList = []
	for i in RibInfo:
		if i['mask'] == '24':
			TmpStr = i['network']+'/'+i['mask']
			TmpList.append(TmpStr)
		else:
			continue
	#用Set给列表去重，防止有多个下一跳ECMP的情况，再转回列表返回。
	return list(set(TmpList))

def PingProc(address): #定义一个Ping的线程函数
	#Ping一个地址，Ping3次，间隔0.3秒，超时0.3秒，等待1秒。
	PingState = subprocess.call(['ping',str(address),'-c 3','-i 0.3','-W 0.3','-w 1'],stdout=subprocess.PIPE)
	if PingState == 0:#返回0表示ping通
		PR = 'Yes'
	elif PingState == 1:#返回1表示没ping通
		PR = 'No'
	else:#其他返回值
		PR = 'ERR'
	#返回两个值，一个是被Ping的地址，一个是Ping的结果
	return str(address),PR

#将结果写入表格，每个子网一个Sheet。传入两个参数，一个是ping时的子网列表，一个是结果字典
def Writexls(addlist,resultdict):
	CapTime = time.strftime('%Y_%m_%d-%H_%M_%S',time.localtime())#取个时间
	# 公共表格属性
	# 对齐方式：上下居中，左右居中
	Alignment = xlwt.Alignment ()
	Alignment.horz = 0x02
	Alignment.vert = 0x02
	# 字体：consolas 14号
	Font = xlwt.Font ()
	Font.name = 'Consolas'
	Font.height = 20 * 14
	# 结果为NO的单元格（地址可用）颜色-绿色
	PatternYes = xlwt.Pattern ()
	PatternYes.pattern = xlwt.Pattern.SOLID_PATTERN
	PatternYes.pattern_fore_colour = xlwt.Style.colour_map['green']
	# 结果为Yes的单元格（地址不可用）颜色-红色
	PatternNo = xlwt.Pattern ()
	PatternNo.pattern = xlwt.Pattern.SOLID_PATTERN
	PatternNo.pattern_fore_colour = xlwt.Style.colour_map['red']
	# 设置地址可用时的格式
	StlYes = xlwt.XFStyle ()
	StlYes.pattern = PatternYes
	StlYes.alignment = Alignment
	StlYes.font = Font
	# 设置地址不可用的格式
	StlNo = xlwt.XFStyle ()
	StlNo.pattern = PatternNo
	StlNo.alignment = Alignment
	StlNo.font = Font
	# 设置第一行的格式
	StlTitle = xlwt.XFStyle ()
	StlTitle.alignment = Alignment
	StlTitle.font = Font
	
	ListLenth = len(addlist)
	OutXls = xlwt.Workbook ()
	#创建一个列表，将每个sheet作为一个对象放入列表中。多sheet写入的情况，在此处卡了很久。
	SheetList = []
	for i in range(0,ListLenth):
		SheetList.append(OutXls.add_sheet(addlist[i].replace('/', '_')))

	#两个列表元素，双循环，省事。
	for sht,addr in zip(SheetList,addlist):
		# 写表头：描述是哪个网段
		# worksheet.write_merge(开始行,结束行, 开始列, 结束列, '内容', style)
		abc =''#这个就是用来处理个字段没啥用。
		for i in addr.split('.')[:3]:
			abc = abc + i + '.'
		
		sht.write_merge (0, 0, 1, 16, addr, style=StlTitle)
		for i in range (0, 16):
			for j in range (0, 16):
				if i * 16 + j == 0 or i * 16 + j == 255:
					sht.write (i + 1, j + 1, label=str (i * 16 + j), style=StlNo)
				else:
					if resultdict[abc + str (i * 16 + j)] == 'No':
						sht.write (i + 1, j + 1, label=str (i * 16 + j), style=StlYes)
					elif resultdict[abc + str (i * 16 + j)] == 'Yes':
						sht.write (i + 1, j + 1, label=str (i * 16 + j), style=StlNo)
					else:
						sht.write (i + 1, j + 1, label=str (i * 16 + j))
	
	OutXls.save (r'/root/Mping/Xls_file/%s_IPused.xls'%CapTime)
	return

if __name__ == '__main__':
	#通过登录外联3750，获取所有/24的路由，根据路由计算子网内地址。
	#有几个不是/24网段的，加入进来。
	Not24Subnet = ['10.12.254.0/24','10.12.255.0/24','10.12.15.0/24']
	AvlAdd = CollIPRIB() + Not24Subnet	
	#AvlAdd = ['10.12.32.0/24','10.12.42.0/24']#For testing data.
	PingResult = {}#最终ping的结果字典，格式‘IP’：‘YES/NO/ERR’
	#给IP子网列表排个序，否则输出会比较乱
	AvlIPAdd = sorted(AvlAdd,key = lambda x: (int(x.split('.')[0]), int(x.split('.')[1]), int(x.split('.')[2]), str(x.split('.')[3])))

	for IPPref in AvlIPAdd:
		#根据子网，计算子网内的IP地址，结果=1-254，没有全0和全1地址。
		DstAddList = ipaddress.ip_network(IPPref,strict=False).hosts()
		#定义进程池，括号内是最多有多少个进程，目前40个子网，定义128进程，大概不到2分钟完成。
		ProcNum = Pool(128)
		ProcResList = [] #进程以对象方式进入此列表，一个地址一个进程。
		for i in DstAddList:
			ProcRes = ProcNum.apply_async(PingProc, args=(i,))
			ProcResList.append(ProcRes)
		for PRL in ProcResList:
			RTN = PRL.get()
			PingResult[RTN[0]] = RTN[1]
		ProcNum.close() #关闭进程接收
		ProcNum.join() #等待所有进程完成
	#根据IP段和ping结果，写Excel
	Writexls(AvlIPAdd,PingResult)

	print('******The end**********')
	#pprint.pprint(PingResult)
	#print(AvlIPAdd)
