#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
文件会在服务器启动时被执行，用于执行一些初始化的命令
'''

import os, sys, cmd

def main():
	cmd.run('python /home/adp/product/web/tsssite/updata.py')
	cmd.run("service vsftpd start")
	cmd.run("service iptables stop")
	file_name="/var/lib/mysql/mysql.sock"
	if os.path.exists(file_name):
		cmd.run("rm -f /var/lib/mysql/mysql.sock")
	cmd.run("service mysqld start")
	cmd.run("setenforce 0")
	cmd.run("rm -f /home/checkbrs.txt")
	cmd.run('python /home/adp/product/web/manage.py runserver 0.0.0.0:80 &', getoutput = False)
	cmd.run("python /home/adp/product/web/console/webvirtmgr-novnc &", getoutput = False)
	cmd.run("rm -f /usr/local/var/run/openvswitch/db.sock")
	cmd.run("insmod /home/adp/packages/openvswitch-1.10.0/datapath/linux/openvswitch.ko")
	cmd.run("/usr/local/sbin/ovsdb-server /usr/local/etc/openvswitch/conf.db --remote=punix:/usr/local/var/run/openvswitch/db.sock --remote=db:Open_vSwitch,manager_options --detach")
	cmd.run("/usr/local/sbin/ovs-vswitchd unix:/usr/local/var/run/openvswitch/db.sock --pidfile --detach")
	#cmd.run("python /home/adp/web/tsssite/sysinit.py")
	
if __name__ == '__main__':
	main()
