#!/bin/bash

video_name=$1
base_dir="/home/hauke/Master/MasterThesis/data/3dmovies/"
input="${base_dir}mvc_videos/${video_name}.mkv"
outputTitle="${video_name}_SBS"
outputFolder="${base_dir}sbs_videos/${outputTitle}/"
FRIMDecode="/home/hauke/Master/MasterThesis/FRIM_x86_version_1.31/FRIMDecode32"

echo "Converting ${input} to SBS format."

mkdir -p $outputFolder

ffmpeg -i ${input} 2>&1 | grep Chapter | grep start | awk '{print $4 $6}' >> ${outputFolder}chapters.txt

mkvextract tracks ${input} 0:${input}.264

wine ${FRIMDecode} -i:mvc ${input}.264 -o - -sbs | ffmpeg -y -f rawvideo -s:v 3840x1080 -r 24000/1001 -i - -c:v libx264 ${outputFolder}${outputTitle}.mkv

rm ${input}.264
