from __future__ import print_function
from PIL import Image
import argparse
import glob


parser = argparse.ArgumentParser(description='split sbs (side-by-side) stereo images.')

parser.add_argument('--raw', type=str, help='path to raw folder', required=True)
parser.add_argument('--outLeft', type=str, help='path to left folder', required=True)
parser.add_argument('--outRight', type=str, help='path to right folder', required=True)
parser.add_argument('--txtList', type=str, help='path to new output img', required=True)
parser.add_argument('--paddingAR', type=int, help='padding due to aspect ratio', default=0)
parser.add_argument('--paddingAR_side', type=int, help='padding due to aspect ratio left/right', default=0)
parser.add_argument('--flip', type=bool, help='RL instead of LR', default=False)

args = parser.parse_args()

def main():
	imgList = glob.glob(args.raw + "*.jpg")

	for imgPath in imgList:
		imNameSplit = imgPath.split('/')
		imName = imNameSplit[-1]
		im1 = Image.open(imgPath)

		(widthDouble,height) = im1.size

		height = height - args.paddingAR
		width = int(widthDouble/2 - args.paddingAR_side)

		result1 = Image.new('RGB', (width, height))
		result2 = Image.new('RGB', (width, height))
		if args.flip:
			result1 = im1.crop((width+args.paddingAR_side+args.paddingAR_side/2,args.paddingAR/2,widthDouble-args.paddingAR_side/2,height+args.paddingAR/2))
			result2 = im1.crop((args.paddingAR_side/2,args.paddingAR/2,width,height+args.paddingAR/2))
		else:
			result1 = im1.crop((args.paddingAR_side/2,args.paddingAR/2,width+args.paddingAR_side/2,height+args.paddingAR/2))
			result2 = im1.crop((width+args.paddingAR_side+args.paddingAR_side/2,args.paddingAR/2,widthDouble-args.paddingAR_side/2,height+args.paddingAR/2))

		result1.save(args.outLeft+imName, format='JPEG', quality=85, subsampling=0, optimize=True)
		result2.save(args.outRight+imName, format='JPEG', quality=85, subsampling=0, optimize=True)

		# add image pair to data list
		file = open(args.txtList,"a")
		file.write(args.outLeft+imName+" "+args.outRight+imName+"\n")
		file.close()

main()
