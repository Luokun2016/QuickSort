import zipfile
# from tsssite.settings import STATIC_UPDATA, STATIC_FIELNAME
import os
import re

def UNZIPFILE(STATIC_UPDATA,STATIC_FIELNAME):
    unziptodir=STATIC_UPDATA[:-1]
    zipfilename=STATIC_UPDATA+STATIC_FIELNAME
    m_delfolder=STATIC_FIELNAME[:-4]
    if os.path.exists(unziptodir):
        os.popen('rm -rf '+STATIC_UPDATA+ m_delfolder)
    if not os.path.exists(unziptodir):
        os.makedirs(unziptodir, 0777)
    zfobj = zipfile.ZipFile(zipfilename)
    files={}
    num=0
    for name in zfobj.namelist():
        name = name.replace('\\','/')
        if name.endswith('/'):
            os.makedirs(os.path.join(unziptodir, name))
        else:
            num+=1
            files[num]=name
            ext_filename = os.path.join(unziptodir, name)
            ext_dir= os.path.dirname(ext_filename)
            if not os.path.exists(ext_dir):
                os.makedirs(ext_dir,0777)
            outfile = open(ext_filename, 'wb')
            outfile.write(zfobj.read(name))
            outfile.close()

def useupsata():
    if os.path.exists('/home/updatafile/updatafile.py'):
        cmd.run('python /home/updatafile/updatafile.py')

if __name__ == '__main__':  
    useupsata()  
