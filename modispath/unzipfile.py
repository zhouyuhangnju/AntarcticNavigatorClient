#/usr/bin/python
#coding=utf-8

import os,sys,time
import zipfile

def unzipfile(filename, filedir):

    times = time.time()
    r = zipfile.is_zipfile(filename)
    if r:
        starttime = time.time()
        fz = zipfile.ZipFile(filename,'r')
        for file in fz.namelist():
            print(file)  #打印zip归档中目录
            fz.extract(file,filedir)
        endtime = time.time()
        times = endtime - starttime
    else:
        print('This file is not zip file')
    print('times' + str(times))

# unzipfile('download/test.zip', 'data/')
