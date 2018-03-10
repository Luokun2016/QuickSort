#-*- coding: utf-8 -*- 

#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tsssite.settings")

    from django.core.management import execute_from_command_line
    from client.views import checkBrs

    # if包含的语句用于在服务器突然断电后，启动服务器时，检查虚拟机并修复
    # checkbrs.txt文件仅仅用于标识是否是刚刚启动服务器
    if not os.path.exists('/home/checkbrs.txt'):
        with open('/home/checkbrs.txt', 'w') as f:
            f.write("don't delete this file!!!!")
        checkBrs()
    execute_from_command_line(sys.argv)
