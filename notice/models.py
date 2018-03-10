# encoding:utf-8
'''定义通知公告的数据库模型'''

from django.db import models

# Create your models here.
#Create your models here.
from django.db import models
from teachers.models import Teacher
class Notice(models.Model):
  survery   = models.CharField(max_length=50)
  content      = models.CharField(max_length=50)
  createtime = models.DateTimeField()
  edittime   = models.DateTimeField()
  createbytea = models.ForeignKey(Teacher)
