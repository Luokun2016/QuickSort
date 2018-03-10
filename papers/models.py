#-*- coding: utf-8 -*-
'''
Paper用于定义试卷
PaperQuestion用于定义与试卷关联的所有题目
'''

from django.db import models
from teachers.models import Teacher
from questions.models import Question
# Create your models here.
class Paper(models.Model):
	papid = models.CharField(max_length=50)
	papname = models.CharField(max_length=50)
	creatorid = models.ForeignKey(Teacher)
	remark = models.TextField(blank=True,null=True)
	score = models.IntegerField()
	frequency = models.IntegerField()
	createtime = models.DateTimeField(blank=True,null=True)
	edittime =models.DateTimeField()

class PaperQuestion(models.Model):
	paperid = models.ForeignKey(Paper)
	questionid = models.ForeignKey(Question)