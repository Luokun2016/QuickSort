# -*- coding: UTF-8 -*-

'''
Device定义了物理设备的数据库模型
'''

from django.db import models
from examinations.models import Examinations
# Create your models here.

class Device(models.Model):
	devname = models.CharField(max_length=50)
	devtype   = models.CharField(max_length=50)
	devxh  = models.CharField(max_length=50)
	devpub  = models.CharField(max_length=50)
	devfac = models.CharField(max_length=50)
	remark  = models.CharField(max_length=200)
	state	= models.BooleanField()
	ethx = models.CharField(max_length=500,blank=True,null=True)
	examuseNo = models.CharField(max_length=50,blank=True,null=True)
	usetype = models.IntegerField(blank=True,null=True)
	pyscript = models.CharField(max_length=100,blank=True,null=True)

