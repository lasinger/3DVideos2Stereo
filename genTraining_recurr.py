from __future__ import print_function
import numpy as np
import argparse
import glob
import os
import errno
import math
import cv2
from random import shuffle
from shutil import copyfile

parser = argparse.ArgumentParser(
    description="create training/test/validation sets from video list"
)

parser.add_argument("--videoListPath", type=str, help="path to videos", required=True)
parser.add_argument(
    "--fpsSingle", type=int, help="fps for single frame processing", default=2
)
parser.add_argument(
    "--numRecurrent", type=int, help="how many recurent steps", default=3
)
parser.add_argument(
    "--fpsRecurrent", type=int, help="fps for reccurent part", default=24
)
parser.add_argument(
    "--chapterTiming",
    type=str,
    help="start and end timing list for all chapters",
    default="timingChapters.txt",
)
parser.add_argument("--name", type=str, help="run name", default="training")
parser.add_argument("--blacklist", type=str, help="ignore video", default="-1")
parser.add_argument(
    "--whitelist",
    type=str,
    help="specifies list of selected videos, if not set all videos are selected",
    default="-1",
)

args = parser.parse_args()


def silentremove(filename):
    try:
        os.remove(filename)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise  # re-raise exception if a different error occurred


def processChapter_cutlist(
    video,
    chap,
    origFramerate,
    timing,
    outputFileSingle,
    cutList,
    numRecurrent,
    fpsRecurrent,
):
    videoNameSplit = video.split("/")
    videoName = videoNameSplit[-2]

    imgPathRel = videoName + "/chapter" + str(chap) + "/"

    modFrameFactorSingle = int(round(origFramerate / args.fpsSingle))

    stepRecurrent = int(round(origFramerate / fpsRecurrent))
    numRecurrent = (
        numRecurrent + stepRecurrent * 2
    )  # extra frames in case of flow estimation

    logFilename = video + "log" + str(chap) + ".txt"
    with open(logFilename, "r") as fp:
        with open(outputFileSingle, "a") as ofp_single:
            prevIdx = -1
            # iterate over log list
            for cnt, line in enumerate(fp):

                idx = line.find("pts_time:")
                if idx == -1:
                    continue

                pts_time = float(line[idx + 9 : idx + 9 + 7])
                idx2 = line.find("n:")
                frame_idx = int(line[idx2 + 2 : idx2 + 2 + 5]) + 1
                # use floor here to be on the save side
                if pts_time <= timing[0] or pts_time > math.floor(timing[1]):
                    continue
                # ignore if at cut position
                if pts_time in cutList:
                    continue
                # sequence already processed
                if frame_idx < prevIdx:
                    continue

                largerElemCutList = [
                    x for x in cutList if x > pts_time and x < timing[1]
                ]
                largerElemCutList.append(timing[1])
                cutTimeNext = min(largerElemCutList)
                smallerElemCutList = [
                    x for x in cutList if x < pts_time and x > timing[0]
                ]
                smallerElemCutList.append(timing[0])

                seqLength = (cutTimeNext - pts_time) * origFramerate
                # for long sequences jump to some point later in the same sequence
                jump = min(int(seqLength), origFramerate * 4)
                prevIdx = frame_idx + int(jump)

                # ignore if sequence to short
                if seqLength < numRecurrent * stepRecurrent:
                    continue

                imgFilename = {}

                existing = True

                for ri in range(0, numRecurrent * stepRecurrent):
                    frame_recurr = int(frame_idx + ri + 1)
                    frame_str = str(frame_recurr).zfill(8)

                    if ri % stepRecurrent != 0:
                        continue

                    ri_rec = int(ri / stepRecurrent)
                    imgFilename[ri_rec] = "out" + frame_str

                if existing == False:
                    continue

                for ri in range(stepRecurrent * 2, numRecurrent):
                    if (ri - stepRecurrent * 2) % modFrameFactorSingle == 0:
                        ofp_single.write(imgPathRel + imgFilename[ri] + "\n")


def processShotFile(video, shotFile):
    numFrames = 0
    cutList = []
    with open(video + shotFile, "r") as fp:

        for cnt, line in enumerate(fp):
            # get cuts
            idx = line.find("pkt_pts_time=")
            if idx != -1:
                numFrames = numFrames + 1
                pts_time = float(line[idx + 13 : idx + 13 + 8])
                cutList.append(pts_time)
    return cutList


def main():
    videoList = glob.glob(args.videoListPath + "*/")
    origFramerate = 24

    trainingSingleFile = (
        args.videoListPath
        + args.name
        + "_"
        + str(args.fpsSingle)
        + "fpsSingle_"
        + str(args.fpsRecurrent)
        + "fps_"
        + str(args.numRecurrent)
        + "frames"
        + "_single.txt"
    )

    silentremove(trainingSingleFile)

    for video in videoList:

        print(video)
        videoNameSplit = video.split("/")
        videoName = videoNameSplit[-2]
        if videoName in args.blacklist:
            print(videoName + " on blacklist")
            continue
        if args.whitelist != "-1" and videoName not in args.whitelist:
            print(videoName + " not on whitelist")
            continue
        print("processing " + videoName)
        cutList = processShotFile(video, "shots.txt")
        print(len(cutList))
        timingList = []
        with open(video + args.chapterTiming, "r") as fp:
            timingListTmp = fp.read().splitlines()
            for timingLine in timingListTmp:
                timingList.append([float(x) for x in timingLine.split(",")])

        chapterList = glob.glob(video + "log*.txt")
        numChapters = len(chapterList)
        validChapters = range(2, numChapters)
        trainingSet = validChapters
        for chap in trainingSet:
            processChapter_cutlist(
                video,
                chap,
                origFramerate,
                timingList[chap - 1],
                trainingSingleFile,
                cutList,
                args.numRecurrent,
                args.fpsRecurrent,
            )


main()
