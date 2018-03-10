#-*- coding: utf-8 -*- 

'''
enumtype：枚举类型
enumdesc：枚举信息

typename：信息类型
enumid：类型民称



'''
from django.db import models
# Create your models here.
class DicType(models.Model):
	enumtype = models.CharField(max_length=50)			
	enumdesc = models.CharField(max_length=50)			

class DicContent(models.Model):
	typename = models.CharField(max_length=50)
	enumid = models.ForeignKey(DicType)