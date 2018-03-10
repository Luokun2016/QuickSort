#-*- coding: utf-8 -*- 

'''
Question定义了题目的数据库模型，表中存放了所有题目，以及各个类型题目的公共信息
Choose定义了基础题的数据库模型，包含了题目内容，题目图片以及与Question表中对应的id
Option是基础题的选项模型，表示该选项属于哪一个选择题，选项内容以及是否是正确选项
Skill定义了技能题的数据库模型
Infiltration定义了渗透题的数据库模型
Ask定义了简答题的数据库模型
'''

from django.db import models
from teachers.models import Teacher
# Create your models here.

class Question(models.Model):
	qid = models.CharField(max_length=50)
	qtype = models.CharField(max_length=50)
	qtitle = models.CharField(max_length=50)
	qscore = models.CharField(max_length=50)
	isfactory = models.CharField(max_length=50)
	teacherid = models.ForeignKey(Teacher)
	createtime = models.DateTimeField()
	edittime = models.DateTimeField()
	times = models.IntegerField()

	# def to_dict(self):
	# 	question = {
	# 		'id': self.pk
	# 		'type': self.qtype,
	# 		'title': self.qtitle,
	# 		'score': self.qscore
	# 	}

	# 	if self.qtype == '2':

	# 		choice = self.choose_set.all()[0]

	# 		question['content'] = choice.content

	# 		options = []

	# 		for option in choice.option_set.all():

	# 			options.put({
	# 					'id': option.pk,
	# 					'content': option.content,
	# 					'is_result': option.isresult
	# 				})

class Choose(models.Model):
	content =  models.CharField(max_length=50)
	picturedir = models.CharField(max_length=50,blank=True,null=True)	
	queid = models.ForeignKey(Question)


class Option(models.Model):
	oid  =  models.CharField(max_length=50)
	content = models.CharField(max_length=50)
	isresult = models.CharField(max_length=50)
	choid = models.ForeignKey(Choose)


class Skill(models.Model):
	link = models.CharField(max_length=100)
	result = models.CharField(max_length=200)	
	queid = models.ForeignKey(Question)
	topo = models.TextField(blank=True,null=True)


class Infiltration(models.Model):
	link = models.CharField(max_length=100)
	result = models.CharField(max_length=200)	
	queid = models.ForeignKey(Question)
	topo = models.TextField(blank=True,null=True)

class Ask(models.Model):
	content =  models.TextField(blank=True,null=True)
	contentpic = models.TextField(blank=True,null=True)
	result = models.TextField(blank=True,null=True)
	resultpic = models.CharField(max_length=50,blank=True,null=True)
	queid = models.ForeignKey(Question)


