#!/bin/bash

video_name=$1
input="/home/hauke/Master/MasterThesis/data/3dmovies/${video_name}.mkv"
outputTitle="${video_name}_SBS"
outputFolder="/home/hauke/Master/MasterThesis/data/3dmovies/sbs_videos/${outputTitle}/"
FRIMDecode="/home/hauke/Master/MasterThesis/FRIM_x86_version_1.31/FRIMDecode32"

mkdir $outputFolder

ffmpeg -i ${input} 2>&1 | grep Chapter | grep start | awk '{print $4 $6}' >> ${outputFolder}chapters.txt

mkvextract tracks ${input} 0:${input}.264

wine ${FRIMDecode} -i:mvc ${input}.264 -o - -sbs | ffmpeg -y -f rawvideo -s:v 3840x1080 -r 24000/1001 -i - -c:v libx264 ${outputFolder}${outputTitle}.mkv

rm ${input}.264
