# -*- coding: UTF-8 -*-
'''
Tool定义了上传工具的数据库存储模型
'''

from django.db import models
from classes.models import Class
#Create your models here.
class Tool(models.Model):
  toolname    = models.CharField(max_length=50)
  toolmessage      = models.CharField(max_length=50)
  toolcreatetime = models.DateTimeField()
  toolinformation   = models.CharField(max_length=50)
  toolfile	=	models.CharField(max_length=50)