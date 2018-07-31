import time
import sys
import scipy
import scipy.io.wavfile
import scipy.signal
import pickle
import os
import numpy as np
import subprocess
import matplotlib.pyplot as plt


def get_sound(file_path,clip_start=0,clip_length=0,sampling_rate=0):
    folder=os.path.split(file_path)[0]
    # ffmpeg = "ffmpeg"
    ffmpeg = "E:/LW/MP/github/VideoSync-master/ffmpeg-20180713-97d766f-win64-static/bin/ffmpeg.exe"
    temp_base_name="temp"
    x=0
    while os.path.exists(os.path.join(folder,temp_base_name+str(x)+".wav")):
        x+=1
    temp_file_path=os.path.join(folder,temp_base_name+str(x)+".wav")


    command = "{} -i {} -ss {} -t {} -ac 1 -ar {}  {}".format(ffmpeg,file_path,clip_start,clip_length,sampling_rate,temp_file_path)
    subprocess.call(command,stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

    rate,out=scipy.io.wavfile.read(temp_file_path)

    # out=np.abs(out*0.1)
    # out*=0.1
    out=out.clip(min=0)*0.1

    os.remove(temp_file_path)


    return out


def normalize(v:np.array):
    v_min=v.min()
    v_max=v.max()
    v-=v_min
    v*=v_max-v_min
    return  v

def align(va,vb):
    long=normalize(va)
    short=normalize(vb)

    is_flipped=False

    if long.size<short.size:
        long,short=short,long
        is_flipped=True


    tiled_long=np.tile(long,3)[long.size-short.size:long.size*2+short.size]

    convolution=scipy.signal.fftconvolve(tiled_long,np.flipud(short),'valid')



    shift = (convolution.argmax() + (long.size - short.size)) % long.size

    if shift+short.size>long.size:
        forward=np.sum(long[shift:]*short[:long.size-shift])
        backward=np.sum(short[long.size-shift:]*long[:short.size- (long.size-shift) ])
        if backward>=forward :
            shift=-(long.size-shift)
    if is_flipped:
        shift=-shift

    # plt.plot(convolution)
    # plt.plot( np.tile(va,3),color=(1,0,0))
    # plt.plot(np.arange(long.size) + long.size, long, color=(1, 0, 0))
    # plt.plot(np.arange(short.size) + long.size + shift, short, color=(0, 1, 0))
    # plt.show()

    return shift


# sampling_rate=10000
#
# va=get_sound(os.path.normpath("E:/LW/MP/github/VideoSync-master/test1/v1.wav"),0,500,sampling_rate)
# vb=get_sound(os.path.normpath("E:/LW/MP/github/VideoSync-master/test1/v0.wav"),0,500,sampling_rate)
#
# # shift=0
# shift=align(va,vb)
#
#
# plt.plot(np.arange(va.size) + va.size, va,color=(1,0,0))
# # plt.plot( np.tile(va,3),color=(1,0,0))
# plt.plot(np.arange(vb.size) + va.size + shift, vb,color=(0,1,0))
# plt.show()



(active_path,active_clip_start,active_clip_length),selected_strips,sampling_rate=pickle.loads(sys.stdin.buffer.read())
active_sound=get_sound(os.path.normpath(active_path),active_clip_start,active_clip_length,sampling_rate)
shifts=[align(active_sound,get_sound(os.path.normpath(selected_path),selected_clip_start,selected_clip_length,sampling_rate))/sampling_rate for selected_path,selected_clip_start,selected_clip_length in selected_strips]
pickle.dump(shifts,sys.stdout.buffer)





