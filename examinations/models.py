#-*- coding: utf-8 -*- 

'''
本文件定义了竞赛的数据库模型
Examinations定义了竞赛的基本信息，主要包括使用的试卷，竞赛名称以及竞赛时间等
ExamTeacher保存了与竞赛对应的老师
ExamGroup保存了参加竞赛的团队
'''

from django.db import models
from teachers.models import Teacher
from papers.models import Paper
from groups.models import Group
from vms.models import Vm
from vgates.models import Vgate
from vswitches.models import Vswitch
# Create your models here.

class Examinations(models.Model):
	examNo = models.CharField(max_length=50)
	examName = models.CharField(max_length=50)
	examDescription = models.TextField(blank=True,null=True)
	examStartTime = models.DateTimeField()
	examEndTime = models.DateTimeField()
	examCreatorID = models.ForeignKey(Teacher)
	examCreateTime = models.DateTimeField()
	examEditTime = models.DateTimeField()
	examStatus = models.IntegerField()
	examPaperID = models.ForeignKey(Paper)

class ExamTeacher(models.Model):
	examID = models.ForeignKey(Examinations)
	teaID = models.ForeignKey(Teacher)

class ExamGroup(models.Model):
	examID =  models.ForeignKey(Examinations)
	groupID =  models.ForeignKey(Group)
