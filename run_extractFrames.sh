#!/bin/bash

video_name=$1
base_dir="/home/hauke/Master/MasterThesis/data/3dmovies/"
frame_dir="sbs_frames/"
output_dir="${base_dir}${frame_dir}"
video_filename="${video_name}.mkv"

video_path="${base_dir}sbs_videos/${video_name}/"
output_frames_left="${output_dir}image_left/${video_name}/"
output_frames_right="${output_dir}image_right/${video_name}/"
output_meta="${output_dir}image_meta/${video_name}/"
output_frames_raw="${output_dir}image_raw/${video_name}/"
chapter_file="${video_path}chapters.txt"
chap_idx="0"
#

echo "Created directories: " 
echo "    $output_frames_left"
echo "    $output_frames_right"
echo "    $output_meta"
echo "    $output_frames_raw"
echo " "

mkdir -p $output_frames_left
mkdir -p $output_frames_right
mkdir -p $output_meta
mkdir -p $output_frames_raw


#get cut information

echo "Extracting scenes from ${video_name} ..."

#ffprobe -show_frames -of compact=p=0 -f lavfi "movie=${video_path}${video_filename},select=gt(scene\,0.1)" >> ${output_meta}shots.txt 2>&1 

echo " "

#per chapter extract raw images (full frame rate, full resolution, no clipping, left and right image combined in one image sbs)
#additional log info is stored

echo "Extracting sbs images from ${video_name} into ${output_frames_raw} ..."
start_time=$(date +%s.%N)

while IFS='' read -r line
do
	((chap_idx++))
	startTs=${line%%,*}
	endTs=${line##*,}
	duration=$(awk '{print $1-$2-$3}' <<< "$endTs $startTs 0.1")
	echo "Started chapter ${chap_idx}: $startTs $endTs $duration"
	mkdir -p ${output_frames_raw}chapter${chap_idx}/
	ffmpeg -ss $startTs -i ${video_path}${video_filename} -to $endTs -copyts -vf showinfo -qscale:v 1 ${output_frames_raw}chapter${chap_idx}/out%08d.jpg </dev/null >> ${output_meta}log${chap_idx}.txt 2>&1 &
done < "$chapter_file"
wait
# Conver the time to some useful values
end_time=$(date +%s.%N)
dt=$(echo "$end_time - $start_time" | bc)
dd=$(echo "$dt/86400" | bc)
dt2=$(echo "$dt-86400*$dd" | bc)
dh=$(echo "$dt2/3600" | bc)
dt3=$(echo "$dt2-3600*$dh" | bc)
dm=$(echo "$dt3/60" | bc)
ds=$(echo "$dt3-60*$dm" | bc)

LC_NUMERIC=C printf "Total runtime: %d:%02d:%02d:%02.4f\n" $dd $dh $dm $ds

echo " "

# extract clipped left and right images from raw images (clipping is done to remove black borders)
# see python script for parameters and details
echo "Extracting left and right images from ${video_name} ..."

for subfolder in ${output_frames_raw}*/ ; do
	b_subfolder=$(basename $subfolder)
	echo $b_subfolder
	mkdir -p ${output_frames_left}${b_subfolder}/
	mkdir -p ${output_frames_right}${b_subfolder}/
	python splitImagesChapters.py --raw ${output_frames_raw}${b_subfolder}/ --outLeft ${output_frames_left}${b_subfolder}/ --outRight ${output_frames_right}${b_subfolder}/ --txtList ${output_meta}${b_subfolder}.txt --paddingAR 280 --paddingAR_side 40 --numCores 8 
done

# copy chapter info and remove uneeded files (esp raw files), move files back to server
cp ${chapter_file} ${output_meta}timingChapters.txt
rm -r ${output_frames_raw}

echo "Done!"
