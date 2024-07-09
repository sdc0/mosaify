from PIL import Image
import numpy as np
from mosaify import getParser, debugParser

def displayMosaic(path, threads, img_size):
    mosaic = np.ndarray((img_size[0], img_size[1]))
    
    with open(path, "r") as file:
        text = file.readlines()
        
    thread_expand = (img_size[0] - (img_size[0] % threads)) // threads
    for i, row in enumerate(text):
        row = row.strip()
        for j, char in enumerate(list(row)):
            for k in range(i*thread_expand, (i+1)*thread_expand):
                mosaic[k][j] = int(char) * 255
            
    img = Image.fromarray(mosaic, "L")
    img.show()
    #for row in mosaic: print(row)        
    
if __name__ == "__main__":
    parser = debugParser()
    args = parser.parse_args()
    
    args.image = "mosaify/imgs/testRed.png"
    args.output = "mosaify/mosaics/testRed.msc"
    args.mode = "greyscale"
    args.threshold = 100
    args.threads = 20
    
    displayMosaic(args.output, args.threads, (225, 225))