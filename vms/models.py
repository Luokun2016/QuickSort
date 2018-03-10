#-*- coding: utf-8 -*- 
'''
文件定义了虚拟终端设备的数据库模型
Img类型定义的是虚拟终端设备类型
Vm定义的是虚拟终端设备实例
'''

from django.db import models
from myexp.models import *
# Create your models here.
class Img(models.Model):
	name = models.CharField(max_length=50)
	exptype  = models.CharField(max_length=50)
	ostype = models.ForeignKey(DicContent)
	vmcount   = models.IntegerField()
	osversion  = models.CharField(max_length=50)
	filename  = models.CharField(max_length=50)
	remark = models.CharField(max_length=500)
	memory = models.IntegerField()
	cpu = models.IntegerField()
	osstruct = models.CharField(max_length=50)

class Vm(models.Model):
	name = models.CharField(max_length=50)
	imgtype  = models.ForeignKey(Img)
	mgrip   = models.CharField(max_length=50)
	mgrport  = models.IntegerField()
	state  = models.BooleanField()
	remark = models.CharField(max_length=500)
	memory = models.IntegerField()
	cpu = models.IntegerField()
	
	useNo = models.CharField(max_length=50,blank=True,null=True)
	usetype = models.IntegerField(blank=True,null=True)

	osstruct = models.CharField(max_length=50)
	containerIP = models.IPAddressField(default='127.0.0.1')