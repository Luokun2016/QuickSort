#-*- coding: utf-8 -*- 

'''
定义了虚拟安全设备所使用的数据库模型
ImgVgt定义的是虚拟安全设备类型
Vgate定义的是虚拟安全设备实例
'''

from django.db import models
from myexp.models import *
# Create your models here.
class ImgVgt(models.Model):
	name = models.CharField(max_length=50)
	xh  = models.CharField(max_length=50)
	vgttype  = models.ForeignKey(DicContent)
	version = models.CharField(max_length=50)
	validate = models.DateField(auto_now=False, auto_now_add=False)
	license  = models.IntegerField()
	vgtcount = models.IntegerField()
	filename  = models.CharField(max_length=50)
	remark = models.CharField(max_length=500)
	memory = models.IntegerField()
	cpu = models.IntegerField()
	osstruct = models.CharField(max_length=50)

class Vgate(models.Model):
	name = models.CharField(max_length=50)
	imgtype  = models.ForeignKey(ImgVgt)
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