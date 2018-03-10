#-*- coding: utf-8 -*- 
'''recodes用于记录一些重要的操作，记录结果可在系统管理模块的系统日志中看到'''
from django.db import models


# Create your models here.
class Records(models.Model):
    userid = models.CharField(max_length=50)
    usertype = models.IntegerField(default=0)#0:teacher;1:client

    operate = models.CharField(max_length=150)
    starttime = models.DateTimeField(auto_now_add=True)
    endtime = models.DateTimeField(auto_now=True)
    result = models.NullBooleanField()


