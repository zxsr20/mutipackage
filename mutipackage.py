#_*_encoding:utf-8_*_
#-------------------------------------------------------------------------------
# Name:        自动打包工具
# Purpose:     通过在py目录下配置渠道文件，keystore等参数，进行apk的注入asset渠道文件，重签名，zipalign
#-------------------------------------------------------------------------------


import os,sys,shutil,zipfile,md5

pypath = os.getcwd()+os.path.sep

#可配置参数
CHANNEL_LIST = 'channel_list'#渠道文件
SRC_APK_DIR = 'src'+os.path.sep#apk所在文件
OUT_APK_DIR = 'out'+os.path.sep#输出文件夹
KEY_STORE = 'wasu-key'#签名文件
KEY_SECRET = 'wasu3gjsyy'#签名密码
CHANNEL_FILE_NAME = 'channnel'#注入的渠道文件名称

SCAN_FILE_EXT = '.apk'


##查找源APK
def findApk(filePath):
    for file in os.listdir(filePath):
        if os.path.splitext(file)[1] == SCAN_FILE_EXT:
            return os.path.splitext(file)
    return ''


##生成临时文件
def createFile(fileName):
    removeDirWithoutME('assets')
    fileHandle = open ( 'assets'+os.path.sep+CHANNEL_FILE_NAME, 'w' )
    fileHandle.write ( fileName )
    fileHandle.close()

##移动渠道文件
def moveChannelFile(fileName):
    os.remove ( 'assets/'+fileName)

##拷贝文件
def copyFile(srcFileName,dstFileName):
    shutil.copy(srcFileName, dstFileName)

##导入渠道包方式
def importChannel(srcFile,channelFile):
    zipped = zipfile.ZipFile(srcFile, 'a', zipfile.ZIP_DEFLATED)
    empty_channel_file = "assets/{channel}".format(channel=channelFile)
    zipped.write('assets/'+channelFile, empty_channel_file)
    zipped.close()
    
##导入渠道包
def importChannelbyAAPT(srcFile,channelFile):
    print "aapt a "+srcFile+ " "+pypath+"assets"+os.path.sep+CHANNEL_FILE_NAME
    os.system("cd /d "+pypath)
    os.system("aapt a "+srcFile+" assets"+os.path.sep+CHANNEL_FILE_NAME)
    
##删除签名
def deleteMETAbyAAPT(srcFile):
#     print "aapt a "+srcFile+ " "+pypath+"assets"+os.path.sep+channelFile
    os.system("cd /d "+pypath)
    os.system("aapt r "+srcFile+" META-INF/MANIFEST.MF")
    os.system("aapt r "+srcFile+" META-INF/CERT.SF")
    os.system("aapt r "+srcFile+" META-INF/CERT.RSA")
    
##重签名
def signAPK(srcFile,signkey):
    signWord = "jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore {key_store} \
                {zipname} -storepass {key_store_pass} \
                -keypass {key_alias_pass} {key_alias}".format(key_store=pypath+signkey,tmp_target=srcFile,zipname=pypath+srcFile,key_store_pass=KEY_SECRET,key_alias_pass=KEY_SECRET,key_alias='wasu-key')
    print signWord
    os.system(signWord)
    
##内存对齐
def zipAPK(srcFile,toFile):
    os.system("cd /d "+pypath)
    zipWord = "zipalign 4 {tmp_target} {target}".format(tmp_target=srcFile,target=toFile)
    print zipWord
    os.system(zipWord)
    os.remove (srcFile)

##移动文件
def moveFile(fileName,outFileName):
    shutil.move(fileName, OUT_APK_DIR+outFileName)

##删除目录下的所有文件包括自己
def removeDir(dirPath):
    if not os.path.isdir(dirPath):
        return
    files = os.listdir(dirPath)
    try:
        for file in files:
            filePath = os.path.join(dirPath, file)
            if os.path.isfile(filePath):
                os.remove(filePath)
            elif os.path.isdir(filePath):
                removeDir(filePath)
        os.rmdir(dirPath)
    except Exception, e:
        print e
    
##删除目录下的所有文件不包括自己    
def removeDirWithoutME(dirPath):
    if not os.path.isdir(dirPath):
        return
    files = os.listdir(dirPath)
    try:
        for file in files:
            filePath = os.path.join(dirPath, file)
            if os.path.isfile(filePath):
                os.remove(filePath)
            elif os.path.isdir(filePath):
                removeDir(filePath)
    except Exception, e:
        print e

if __name__ == '__main__':
    
    
    srcApk = findApk(SRC_APK_DIR)
    if len(srcApk) == 0:
        print 'apk is not exist'
        sys.exit(1)
    print SRC_APK_DIR+srcApk[0]+srcApk[1]
    print OUT_APK_DIR+srcApk[0]+srcApk[1]
    
    print os.getcwd()
    
    channelFile = open ( CHANNEL_LIST)#获取渠道文件md5
    channels = channelFile.read()
    key = md5.new()
    key.update(channels)
    channelMD5 = key.hexdigest()
    
    if os.path.exists(OUT_APK_DIR+channelMD5+os.path.sep):#如果存在，就要删除，为了保证不重复
        removeDirWithoutME(OUT_APK_DIR+channelMD5+os.path.sep)
    else:
        os.makedirs(OUT_APK_DIR+channelMD5+os.path.sep)
    
    
    fileHandle = open ( CHANNEL_LIST)#打开渠道文件进行打包
    while 1:
        line = fileHandle.readline()
        if not line:
            break
        createFile(line.rstrip())#创建要导入的渠道文件
        copyFile(SRC_APK_DIR+srcApk[0]+srcApk[1],OUT_APK_DIR+channelMD5+os.path.sep+srcApk[0]+'_'+line.rstrip()+srcApk[1])#拷贝源apk文件到out目录
        importChannelbyAAPT(OUT_APK_DIR+channelMD5+os.path.sep+srcApk[0]+'_'+line.rstrip()+srcApk[1],line.rstrip())#导入渠道文件
        deleteMETAbyAAPT(OUT_APK_DIR+channelMD5+os.path.sep+srcApk[0]+'_'+line.rstrip()+srcApk[1])
        signAPK(OUT_APK_DIR+channelMD5+os.path.sep+srcApk[0]+'_'+line.rstrip()+srcApk[1],KEY_STORE)
        zipAPK(OUT_APK_DIR+channelMD5+os.path.sep+srcApk[0]+'_'+line.rstrip()+srcApk[1],OUT_APK_DIR+channelMD5+os.path.sep+srcApk[0]+'_sign_align_'+line.rstrip()+srcApk[1])
        print 'channel: %s build complete'%(line.rstrip())




