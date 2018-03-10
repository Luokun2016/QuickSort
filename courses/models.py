#-*- coding: utf-8 -*- 
'''
Course定义了课程的数据库模型
Coursestudent用于记录参加课程的所有学员
Courseteacher为课程的任课老师
'''

from django.db import models
from teachers.models import Teacher
from outlines.models import Outline
from students.models import Student

# Create your models here.
class Course(models.Model):
	cname = models.CharField(max_length=50)
	createrid = models.ForeignKey(Teacher,related_name='creater')
	comments=models.CharField(max_length=1024)
	begintime = models.DateTimeField()
	endtime = models.DateTimeField()
	createtime = models.DateTimeField()
	edittime = models.DateTimeField()
	outlineid = models.ForeignKey(Outline)

class Coursestudent(models.Model):
	courseid = models.ForeignKey(Course)
	studentid = models.ForeignKey(Student)
class Courseteacher(models.Model):
	courseid = models.ForeignKey(Course)
	teacherid = models.ForeignKey(Teacher)