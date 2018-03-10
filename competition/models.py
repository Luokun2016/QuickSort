# -*- coding: UTF-8 -*-
'''这个数据表没有用'''

from django.db import models

# Create your models here.

class StudentAnwser(models.Model):

    class Meta:
        db_table = 'competition_student_answer'

    examination = models.OneToOneField('examinations.Examinations')

    student = models.OneToOneField('students.Student')

    question = models.OneToOneField('questions.Question')

    is_correct = models.BooleanField()

    options = models.ManyToManyField('questions.Option')

    content = models.CharField(max_length=200)
