#-*- coding: utf-8 -*- 
'''
完成对虚拟交换机的增删改查功能。
但实际上这些功能并没有被使用！！！
'''

from django.shortcuts import render_to_response
from vswitches.models import *
from libvirt import libvirtError
from sysmgr.models import *
from tsssite.server import ConnServer
from tsssite.settings import TIME_JS_REFRESH
from myexp.models import *
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseServerError
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage
import json, os
from django.db.models import Q
import logging
logger = logging.getLogger('mysite.log')
vswitchls_pages = 1
imgvshls_pages = 1

def mgrvswitches(request):
    if not 'username' in request.session:
        return HttpResponseRedirect('/Login/')
    username = request.session['username']
    imgvshls = ImgVsh.objects.order_by('-id')
    vswitchls = Vswitch.objects.order_by('-id')
    dictype = DicType.objects.get(enumtype='vswitchtype')
    vshtypels= DicContent.objects.order_by('id').filter(enumid_id=dictype.id)
    querytext = ''
    queryimg = ''
    if 'querytext' in request.GET and request.GET['querytext']:
        querytext = request.GET['querytext']
    if 'queryimg' in request.GET and request.GET['queryimg']:
        queryimg = request.GET['queryimg']
    tabtype = 'vm'

    types="vswitchls"
    try:
        types = request.GET.get("type")
        if types == "img":
            request.session['tabtype'] = 'img'
    except ValueError:
        types="vswitchls" 
    
    if 'btnqueryimg' in request.GET:
        request.session['tabtype'] = 'img'
    vswitchls=vswitchls.filter(Q(name__icontains=querytext)|Q(mgrip__icontains=querytext))
    imgvshls=imgvshls.filter(Q(name__icontains=queryimg)|Q(xh__icontains=queryimg))
    if 'tabtype' in request.session:
        tabtype=request.session['tabtype']
        request.session.pop('tabtype')

    after_range_num = 5
    befor_range_num = 4
    try:
        page = int(request.GET.get("page",1))
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    if(types == "img"):
        global imgvshls_pages
        imgvshls_pages=page        
    else:
        global vswitchls_pages
        vswitchls_pages = page
      
    paginator_vswitchls = Paginator(vswitchls,10)
    try:
        vswitchls = paginator_vswitchls.page(vswitchls_pages)
    except(EmptyPage,InvalidPage,PageNotAnInteger):
        vswitchls = paginator_vswitchls.page(paginator_vswitchls.num_pages)
    if vswitchls_pages >= after_range_num:
        page_range = paginator_vswitchls.page_range[page-after_range_num:page+befor_range_num]
    else:
        page_range = paginator_vswitchls.page_range[0:int(vswitchls_pages)+befor_range_num]
    page_range_vswitchls=page_range
    page_range=''
    paginator_imgvshls = Paginator(imgvshls,10)
    try:
        imgvshls = paginator_imgvshls.page(imgvshls_pages)
    except(EmptyPage,InvalidPage,PageNotAnInteger):
        imgvshls = paginator_imgvshls.page(paginator_imgvshls.num_pages)
    if imgvshls_pages >= after_range_num:
        page_range = paginator_imgvshls.page_range[page-after_range_num:page+befor_range_num]
    else:
        page_range = paginator_imgvshls.page_range[0:int(imgvshls_pages)+befor_range_num]           
    page_range_imgvshls = page_range   
    return render_to_response('templates/vSwitch.html',{'queryimg':queryimg,'querytext':querytext,'tabtype':tabtype,'vswitchls': vswitchls, 'vshtypels': vshtypels, 'imgvshls': imgvshls, 'username':username,'page_range_vswitchls':page_range_vswitchls,'page_range_imgvshls':page_range_imgvshls}, context_instance=RequestContext(request))

def vshinfo(request):
	vm = ''
	if request.method == 'POST':
		vshid = request.POST['vshid']
		vsh = Vswitch.objects.get(id=vshid)
	data = {}
	data["vshid"] = vsh.id
	data["vshname"] = vsh.name
	data["vshtype"] = vsh.imgtype.id
	data["vshmgrip"] = vsh.mgrip
	data["vshmgrport"] = vsh.mgrport
	data["remark"] = vsh.remark
	return HttpResponse(json.dumps(data))

def editvsh(request):
        global logger
        try:
                did = int(request.POST['vshid'])
                vsh = Vswitch.objects.get(id=did)   
        except ValueError:
                logger.error("vswitch")
                raise Http404()				
        if request.method == 'POST':
                vsh.name = request.POST['vshname']
                vsh.mgrip = request.POST['vshmgrip']
                vsh.remark = request.POST['vshremark']
                vsh.mgrport = request.POST['vshmgrport']
                vsh.imgtype_id = int(request.POST['vshtype'])
                vsh.save()
        return HttpResponseRedirect('/vswitches/')
def delvsh(request, did):
    global logger
    error = ''
    try:
        did = int(did)
        vm = Vswitch.objects.get(id=did)
    except ValueError:
        logger.error("vswitch")
        raise Http404()
    
    vname = vm.name
    vm.delete()
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
        except libvirtError as msg_error:
            errors.append(msg_error.message)
    return HttpResponseRedirect('/vswitches/')

def imgvshinfo(request):
	img = ''
	if request.method == 'POST':
		imgid = request.POST['imgid']
		img = ImgVsh.objects.get(id=imgid)
	data = {}
	data["imgid"] = img.id
	data["imgname"] = img.name
	data["imgxh"] = img.xh
	data["imgvshtype"] = img.vshtype.id
	data["imgfac"] = img.fac
	data["imgversion"] = img.version
	data["imgfilename"] = img.filename
	data["imgstarting"] = img.starting
	data["remark"] = img.remark
	return HttpResponse(json.dumps(data))

def uploadimg(request):
    if request.method == 'POST':
        data = request.FILES['image_file']
        userid = request.session["userid"]
        uid = '%s' % userid
        handle_uploaded_file(uid, data)
    return HttpResponse(data.name)

def addimgvsh(request):
    if request.method == 'POST':
        img = ImgVsh(
            name=request.POST['img_name'], 
            xh = request.POST['img_xh'],
            vshtype_id = int(request.POST['img_vshtype']), 
            fac = request.POST['img_fac'],
            version=request.POST['img_version'], 
            filename=request.POST['imagefilename'], 
            starting = request.POST['img_starting'],
            vshcount=0,
            remark=request.POST['img_remark'])
        img.save()
        curpath = STATIC_DOCUMENT + 'vsh/%s' % img.id
        if not os.path.exists(curpath):
            os.mkdir(curpath)
        userid = request.session["userid"]
        uid = '%s' % userid
        sourcepath = STATIC_DOCUMENT + 'user/%s' % uid
        os.system('mv ' +  sourcepath + '/' + img.filename + ' ' + curpath + '/' + img.filename)
    request.session['tabtype'] = 'img'
    return HttpResponseRedirect('/vswitches/')

def editimgvsh(request):
        global logger
        if request.method == 'POST':
                try:
                        did = int(request.POST['imgid'])
                except ValueError:
                        logger.error("vswitch")
                        raise Http404()
                data = None
                if request.FILES.has_key("imgfilename"):
                        data = request.FILES['imgfilename']
                img = None
                img = ImgVsh.objects.get(id=did)
                if img != None:
                        img.name = request.POST['imgname']
                        img.fac = request.POST['imgfac']
                        img.xh = request.POST['imgxh']
                        img.vshtype_id = int(request.POST['imgvshtype'])
                        img.version = request.POST['imgversion']
                        img.starting = request.POST['imgstarting']
                        if data != None:
                                handle_uploaded_file(data)
                                img.filename=data.name
                        img.remark=request.POST['imgremark']
                        img.save()
        request.session['tabtype'] = 'img'
        return HttpResponseRedirect('/vswitches/')

def delimgvsh(request, did):
        global logger
        error = ''
        try:
                did = int(did)
                img = ImgVsh.objects.get(id=did)
        except ValueError:
                logger.error("vswitch")
                raise Http404()	
        img.delete()
        request.session['tabtype'] = 'img'
        return HttpResponseRedirect('/vswitches/')

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

def vmstart(request, vid):
    host_id = 1
    vid = int(vid)
    vm = Vswitch.objects.get(id=vid) 
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
            dom.create()
            vm.state = 1
            vm.save()
        except libvirtError as msg_error:
            errors.append(msg_error.message)
    return HttpResponseRedirect('/vswitches/')

def vmstop(request, vid):
    host_id = 1
    vid = int(vid)
    vm = Vswitch.objects.get(id=vid) 
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
            dom.destroy()
            vm.state = 0
            vm.save()
        except libvirtError as msg_error:
            errors.append(msg_error.message)
    return HttpResponseRedirect('/vswitches/')

def instance(request, vid):
    """
    VDS block
    """
    #if not request.user.is_authenticated():
      #  return HttpResponseRedirect('/login')
    host_id = 1
    vid = int(vid)
    vm = Vswitch.objects.get(id=vid)   
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
        vcpu, memory, networks, description = conn.vds_get_info(vname)
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
    redirecturl = "/vswitches/"
    return render_to_response('templates/instance.html', {'host_id': host_id,
                                                'vname': vname,
                                                'messages': messages,
                                                'errors': errors,
                                                'instance': instance,
                                                #'all_vm': all_vm,
                                                'vcpu': vcpu, 'cpu_usage': cpu_usage, 'vcpu_range': vcpu_range,
                                                'description': description,
                                                'networks': networks,
                                                'memory': memory, 'memory_usage': memory_usage, 'memory_range': memory_range,
                                                'hdd_image': hdd_image, #'iso_images': iso_images,
                                                'media': media, 'path': media_path,
                                                'dom': dom,
                                                #'vm_xml': dom.XMLDesc(VIR_DOMAIN_XML_SECURE),
                                                'vnc_port': vnc_port,
                                                'time_refresh': time_refresh,
                                                'redirecturl':redirecturl
                                                },
                              context_instance=RequestContext(request))