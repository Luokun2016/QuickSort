#-*- coding: utf-8 -*- 
'''
本文件定义了攻防对抗的数据库模型
Atkdfs定义了攻防对抗的基本信息
AtkdfsTeacher保存了与攻防对应的老师
AtkdfsGroup保存了参加攻防的团队
'''
from django.db import models
from teachers.models import Teacher
from papers.models import Paper
from groups.models import Group
from vms.models import Vm
from vgates.models import Vgate
from vswitches.models import Vswitch
from questions.models import Question
# Create your models here.

class Atkdfs(models.Model):
	atkdfsNo = models.CharField(max_length=50)
	atkdfsName = models.CharField(max_length=50)
	atkdfsDescription = models.TextField(blank=True,null=True)
	atkdfsStartTime = models.DateTimeField()
	atkdfsEndTime = models.DateTimeField()
	atkdfsCreatorID = models.ForeignKey(Teacher)
	atkdfsCreateTime = models.DateTimeField()
	atkdfsEditTime = models.DateTimeField()
	atkdfsStatus = models.IntegerField()
	atkdfsPaperID = models.ForeignKey(Paper)

class AtkdfsTeacher(models.Model):
	atkdfsID = models.ForeignKey(Atkdfs)
	teaID = models.ForeignKey(Teacher)

class AtkdfsGroup(models.Model):
	atkdfsID =  models.ForeignKey(Atkdfs)
	groupID =  models.ForeignKey(Group)
	quesID =  models.ForeignKey(Question,blank=True,null=True)
	copytopo =  models.TextField(blank=True,null=True)


