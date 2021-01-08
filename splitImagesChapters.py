from PIL import Image
import argparse
import glob
import os
import multiprocessing
from joblib import Parallel, delayed
from tqdm import tqdm

parser = argparse.ArgumentParser(
    description='split sbs (side-by-side) stereo images.')

parser.add_argument('--raw', type=str,
                    help='path to raw folder', required=True)
parser.add_argument('--outLeft', type=str,
                    help='path to left folder', required=True)
parser.add_argument('--outRight', type=str,
                    help='path to right folder', required=True)
parser.add_argument('--txtList', type=str,
                    help='path to new output img', required=True)
parser.add_argument('--paddingAR', type=int,
                    help='padding due to aspect ratio', default=0)
parser.add_argument('--paddingAR_side', type=int,
                    help='padding due to aspect ratio left/right', default=0)
parser.add_argument('--flip', type=bool,
                    help='RL instead of LR', default=False)
parser.add_argument('--numCores', type=int,
                    help='number of cores to run the extraction on', default=8)
args = parser.parse_args()


def process_single_image(args, imgPath):

    imNameSplit = imgPath.split('/')
    imName = imNameSplit[-1]
    im1 = Image.open(imgPath)

    (widthDouble, height) = im1.size

    height = height - args.paddingAR
    width = int(widthDouble/2 - args.paddingAR_side)

    result1 = Image.new('RGB', (width, height))
    result2 = Image.new('RGB', (width, height))
    if args.flip:
        result1 = im1.crop((width+args.paddingAR_side+args.paddingAR_side/2,
                            args.paddingAR/2, widthDouble-args.paddingAR_side/2, height+args.paddingAR/2))
        result2 = im1.crop(
            (args.paddingAR_side/2, args.paddingAR/2, width, height+args.paddingAR/2))
    else:
        result1 = im1.crop((args.paddingAR_side/2, args.paddingAR/2,
                            width+args.paddingAR_side/2, height+args.paddingAR/2))
        result2 = im1.crop((width+args.paddingAR_side+args.paddingAR_side/2,
                            args.paddingAR/2, widthDouble-args.paddingAR_side/2, height+args.paddingAR/2))

    result1.save(args.outLeft+imName, format='JPEG',
                 quality=85, subsampling=0, optimize=True)
    result2.save(args.outRight+imName, format='JPEG',
                 quality=85, subsampling=0, optimize=True)

    # add image pair to data list - use relative paths so the data can be moved (base dir is the folder containing the folder sbs_frames/ and sbs_videos/)
    # first get relative path

    tempL = args.outLeft.split("/")
    tempR = args.outRight.split("/")

    relativePathLeft = os.path.join(
        tempL[-4], tempL[-3], tempL[-2], tempL[-1])
    relativePathRight = os.path.join(
        tempR[-4], tempR[-3], tempR[-2], tempR[-1])

    file = open(args.txtList, "a")
    file.write(os.path.join(relativePathLeft, imName)+" " +
               os.path.join(relativePathRight, imName)+"\n")
    file.close()


def main():
    imgList = glob.glob(args.raw + "*.jpg")

    num_cores = args.numCores

    # check if chapter is very small and using multiple cores is not necessary
    if len(imgList) < 100:
        print("Current chapter is small -> using only one core.")
        num_cores = 1
    else:
        # get number of cores
        max_cores = multiprocessing.cpu_count()
        if max_cores < num_cores:
            print(
                f"Not enough cores available. Using maximum of {num_cores} cores.")
            num_cores = max_cores
        else:
            print(f"Using {args.numCores} out of {num_cores} cores.")

    inputs = tqdm(imgList)

    Parallel(n_jobs=num_cores)(
        delayed(process_single_image)(args, image) for image in inputs)


main()
