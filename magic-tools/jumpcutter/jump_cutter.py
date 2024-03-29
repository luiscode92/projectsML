from contextlib import closing
from PIL import Image
import subprocess
from audiotsm import phasevocoder
from audiotsm.io.wav import WavReader, WavWriter
from scipy.io import wavfile
import numpy as np
import re
import math
from shutil import copyfile, rmtree
import os
import argparse
from pytube import YouTube
import streamlit as st
import io
import tempfile


def jump_cutter(input_file, output_file, silent_threshold, sounded_speed=1.00, silent_speed=5.00, frame_margin=1, sample_rate=44100, frame_rate=30, frame_quality=3):
    # Your original script goes here, but replace the uses of args.something with corresponding parameters

    #defining utility funcitons
    def downloadFile(url):
        name = YouTube(url).streams.first().download()
        newname = name.replace(' ','_')
        os.rename(name,newname)
        return newname

    def getMaxVolume(s):
        maxv = float(np.max(s))
        minv = float(np.min(s))
        return max(maxv,-minv)

    def copyFrame(inputFrame,outputFrame):
        src = TEMP_FOLDER+"/frame{:06d}".format(inputFrame+1)+".jpg"
        dst = TEMP_FOLDER+"/newFrame{:06d}".format(outputFrame+1)+".jpg"
        if not os.path.isfile(src):
            return False
        copyfile(src, dst)
        if outputFrame%20 == 19:
            print(str(outputFrame+1)+" time-altered frames saved.")
        return True

    def inputToOutputFilename(filename):
        dotIndex = filename.rfind(".")
        return filename[:dotIndex]+"_ALTERED"+filename[dotIndex:]

    def createPath(s):
        try:
            if not os.path.exists(s):
                os.makedirs(s)
        except Exception as e:
            print(f"Creation of the directory {s} failed with error {e}")

    def deletePath(s): # Dangerous! Watch out!
        try:  
            rmtree(s,ignore_errors=False)
        except OSError:  
            print ("Deletion of the directory %s failed" % s)
            print(OSError)
    
        
    #processing args
    frameRate = frame_rate
    SAMPLE_RATE = sample_rate
    SILENT_THRESHOLD = silent_threshold
    FRAME_SPREADAGE = frame_margin
    NEW_SPEED = [silent_speed, sounded_speed]
    INPUT_FILE = input_file

    FRAME_QUALITY = frame_quality

    assert INPUT_FILE != None , "why u put no input file, that dum"
        
    if len(output_file) >= 1:
        OUTPUT_FILE = output_file
    else:
        OUTPUT_FILE = inputToOutputFilename(INPUT_FILE)


    #create temp directory
    TEMP_FOLDER = "TEMP"
    AUDIO_FADE_ENVELOPE_SIZE = 400 # smooth out transitiion's audio by quickly fading in/out (arbitrary magic number whatever)
        
    with tempfile.TemporaryDirectory() as TEMP_FOLDER:
        createPath(TEMP_FOLDER)

        #Extracting frames and audio
        command = "ffmpeg -i "+INPUT_FILE+" -qscale:v "+str(FRAME_QUALITY)+" "+TEMP_FOLDER+"/frame%06d.jpg -hide_banner"
        subprocess.call(command, shell=True)

        command = "ffmpeg -i "+INPUT_FILE+" -ab 160k -ac 2 -ar "+str(SAMPLE_RATE)+" -vn "+TEMP_FOLDER+"/audio.wav"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, _ = process.communicate()
        #st.write(output.decode())


        command = "ffmpeg -i "+TEMP_FOLDER+"/input.mp4 2>&1"
        f = open(TEMP_FOLDER+"/params.txt", "w")
        subprocess.call(command, shell=True, stdout=f)


        #Analyzing audio volume
        sampleRate, audioData = wavfile.read(TEMP_FOLDER+"/audio.wav")
        audioSampleCount = audioData.shape[0]
        maxAudioVolume = getMaxVolume(audioData)

        f = open(TEMP_FOLDER+"/params.txt", 'r+')
        pre_params = f.read()
        f.close()
        params = pre_params.split('\n')
        for line in params:
            m = re.search('Stream #.*Video.* ([0-9]*) fps',line)
            if m is not None:
                frameRate = float(m.group(1))

        samplesPerFrame = sampleRate/frameRate

        audioFrameCount = int(math.ceil(audioSampleCount/samplesPerFrame))

        hasLoudAudio = np.zeros((audioFrameCount))



        for i in range(audioFrameCount):
            start = int(i*samplesPerFrame)
            end = min(int((i+1)*samplesPerFrame),audioSampleCount)
            audiochunks = audioData[start:end]
            maxchunksVolume = float(getMaxVolume(audiochunks))/maxAudioVolume
            if maxchunksVolume >= SILENT_THRESHOLD:
                hasLoudAudio[i] = 1

        chunks = [[0,0,0]]
        shouldIncludeFrame = np.zeros((audioFrameCount))
        for i in range(audioFrameCount):
            start = int(max(0,i-FRAME_SPREADAGE))
            end = int(min(audioFrameCount,i+1+FRAME_SPREADAGE))
            shouldIncludeFrame[i] = np.max(hasLoudAudio[start:end])
            if (i >= 1 and shouldIncludeFrame[i] != shouldIncludeFrame[i-1]): # Did we flip?
                chunks.append([chunks[-1][1],i,shouldIncludeFrame[i-1]])

        chunks.append([chunks[-1][1],audioFrameCount,shouldIncludeFrame[i-1]])
        chunks = chunks[1:]


        #generating new video
        outputAudioData = np.zeros((0,audioData.shape[1]))
        outputPointer = 0

        lastExistingFrame = None
        for chunk in chunks:
            audioChunk = audioData[int(chunk[0]*samplesPerFrame):int(chunk[1]*samplesPerFrame)]
            
            sFile = TEMP_FOLDER+"/tempStart.wav"
            eFile = TEMP_FOLDER+"/tempEnd.wav"
            wavfile.write(sFile,SAMPLE_RATE,audioChunk)
            with WavReader(sFile) as reader:
                with WavWriter(eFile, reader.channels, reader.samplerate) as writer:
                    tsm = phasevocoder(reader.channels, speed=NEW_SPEED[int(chunk[2])])
                    tsm.run(reader, writer)
            _, alteredAudioData = wavfile.read(eFile)
            leng = alteredAudioData.shape[0]
            endPointer = outputPointer+leng
            outputAudioData = np.concatenate((outputAudioData,alteredAudioData/maxAudioVolume))

            #outputAudioData[outputPointer:endPointer] = alteredAudioData/maxAudioVolume

            # smooth out transitiion's audio by quickly fading in/out
            
            if leng < AUDIO_FADE_ENVELOPE_SIZE:
                outputAudioData[outputPointer:endPointer] = 0 # audio is less than 0.01 sec, let's just remove it.
            else:
                premask = np.arange(AUDIO_FADE_ENVELOPE_SIZE)/AUDIO_FADE_ENVELOPE_SIZE
                mask = np.repeat(premask[:, np.newaxis],2,axis=1) # make the fade-envelope mask stereo
                outputAudioData[outputPointer:outputPointer+AUDIO_FADE_ENVELOPE_SIZE] *= mask
                outputAudioData[endPointer-AUDIO_FADE_ENVELOPE_SIZE:endPointer] *= 1-mask

            startOutputFrame = int(math.ceil(outputPointer/samplesPerFrame))
            endOutputFrame = int(math.ceil(endPointer/samplesPerFrame))
            for outputFrame in range(startOutputFrame, endOutputFrame):
                inputFrame = int(chunk[0]+NEW_SPEED[int(chunk[2])]*(outputFrame-startOutputFrame))
                didItWork = copyFrame(inputFrame,outputFrame)
                if didItWork:
                    lastExistingFrame = inputFrame
                else:
                    copyFrame(lastExistingFrame,outputFrame)

            outputPointer = endPointer

        wavfile.write(TEMP_FOLDER+"/audioNew.wav",SAMPLE_RATE,outputAudioData)

        '''
        outputFrame = math.ceil(outputPointer/samplesPerFrame)
        for endGap in range(outputFrame,audioFrameCount):
            copyFrame(int(audioSampleCount/samplesPerFrame)-1,endGap)
        '''



        # Modified to write to a temp file first
        TEMP_OUTPUT = TEMP_FOLDER + "/output." + INPUT_FILE.split('.')[-1]
        command = "ffmpeg -framerate "+str(frameRate)+" -i "+TEMP_FOLDER+"/newFrame%06d.jpg -i "+TEMP_FOLDER+"/audioNew.wav -strict -2 "+TEMP_OUTPUT
        subprocess.call(command, shell=True)

        # Read the temp output file into memory as bytes
        with open(TEMP_OUTPUT, 'rb') as f:
            bytes = f.read()

        # Use Streamlit to create a download button for the file
        st.download_button(
            label="Download video",
            data=bytes,
            file_name=OUTPUT_FILE,
            mime='video/mp4',
        )


        deletePath(TEMP_FOLDER)




