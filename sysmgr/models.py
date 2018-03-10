#-*- coding: utf-8 -*-
'''
Host定义了物理服务器的数据库模型，该表用于对服务器进行管理，服务器集群功能需要使用该表中的数据，
此外在连接服务器本机的libvirt进行虚拟机管理操作时，也需要使用这个表

Instance数据表没有被使用
'''

from django.db import models

# Create your models here.
class Host(models.Model):
    name = models.CharField(max_length=20)
    hostname = models.CharField(max_length=20)
    login = models.CharField(max_length=20)
    password = models.CharField(max_length=14, blank=True, null=True)
    type = models.CharField(max_length=3)
    port = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return self.hostname

class Instance(models.Model):
    host = models.ForeignKey(Host)
    vname = models.CharField(max_length=12)
    vnc_passwd = models.CharField(max_length=12)

    def __unicode__(self):
        return self.vname