#-*- coding: utf-8 -*- 

from django.db import models
from students.models import Student
from teachers.models import Teacher
#团队管理部分数据库字段
# Create your models here.
class Group(models.Model):
	gname = models.CharField(max_length=50)
	createrid = models.ForeignKey(Teacher)
	createtime = models.DateTimeField()
	edittime = models.DateTimeField()

class GroupMembers(models.Model):
	groupid = models.ForeignKey(Group)
	studentid = models.ForeignKey(Student)
	iscaptain = models.BooleanField()
