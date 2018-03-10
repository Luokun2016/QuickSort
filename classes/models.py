#-*- coding: utf-8 -*- 
'''
Department定义了院系的数据库模型
Class定义了班级的数据库模型
'''

from django.db import models
from teachers.models import Teacher
# Create your models here.
class Department(models.Model):	
    deptname = models.CharField(max_length=50)
    teacherid=models.ForeignKey(Teacher)
    createtime=models.DateTimeField()
    edittime=models.DateTimeField()
class Class(models.Model):
    claname = models.CharField(max_length=50)
    grade = models.IntegerField()  
    departmentid = models.ForeignKey(Department)
    teacherid=models.ForeignKey(Teacher)
    createtime=models.DateTimeField()
    edittime=models.DateTimeField()
