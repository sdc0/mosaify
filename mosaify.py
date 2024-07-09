from PIL import Image
import numpy as np
from argparse import ArgumentParser
import os

def debugParser():
    parser = ArgumentParser()
    parser.add_argument("-i", "--image", help="Image to file to mosaify")
    parser.add_argument("-o", "--output", help="File to write mosaic data to")
    parser.add_argument("-t", "--threads", help="Number of threads horizonntally across mosaic pattern")
    parser.add_argument("-l", "--layers", default=None, help="The number of vertical layers of thread to use, defaults to image resolution")
    parser.add_argument("-m", "--mode", choices=["rgb", "greyscale"], default="greyscale", help="Mode of mosaic, either colored or not")
    parser.add_argument("--threshold", default=128, help="Threshold for color writing, any color below is treated as white")
    return parser

def getParser():
    parser = ArgumentParser()
    parser.add_argument("-i", "--image", required=True, help="Image to file to mosaify")
    parser.add_argument("-o", "--output", required=True, help="File to write mosaic data to")
    parser.add_argument("-t", "--threads", required=True, help="Number of threads horizonntally across mosaic pattern")
    parser.add_argument("-l", "--layers", default=None, help="The number of vertical layers of thread to use, defaults to image resolution")
    parser.add_argument("-m", "--mode", choices=["rgb", "greyscale"], default="greyscale", help="Mode of mosaic, either colored or not")
    parser.add_argument("--threshold", default=128, help="Threshold for color writing, any color below is treated as white")
    return parser

def writeMosaic(mosaic, outFile, threshold):
    with open(outFile, "w") as file:
        for row in mosaic:
            for element in row:
                file.write("0" if int(element) < threshold else "1")
            file.write("\n")

def getImage(path, mode):
    img = Image.open(path)
    img = img.convert("L" if mode == "greyscale" else "RGB")
    data = np.asarray(img, dtype="int32")
    return data

def mosaifyAxis(img, dim, num):
    # img is assumed to be a numpy array of shape (h, w, c) or (h, w)
    # dim is assumed to be either 0 or 1, corresponding to h and w
    # num is assumed to be an even divisor of the current image dimension, otherwise excess is cut off
    data = img.transpose((dim, 0 if dim == 1 else 1) if len(img.shape) == 2 else (dim, 0 if dim == 1 else 1, data.shape[2]))
    newdata = np.zeros((num, data.shape[1]) if len(img.shape) == 2 else (num, data.shape[1], data.shape[2]))
    for i, group in enumerate(np.split(data[:(len(data) - (len(data) % num))], num, 0)):
        newdata[i] = np.average(group, 0)
    return newdata

if __name__ == "__main__":
    parser = getParser()
    args = parser.parse_args()
    
    '''args.image = "mosaify/imgs/testRed.png"
    args.output = "mosaify/mosaics/testRed.msc"
    args.mode = "greyscale"
    args.threshold = 100
    args.threads = 20'''
    
    if not os.path.exists(os.path.dirname(args.output)):
        os.makedirs(os.path.dirname(args.output))
    
    img = getImage(args.image, args.mode)
    
    if args.mode == "greyscale" and len(img.shape) != 2: img = img.mean(2)

    img = mosaifyAxis(img, 0, int(args.layers) if args.layers else img.shape[0])
    img = mosaifyAxis(img, 1, int(args.threads))
    
    writeMosaic(img, args.output, int(args.threshold))
    