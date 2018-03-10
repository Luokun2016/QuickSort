#-*- coding: utf-8 -*- 
'''
ImgVsh定义了虚拟交换机的类型
Vswitch定义了虚拟交换机的实例
'''

from django.db import models
from myexp.models import *
# Create your models here.
class ImgVsh(models.Model):
	name = models.CharField(max_length=50)
	fac = models.CharField(max_length=50)
	xh  = models.CharField(max_length=50)
	vshtype  = models.ForeignKey(DicContent)
	version = models.CharField(max_length=50)
	starting = models.CharField(max_length=50)
	vshcount = models.IntegerField()
	filename  = models.CharField(max_length=50, blank=True, null=True)
	remark = models.CharField(max_length=500)
	
class Vswitch(models.Model):
	name = models.CharField(max_length=50)
	imgtype  = models.ForeignKey(ImgVsh)
	mgrip   = models.CharField(max_length=50, blank=True, null=True)
	mgrport  = models.IntegerField(blank=True,null=True)
	state  = models.BooleanField()
	remark = models.CharField(max_length=500)
	containerIP = models.IPAddressField(default='127.0.0.1')