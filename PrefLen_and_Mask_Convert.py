#!/usr/bin/env python3
# -*- coding:UTF-8 -*-

def Pref_to_Mask(Prefix):
	if Prefix.isdigit():
		if int(Prefix) > 32 :
			print('The prefix number are great than 32 , it IPv4 address mask !')
		elif int(Prefix) < 0:
			print('The prefix number are less than 0 .')
		else:
			#Prefix = input('input your prefix number:')
			mask_bin = '1'*int(Prefix) + '0'*(32-int(Prefix))
			mask_dec = ''
			for i in range(0,4):
				mask_dec = mask_dec+ '.' +  str(int(mask_bin[i*8:(i+1)*8],2))
			return mask_dec[1:]
	else:
		print('Can you input a number ?')
def Mask_to_Pref(Mask):
	BinMask = ''
	PrefLen = 0
	for i in Mask.split('.'):
		TMask = str(bin(int(i))).replace('0b','')
		if len(TMask) < 8 :
			BinMask = BinMask + '0'*(8-len(TMask)) + TMask
		elif len(TMask) > 8 :
			print('The mask is not correct !')
		else: 
			BinMask = BinMask + TMask
	for i in BinMask:
		if i == '0':
			break
		elif i == '1':
			PrefLen += 1
	return PrefLen

if __name__ == '__main__':
	print(Pref_to_Mask(input('Input your prefix number:')))
	print(Mask_to_Pref(input('Input your net mask :')))



 
