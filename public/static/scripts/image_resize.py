from PIL import Image
import sys
from resizeimage import resizeimage


with open(sys.argv[1], 'r+b') as f:
    with Image.open(f) as image:
        cover = resizeimage.resize_cover(image, [int(sys.argv[2]), int(sys.argv[3])])
        cover.save(sys.argv[4], image.format)
