"""
"""

import os
import sys
from moviepy.video.compositing import MultiCam
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.io.preview import show, preview
from moviepy.conf import FFMPEG_BINARY
import numpy as np
import datetime
import csv
import pygame as pg
import numpy as np
import subprocess
import psutil

def default_cut(start_time,n):
    """
    :param n: number of cameras
    """
    times = [[start_time-1,0]]
    time = start_time+2.0/25
    for i in range(n-1):
        time = time + 2.0/25
        times.append([time,i+1])
        
    time = round(time*25)/25
    times.append([time+1 + 2.0/25])
    return times
    
    
def get_time(event,img,t):
    """
    Returns time clicked (to be given to preview)
    """
    if event.type == pg.MOUSEBUTTONDOWN:
        x,y = pg.mouse.get_pos()
        print t
        return t

class edit:
    """
    If trigger_times is not defined it is read from is trigger_times_file. Similar with record_times,filenames and shift.
    
    :param base_folder: Folder path where each camera footage folder is located.
    :param cameras: The name of each camera folder
    :param extension: The extension of the videos. (So that thumbnails, etc. are skipped.)
    :param latency: An array containing the entries of the latency relative to the trigger times the effect will be cut. If a scalar is given, the value will be expanded into an array. Default 0.
    :param fps: Frames per second of (majority) cameras.
    :param slowmo_cameras: Dictionary where keys are cameras who shot in higher framerate, values are what speed it shot at.
    :param times_file: A csv file containing datetime codes when trigger should be was fired. Default None, then file becomes base_folde/biker_times.csv
    :param record_times_file: A csv file containing two datetime codes on each row, where the first and second values are the start and stop recoding times respecively. Default None, then file becomes base_folde/record_times.csv
    :param filenames_file: A numpy file containing array of filenames formatted as output from moviepy.video.compositing.MultiCam.MultiCam.get_files. Default None, then file becomes base_folde/filenames.npy
    :param shift_file: A numpy file containing array the size of filenames of the shift of each video file relative to the first. Default None, then file becomes base_folde/shift.npy
    """
    def __init__(self,base_folder,cameras,extension='.MP4',latency=0,fps=25,slowmo_cameras={},
            trigger_times_file=None,record_times_file=None,trigger_times = None,
            record_times = None,filenames_file=None,filenames=None,
            shift_file=None,shift=None,**kwargs):
        self.base_folder = base_folder
        self.cameras = cameras
        self.fps = fps
        self.extension = extension
        self.slowmo_cameras = slowmo_cameras
        self.concat_args = kwargs
        
        #### get saved data if available ####
        # default file names
        if trigger_times_file == None:
            self.trigger_times_file = base_folder + '/biker_times.csv'
        else:
            self.trigger_times_file = trigger_times_file
        
        if record_times_file == None:
            self.record_times_file = base_folder + '/recording_times.csv'
        else:
            self.record_times_file = record_times_file
            
        if filenames_file == None:
            self.filenames_file = base_folder + '/filenames.npy'
        else:
            self.filenames_file = filenames_file
            
        if shift_file == None:
            self.shift_file = base_folder + '/shift.npy'
        else:
            self.shift_file = shift_file
            
        # get data from filenames if possible or print how to get it
        if trigger_times == None:
            try:
                self.read_trigger_times()
            except Exception, e:
                print "Could not read trigger times. With error:"
                print e
                print "Run get_trigger times"
        else:
            self.trigger_times = trigger_times
            
        if record_times == None:
            self.read_record_times()
        else:
            self.record_times = record_times
            
        if filenames == None:
            try:
                self.filenames = np.load(self.filenames_file)
                if len(self.filenames) != len(self.record_times):
                    print 'Warning: Number of record times and number of filenames to not match.'
                    
            except Exception, e:
                print "Could not read filenames, with error:"
                print e
                print "Run check_filenames then get_filenames"
                
        if shift == None:
            try:
                self.shift = np.load(self.shift_file)
            except Exception, e:
                print "Could not read shift, with error:"
                print e
                print "Run get_shift"
            
        # build latency array
        if type(latency) == list:
            self.latency = latency
        else:
            self.latency = [latency for i in range(len(self.record_times))]
            
        # check that camera_slowmo exists else run reinterpret
        for camera in slowmo_cameras:
            if camera+'_slow' not in os.listdir(self.base_folder):
                print camera+" is not yet reinterpreted. Run reinterpret."
                
        
        
    def read_trigger_times(self,print_progress = True):
        """
        Reads times from the trigger_times_file attribute [csv file] and saves in trigger_times attributes.
        """
        if not os.path.exists(self.trigger_times_file):
            raise Exception("trigger_times_file "+self.trigger_times_file+" is not found.")
            
        if print_progress:
            print "Reading times"
            
        with open(self.trigger_times_file, 'rb') as f:
            rb = csv.reader(f)
            self.trigger_times = []
            for timestr in rb:
                self.trigger_times.append( datetime.datetime.strptime(timestr[0], "%Y-%m-%d %H:%M:%S.%f") )
        
    def get_trigger_times(self,save=True):
        """
        get trigger times manually, and save.
        """
        trigger_times = []

        if save:
            f = open(self.trigger_times_file, 'wb')
            writer = csv.writer(f)

        for i,record_times in enumerate(self.record_times):
            
            # load each clip individualy to save memory
            if i>=0:
                clip = VideoFileClip(self.filenames[i][0], audio=False)
                
                print "Click to record time."
                try:
                    times = preview(clip,fps=5,audio=False,func=get_time)
                    for t in times:
                        print record_times[0]+datetime.timedelta(0,t)
                        trigger_times.append(record_times[0]+datetime.timedelta(0,t))
                        if save:
                            writer.writerow([str(record_times[0]+datetime.timedelta(0,t))])
                except AssertionError:
                    print "Preview Failed, carrying on..."
                except KeyboardInterrupt:
                    ##### clean up #####
                    clip.reader.close()
                    if clip.audio:
                        clip.audio.reader.close_proc()
                    del clip
                    break
                ##### clean up #####
                clip.reader.close()
                if clip.audio:
                    clip.audio.reader.close_proc()
                del clip
        self.trigger_times = trigger_times
        if save:
            f.close()
            
        return trigger_times
        
    def read_record_times(self,print_progress = True):
        """
        Reads times from the record_times_file attribute [csv file] and saves in record_times attributes.
        """
        if not os.path.exists(self.record_times_file):
            raise Exception("recoring_times_file "+self.record_times_file+" is not found.")
            
        if print_progress:
            print "Reading recoring times"
            
        with open(self.record_times_file,'rb') as f:
            rc = csv.reader(f)
            self.record_times = []
            for ss in rc:
                start_time = datetime.datetime.strptime(ss[0], "%Y-%m-%d %H:%M:%S.%f")
                stop_time = datetime.datetime.strptime(ss[1], "%Y-%m-%d %H:%M:%S.%f")
                self.record_times.append( [start_time,stop_time] )
        
    def check_filenames(self):
        """
        checks files
        """
        return MultiCam.check_files(self.base_folder,self.cameras)
        
    def get_filenames(self,save = True):
        """
        Stores filenames in filenames attribute, and saves at filenames_file attribute if save is True.
        """
        self.filenames = MultiCam.get_files(self.base_folder,self.cameras)
        if save:
            np.save(self.filenames_file,self.filenames)
        return self.filenames
        
    def get_shift(self,save=True,print_progress=True,**kwargs):
        """
        Gets shift from sync in MultiCam. If save is True it saves it to a numpy array at shift_file.
        """
        self.shift = []
        for i,f in enumerate(self.filenames):
            if print_progress:
                print "syncing "+str(i+1)+" of "+str(len(self.filenames))
            seq = MultiCam.MultiCam(f)
            self.shift.append(seq.sync(**kwargs))
            del seq
            
        if save:
            np.save(self.shift_file,self.shift)
        return self.shift
            
        
    def reinterpret(self):
        """
        Reinterprets cameras in slowmo_cameras
        """
        # add output options/make the same as input
        for camera in self.slowmo_cameras:
            out_path = os.path.abspath(os.path.join(self.base_folder,camera+'_slow'))
            if not os.path.exists(out_path):
                os.mkdir(out_path)
                
            for f in os.listdir(os.path.join(self.base_folder,camera)):
                if self.extension in f:
                    in_clip = os.path.abspath(os.path.join(self.base_folder,camera,f))
                    out_clip = os.path.join(out_path,f)
                    cmd = [FFMPEG_BINARY,'-i',in_clip,'-vf',
                        'setpts='+str(float(self.slowmo_cameras[camera]))+'*PTS','-r','25',
                        '-vcodec','libx264','-preset','fast','-b:v','5000k','-y',out_clip]
                    os.system(' '.join(cmd))
                    #print p
                    
            
    def edit(self,cut = default_cut,filename='Exports/',extension='.MP4',**kwargs):
        """
        """
        count = 0
        for time in self.trigger_times:
            for j,record_times in enumerate(self.record_times):
                if time >= record_times[0] and time <= record_times[1]:
                    if count >=36:
                        start = (time - record_times[0]).total_seconds() + self.latency[j]
                        times = cut(start,len(self.filenames[j]))
                        filenames = []
                        slowmo = {}
                        for i,camera in enumerate(self.cameras):
                            if camera in self.slowmo_cameras:
                                if os.path.exists(os.path.join(self.base_folder,camera+"_slow")):
                                    
                                    slowmo[i] = self.slowmo_cameras[camera]
                                    new_path = os.path.abspath(os.path.join(self.base_folder,camera+"_slow",os.path.split(self.filenames[j][i])[1]))
                                    filenames.append(new_path)
                                else:
                                    print camera+" does not have a slow version. Run reinterpret. Using normal version."
                                    filenames.append(self.filenames[j][i])
                            else:
                                filenames.append(self.filenames[j][i])
                                
                        seq = MultiCam.MultiCam(filenames,
                            times=times,shift=self.shift[j],slowmo=slowmo)
                        video = seq.get_clip(**self.concat_args)
                        print psutil.virtual_memory()
                        video.to_videofile(filename+str(count)+extension,**kwargs)
                        print "Done"
                        print psutil.virtual_memory()
                        print "Close MultiCam"
                        seq.close()
                        del seq
                        print psutil.virtual_memory()
                        print "Close Video"
                        for c in video.clips:
                            if isinstance(c,VideoFileClip):
                                c.reader.close()
                                if c.audio:
                                    c.audio.reader.close_proc()
                        del video
                        print psutil.virtual_memory()
                    count = count + 1

    
