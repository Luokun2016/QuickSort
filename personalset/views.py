# Create your views here.
from django.shortcuts import render_to_response
from teachers.models import Teacher
from experments.models import ExpModule, Experment, ExpDoc
from vms.models import Vm
from devices.models import Device
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.paginator import Paginator, PageNotAnInteger, InvalidPage, EmptyPage

def mgrpwd(request):
		expermentls = Experment.objects.order_by('-id')
		modulels = ExpModule.objects.order_by('-id')
		return render_to_response('personalset/modifypwd.html',{'expermentls': expermentls, 'modulels': modulels}, context_instance=RequestContext(request))
