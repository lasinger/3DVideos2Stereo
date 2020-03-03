# 3DVideos2Stereo

The provided scripts help to extract stereo data as described in our [paper](https://arxiv.org/abs/1907.01341):

>Towards Robust Monocular Depth Estimation: Mixing Datasets for Zero-shot Cross-dataset Transfer  
René Ranftl, Katrin Lasinger, David Hafner, Konrad Schindler, Vladlen Koltun

Code for monocular depth estimation: [https://github.com/intel-isl/MiDaS](https://github.com/intel-isl/MiDaS)

## Frame Extraction

There exist multiple different formats to store stereo videos.

For our frame extraction scripts we expect videos to be stored as 1080p SBS (side-by-side) MKVs, i.e. the image resolution should be 3840x1080px (2x 1920x1080).
Additionally we extract chapter information using ffmpeg:

```
ffmpeg -i ${video}.mkv 2>&1 | grep Chapter | grep start | awk '{print $4 $6}' >> ${outputFolder}chapter.txt
```

Script to extract left and right frames: *run_extractFrames.sh*

We extracted left and right frames (on full 24fps), centrally cropped to 1880x800 --> aspect ratio 2.35:1 (original input has varying aspect ratios and thus black bars on top/bottom and sometimes left/right due to the floating window effect).

In case a video is stored in MVC format, the script *convertToSbs.sh* can be used to convert it to SBS format.

Requirements:
- [ffmpeg](https://www.ffmpeg.org/)

Addtional requirements for MVC to SBS conversion:
- [mkvtoolnix](https://mkvtoolnix.download/)
- [FRIMDecode](https://forum.doom9.org/showthread.php?t=169651) (Windows only, can be run on Linux using [wine](https://www.winehq.org/))

## Clip Extraction

To generate our 1 second clips sampled at 4fps for all training data according to our Supplementary (using shot detection but no disparity filtering) we used:
```
python genTraining_recurr.py --videoListPath 3DVideos/data/ --numRecurrent 24 --fpsRecurrent 24 --fpsSingle 4 --name training_set --blacklist testVid1,testVid2,valVid1,valVid2
```

For our validation set we used the following:
```
python genTraining_recurr.py --videoListPath 3DVideos/data/ --numRecurrent 24 --fpsRecurrent 24 --fpsSingle 1 --name validation_set --whitelist valVid1,valVid2
```

Data path and video names (for whitelist and blacklist) have to be adapted accordingly.

## Sky Computation

Please use your favorite segmenation algorithm for sky segmentation. We used Mapillary's Inplace ABN (https://github.com/mapillary/inplace_abn) and adapted *test_vistas_single_gpu.py*.
Sky should have ID 27, e.g. in *get_pred_image* you can do:
```
mask = (tensor==27)
img = Image.fromarray(mask.astype(np.uint8)*255, mode="L")
```
For faster processing we reduced the input image size from 2048 to 1024:
```
transformation = SegmentationTransform(
        1024,
        (0.41738699, 0.45732192, 0.46886091),
        (0.25685097, 0.26509955, 0.29067996),
    )
```

## Flow Computation

Please compute the backward and forward flow fields with your favorite flow algorithm (at full resolution; i.e. 1880x800).
We used PWC-Net-Plus (https://github.com/NVlabs/PWC-Net).

You can use the filelists "train.txt", "validation.txt", and "test.txt".

Please make sure that the resulting flow fields ("flow_backward" and "flow_forward") are in a similar folder structure as "image_left" and "image_right".

## Disparity and Uncertainty Computation

The filelists "train.txt", "validation.txt", and "test.txt" are constructed in a way that only "good" flow fields are to be expected. Hence, you can create the disparity and uncertainty maps without a filtering of the flow fields as follows:

```python
python get_disp_and_uncertainty.py
```

This script generates disparity and corresponding uncertainty maps and outputs them in the folders "disparity" and "uncertainty".
Please note that those disparity and uncertainty maps are at half of the resolution (940x400). This is also the resolution that we use for testing.

If you need to enable an explicit flow filtering, you can use the option "--filter".

## Data Reading

### Read Disparity

```python
disp = imageio.imread("disp.png")

offset = float(disp.meta["offset"])
scale = float(disp.meta["scale"])

disp = (offset + scale * disp).astype(np.float32)
```

### Read Uncertainty

```python
uncertainty = imageio.imread("uncertainty.png")
uncertainty = 0.1 * uncertainty
```

## Citation

Please cite our paper if you use this code in your research:
```
@article{Ranftl2019,
	author    = {Ren\'{e} Ranftl and Katrin Lasinger and David Hafner and Konrad Schindler and Vladlen Koltun},
	title     = {Towards Robust Monocular Depth Estimation: Mixing Datasets for Zero-shot Cross-dataset Transfer},
	journal   = {arXiv:1907.01341},
	year      = {2019},
}
```
## License 

MIT License 
