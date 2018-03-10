#-*- coding: utf-8 -*- 

'''
1. 显示虚拟安全设备界面：调用mgrvgates方法；
2. 添加虚拟安全设备类型：调用addimgvgt方法，在数据库中加入数据，并将上传的虚拟机镜像同步到所有服务器上
的相同目录下；
3. 修改虚拟安全设备类型：调用editimgvgt方法，修改数据库中的数据，如果上传了新的设备镜像，则调用所有服务
器上的rmPreImgVgt方法，删除原始镜像，并将新上传的镜像同步到原来的目录下；
4. 删除虚拟安全设备类型：调用delimgvgtall方法，先调用delimgvgt方法，将所有服务器上的原始镜像删除，然后
删除数据库中的数据；
5. 创建虚拟安全设备：调用selectServer方法，获取最适合创建新虚拟机的服务器，调用该服务器上的createvm方法，
向数据库中添加新的数据，并根据选择的虚拟安全设备类型，以及提供的虚拟机参数，创建一个完全相同的虚拟机；
6. 虚拟安全设备详情：调用getInstanceInfo方法，得到该虚拟机所在服务器ip，调用该服务器上的instance方法，
获取并返回虚拟机信息；
7. 启动虚拟安全设备：调用selectServerVgtStart方法，获取该虚拟机所在服务器ip，调用该服务器上的vmstart方法，
启动该虚拟机；
8. 虚拟机控制台：调用client模块下views.py文件中的getServerIp方法，返回虚拟机所在服务器ip，并构建控制台
链接；
9. 关闭虚拟安全设备：调用selectServerVgtStop方法，获取虚拟机所在服务器ip，调用该服务器上的vgtstop方法，
关闭该虚拟机；
10. 编辑虚拟安全设备：调用selectServerEditVgt方法，获取虚拟机所在服务器ip，调用该服务器上的editvgt方法，
修改数据库与虚拟机配置文件；
11. 删除虚拟安全设备：调用selectServerDelVgt方法，获取虚拟机所在服务器ip，调用该服务器上的delvgt方法，
删除数据库中的数据与镜像文件。
'''

from django.shortcuts import render_to_response
from vgates.models import *
from libvirt import libvirtError
from sysmgr.models import *
from tsssite.server import ConnServer
from tsssite.settings import TIME_JS_REFRESH, STATIC_DOCUMENT, IMAGE_PATH
from myexp.models import *
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseServerError
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
import json, time, datetime, os
from vms.models import Img, Vm
from django.utils.datastructures import SortedDict
from django.db.models import Q
import logging
logger = logging.getLogger('mysite.log')
vgatels_pages = 1
imgvgtls_pages = 1
import urllib
import urllib2
from client.models import *

def mgrvgates(request):
        if not 'username' in request.session:
                return HttpResponseRedirect('/Login/')
        username = request.session['username']
        imgvgtls = ImgVgt.objects.order_by('-id')
        vgatels = Vgate.objects.order_by('name')
        dictype = DicType.objects.get(enumtype='vgatetype')
        vgatetypels= DicContent.objects.order_by('id').filter(enumid_id=dictype.id)
        querytext = ''
        queryimg = ''
        if 'querytext' in request.GET and request.GET['querytext']:
            querytext = request.GET['querytext']
        if 'queryimg' in request.GET and request.GET['queryimg']:
            queryimg = request.GET['queryimg']
        # tabtype = 'vm'

        types="vgatels"
        try:
            m_type = request.GET.get("type")
            if m_type == "img":
                types='img'
        except ValueError:
            types="vgatels" 
                   
        # if 'btnqueryimg' in request.GET:
        #     request.session['tabtype'] = 'img'
        goon=0
        for imgvgtl in imgvgtls:
            if querytext == imgvgtl.name:
                num=imgvgtl.id
                vgatels=vgatels.filter(Q(name__icontains=querytext)|Q(imgtype_id=num))
                goon=1
                break
        if goon==0:
            vgatels=vgatels.filter(Q(name__icontains=querytext))
        imgvgtls=imgvgtls.filter(Q(name__icontains=queryimg)|Q(xh__icontains=queryimg))

        try:
            page = int(request.GET.get("page",1))
            if page < 1:
                page = 1
        except ValueError:
            page = 1

        if(types == "img"):
            global imgvgtls_pages
            imgvgtls_pages=page
        else:
            global vgatels_pages
            vgatels_pages = page

  
        paginator_vgatels = Paginator(vgatels,10)
        try:
            vgatels = paginator_vgatels.page(vgatels_pages)
        except(EmptyPage,InvalidPage,PageNotAnInteger):
            vgatels = paginator_vgatels.page(paginator_vgatels.num_pages)

        # 记录总页数    
        page_long = len(paginator_vgatels.page_range)
        if page_long<=5:
            page_range = paginator_vgatels.page_range[0:page_long]    
        else:
            if vgatels_pages<=3:
                page_range = paginator_vgatels.page_range[0:5]
            else:
                if (page_long-vgatels_pages) >= 2:   
                    page_range = paginator_vgatels.page_range[vgatels_pages-3:vgatels_pages+2]
                else:
                    page_range = paginator_vgatels.page_range[page_long-5:page_long]  

        page_range_vgatels=page_range

        paginator_imgvgtls = Paginator(imgvgtls,10)
        try:
            imgvgtls = paginator_imgvgtls.page(imgvgtls_pages)
        except(EmptyPage,InvalidPage,PageNotAnInteger):
            imgvgtls = paginator_imgvgtls.page(paginator_imgvgtls.num_pages)

         # 记录总页数    
        page_long = len(paginator_imgvgtls.page_range)
        if page_long<=5:
            page_range = paginator_imgvgtls.page_range[0:page_long]    
        else:
            if vgatels_pages<=3:
                page_range = paginator_imgvgtls.page_range[0:5]
            else:
                if (page_long-vgatels_pages) >= 2:   
                    page_range = paginator_imgvgtls.page_range[vgatels_pages-3:vgatels_pages+2]
                else:
                    page_range = paginator_imgvgtls.page_range[page_long-5:page_long] 
   
        page_range_imgvgtls=page_range
        return render_to_response('templates/vGate.html',{'querytext':querytext,'queryimg':queryimg,'type':types,'vgatels': vgatels, 'vgatetypels': vgatetypels, 'imgvgtls': imgvgtls, 'username':username,'page_range_vgatels':page_range_vgatels,'page_range_imgvgtls':page_range_imgvgtls,'page':page}, context_instance=RequestContext(request))

def vgtinfo(request):
    vm = ''
    if request.method == 'POST':
        vgtid = request.POST['vgtid']
        vgt = Vgate.objects.get(id=vgtid)
        data = {}
        data["vgtid"] = vgt.id
        data["vgtname"] = vgt.name
        data["vgttype"] = vgt.imgtype.id
        data["vgtmgrip"] = vgt.mgrip
        data["vgtmgrport"] = vgt.mgrport
        data["vgtram"] = vgt.memory
        data["vgtcpu"] = vgt.cpu   
        data["remark"] = vgt.remark
    return HttpResponse(json.dumps(data))


def selectServerEditVgt(request):
    try:
        did = int(request.POST['vgtid'])
        vgt = Vgate.objects.get(id=did)
        datas = {
            'vgtid': request.POST['vgtid'],
            'vgt_name': request.POST['vgt_name'],
            'vgtmgrip': request.POST['vgtmgrip'],
            'vgtremark': request.POST['vgtremark'],
            'vgtmgrport': request.POST['vgtmgrport'],
            'vgtram': int(request.POST['vgtram']),
            'vgtcpu': int(request.POST['vgtcpu'])
        }
        re = post("http://" + vgt.containerIP + "/vgtedit/", datas)
        return HttpResponse(re)
    except ValueError:
        logger.error("vms")
        raise Http404()


def editvgt(request):
    global logger
    try:
        did = int(request.POST['vgtid'])
        vgt = Vgate.objects.get(id=did)

    except ValueError:
        logger.error("vgates")
        raise Http404()                 
    if request.method == 'POST':
        vgt.name = request.POST['vgt_name']
        vgt.mgrip = request.POST['vgtmgrip']
        vgt.remark = request.POST['vgtremark']
        vgt.mgrport = request.POST['vgtmgrport']
       # vgt.imgtype_id = int(request.POST['vgttype'])
        vgt.memory = int(request.POST['vgtram'])
        vgt.cpu = int(request.POST['vgtcpu'])
    vgt.save()
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
            conn.vds_edit(vgt.name, 'None', vgt.memory, vgt.cpu) 
        except libvirtError as msg_error:
            errors.append(msg_error.message)
            result = 0
            data["result"] = result
            return HttpResponse(json.dumps(data))
        conn.close()
    # return HttpResponseRedirect('/vgates/')
    data["result"] = result
    return HttpResponse(json.dumps(data))

def getVgateStatus(request):
    try:
        did = int(request.POST['id'])
        vgates = ImgVgt.objects.get(id=did).vgate_set.all()
        flag = 0
        for vgate in vgates:
            if vgate.state == 1:
                flag = 1
                break
        return HttpResponse(json.dumps(flag))
    except Exception:
        logger.exception("get vgate error")
        raise Http404

def selectServerDelVgt(rquest, did):
    try:
        vm = Vgate.objects.get(id=int(did))
        urllib.urlopen("http://" + vm.containerIP + "/tools/vgtdelonserver/" + did + "/")
        return HttpResponseRedirect('/vgates/')
    except ValueError:
        logger.error("vgates")
        raise Http404()


def delvgt(request, did):
    global logger
    error = ''
    try:
        did = int(did)
        vm = Vgate.objects.get(id=did)
    except ValueError:
        logger.error("vgates")
        raise Http404()
    
    vname = vm.name
    imgid = vm.imgtype.id
    img = ImgVgt.objects.get(id=imgid)
    try:
        img.vgtcount = img.vgtcount - 1
        img.save()
        vm.delete()
    except Exception, e:
        m_vgates=Vgate.objects.get(imgtype_id=img.id)
        img.vgtcount = len(m_vgates)
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
    return HttpResponseRedirect('/vgates/')

def imgvgtinfo(request):
    img = ''
    if request.method == 'POST':
        imgid = request.POST['imgid']
        img = ImgVgt.objects.get(id=imgid)
        data = {}
        data["imgid"] = img.id
        data["imgname"] = img.name
        data["imgxh"] = img.xh
        data["imgvgttype"] = img.vgttype_id
        data["imgvalidate"] = img.validate.strftime('%Y-%m-%d')
        data["imgversion"] = img.version
        data["imgfilename"] = img.filename
        data["imgram"] = img.memory
        data["imgcpu"] = img.cpu
        data["imgarc"] = img.osstruct
        data["remark"] = img.remark
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
        print(filename)
        # with open(filename, 'a+') as info:
        #     for chunk in data.chunks():
        #         info.write(chunk)
        # handle_uploaded_file(uid, data,name)
    return HttpResponse(data.name)        

def addimgvgt(request):
    if request.method == 'POST':
        strvdate = request.POST['img_validate']
        strvdate = time.strptime(strvdate,'%Y-%m-%d')
        y, m, d = strvdate[0:3]
        name=request.POST['img_name']
        xh = request.POST['img_xh']
        vgttype_id = int(request.POST['img_vgttype'])
        img = ImgVgt(
            name=request.POST['img_name'], 
            xh = request.POST['img_xh'],
            vgttype_id = int(request.POST['img_vgttype']), 
            memory=int(request.POST['img_ram']),
            cpu=int(request.POST['img_cpu']),
            osstruct=request.POST['img_arc'],
            validate = datetime.datetime(y, m, d),
            version=request.POST['img_version'], 
            filename=request.POST['imagefilename'],
            license = 0,
            vgtcount=0,
            remark=request.POST['img_remark'])
        img.save()

        curpath = STATIC_DOCUMENT + 'vgt/%s' % img.id
        if not os.path.exists(curpath):
            os.mkdir(curpath)
        userid = request.session["userid"]
        uid = '%s' % userid
        sourcepath = STATIC_DOCUMENT + 'user/%s' % uid

        if request.POST['imagefilename'] != '':
            os.system('mv ' +  sourcepath + '/' + img.filename + ' ' + curpath + '/' + img.filename)

        ips = Host.objects.order_by('id')[2:]
        for ip in ips:
            os.system("scp -r " + curpath + "/ root@" + ip.hostname + ":" + curpath)

    request.session['tabtype'] = 'img'
    return HttpResponseRedirect('/vgates/')

def editimgvgt(request):
    global logger
    if request.method == 'POST':
        try:
            did = int(request.POST['imgid'])
        except ValueError:
            logger.error("vgates")
            raise Http404()

        data = None
        img = None
        img = ImgVgt.objects.get(id=did)
        strvdate = request.POST['imgvalidate']
        strvdate = time.strptime(strvdate,'%Y-%m-%d')
        y, m, d = strvdate[0:3]
        if img != None:
            img.name = request.POST['img_name']
            img.xh = request.POST['imgxh']
            img.vgttype_id = int(request.POST['imgvgttype'])
            img.memory=int(request.POST['imgram'])
            img.cpu=int(request.POST['imgcpu'])
            img.osstruct=request.POST['imgarc']
            img.validate = datetime.datetime(y, m, d)
            img.version = request.POST['imgversion']
            if request.POST['imagefilename'] != "":
                img.filename=request.POST['imagefilename']
            img.remark=request.POST['imgremark']
            userid = request.session["userid"]
            uid = '%s' % userid
            sourcepath = STATIC_DOCUMENT + 'user/%s' % uid
            # if request.POST['imagefilename'] != "":
            #     path = STATIC_DOCUMENT + 'vgt/%s' % img.id
            #     if os.path.exists(path):
            #         os.system('rm -rf ' + path)
            #     os.mkdir(path)
            #     os.system('mv ' + sourcepath + '/' + img.filename + ' ' + path + '/' + img.filename)
            if request.POST['imagefilename'] != "":
                path = STATIC_DOCUMENT + 'vgt/%s' % img.id
                # if os.path.exists(path):
                #     os.system('rm -rf ' + path)
                # 移除所有服务器上相应的img文件夹
                servers = Host.objects.order_by('id')[1:]
                for server in servers:
                    post("http://" + server.hostname + "/tools/rmPreImgVgt/", {'path': path})
                # 在主服务器上创建新的文件夹
                os.mkdir(path)
                os.system('mv ' + sourcepath + '/' + img.filename + ' ' + path + '/' + img.filename)
                # 拷贝文件到所有的次服务器上
                for server in servers[1:]:
                    os.system("scp -r " + path + "/ root@" + server.hostname + ":" + path)
            img.save()
    request.session['tabtype'] = 'img'
    return HttpResponseRedirect('/vgates/')


def post(url, data):
    req = urllib2.Request(url)
    data = urllib.urlencode(data)
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    response = opener.open(req, data)
    return response.read()


#移除之前的镜像
def rmPreImgVgt(request):
    path = request.POST['path']
    if os.path.exists(path):
        os.system('rm -rf ' + path)
    return HttpResponse('ok')


def delimgvgtall(request, did):
    ips=Host.objects.order_by('id')[1:]
    for ip in ips:
        urllib.urlopen("http://"+ip.hostname+"/imgvgtdelall/"+did+"/")
    #所有镜像删除完毕后，再从数据库中清除记录
    img = ImgVgt.objects.get(id=did)
    img.delete()
    return HttpResponseRedirect('/vgates/')


def delimgvgt(request, did):
    global logger
    error = ''
    try:
        did = int(did)
    except ValueError:
        logger.error("vgates")
        raise Http404()
    host_id = 1
    host = Host.objects.get(id=host_id)
    img = ImgVgt.objects.get(id=did)
    try:#删除镜像的虚拟机
        os.system('rm -rf ' + STATIC_DOCUMENT + 'vgt/%s' % img.id)
    except:
        pass
    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None
    #删除镜像的所有虚拟机的文件
    vgates = img.vgate_set.all().filter(containerIP=request.get_host())
    if vgates and conn:
        for vg in vgates:
            vname=vg.name
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
    return HttpResponseRedirect('/vgates/')

def handle_uploaded_file(uid, f):
    curpath = STATIC_DOCUMENT + 'user/' + uid
    if os.path.exists(curpath):
        os.system('rm -rf ' + curpath)
    os.mkdir(curpath)
    filename = curpath + '/' + f.name
    with open(filename, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def sort_host(hosts):
    """

    Sorts dictionary of hosts by key

    """
    if hosts:
        sorted_hosts = []
        for host in sorted(hosts.iterkeys()):
            sorted_hosts.append((host, hosts[host]))
        return SortedDict(sorted_hosts)


def selectServerVgtStart(rquest, vid):
    vm = Vgate.objects.get(id=int(vid))
    re = urllib.urlopen("http://" + vm.containerIP + "/vgtstart/" + vid + "/")
    return HttpResponse(re)


def vmstart(request, vid):
    host_id = 1
    vid = int(vid)
    vm = Vgate.objects.get(id=vid) 
    vname = vm.name 
    errors = []
    result = 1
    data={}
    messages = []
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
            dom.create()
            vm.state = 1
            vm.save()
        except libvirtError as msg_error:
            errors.append(msg_error.message)
            result = 0
            data["result"] = result
            return HttpResponse(json.dumps(data))
    data["result"] = result
    return HttpResponse(json.dumps(data))


def selectServerVgtStop(request, vid):
    vm = Vgate.objects.get(id=int(vid))
    re = urllib.urlopen("http://" + vm.containerIP + "/vgtstop/" + vid + "/")
    return HttpResponse(re)


def vmstop(request, vid):
    host_id = 1
    vid = int(vid)
    vm = Vgate.objects.get(id=vid) 
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
    # return HttpResponseRedirect('/vgates/')


# 获取虚拟机所在服务器ip，将请求转发给相应的服务器
def getInstanceInfo(request, vid):
    try:
        vm = Vgate.objects.get(id=int(vid))
        re = urllib.urlopen("http://" + vm.containerIP + "/vgtdetail/" + vid)
        return HttpResponse(re)
    except Exception, e:
        return HttpResponseRedirect('/vgates/')


def instance(request, vid):
    """
    VDS block
    """
    #if not request.user.is_authenticated():
      #  return HttpResponseRedirect('/login')
    tabpage = request.GET.get('page', 1)  
    host_id = 1
    vid = int(vid)
    vm = Vgate.objects.get(id=vid)   
    vname = vm.name 
    errors = []
    time_refresh = TIME_JS_REFRESH
    messages = []
    host = Host.objects.get(id=host_id)
    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None
    if not conn:
        errors.append(e.message)
    else:
        #all_vm = sort_host(conn.vds_get_node())
        vcpu, memory, description = conn.vds_get_info(vname)
        cpu_usage = conn.vds_cpu_usage(vname)
        memory_usage = conn.vds_memory_usage(vname)[1]
        hdd_image = conn.vds_get_hdd(vname)
        #iso_images = sorted(conn.get_all_media()) ??????????????????
        media, media_path = conn.vds_get_media(vname)
        dom = conn.lookupVM(vname)
        vcpu_range = [str(x) for x in range(1, 9)]
        memory_range = [128, 256, 512, 768, 1024, 2048, 4096, 8192, 16384]
        vnc_port = conn.vnc_get_port(vname)

        try:
            instance = Instance.objects.get(vname=vname)
        except:
            instance = None
        conn.close()
    redirecturl = "/vgates/"

    # 获取虚拟机的使用情况
    records = VmsUseRecord.objects.filter(vmtype="imgvgtls", vmid=vid)
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

    description = vm.remark

    return render_to_response('templates/instance.html', {'host_id': host_id,
                                                'vname': vname,
                                                'messages': messages,
                                                'errors': errors,
                                                'instance': instance,
                                                #'all_vm': all_vm,
                                                'vcpu': vcpu, 'cpu_usage': cpu_usage, 'vcpu_range': vcpu_range,
                                                'description': description,
                                                #'networks': networks,
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


def selectServer(request):
    # 获取host表中服务器的虚拟机个数，选择虚拟机个数最少的服务器
    servers = Host.objects.order_by('id')[1:]
    counts = []
    for server in servers:
        counts.append(len(Vgate.objects.filter(containerIP=server.hostname, imgtype_id=int(request.POST['vgt_type']))))
    # 虚拟机个数最少的服务器id，在虚拟机个数相同时，优先选择id最大的服务器
    counts.reverse()
    serverid = len(servers) - counts.index(min(counts)) + 1
    ip = Host.objects.get(id=serverid).hostname
    # 将创建请求发送给相应的服务器
    datas = {
        'vgt_name': request.POST['vgt_name'],
        'vgt_mgrip': request.POST['vgt_mgrip'],
        'vgt_type': int(request.POST['vgt_type']),
        'vgt_ram': int(request.POST["vgt_ram"]),
        'vgt_cpu': int(request.POST["vgt_cpu"]),
        'vgt_mgrport': request.POST['vgt_mgrport'],
        'vgt_remark': request.POST['vgt_remark'],
        'containerIP': ip
    }
    data = post("http://" + ip + "/createvgt/", datas)
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
        # all_vm = sort_host(conn.vds_get_node())
        if request.method == 'POST':
            # if 'instance_add' in request.POST:
            img = ImgVgt.objects.get(id=request.POST["vgt_type"])
            data['name'] = request.POST["vgt_name"]
            data['ram'] = int(request.POST["vgt_ram"])
            data['vcpu'] = int(request.POST["vgt_cpu"])
            data['arc'] = img.osstruct
            data['image'] = STATIC_DOCUMENT + 'vgt/%s/' %img.id + img.filename
            vm = Vgate(
                name=request.POST['vgt_name'],
                mgrip=request.POST['vgt_mgrip'],
                imgtype_id=int(request.POST['vgt_type']),
                memory=int(request.POST['vgt_ram']),
                cpu=int(request.POST['vgt_cpu']),
                osstruct=img.osstruct,
                mgrport=request.POST['vgt_mgrport'],
                state=0,
                remark=request.POST['vgt_remark'],
                containerIP=request.POST['containerIP'])
            # vm.save()
            try:
                conn.add_vm(data['name'], data['ram'], data['vcpu'], data['image'], data['arc'],'vgt')
                vm.save()
                img.vgtcount = img.vgtcount + 1
                img.save()
            except libvirtError as msg_error:
                errors.append(msg_error.message)
                data1["result"] = 0
                vm.delete()
                m_vgates=Vgate.objects.get(imgtype_id=img.id)
                img.vgtcount = len(m_vgates)
                img.save()
                return HttpResponse(json.dumps(data1))
        conn.close()
    try:
        conn = ConnServer(host)
        if conn:
            conn.vds_set_vnc_passwd(data['name'], '123456')
    except libvirtError as e:
        conn = None
        data1["result"] = 0
        vm.delete()
        m_vgates=Vgate.objects.get(imgtype_id=img.id)
        img.vgtcount = len(m_vgates)
        img.save()
        return HttpResponse(json.dumps(data1))
    conn.close()
    data1["result"] = 1
    return HttpResponse(json.dumps(data1))
    # return HttpResponseRedirect('/vgates/')

def sort_host(hosts):
    """
    Sorts dictionary of hosts by key
    """
    if hosts:
        sorted_hosts = []
        for host in sorted(hosts.iterkeys()):
            sorted_hosts.append((host, hosts[host]))
        return SortedDict(sorted_hosts)

def vganamecheck(request):
    global logger
    judgevgateimg=0
    if request.method == 'POST':
        try:
            vgateimgname = request.POST['img_name']
        except ValueError:
            logger.error("vgates")
            raise Http404()       
        vgateimg= ImgVgt.objects.order_by('id')
        for vimg in vgateimg:
            if vimg.name == vgateimgname:
                judgevgateimg=1
                break
    data = {}
    data['judgename']=judgevgateimg
    return HttpResponse(json.dumps(data))

def vgavmnamecheck(request):
    global logger
    judgevgatevmimg=0
    if request.method == 'POST':
        try:
            vgateimgname = request.POST['vgt_name']
        except ValueError:
            logger.error("vgates")
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

def vgaipnamecheck(request):
    global logger
    judgevgatevmimg=0
    if request.method == 'POST':
        try:
            ipname = request.POST['vgt_mgrip']
        except ValueError:
            logger.error("vgates")
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

def vgaipnamecheckedit(request):
    global logger
    judgevgatevmimg=0
    if request.method == 'POST':
        try:
            ipname = request.POST['vgtmgrip']
        except ValueError:
            logger.error("vgates")
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
