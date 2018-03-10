#-*- coding: utf-8 -*- 

from django.db import models
#教练管理模块数据库表字段
# Create your models here.
class Teacher(models.Model):
        teaname    = models.CharField(max_length=50)
        account    = models.CharField(max_length=50)
        pwd        = models.CharField(max_length=50)
        roletype   = models.IntegerField()
        sex        = models.IntegerField()
        email      = models.CharField(max_length=50,blank=True,null=True)
        mobile     = models.CharField(max_length=50,blank=True,null=True)
        otherlink  = models.CharField(max_length=50,blank=True,null=True)
        createtime = models.DateTimeField()
        edittime   = models.DateTimeField()
        needaudit  = models.IntegerField()