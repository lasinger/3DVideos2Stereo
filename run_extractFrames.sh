#!/bin/bash

video_name=$1
parent_folder_name="sbs_frames"
data_path="mkv_sbs/"
video_filename="${video_name}.mkv"
video_path="${data_path}${video_name}/"
output_frames_left="image_left/${video_name}/"
output_frames_right="image_right/${video_name}/"
output_meta="image_meta/${video_name}/"
output_frames_raw="image_raw/${video_name}/"
chapter_file="${video_path}chapter.txt"
chap_idx="0"
#

mkdir -p $output_frames_left
mkdir -p $output_frames_right
mkdir -p $output_meta
mkdir -p $output_frames_raw

#get cut information
ffprobe -show_frames -of compact=p=0 -f lavfi "movie=${video_path}${video_filename},select=gt(scene\,0.1)" >> ${output_meta}shots.txt 2>&1 

#per chapter extract raw images (full frame rate, full resolution, no clipping, left and right image combined in one image sbs)
#additional log info is stored
while IFS='' read -r line
do
	((chap_idx++))
	startTs=${line%%,*}
	endTs=${line##*,}
	duration=$(awk '{print $1-$2-$3}' <<< "$endTs $startTs 0.1")
	echo "$startTs $endTs $duration"
	mkdir -p ${output_frames_raw}chapter${chap_idx}/
	ffmpeg -ss $startTs -i ${video_path}${video_filename} -to $endTs -copyts -vf showinfo -qscale:v 1 ${output_frames_raw}chapter${chap_idx}/out%08d.jpg </dev/null >> ${output_meta}log${chap_idx}.txt 2>&1
done < "$chapter_file"

# extract clipped left and right images from raw images (clipping is done to remove black borders)
# see python script for parameters and details
echo ${output_frames_raw}
for subfolder in ${output_frames_raw}*/ ; do
	b_subfolder=$(basename $subfolder)
	echo $b_subfolder
	mkdir -p ${output_frames_left}${b_subfolder}/
	mkdir -p ${output_frames_right}${b_subfolder}/
	python splitImagesChapters.py --raw ${output_frames_raw}${b_subfolder}/ --outLeft ${output_frames_left}${b_subfolder}/ --outRight ${output_frames_right}${b_subfolder}/ --txtList ${output_meta}${b_subfolder}.txt --paddingAR 280 --paddingAR_side 40
done

# copy chapter info and remove uneeded files (esp raw files), move files back to server
cp ${chapter_file} ${output_meta}timingChapters.txt
rm -r ${output_frames_raw}

