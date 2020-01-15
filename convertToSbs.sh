#!/bin/bash

input="mkv_mvc/video1.mkv"
outputTitle="video1"
outputFolder="mkv_sbs/${outputTitle}/"

mkdir $outputFolder

ffmpeg -i ${input} 2>&1 | grep Chapter | grep start | awk '{print $4 $6}' >> ${outputFolder}chapter.txt

mkvextract tracks ${input} 0:${input}.264

wine /home/klasinge/Downloads/FRIM_x86_version_1.29/x86/FRIMDecode32 -i:mvc ${input}.264 -o - -sbs | ffmpeg -y -f rawvideo -s:v 3840x1080 -r 24000/1001 -i - -c:v libx264 ${outputFolder}${outputTitle}.mkv
rm ${input}.264
