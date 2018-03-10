#-*- coding: utf-8 -*- 

'''
1. 显示虚拟终端设备界面：调用mgrvm方法；
2. 添加虚拟服务器类型：调用addimg方法，在数据库中添加数据，并将上传的虚拟机镜像同步到所有服务器的
相同目录下；
3. 修改虚拟服务器类型：调用editimg方法，修改数据库中的数据，如果上传有新的镜像文件，则先调用rmPreImg
方法，将所有服务器上原来的镜像文件删除，然后使用新的镜像文件替换；
4. 删除虚拟服务器类型：首先调用delimgall方法，在方法中调用所有服务器上的delimg方法，删除所有服务器上
的镜像文件，完全删除之后，清除数据库中的数据；
5. 创建虚拟服务器：首先调用selectServer方法，选择一台最合适的服务器用于创建新的虚拟机，选择好之后，调
用该服务器上的createvm方法，复制一个全新的镜像到指定的目录下，并根据提供的参数创建一个xml文件用于定义
新建的虚拟机；
6. 虚拟服务器详情：调用getInstanceInfo方法，获取该虚拟机存在于哪一台服务器之上，然后调用该服务器上的
instance方法，获取虚拟机详情，并返回一个新的页面；
7. 启动虚拟机：首先调用selectServerVMStart方法，获取该虚拟机所在服务器的ip，然后调用该服务器上的vmstart
方法，启动该虚拟机；
8. 虚拟机控制台：调用client模块下views.py文件中的getServerIp方法，返回虚拟机所在服务器ip，并构建控制台
链接；
9. 停止虚拟机：调用selectServerVMStop方法，获取虚拟机所在服务器ip，调用该服务器上的vmstop方法，停止该
虚拟机的运行；
10. 编辑虚拟机：首先调用selectServerEditVM方法，确定虚拟机所在服务器，并调用该服务器上的editvm方法，修改
该虚拟机的参数；
11. 还原虚拟机：首先调用selectServerResetVM方法，确定虚拟机所在服务器，然后调用该服务器上的resetvm方法，
删除指定的虚拟机，并使用原始镜像创建一台相同名字的虚拟机；
12. 删除虚拟机：首先调用selectServerDelVM方法，确定虚拟机所在服务器，然后调用该服务器上的delvm方法，删除
数据库中的数据与虚拟机镜像文件。
'''

# Create your views here.
from django.shortcuts import render_to_response
from vms.models import *
from vgates.models import *
from vswitches.models import *
from libvirt import libvirtError
from sysmgr.models import *
from tsssite.server import ConnServer,get_xml_path
from tsssite.settings import TIME_JS_REFRESH, STATIC_DOCUMENT
from tsssite.settings import IMAGE_PATH
from myexp.models import *
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseServerError
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
import json, re, random, os
from django.db.models import Q
from django.utils.datastructures import SortedDict
from vgates.models import Vgate
import time, os,os.path, shutil
import logging
from django.core.urlresolvers import reverse
import urllib
import urllib2
from client.models import *

logger = logging.getLogger('mysite.log')
vmls_pages = 1
imgls_pages = 1
#@csrf_protect
def mgrvm(request):
    if not 'username' in request.session:
        return HttpResponseRedirect('/Login/')

    username = request.session['username']
    imgls = Img.objects.order_by('-id')
    vmls = Vm.objects.order_by('name')
    dictype = DicType.objects.get(enumtype='ostype')
    ostypels= DicContent.objects.order_by('id').filter(enumid_id=dictype.id)
    querytext = ''
    queryimg = ''

    if 'querytext' in request.GET and request.GET['querytext']:
        querytext = request.GET['querytext']
        request.session['querytext'] = querytext

    if 'queryimg' in request.GET and request.GET['queryimg']:
        queryimg = request.GET['queryimg']
        request.session['querytext'] = querytext

    # tabtype = 'vm'
    types="vmls"
    try:
        m_type = request.GET.get("type")
        if m_type == "img":
            types='img'
    except ValueError:
        types="vmls" 


    # if 'btnqueryimg' in request.GET:
    #     request.session['tabtype'] = 'img'

    if querytext in request.session:
        querytext = request.session['querytext']
    goon=0
    for imgl in imgls:
        if querytext == imgl.name:
            num=imgl.id
            vmls=vmls.filter(Q(name__icontains=querytext)|Q(imgtype_id=num))
            goon=1
            break
    if goon==0:
        vmls=vmls.filter(Q(name__icontains=querytext))# |Q(mgrip__icontains=querytext)
    imgls=imgls.filter(Q(name__icontains=queryimg)|Q(exptype__icontains=queryimg))
    
    # if 'tabtype' in request.session:
    #     tabtype=request.session['tabtype']
    #     request.session.pop('tabtype')

    try:
        page = int(request.GET.get("page",1))
        if page < 1:
            page = 1
    except ValueError:
        page = 1    
    # 分别控制两个Tab翻页的页数
    if(types == "img"):
        global imgls_pages
        imgls_pages = page
    else:
        global vmls_pages
        vmls_pages=page
    paginator_vmls = Paginator(vmls,10)
    try:
        vmls = paginator_vmls.page(vmls_pages)
    except(EmptyPage,InvalidPage,PageNotAnInteger):
        vmls = paginator_vmls.page(paginator_vmls.num_pages)
    # 记录总页数    
    page_long = len(paginator_vmls.page_range)
    page_long_vmls=page_long
    if page_long<=5:
        page_range = paginator_vmls.page_range[0:page_long]    
    else:
        if vmls_pages<=3:
            page_range = paginator_vmls.page_range[0:5]
        else:
            if (page_long-vmls_pages) >= 2:   
                page_range = paginator_vmls.page_range[vmls_pages-3:vmls_pages+2]
            else:
                page_range = paginator_vmls.page_range[page_long-5:page_long]  
    page_range_vmls =  page_range

    paginator_imgls = Paginator(imgls,10)
    try:
        imgls = paginator_imgls.page(imgls_pages)
    except(EmptyPage,InvalidPage,PageNotAnInteger):
        imgls = paginator_imgls.page(paginator_imgls.num_pages)

    # 记录总页数    
    page_long = len(paginator_imgls.page_range)
    page_long_imgls=page_long
    if page_long<=5:
        page_range = paginator_imgls.page_range[0:page_long]    
    else:
        if vmls_pages<=3:
            page_range = paginator_imgls.page_range[0:5]
        else:
            if (page_long-vmls_pages) >= 2:   
                page_range = paginator_imgls.page_range[vmls_pages-3:vmls_pages+2]
            else:
                page_range = paginator_imgls.page_range[page_long-5:page_long]  
  
    page_range_imgls =  page_range

    return render_to_response('templates/vm.html',{'queryimg':queryimg,'querytext':querytext,'type':types,'vmls': vmls, 'ostypels': ostypels, 'imgls': imgls,'username':username,'page_long_vmls':page_long_vmls,'page_long_imgls':page_long_imgls,'page_range_vmls':page_range_vmls,'page_range_imgls':page_range_imgls,'page':page}, context_instance=RequestContext(request))

def vminfo(request):
    vm = ''
    if request.method == 'POST':
        vmid = request.POST['vmid']
        vm = Vm.objects.get(id=vmid)
        data = {}
        data["vmid"] = vm.id
        data["vmname"] = vm.name
        data["vmtype"] = vm.imgtype.id
        data["vmram"] = vm.memory
        data["vmcpu"] = vm.cpu    
        data["vmmgrip"] = vm.mgrip
        data["vmmgrport"] = vm.mgrport
        data["remark"] = vm.remark
    return HttpResponse(json.dumps(data))


def selectServerEditVM(request):
    try:
        did = int(request.POST['vmid'])
        vm = Vm.objects.get(id=did)
        datas = {
            'vmid': request.POST['vmid'],
            'vmname': request.POST['vmname'],
            'vmmgrip': request.POST['vmmgrip'],
            'vmremark': request.POST['vmremark'],
            'vmmgrport': request.POST['vmmgrport'],
            'vmram': int(request.POST['vmram']),
            'vmcpu': int(request.POST['vmcpu'])
        }
        re = post("http://" + vm.containerIP + "/vmedit/", datas)
        return HttpResponse(re)
    except ValueError:
        logger.error("vms")
        raise Http404()


def editvm(request):
    global logger
    try:
        did = int(request.POST['vmid'])
        vm = Vm.objects.get(id=did) 
    except ValueError:
        logger.error("vms")
        raise Http404()
                
    if request.method == 'POST':
        vm.name = request.POST['vmname']
        vm.mgrip = request.POST['vmmgrip']
        vm.remark = request.POST['vmremark']
        vm.mgrport = request.POST['vmmgrport']
        #vm.imgtype_id = int(request.POST['vmtype'])
        vm.memory = int(request.POST['vmram'])
        vm.cpu = int(request.POST['vmcpu'])
    vm.save()
    host_id = 1
    errors = []
    data={}
    result = 1
    form = None
    host = Host.objects.get(id=host_id)
    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None
        result = 0
        data["result"] = result
        return HttpResponse(json.dumps(data))

    if not conn:
        errors.append(e.message)
    else:
        try:
            conn.vds_edit(vm.name, 'None', vm.memory, vm.cpu) 
        except libvirtError as msg_error:
            errors.append(msg_error.message)
            result = 0
            data["result"] = result
            return HttpResponse(json.dumps(data))
        conn.close()
    # return HttpResponseRedirect('/vms/')
    data["result"] = result
    return HttpResponse(json.dumps(data))


def selectServerResetVM(request):
    try:
        vm = Vm.objects.get(id=int(request.POST["vmid"]))
        logger.info('start to reset vm %s on server %s' % (vm.name, vm.containerIP))
        data = post("http://" + vm.containerIP + "/resetvm/", {"vmid": request.POST["vmid"]})
        logger.info('reset end. ' + str(data))
        return HttpResponse(data)
    except ValueError:
        logger.exception('vms')
        raise Http404()


def resetvm(request):
    global logger
    result = 1
    host_id = 1
    data={}
    try:
        did = int(request.POST['vmid'])
        vm = Vm.objects.get(id=did)
    except ValueError:
        logger.error("vms")
        raise Http404()

    img = vm.imgtype
    imgpath = STATIC_DOCUMENT + 'vm/%s/' % img.id
    try:
        host = Host.objects.get(id=host_id)
    except Exception, e:
        return HttpResponseRedirect('/vms/')
    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None
    if conn:
        dom = conn.lookupVM(vm.name)
        vmimg = get_xml_path(dom.XMLDesc(0), "/domain/devices/disk[1]/source/@file")
    img = imgpath + os.listdir(imgpath)[0]
    # f = file("/home/1.txt","w+")
    # f.write(img)
    # f.close()
    if os.path.isfile(vmimg):
        cmd = 'rm -rf ' + vmimg
        os.system(cmd)
        shutil.copyfile(img, vmimg)
    data['result'] = 0
    return HttpResponse(json.dumps(data))

def getVmStatus(request):
    try:
        did = int(request.POST['id'])
        vms = Img.objects.get(id=did).vm_set.all()
        flag = 0
        for vm in vms:
            if vm.state == 1:
                flag = 1
                break
        return HttpResponse(json.dumps(flag))
    except Exception:
        logger.exception("get vgate error")
        raise Http404

def selectServerDelVM(request, did):
    try:
        vm = Vm.objects.get(id=int(did))
        urllib.urlopen("http://" + vm.containerIP + "/tools/vmdelonserver/" + did + "/")
        return HttpResponseRedirect('/vms/')
    except ValueError:
        logger.error("vms")
        raise Http404()


def delvm(request, did):
    global logger
    error = ''
    try:
        did = int(did)
        vm = Vm.objects.get(id=did)
    except ValueError:
        logger.error("vms")
        raise Http404()

    
    vname = vm.name
    imgid = vm.imgtype.id
    img = Img.objects.get(id=imgid)
    try:
        img.vmcount = img.vmcount - 1
        img.save()
        vm.delete()
    except Exception, e:
        ing_list = Vm.objects.get(imgtype_id=img[0].id)
        img.vmcount = len(ing_list)
        img.save()

    host_id = 1
    host = Host.objects.get(id=host_id)
    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None
    if conn:
        dom = conn.lookupVM(vname)
        try:
            if dom.info()[0] == 1:
                dom.destroy()
            dom.undefine()
            if os.path.exists(IMAGE_PATH + vname + ".img"):
                os.system('rm -rf ' + IMAGE_PATH + vname + ".img")
            elif os.path.exists(IMAGE_PATH + vname + ".qcow2"):
                os.system('rm -rf ' + IMAGE_PATH + vname + ".qcow2")
        except libvirtError as msg_error:
            errors.append(msg_error.message)
    return HttpResponseRedirect('/vms/')

def imginfo(request):
    img = ''
    if request.method == 'POST':
        imgid = request.POST['imgid']
        img = Img.objects.get(id=imgid)
        data = {}
        data["imgid"] = img.id
        data["imgname"] = img.name
        data["imgexptype"] = img.exptype
        data["imgostype"] = img.ostype.id
        data["imgvmcount"] = img.vmcount
        data["imgosversion"] = img.osversion
        data["imgfilename"] = img.filename
        data["imgram"] = img.memory
        data["imgcpu"] = img.cpu
        data["imgarc"] = img.osstruct
        data["remark"] = img.remark
    return HttpResponse(json.dumps(data))

def getfilelength(request):
    if request.method == 'POST':
        filepath= request.POST['filepath']
        try:
            length=os.path.getsize(filepath)
        except Exception, e:
            length=-1
        data = {}
        data["filepath"] = length
    return HttpResponse(json.dumps(data))

def deletefile(request):
    if request.method == 'POST':
        name=request.POST["name"]
        userid = request.session["userid"]
        uid = '%s' % userid
        curpath = STATIC_DOCUMENT + 'user/' + uid
        filename = curpath + '/' + name
        data = {}    
        try:
            os.system('rm -rf ' + filename)
            data["success"] = "true"
        except Exception, e:
            data["success"] = "false"
    return HttpResponse(json.dumps(data))

def uploadimg(request):
    # if request.method == 'POST':
    #     data = request.FILES['image_file']
    #     userid = request.session["userid"]
    #     uid = '%s' % userid
    #     handle_uploaded_file(uid, data)
    # return HttpResponse(data.name)
    if request.method == 'POST':
        data = request.FILES['data']
        name=request.POST["name"]
        userid = request.session["userid"]
        uid = '%s' % userid
        curpath = STATIC_DOCUMENT + 'user/' + uid
        filename = curpath + '/' + name
        if not os.path.isdir(curpath):
            comd = "mkdir "+curpath
            os.system(comd)
        f=open(filename, 'a+')    
        print filename
        with f as info:
            for chunk in data.chunks():
                info.write(chunk)  
        f.close()           
        # handle_uploaded_file(uid, data,name)
    return HttpResponse(data.name)    

def addimg(request):
    if request.method == 'POST':
        # print request.POST['imagefilename']

        img = Img(
            name=request.POST['img_name'], 
            exptype=request.POST['img_name'], 
            ostype_id=int(request.POST['img_ostype']), 
            memory=int(request.POST['img_ram']),
            cpu=int(request.POST['img_cpu']),
            osstruct=request.POST['img_arc'],
            osversion=request.POST['img_osversion'], 
            filename=request.POST['imagefilename'],

            vmcount=0,
            remark=request.POST['img_remark'])
        img.save()

        curpath = STATIC_DOCUMENT + 'vm/%s' % img.id
        if not os.path.exists(curpath):
            os.mkdir(curpath)
        userid = request.session["userid"]
        uid = '%s' % userid
        filename=request.POST['imagefilename']
        imgname=request.POST['img_name']
        # stringcmd='qemu-img snapshot -c  snapshot   '+filename
        sourcepath = STATIC_DOCUMENT + 'user/%s' % uid

        if filename != '':
            cmd = 'mv ' +  sourcepath + '/' + img.filename + ' ' + curpath + '/' + img.filename
            result = os.system(cmd)

        ####################################
        # time.sleep(1)
        #dom.vds_create_snapshot(imgname)
        #commend1=os.popen('cd  '+curpath+'&&'+stringcmd)
        # time.sleep(1)

        # 获取另外两台服务器的ip地址，使用scp命令，将该镜像拷贝到另外的服务器中
        # scp -r /home/lizc/Documents/vm/97/ root@172.19.8.200:/home/lizc/Documents/vm/
        ips = Host.objects.order_by('id')[2:]
        for ip in ips:
            os.system("scp -r " + curpath + "/ root@" + ip.hostname + ":" + curpath)

    request.session['tabtype'] = 'img'
    return HttpResponseRedirect('/vms/')


def post(url, data):
    req = urllib2.Request(url)
    data = urllib.urlencode(data)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    response = opener.open(req, data)
    return response.read()


def editimg(request):
    global logger
    if request.method == 'POST':
        try:
            did = int(request.POST['imgid'])
        except ValueError:
            logger.error("vms")
            raise Http404()
        data = None
        img = None
        img = Img.objects.get(id=did)
        if img != None:
            img.name = request.POST['img_name']
            # img.exptype = request.POST['typename']
            img.ostype_id = int(request.POST['imgostype'])
            img.memory=int(request.POST['imgram'])
            img.cpu=int(request.POST['imgcpu'])
            img.osstruct=request.POST['imgarc']
            img.osversion = request.POST['imgosversion']
            if request.POST['imagefilename'] != "":
                img.filename=request.POST['imagefilename']
            img.remark=request.POST['remark']
            userid = request.session["userid"]
            uid = '%s' % userid
            sourcepath = STATIC_DOCUMENT + 'user/%s' % uid
            # if request.POST['imagefilename'] != "":
            #     path = STATIC_DOCUMENT + 'vm/%s' % img.id
            #     if os.path.exists(path):
            #         os.system('rm -rf ' + path)
            #     os.mkdir(path)
            #     os.system('mv ' + sourcepath + '/' + img.filename + ' ' + path + '/' + img.filename)
            if request.POST['imagefilename'] != "":
                path = STATIC_DOCUMENT + 'vm/%s' % img.id
                # if os.path.exists(path):
                #     os.system('rm -rf ' + path)
                # 移除所有服务器上相应的img文件夹
                servers = Host.objects.order_by('id')[1:]
                for server in servers:
                    post("http://" + server.hostname + "/tools/rmPreImg/", {'path': path})
                # 在主服务器上创建新的文件夹
                os.mkdir(path)
                os.system('mv ' + sourcepath + '/' + img.filename + ' ' + path + '/' + img.filename)
                # 拷贝文件到所有的次服务器上
                for server in servers[1:]:
                    os.system("scp -r " + path + "/ root@" + server.hostname + ":" + path)
            img.save()
    request.session['tabtype'] = 'img'
    return HttpResponseRedirect('/vms/')


# 移除之前的镜像
def rmPreImg(request):
    path = request.POST['path']
    if os.path.exists(path):
        os.system('rm -rf ' + path)
    return HttpResponse('ok')


def delimgall(request, did):
    ips = Host.objects.order_by('id')[1:]
    for ip in ips:
        urllib.urlopen("http://" + ip.hostname + "/imgdelall/" + did + "/")
    # 所有镜像删除完毕后，再从数据库中清除记录
    img = Img.objects.get(id=did)
    img.delete()
    return HttpResponseRedirect('/vms/')


def delimg(request, did):
    global logger
    error = ''
    try:
        did = int(did)
        img = Img.objects.get(id=did)
        host_id = 1
        host = Host.objects.get(id=host_id)
    except ValueError:
        logger.error("vms")
        raise Http404()   
    try:
        os.system('rm -rf ' + STATIC_DOCUMENT + 'vm/%s' % img.id)
    except:
        pass
    #删除镜像的所有虚拟机的文件
    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None
    vms = img.vm_set.all().filter(containerIP=request.get_host())
    if vms and conn:
        for vm in vms:
            vname=vm.name
            dom = conn.lookupVM(vname)
            try:
                if dom.info()[0] == 1:
                    dom.destroy()
                dom.undefine()
                if os.path.exists(IMAGE_PATH + vname + ".img"):
                    os.system('rm -rf ' + IMAGE_PATH + vname + ".img")
                elif os.path.exists(IMAGE_PATH + vname + ".qcow2"):
                    os.system('rm -rf ' + IMAGE_PATH + vname + ".qcow2")
            except libvirtError as msg_error:
                errors.append(msg_error.message)
    # img.delete()
    request.session['tabtype'] = 'img'
    return HttpResponseRedirect('/vms/')
            
def handle_uploaded_file(uid, f):
    curpath = STATIC_DOCUMENT + 'user/' + uid
    if os.path.exists(curpath):
        os.system('rm -rf ' + curpath)
    os.mkdir(curpath)
    filename = curpath + '/' + f.name
    with open(filename, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def cpuusage(request, vname):
    """
    VM Cpu Usage
    """
    #if not request.user.is_authenticated():
        #return HttpResponseRedirect('/login')
    host_id = 1
    host = Host.objects.get(id=host_id)
    try:
        conn = ConnServer(host)
    except:
        conn = None
    if conn:
        cpu_usage = conn.vds_cpu_usage(vname)
    return HttpResponse(cpu_usage)

def memusage(request, vname):
    """
    VM Memory Usage
    """
    #if not request.user.is_authenticated():
      #  return HttpResponseRedirect('/login')
    host_id = 1
    host = Host.objects.get(id=host_id)
    try:
        conn = ConnServer(host)
    except:
        conn = None
    if conn:
        memory_usage = conn.vds_memory_usage(vname)[1] 
    return HttpResponse(memory_usage)

def sort_host(hosts):
    """

    Sorts dictionary of hosts by key

    """
    if hosts:
        sorted_hosts = []
        for host in sorted(hosts.iterkeys()):
            sorted_hosts.append((host, hosts[host]))
        return SortedDict(sorted_hosts)


def selectServerVMStart(rquest, vid):
    vm = Vm.objects.get(id=int(vid))
    re = urllib.urlopen("http://" + vm.containerIP + "/vmstart/" + vid + "/")
    return HttpResponse(re)


def vmstart(request, vid):
    host_id = 1
    vid = int(vid)
    vm = Vm.objects.get(id=vid) 
    vname = vm.name 
    #snapshotstart="qemu-img snapshot -a snapshot  "+vname+'.img'
    #commend1=os.popen('cd  /home/lizc/lizcDisk && '+snapshotstart)
    #print commend1
    #time.sleep(15)
    errors = []
    messages = []
    host = Host.objects.get(id=host_id)
    result = 1
    data={}
    try:
        conn = ConnServer(host)
    except libvirtError as e:
        logger.exception('connect libvirt error')
        conn = None
        result = 0
        data["result"] = result
        return HttpResponse(json.dumps(data))
    if not conn:
        errors.append(e.message)
    else:
        dom = conn.lookupVM(vname)
        if dom is None:
            logger.error('%s does not exist in libvirt' % (vname))
            data["result"] = 0
            return HttpResponse(json.dumps(data))

        try:
            dom.create()
            vm.state = 1
            vm.save()
        except libvirtError as msg_error:
            logger.exception('start %s failed' % (vname))
            errors.append(msg_error.message)
            result = 0
            data["result"] = result
            return HttpResponse(json.dumps(data))
        data["result"] = result
        return HttpResponse(json.dumps(data))




def vmsuspend(request, vid):
    host_id = 1
    vid = int(vid)
    vm = Vm.objects.get(id=vid) 
    vname = vm.name 
    errors = []
    messages = []
    host = Host.objects.get(id=host_id)
    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None
    if not conn:
        errors.append(e.message)
    else:
        dom = conn.lookupVM(vname)
        try:
            dom.suspend()
            vm.state = 1
            vm.save()
        except libvirtError as msg_error:
            errors.append(msg_error.message)
    return HttpResponseRedirect('/vms/')

def vmresume(request, vid):
    host_id = 1
    vid = int(vid)
    vm = Vm.objects.get(id=vid) 
    vname = vm.name 
    errors = []
    messages = []
    host = Host.objects.get(id=host_id)
    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None
    if not conn:
        errors.append(e.message)
    else:
        dom = conn.lookupVM(vname)
        try:
            dom.resume()
            vm.state = 1
            vm.save()
        except libvirtError as msg_error:
            errors.append(msg_error.message)
    return HttpResponseRedirect('/vms/')


def selectServerVMStop(request, vid):
    vm = Vm.objects.get(id=int(vid))
    re = urllib.urlopen("http://" + vm.containerIP + "/vmstop/" + vid + "/")
    return HttpResponse(re)


def vmstop(request, vid):
    host_id = 1
    vid = int(vid)
    vm = Vm.objects.get(id=vid) 
    vname = vm.name 
    errors = []
    messages = []
    result = 1
    data={}
    host = Host.objects.get(id=host_id)
    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None
        result = 0
        data["result"] = result
        return HttpResponse(json.dumps(data))
    if not conn:
        errors.append(e.message)
    else:
        dom = conn.lookupVM(vname)
        try:
            if dom.info()[0] == 5:#关机
                pass
            elif dom.info()[0] == 1:
                dom.destroy()
            vm.state = 0
            vm.save()
        except libvirtError as msg_error:
            errors.append(msg_error.message)
            result = 0
            data["result"] = result
            return HttpResponse(json.dumps(data))
        data["result"] = result
        return HttpResponse(json.dumps(data))


# 获取虚拟机所在服务器ip，将请求转发给相应的服务器
def getInstanceInfo(request, vid):
    try:
        vm = Vm.objects.get(id=int(vid))
        re = urllib.urlopen("http://" + vm.containerIP + "/vmdetail/" + vid)
        return HttpResponse(re)
    except Exception, e:
        return HttpResponseRedirect('/vms/')


def instance(request, vid):
    """
    VDS block
    """
    #if not request.user.is_authenticated():
      #  return HttpResponseRedirect('/login')  
    tabpage = request.GET.get('page', 1)

    host_id = 1
    vid = int(vid)
    try:
        vm = Vm.objects.get(id=vid)   
    except Exception, e:
        return HttpResponseRedirect('/vms/')
    vname = vm.name 
    errors = []
    time_refresh = TIME_JS_REFRESH
    messages = []
    try:
        host = Host.objects.get(id=host_id)
    except Exception, e:
        return HttpResponseRedirect('/vms/')
    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None
    if not conn:
        errors.append(e.message)
    else:
        #all_vm = sort_host(conn.vds_get_node())
        # vcpu, memory, networks, description = conn.vds_get_info(vname)
        try:
            vcpu, memory,  description = conn.vds_get_info(vname)

            cpu_usage = conn.vds_cpu_usage(vname)
            memory_usage = conn.vds_memory_usage(vname)[1]

            hdd_image = conn.vds_get_hdd(vname)

            #iso_images = sorted(conn.get_all_media()) ??????????????????
            media, media_path = conn.vds_get_media(vname)

            dom = conn.lookupVM(vname)
            vcpu_range = [str(x) for x in range(1, 9)]
            memory_range = [128, 256, 512, 768, 1024, 2048, 4096, 8192, 16384]
            vnc_port = conn.vnc_get_port(vname)   
        except Exception, e:
            vm.delete()
            return HttpResponseRedirect('/vms/')
        try:
            instance = Instance.objects.get(vname=vname)
        except:
            instance = None

        if request.method == 'POST':
            if 'start' in request.POST:
                try:
                    dom.create()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'power' in request.POST:
                if 'shutdown' == request.POST.get('power', ''):
                    try:
                        dom.shutdown()
                        return HttpResponseRedirect(request.get_full_path())
                    except libvirtError as msg_error:
                        errors.append(msg_error.message)
                if 'destroy' == request.POST.get('power', ''):
                    try:
                        dom.destroy()
                        return HttpResponseRedirect(request.get_full_path())
                    except libvirtError as msg_error:
                        errors.append(msg_error.message)
            if 'suspend' in request.POST:
                try:
                    dom.suspend()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'resume' in request.POST:
                try:
                    dom.resume()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'delete' in request.POST:
                try:
                    if dom.info()[0] == 1:
                        dom.destroy()
                    if request.POST.get('image', ''):
                        conn.vds_remove_hdd(vname)
                    try:
                        instance = Instance.objects.get(host=host_id, vname=vname)
                        instance.delete()
                    except:
                        pass
                    dom.undefine()
                    return HttpResponseRedirect('/overview/%s/' % host_id)
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'snapshot' in request.POST:
                try:
                    conn.vds_create_snapshot(vname)
                    msg = _("Create snapshot for instance successful")
                    messages.append(msg)
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'remove_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                try:
                    conn.vds_umount_iso(vname, image)
                    if instance:
                        conn.vds_set_vnc_passwd(vname, instance.vnc_passwd)
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'add_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                try:
                    conn.vds_mount_iso(vname, image)
                    if instance:
                        conn.vds_set_vnc_passwd(vname, instance.vnc_passwd)
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'edit' in request.POST:
                description = request.POST.get('description', '')
                vcpu = request.POST.get('vcpu', '')
                ram = request.POST.get('ram', '')
                try:
                    conn.vds_edit(vname, description, ram, vcpu)
                    if instance:
                        conn.vds_set_vnc_passwd(vname, instance.vnc_passwd)
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'xml_edit' in request.POST:
                xml = request.POST.get('vm_xml', '')
                try:
                    if xml:
                        conn.defineXML(xml)
                        if instance:
                            conn.vds_set_vnc_passwd(vname, instance.vnc_passwd)
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'vnc_pass' in request.POST:
                if request.POST.get('auto_pass', ''):
                    from string import letters, digits
                    from random import choice
                    passwd = ''.join([choice(letters + digits) for i in range(12)])
                else:
                    passwd = request.POST.get('vnc_passwd', '')
                    if not passwd:
                        msg = _("Enter the VNC password or select Generate")
                        errors.append(msg)
                if not errors:
                    try:
                        conn.vds_set_vnc_passwd(vname, passwd)
                        vnc_pass = Instance(host_id=host_id, vname=vname, vnc_passwd=passwd)
                        vnc_pass.save()
                    except libvirtError as msg_error:
                        errors.append(msg_error.message)
                    return HttpResponseRedirect(request.get_full_path())
        conn.close()
    redirecturl = "/vms/"
    try:
        re = Vm.objects.get(name=vname).remark
    except Exception, e:
        re=''

    # 获取虚拟机的使用情况
    records = VmsUseRecord.objects.filter(vmtype="imgls", vmid=vid)
    use_count = 0
    use_details = []
    for record in records:
        use_count += 1
        detail = {
            "deptname": record.deptname,
            "grade": record.grade,
            "claname": record.claname,
            "stuname": record.stuname,
            "expname": record.expname,
            "starttime": record.starttime.strftime('%Y-%m-%d %H:%M:%S')
        }
        use_details.append(detail)

    return render_to_response('templates/instance.html', {'host_id': host_id,
                                                'vname': vname,
                                                'messages': messages,
                                                'errors': errors,
                                                'instance': instance,
                                                #'all_vm': all_vm,
                                                'vcpu': vcpu, 'cpu_usage': cpu_usage, 'vcpu_range': vcpu_range,
                                                'description': re,
                                                # 'networks': networks,
                                                'memory': memory, 'memory_usage': memory_usage, 'memory_range': memory_range,
                                                'hdd_image': hdd_image, #'iso_images': iso_images,
                                                'media': media, 'path': media_path,
                                                'dom': dom,
                                                #'vm_xml': dom.XMLDesc(VIR_DOMAIN_XML_SECURE),
                                                'page':tabpage,
                                                'vnc_port': vnc_port,
                                                'time_refresh': time_refresh,
                                                'redirecturl':redirecturl,
                                                'use_count': use_count,
                                                'use_details': use_details
                                                },
                              context_instance=RequestContext(request))

def console(request, vid, vtype):
    """

    VNC vm's block

    """
    #if not request.user.is_authenticated():
      #  return HttpResponseRedirect('/login')
    errors = []
    vnc_port = socket_host = socket_port = None
    host_id = 1
    host = Host.objects.get(id=host_id)
    vid = int(vid)
    vm = None
    if vtype == "vm":
        vm = Vm.objects.get(id=vid)
    if vtype == "vgt":
        vm = Vgate.objects.get(id=vid)
    if vtype == "vsh":
        vm = Vswitch.objects.get(id=vid)
    vname = vm.name
    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None

    if not conn:
        errors.append(e.message)
    else:
        vnc_port = conn.vnc_get_port(vname)
        try:
            #instance = Instance.objects.get(host=host_id, vname=vname)
            socket_port = 6080
            socket_host = request.get_host()
            print socket_host
            if ':' in socket_host:
                socket_host = re.sub(':[0-9]+', '', socket_host)
        except:
            #instance = None
            pass
        vnc_passwd = '123456'
        conn.close()

    response = render_to_response('templates/console.html', {'vnc_port': vnc_port,
                                                   'socket_port': socket_port,
                                                   'socket_host': socket_host,
                                                   'vnc_passwd': vnc_passwd,
                                                   'vnc_name': vname,
                                                   'errors': errors
                                                   },
                                  context_instance=RequestContext(request))
   
    response.set_cookie('token', vname)
    return response


def selectServer(request):
    # 获取host表中服务器的虚拟机个数，选择指定类型的虚拟机个数最少的服务器
    servers = Host.objects.order_by('id')[1:]
    counts = []
    for server in servers:
        counts.append(len(Vm.objects.filter(containerIP=server.hostname, imgtype_id=int(request.POST['vm_type']))))
    # 虚拟机个数最少的服务器id，在虚拟机个数相同时，优先选择id最大的服务器
    counts.reverse()
    serverid = len(servers) - counts.index(min(counts)) + 1
    ip = Host.objects.get(id=serverid).hostname
    # 将创建请求发送给相应的服务器
    datas = {
        'vm_name': request.POST['vm_name'],
        'vm_mgrip': request.POST['vm_mgrip'],
        'vm_type': int(request.POST['vm_type']),
        'vm_ram': int(request.POST["vm_ram"]),
        'vm_cpu': int(request.POST["vm_cpu"]),
        'vm_mgrport': request.POST['vm_mgrport'],
        'vm_remark': request.POST['vm_remark'],
        'containerIP': ip
    }
    logger.info('start to create vm %s on server %s' % (request.POST['vm_name'], ip))
    data = post("http://" + ip + "/createvm/", datas)
    logger.info('create vm end. result=' + str(data))
    return HttpResponse(data)


def createvm(request):
    """
    Page add new VM.
    """
    host_id = 1
    errors = []
    data={}
    form = None
    host = Host.objects.get(id=host_id)
    data1={}
    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None

    if not conn:
        errors.append(e.message)
    else:
        all_vm = sort_host(conn.vds_get_node())
        if request.method == 'POST':
            # if 'instance_add' in request.POST:
            img = Img.objects.get(id=request.POST["vm_type"])
            data['name'] = request.POST["vm_name"]
            data['ram'] = int(request.POST["vm_ram"])
            data['vcpu'] = int(request.POST["vm_cpu"])
            data['arc'] = img.osstruct
            data['image'] = img.filename
            data['ostype'] = img.ostype.typename
            data['image'] = STATIC_DOCUMENT + 'vm/%s/' %img.id + img.filename
            vm = Vm(
                name=request.POST['vm_name'],
                mgrip=request.POST['vm_mgrip'],
                imgtype_id=int(request.POST['vm_type']),
                memory=int(request.POST['vm_ram']),
                cpu=int(request.POST['vm_cpu']),
                osstruct=img.osstruct,
                mgrport=request.POST['vm_mgrport'],
                state=0,
                remark=request.POST['vm_remark'],
                containerIP=request.POST['containerIP'])
            # vm.save()
            try:
                conn.add_vm(data['name'], data['ram'], data['vcpu'], data['image'], data['arc'],'vm')
                vm.save()
                img.vmcount = img.vmcount + 1
                img.save()
            except libvirtError as msg_error:
                errors.append(msg_error.message)
                data1["result"] = 0
                vm.delete()

                ing_list = Vm.objects.get(imgtype_id=img.id)
                img.vmcount = len(ing_list)
                img.save()

                return HttpResponse(json.dumps(data1))
        conn.close()
    try:
        conn = ConnServer(host)
        if conn:
            conn.vds_set_vnc_passwd(data['name'], '123456')
            #conn.vds_create_snapshot(data['image'])
    except libvirtError as e:
        conn = None
        data1["result"] = 0
        vm.delete()
        ing_list = Vm.objects.get(imgtype_id=img[0].id)
        img.vmcount = len(ing_list)
        img.save()  
        return HttpResponse(json.dumps(data1))
    conn.close()
    data1["result"] = 1
    return HttpResponse(json.dumps(data1))
    # return HttpResponseRedirect('/vms/')

def sort_host(hosts):
    """
    Sorts dictionary of hosts by key
    """
    if hosts:
        sorted_hosts = []
        for host in sorted(hosts.iterkeys()):
            sorted_hosts.append((host, hosts[host]))
        return SortedDict(sorted_hosts)

def vmnamecheck(request):
    global logger
    judgevmimg=0
    if request.method == 'POST':
        try:
            vmimgname = request.POST['img_name']
        except ValueError:
            logger.error("vms")
            raise Http404()       
        vmimg= Img.objects.order_by('id')
        for vimg in vmimg:
            if vimg.name == vmimgname:
                judgevmimg=1
                break
    data = {}
    data['judgename']=judgevmimg
    return HttpResponse(json.dumps(data))

def vgavmnamecheckt(request):
    global logger
    judgevgatevmimg=0
    if request.method == 'POST':
        try:
            vgateimgname = request.POST['vm_name']
        except ValueError:
            logger.error("vms")
            raise Http404()               
        vgateimg=Vgate.objects.order_by('id')
        for vimg in vgateimg:
            if vimg.name == vgateimgname:
                judgevgatevmimg=1
                break
        vmimg= Vm.objects.order_by('id')
        for v in vmimg:
            if v.name == vgateimgname:
                judgevgatevmimg=1
                break
    data = {}
    data['judgename']=judgevgatevmimg
    return HttpResponse(json.dumps(data))

def vmipnamecheck(request):
    global logger
    judgevgatevmimg=0
    if request.method == 'POST':
        try:
            ipname = request.POST['vm_mgrip']
        except ValueError:
            logger.error("vms")
            raise Http404()        
        vgateimg=Vgate.objects.order_by('id')
        for vimg in vgateimg:
            if vimg.mgrip == ipname:
                judgevgatevmimg=1
                break
        vmimg= Vm.objects.order_by('id')
        for v in vmimg:
            if v.mgrip == ipname:
                judgevgatevmimg=1
                break
    data = {}
    data['judgename']=judgevgatevmimg
    return HttpResponse(json.dumps(data))

def vmipnamecheckedit(request):
    global logger
    judgevgatevmimg=0
    if request.method == 'POST':
        try:
            ipname = request.POST['vmmgrip']
        except ValueError:
            logger.error("vms")
            raise Http404()               
        vgateimg=Vgate.objects.order_by('id')
        for vimg in vgateimg:
            if vimg.mgrip == ipname:
                judgevgatevmimg=1
                break
        vmimg= Vm.objects.order_by('id')
        for v in vmimg:
            if v.mgrip == ipname:
                judgevgatevmimg=1
                break
    data = {}
    data['judgename']=judgevgatevmimg
    return HttpResponse(json.dumps(data))
