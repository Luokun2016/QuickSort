#-*- coding: utf-8 -*- 

from django.db import models
from teachers.models import Teacher
#实验体系页面用到的数据库字段
# Create your models here.

class Experiment(models.Model):
	parent   = models.ForeignKey("self", blank=True, null=True, related_name="children")
	isFolder = models.BooleanField()
	name = models.CharField(max_length=50)
	code = models.CharField(max_length=50,blank=True,null=True)
	speciality = models.CharField(max_length=50,blank=True,null=True)
	remark = models.TextField(blank=True,null=True)
	description = models.TextField(blank=True,null=True)
	topo = models.TextField(blank=True,null=True)
	elementsType = models.CharField(max_length=1,blank=True,null=True)
	elements = models.TextField(blank=True,null=True)
	stepType = models.CharField(max_length=1,blank=True,null=True)
	step = models.TextField(blank=True,null=True)
	toolType = models.CharField(max_length=1,blank=True,null=True)
	tool = models.TextField(blank=True,null=True)
	videoType = models.CharField(max_length=1,blank=True,null=True)
	video = models.TextField(blank=True,null=True)
	createDate = models.DateTimeField(blank=True,null=True)
	createUser = models.ForeignKey(Teacher)

	def updateFromBak(self,expbakobj):
		self.name = expbakobj.name
		self.code = expbakobj.code
		self.speciality = expbakobj.speciality
		self.remark = expbakobj.remark
		self.description =expbakobj. description
		self.topo = expbakobj.topo
		# self.elementsType = expbakobj.elementsType
		# self.elements = expbakobj.elements
		# self.stepType = expbakobj.stepType
		# self.step = expbakobj.step
		# self.toolType = expbakobj.toolType
		# self.tool = expbakobj.tool
		# self.videoType = expbakobj.videoType
		# self.video = expbakobj.video
		self.save()
		return 1

class ExperimentBak(models.Model):
	parent   = models.ForeignKey("self", blank=True, null=True, related_name="children")
	isFolder = models.BooleanField()
	name = models.CharField(max_length=50)
	code = models.CharField(max_length=50,blank=True,null=True)
	speciality = models.CharField(max_length=50,blank=True,null=True)
	remark = models.TextField(blank=True,null=True)
	description = models.TextField(blank=True,null=True)
	topo = models.TextField(blank=True,null=True)
	elementsType = models.CharField(max_length=1,blank=True,null=True)
	elements = models.TextField(blank=True,null=True)
	stepType = models.CharField(max_length=1,blank=True,null=True)
	step = models.TextField(blank=True,null=True)
	toolType = models.CharField(max_length=1,blank=True,null=True)
	tool = models.TextField(blank=True,null=True)
	videoType = models.CharField(max_length=1,blank=True,null=True)
	video = models.TextField(blank=True,null=True)
	createDate = models.DateTimeField(blank=True,null=True)
	createUser = models.ForeignKey(Teacher)

