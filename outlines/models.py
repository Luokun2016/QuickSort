# -*- coding: UTF-8 -*-
'''
Outline定义一个实验大纲，一个实验大纲会包含很多实验
Chapter用于定义试验大纲的章节
Exprelation用于保存添加到实验大纲中的所有实验
Outlinerelation保存Outline与Exprelation以及Chapter之间的关系
'''

from django.db import models
from experiments.models import Experiment
from teachers.models import Teacher

# Create your models here.
class Outline(models.Model):
    onid = models.CharField(max_length=50)
    onname = models.CharField(max_length=50)
    teacherid = models.ForeignKey(Teacher)
    isdefaultoutline = models.BooleanField()
    remark = models.CharField(max_length=150,blank=True,null=True)
    createtime = models.DateTimeField()
    edittime = models.DateTimeField()
class Chapter(models.Model):
    capname = models.CharField(max_length=50)
class Exprelation(models.Model):
    exp = models.ForeignKey(Experiment)
    expname = models.CharField(max_length=50)
class Outlinerelation(models.Model):
    outlineid = models.ForeignKey(Outline)
    expid = models.ForeignKey(Exprelation,blank=True,null=True)
    chapterid = models.ForeignKey(Chapter,related_name='chapter',blank=True,null=True)
    parentid = models.ForeignKey(Chapter,related_name='parent',blank=True,null=True)