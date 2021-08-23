# -*- coding: utf-8 -*-
"""
@author: jackjt8

title: Chunky JSON generator
      -  Camera interpT

ver: 0.1 (2019-07-14) [Python 3.7]

Current: numpy, scipy, (matplotlib)
"""


import json
import os
import sys
import numpy as np
from scipy import interpolate
import matplotlib.pyplot as plt
import requests
import urllib.request


#%%
def main():
    decimals = 15 # for rounding
    
    framerate = 60
    
    idlist = []

    keyscenes = []
#              [scene_fname, time_stamp]
    keyscenes.append(['interp_1.json', 0.0]) # all time stamps pre 0.0 ignored post interp/convolution
    keyscenes.append(['interp_2.json', 20.0]) # used as template for saving
    
    json_interp = json_interpT(framerate, decimals)
    setup_return = json_interp.keyscene_setup(keyscenes)

    if setup_return == 0:
        print('ERROR - Need at least one keyscene')
        sys.exit(0)
    elif setup_return == 1:
        # ASK for point 2 / B details.
        t2 = 1.0 # ASK
        x2 = 5.0 # ASK
        y2 = 6.0 # ASK
        z2 = 5.0 # ASK
        roll2 = 0.0 # ASK
        yaw2 = 50.0 # ASK
        pitch2 = 5.0 # ASK
        fov2 = 100 # ASK
        dof2 = 200.0 # ASK
        focal2 = 1.0 # ASK
        lightsun2 = 1.0
        animation2 = 0.0
        cloudx = 0.0
        cloudy = 128.0
        cloudz = 0.0
        
        #pass point 2 / B
        json_interp.point2_setup(t2, x2, y2, z2, roll2, pitch2, yaw2, fov2, dof2, focal2, lightsun2, animation2, cloudx, cloudy, cloudz)
        
        # run linear interp
        json_interp.do_interpT('slinear')
        
    elif setup_return == 2:
        # run linear interp
        json_interp.do_interpT('slinear')
        
    elif setup_return == 3 or setup_return == 4:
        # smoothing == 1 (off) OR smoothing > 1 (on/strength)
        json_interp.do_interpT('slinear',5) #ie ('slinear',5)
        
    else:
        """ASK if they want to use:
        slinear
        quad (need to padd)
        cubic (need to padd)
        ---
        smoothing == 1 (off) OR smoothing > 1 (on/strength)
        """
        kind = 'cubic' # ASK
        json_interp.do_interpT(kind)
        
        pass
    
    json_interp.save_json()

    
#%%  
class json_interpT():
    def __init__(self, framerate, decimals):
        self.decimals = decimals
        self.camX = []
        self.camY = []
        self.camZ = []
        self.cloudX = []
        self.cloudY = []
        self.cloudZ = []
        self.camRoll = []
        self.camPitch = []
        self.camYaw = []
        self.lightsun = []
        self.animation = []

        self.camFoV = []
        self.camDoF = []
        self.camfocalOffset = []

        self.source_fname = []      
        self.source_times = []
        self.source_scenes = []
        
        self.tframe = []
        self.nframe = []
        self.frametime = 1.0 / framerate
    
    #%%    
    def jsonload(self, fname):
        return json.load(open(os.path.join(fname),"r"))

    def jsonsave(self, scene, fname):
        json.dump(scene, open(os.path.join(fname),"w"), indent=2)
        print(fname)
        return

    def interpT(self, t, tframe, x, kindtype): # use t,x,and kindtype to create function. use tfrmae with function.
        f = interpolate.interp1d(t, x, kind=kindtype)
        return f(tframe)

    def smooth(self, y, box_pts): # Standard convolve/moving average type of smoothing. Just added y padding to fix
        box = np.ones(box_pts)/box_pts
        y_padded = np.pad(y, (box_pts//2, box_pts-1-box_pts//2), mode='edge')
        y_smooth = np.convolve(y_padded, box, mode='valid')
        return y_smooth
    
    #%%
    def keyscene_setup(self, keyscenes):
        # Unpack (for easier use)
        self.source_fname = [i[0] for i in keyscenes]
        self.source_times = [i[1] for i in keyscenes]
        
        # load scenes
        for fname in self.source_fname:
            self.source_scenes.append(self.jsonload(fname))
        
        # Check how many scenes we have and decide actions.
        if len(self.source_scenes) == 0:
            print('0')
            return 0

        elif len(self.source_scenes) == 1:
            print('1')
            return 1
        
        elif len(self.source_scenes) == 2:
            print('2')
            return 2
        
        elif len(self.source_scenes) == 3 or len(self.source_scenes) == 4:
            print('3')
            return 3
        else:
            print('5')
            return 5
        return
    
    #%%
    def point2_setup(self, t2, x2, y2, z2, roll2, pitch2, yaw2, fov2, dof2, focal2, lightsun2, animation2):    
        # use source_scenes[0] as template
        self.source_scenes.append(self.source_scenes[0])
        # Ask users for point2 details...
        self.source_times.append(t2) # ASK
        self.source_scenes[1]['camera']['position']['x'] = x2 # ASK
        self.source_scenes[1]['camera']['position']['y'] = y2 # ASK
        self.source_scenes[1]['camera']['position']['z'] = z2 # ASK
        self.source_scenes[1]['camera']['orientation']['roll'] = roll2 # ASK
        self.source_scenes[1]['camera']['orientation']['pitch'] = pitch2 # ASK
        self.source_scenes[1]['camera']['orientation']['yaw'] = yaw2 # ASK
        self.source_scenes[1]['sky']['cloudOffset']['x'] = x3 # ASK
        self.source_scenes[1]['sky']['cloudOffset']['y'] = y3 # ASK
        self.source_scenes[1]['sky']['cloudOffset']['z'] = z3 # ASK
        
        self.source_scenes[1]['sun']['azimuth'] = lightsun2
        self.source_scenes[1]['animationTime'] = animation2
        self.source_scenes[1]['camera']['fov'] = fov2 # ASK
        self.source_scenes[1]['camera']['dof'] = dof2 # ASK
        self.source_scenes[1]['camera']['focalOffset'] = focal2 # ASK
            
    #%%
    def do_interpT(self, interp_mode, smoothing_var = 1):
        # Fill the lists with data (at least what we want)
        for scene in self.source_scenes:
            self.camX.append(scene['camera']['position']['x'])
            self.camY.append(scene['camera']['position']['y'])
            self.camZ.append(scene['camera']['position']['z'])
            self.camRoll.append(scene['camera']['orientation']['roll'])
            self.camPitch.append(scene['camera']['orientation']['pitch'])
            self.camYaw.append(scene['camera']['orientation']['yaw'])
            self.lightsun.append(scene['sun']['azimuth'])
            self.animation.append(scene['animationTime'])
            self.cloudX.append(scene['sky']['cloudOffset']['x'])
            self.cloudY.append(scene['sky']['cloudOffset']['y'])
            self.cloudZ.append(scene['sky']['cloudOffset']['z'])

            self.camFoV.append(scene['camera']['fov'])
            self.camDoF.append(scene['camera']['dof'])
            self.camDoF = [999999 if x=='Infinity' else x for x in self.camDoF] # Might need to use a higher value.
            self.camfocalOffset.append(scene['camera']['focalOffset'])
        
        
        self.nframe = (self.source_times[-1] - self.source_times[0]) / self.frametime #number of frames between first and last scene
        self.tframe = np.linspace(self.source_times[0], self.source_times[-1], int(self.nframe)) #time of each frame
        
        # interp data...
        self.new_camX = self.interpT(self.source_times, self.tframe, self.camX, interp_mode)
        self.new_camY = self.interpT(self.source_times, self.tframe, self.camY, interp_mode)
        self.new_camZ = self.interpT(self.source_times, self.tframe, self.camZ, interp_mode)
        self.new_camRoll = self.interpT(self.source_times, self.tframe, self.camRoll, interp_mode)
        self.new_camPitch = self.interpT(self.source_times, self.tframe, self.camPitch, interp_mode)
        self.new_camYaw = self.interpT(self.source_times, self.tframe, self.camYaw, interp_mode)
        self.new_lightsun = self.interpT(self.source_times, self.tframe, self.lightsun, interp_mode)
        self.new_animation = self.interpT(self.source_times, self.tframe, self.animation, interp_mode)
        self.new_cloudX = self.interpT(self.source_times, self.tframe, self.cloudX, interp_mode)
        self.new_cloudY = self.interpT(self.source_times, self.tframe, self.cloudY, interp_mode)
        self.new_cloudZ = self.interpT(self.source_times, self.tframe, self.cloudZ, interp_mode)
        
        self.new_camFoV = self.interpT(self.source_times, self.tframe, self.camFoV, interp_mode) # might go negative
        self.new_camDoF = self.interpT(self.source_times, self.tframe, self.camDoF, interp_mode) # might go negative
        self.new_camfocalOffset = self.interpT(self.source_times, self.tframe, self.camfocalOffset, interp_mode) # might go negative
    
        self.post_interpT_smooth(smoothing_var)
        self.post_interpT_round(self.decimals)
        
        if interp_mode != 'slinear':
            self.post_interpT_trim()
        
        
        
    #%%    
    def post_interpT_smooth(self, smoothing_var = 1):
        #Data smoothing
        self.new_camX = self.smooth(self.new_camX,smoothing_var)
        self.new_camY = self.smooth(self.new_camY,smoothing_var)
        self.new_camZ = self.smooth(self.new_camZ,smoothing_var)
        self.new_camRoll = self.smooth(self.new_camRoll,smoothing_var)
        self.new_camPitch = self.smooth(self.new_camPitch,smoothing_var)
        self.new_camYaw = self.smooth(self.new_camYaw,smoothing_var)
        self.new_lightsun = self.smooth(self.new_lightsun,smoothing_var)
        self.new_animation = self.smooth(self.new_animation,smoothing_var)
        self.new_cloudX = self.smooth(self.new_cloudX,smoothing_var)
        self.new_cloudY = self.smooth(self.new_cloudY,smoothing_var)
        self.new_cloudZ = self.smooth(self.new_cloudZ,smoothing_var)
        
        self.new_camFoV = self.smooth(self.new_camFoV,smoothing_var)
        self.new_camDoF = self.smooth(self.new_camDoF,smoothing_var)
        self.new_camfocalOffset = self.smooth(self.new_camfocalOffset,smoothing_var)
    
    #%%
    def post_interpT_round(self, decimals):
        # Data rounding... (to avoid any issues with Chunky)
        self.new_camX = np.round(self.new_camX,decimals)
        self.new_camY = np.round(self.new_camY,decimals)
        self.new_camZ = np.round(self.new_camZ,decimals)
        self.new_camRoll = np.round(self.new_camRoll,decimals)
        self.new_camPitch = np.round(self.new_camPitch,decimals)
        self.new_camYaw = np.round(self.new_camYaw,decimals)
        self.new_lightsun = np.round(self.new_lightsun,decimals)
        self.new_animation = np.round(self.new_animation,decimals)
        self.new_cloudX = np.round(self.new_cloudX,decimals)
        self.new_cloudY = np.round(self.new_cloudY,decimals)
        self.new_cloudZ = np.round(self.new_cloudZ,decimals)
        
        self.new_camFoV = np.round(self.new_camFoV,decimals)
        self.new_camDoF = np.round(self.new_camDoF,decimals)
        self.new_camfocalOffset = np.round(self.new_camfocalOffset,decimals)
        
    #%%
    def post_interpT_trim(self):
        trim_idx = np.where( (self.tframe > self.source_times[1]) * (self.tframe < self.source_times[-2]) )[0]
        #trim_tframe = [self.tframe[i] for i in trim_idx]
        
        self.new_camX = [self.new_camX[i] for i in trim_idx]
        self.new_camY = [self.new_camY[i] for i in trim_idx]
        self.new_camZ = [self.new_camZ[i] for i in trim_idx]
        self.new_camRoll = [self.new_camRoll[i] for i in trim_idx]
        self.new_camPitch = [self.new_camPitch[i] for i in trim_idx]
        self.new_camYaw = [self.new_camYaw[i] for i in trim_idx]


        self.new_cloudX = [self.new_cloudX[i] for i in trim_idx]
        self.new_cloudY = [self.new_cloudY[i] for i in trim_idx]
        self.new_cloudZ = [self.new_cloudZ[i] for i in trim_idx]

        #misc
        self.new_lightsun = [self.new_lightsun[i] for i in trim_idx]
        self.new_animation = [self.new_animation[i] for i in trim_idx]        
        self.new_camFoV = [self.new_camFoV[i] for i in trim_idx]
        self.new_camDoF = [self.new_camDoF[i] for i in trim_idx]
        self.new_camfocalOffset = [self.new_camfocalOffset[i] for i in trim_idx]

    def chunkycloudhandler(self):
        #somehow write the idlist to a json file
        for i in range(len(self.nframe)):
            self.submit_json(fname, octree, emittergrid, samples)
            
        self.get_json_image(idlist[fname], samples, '/snapshot/' + fname + '.png')
        list_to_json = json.dumps(idlist)

        print(list_to_json)


    def submit_json(self, interpnum, octreenum, emittergridnum, samples1):
        url = "https://api.chunkycloud.lemaik.de/jobs"
        payload={'X-Api-Key': 'APIKEY1',
        'chunkyVersion': '2.x',
        'transient': 'true',
        'targetSpp': samples1}
        files=[
            ('scene',(interpnum,open('E:/Program Files/.chunky/ChunkyAnimationAutomation/' + interpnum,'rb'),'application/json')),
            ('octree',(octreenum + '.octree2',open('E:/Program Files/.chunky/ChunkyAnimationAutomation/' + octreenum + '.octree2','rb'),'application/octet-stream')),
            ('emittergrid',(emittergridnum + '.emittergrid',open('E:/Program Files/.chunky/ChunkyAnimationAutomation/' + emittergridnum + '.emittergrid','rb'),'application/octet-stream'))
        ]

        headers = {}

        response = requests.request("POST", url, headers=headers, data=payload, files=files)
        print(response.text)
        #write response['id'] to json file here:
        responseid = response['id']

        self.idlist.append(fname: responseid) #append to json array



    def get_json_image(self, json_id, targetspp, targetpath):
        contents = urllib.request.urlopen("http://chunkycloud.lemaik.de/jobs/" + json_id).read()
        currentspp = contents['spp']
        if currentspp >= targetspp:
            #download the finished picture
            img = urllib.request.urlopen("https://api.chunkycloud.lemaik.de/jobs/" + json_id + "/latest.png?").read()

            imgURL = "https://api.chunkycloud.lemaik.de/jobs/" + json_id + "/latest.png?"
            urllib.request.urlretrieve(imgURL, targetpath)
        elif:
            print(currentspp)


    #%%    
    def save_json(self, SPP = 0, RD = 0, res_w = 0, res_h = 0):
        for i in range(len(self.new_camX)):
            temp_scene = self.source_scenes[0]
            #camera
            temp_scene['camera']['position']['x'] = self.new_camX[i]
            temp_scene['camera']['position']['y'] = self.new_camY[i]
            temp_scene['camera']['position']['z'] = self.new_camZ[i]
            temp_scene['camera']['orientation']['roll'] = self.new_camRoll[i]
            temp_scene['camera']['orientation']['pitch'] = self.new_camPitch[i]
            temp_scene['camera']['orientation']['yaw'] = self.new_camYaw[i]
            temp_scene['camera']['fov'] = self.new_camFoV[i]
            temp_scene['camera']['dof'] = self.new_camDoF[i]
            temp_scene['camera']['focalOffset'] = self.new_camfocalOffset[i]

            #clouds
            temp_scene['sky']['cloudOffset']['x'] = self.new_camX[i]
            temp_scene['sky']['cloudOffset']['y'] = self.new_camX[i]
            temp_scene['sky']['cloudOffset']['z'] = self.new_camX[i]

            #misc
            temp_scene['animationTime'] = self.new_animation[i]
            temp_scene['sun']['azimuth'] = self.new_lightsun[i]

            
            if SPP != 0:
                temp_scene['spp'] = SPP
                
            if RD != 0:
                temp_scene['rayDepth'] = RD
                
            if res_w != 0 and res_h != 0:
                temp_scene['width'] = res_w
                temp_scene['heigh'] = res_h
            
            name = 'interpolation-' + str(i).zfill( len(str(int(self.nframe))) ) # insure padding in file explorer
            temp_scene['name'] = name
            octree = 'interpolation-000'
            emittergrid = 'interpolation-000'
            samples = 100
            
            fname = name + '.json'
            self.jsonsave(temp_scene, fname)





#%%
if __name__ == '__main__':
    print("interpT - tldr blame jackjt8")
    print("debug code still present...")
    main()

