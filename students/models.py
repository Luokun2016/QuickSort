#-*- coding: utf-8 -*- 
'''
stuname：学员名称
stuno：学号
pwd：密码
sex：性别
clasid：班级ID
email：邮箱
mobile：电话
createtime：编辑时间
createbytea：创建教师
needaudit：审核标示位（0为不需要审核，1为需要审核）
'''

from django.db import models
from classes.models import Class
from teachers.models import Teacher
#Create your models here.
class Student(models.Model):
  stuname    = models.CharField(max_length=50)
  stuno      = models.CharField(max_length=50)
  pwd        = models.CharField(max_length=50)
  sex        = models.IntegerField()
  clasid     = models.ForeignKey(Class)
  email      = models.CharField(max_length=50,blank=True,null=True)
  mobile     = models.CharField(max_length=50,blank=True,null=True)
  createtime = models.DateTimeField()
  edittime   = models.DateTimeField()
  createbytea = models.ForeignKey(Teacher)
  needaudit  = models.IntegerField()
