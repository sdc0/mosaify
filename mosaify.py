import cv2
import math
import numpy as np
from argparse import ArgumentParser
import matplotlib.pyplot as plt
import os
from bitstring import BitStream, BitArray
from dataclasses import dataclass

@dataclass
class MosaicInstructions:
    greyscale: bool
    threads: int
    crosses: int
    data: list

    def writeMosaic(self, file: str):
        """
        writes mosaic instructions to a file

        args:
            file: path to file to write to
        """

        bits = BitStream()

        # write header
        bits.append("0xdeadbeef")
        bits.append("int:32=" + str(self.threads))
        bits.append("int:32=" + str(self.crosses))
        bits.append("bool=" + str(self.greyscale))
        bits.append("0xdeadbeef")

        # write data
        if self.greyscale:
            for array in self.data:
                bits.append(array)
        else:
            for channel in self.data:
                for array in channel:
                    bits.append(array)

        if not os.path.exists(os.path.dirname(file)): os.makedirs(os.path.dirname(file))

        with open(file, "wb") as f:
            bits.tofile(f)

    def readMosaic(file: str):
        """
        reads mosaic instructions from a file

        args:
            file: file to read from

        returns:
            MosaicInstruction from parsed file
        """

        with open(file, "rb") as f:
            bits = BitStream(f.read())

        # read header
        assert bits.read("uint:32") == 0xdeadbeef, "file header does not start correctly"

        threads = bits.read("int:32")
        crosses = bits.read("int:32")
        greyscale = bits.read("bool")

        assert bits.read("uint:32") == 0xdeadbeef, "file header does not end correctly"

        # read data
        data = []
        if greyscale:
            for i in range(crosses):
                data.append(BitArray(bits.read("bits:" + str(threads))))
        else:
            for c in range(3):
                data.append([])
                for i in range(crosses):
                    data[c].append(BitArray(bits.read("bits:" + str(threads))))

        return MosaicInstructions(greyscale, threads, crosses, data)
    
    def displayMosaic(self, save=None):
        """
        Displays a mosaic with OpenCV
        """

        if self.greyscale:
            img = np.zeros((self.crosses, self.threads))
            for i in range(len(self.data)):
                for j in range(len(self.data[i])):
                    img[i][j] = 255 if (self.data[i][j] == 0) else 0
        else:
            img = np.zeros((3, self.crosses, self.threads))
            for c in range(3):
                for i in range(self.crosses):
                    for j in range(self.threads):
                        img[c][i][j] = 255 if (self.data[c][i][j] == 0) else 0
        
        cv2.imshow("Mosaic", np.moveaxis(img, 0, -1) if not self.greyscale else img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        if save is not None:
            print(img.shape)
            cv2.imwrite(save, np.moveaxis(img, 0, -1) if not self.greyscale else img)

    def __str__(self):
        return f"{'Greyscale' if self.greyscale else 'RGB'} mosaic with {self.threads} vertical threads and {self.crosses} horizontal crosses"
    
def getParser():
    """
    Creates a parser for user input

    returns:
        user input parser
    """

    parser = ArgumentParser()

    parser.add_argument("-rgb", "--rgb", dest="greyscale", action="store_false", help="Set mode to RGB")

    parser.add_argument("-i", "--input", type=str, help="Path to input file")
    parser.add_argument("-o", "--output", type=str, help="Path to output file")

    parser.add_argument("-t", "--threads", type=int, help="Number of vertical threads")
    parser.add_argument("-c", "--crosses", type=int, help="Number of horizontal threads across the vertical ones")

    parser.add_argument("-th", "--threshold", default=200, type=int, help="Upper bound for what colors will be counted as positive")

    parser.add_argument("-d", "--display", action="store_true", help="Program will display mosaic file after creating file")
    parser.add_argument("-s", "--save", action="store_true", help="Save image produced by display argument")

    return parser

def mosaify(image: str, greyscale: bool, threads: int, crosses: int, threshold: int) -> MosaicInstructions:
    """
    function that converts an image to a mosaic instruction bitstream

    args:
        image: path to image to convert
        greyscale: bool to determine if greyscale (True) or RGB (False)
        threads: number of vertical threads running in the loom
        crosses: number of horizontal threads will be put across the threads

    returns:
        MosaicInstruction with all encoded data
    """

    img = np.array(cv2.imread(image, 0)) if greyscale else np.array(cv2.imread(image))
    (row, col) = img.shape[0:2]

    v = row / crosses
    h = col / threads

    reduced_img = []

    # downsample image to bitarrays
    if greyscale:
        for i in range(crosses):
            reduced_img.append(BitArray())
            for j in range(threads):
                slice = img[math.floor(i * v):math.floor((i + 1) * v), math.floor(j * h):math.floor((j + 1) * h)]
                reduced_img[i].append("bool=" + str(slice.sum() / slice.size < threshold))
    else:
        for channel in range(3):
            reduced_img.append([])
            for i in range(crosses):
                reduced_img[channel].append(BitArray())
                for j in range(threads):
                    slice = img[math.floor(i * v):math.floor((i + 1) * v), math.floor(j * h):math.floor((j + 1) * h), :]
                    reduced_img[channel][i].append("bool=" + str(slice[:, :, channel].sum() / slice[:, :, channel].size < threshold))

    return MosaicInstructions(greyscale, threads, crosses, reduced_img)

if __name__ == "__main__":
    parser = getParser()
    args = parser.parse_args()
    
    assert args.input is not None, f"provide an input {'image' if args.output is not None else 'mosaic'} file"
    
    if args.output is not None: # in create mosaic mode
        assert os.path.isdir(args.output), "pass a directory to output argument"
        assert args.input.split(".")[-1] in ["bmp", "dib", "jpeg", "jpg", "jpe", "jp2", "png", "webp", "pbm", "pgm", "ppm", "pxm", "pnm", "sr", "ras", "tiff", "tif", "exr", "hdr", "pic"], "provide an image file of accepted format"
        
        assert args.threads is not None, "provide a thread count"
        if args.crosses is None:
            args.crosses = args.threads
    	
    	# get output with file name
        out_path = os.path.join(args.output, args.input.split("/")[-1].split(".")[0] + ".mosaic")
        
        # create and write mosaic
        mosaic = mosaify(args.input, args.greyscale, args.threads, args.crosses, args.threshold)
        mosaic.writeMosaic(out_path)
    
        # display mosaic
        if args.display:
            mosaic.displayMosaic(os.path.join(os.path.dirname(out_path), os.path.basename(out_path).split('.')[0] + '.png') if args.save else None)
    else:
        if args.display:
            assert args.input.split(".")[-1] in ["mosaic"], "provide a .mosaic file to display"
            MosaicInstructions.readMosaic(args.input).displayMosaic(os.path.join(os.path.dirname(args.input), os.path.basename(args.input).split('.')[0] + '.png') if args.save else None)
