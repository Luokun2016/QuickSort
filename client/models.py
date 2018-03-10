#-*- coding: utf-8 -*-
'''
Client，当有学员登录到客户端时，就向client表中添加一条记录，并且每隔几秒就刷新一次lasttime
该表主要用于清除空闲的实验环境

AnswerInfo表用于记录学员在竞赛或者攻防时提交的答案

Res表用于记录在使用过程中启动的虚拟机和添加的openvswitch虚拟网桥

VgateRes表主要用于记录虚拟安全设备中虚拟网卡的mac地址

ExpUseRecord表用于记录在实训过程中实验被使用的次数

VmsUseRecord表用于记录虚拟机被使用的次数
'''

from django.db import models
from experiments.models import Experiment
from students.models import Student
from courses.models import Course
from outlines.models import Exprelation
from groups.models import *
from questions.models import Question
# Create your models here.
class Client(models.Model):
    studentid = models.IntegerField()
    expid = models.ForeignKey(Exprelation,blank=True,null=True)
    coursename = models.CharField(max_length=50,blank=True,null=True) 
    lasttime = models.DateTimeField()
    copytopo =  models.TextField(blank=True,null=True)
    

class AnswerInfo(models.Model):
    groupid = models.ForeignKey(Group)
    examid = models.IntegerField()
    keyid =  models.IntegerField(blank=True,null=True)   
    is_correct = models.BooleanField()
    extime = models.DateTimeField()
    queid = models.ForeignKey(Question)
    answer = models.TextField(blank=True,null=True)
    # subgroupid = models.IntegerField(blank=True,null=True)
    anstype = models.IntegerField(default = 1)
    askActualGrade =  models.IntegerField(blank=True,null=True)


class Res(models.Model):
    userid = models.IntegerField()
    rectname = models.CharField(max_length=50)

    usebystu= models.ForeignKey(Student,blank= True,null=True)
    usebygroup=models.ForeignKey(Group,blank= True,null=True)
    
    rname = models.CharField(max_length=50)
    insname =  models.CharField(max_length=50)
    rtype = models.CharField(max_length=50)
    resid = models.IntegerField()
    coursename = models.CharField(max_length=50,blank= True,null=True)
    mac1 = models.CharField(max_length=50)
    mac2 = models.CharField(max_length=50)
    addr = models.CharField(max_length=50)
    restype = models.IntegerField(default = 0)
    isconsole = models.BooleanField(default=0)
    lasttime = models.DateTimeField()
    containerIP = models.IPAddressField(default='127.0.0.1')
    

class VgateRes(models.Model):
    vgateName = models.CharField(max_length=50)
    macAddr = models.CharField(max_length=50)
    pathKey=models.CharField(max_length=50)
    pathtext=models.CharField(max_length=50)
    userid = models.IntegerField()
    restype = models.IntegerField(default = 0)
    resid=models.IntegerField()


class ExpUseRecord(models.Model):
    expid = models.IntegerField()
    year = models.IntegerField()
    month = models.IntegerField()
    week = models.IntegerField()


class VmsUseRecord(models.Model):
    vmid = models.IntegerField()
    vmtype = models.CharField(max_length=50)
    deptname = models.CharField(max_length=50)
    grade = models.IntegerField()
    claname = models.CharField(max_length=50)
    stuname = models.CharField(max_length=50)
    expname = models.CharField(max_length=50)
    starttime = models.DateTimeField()
