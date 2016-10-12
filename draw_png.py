# coding=utf-8
import re
import pickle
from PIL import Image, ImageDraw

def getColor(c):
    v = (c-minV)/(maxV-minV)
    if v>1:
        #print(c,v)
        v = 1
    if v<0: v=0    
    return (int(v*255), int((1-v)*255), 0, 255)

class Palette:
    def __init__(self, filename, minV, maxV):
        img = Image.open(filename)
        img.load()
        if img.mode != "RGB": raise Exception("Can't use this image mode")
        #self.paletteLen = 
        self.palette = [img.getpixel((i,1)) for i in range(img.getbbox()[2])]
        self.minV = minV
        self.maxV = maxV
        
        #img.save("debug.png", "PNG")
    
    def getColor(self, c):
        v = (c-self.minV)/(self.maxV-self.minV)
        if v>1: v=1
        if v<=0: return False
        return self.palette[int(v*(len(self.palette)-1))]

def RGBstring2array(rgb):
    r = rgb[0:2]
    g = rgb[2:4]
    b = rgb[4:6]
    #print(r, g, b)
    return tuple(int(x, 16) for x in (r, g, b))
    
def getPaletteFixedColors(colors, minV, step):
    steps = len(colors)
    def getColor(c):
        v = int((c-minV)/step)
        if v>=steps: v=steps-1
        if v<=0: return None #v=0    
        return colors[v]
    
    return getColor

def getPaletteFixedColorsNonlinear(colors):
    steps = len(colors)
    def getColor(v):
        v/=60.
        if v<10: return colors[0]
        if v<20: return colors[1]
        if v<30: return colors[2]
        if v<50: return colors[3]
        if v<70: return colors[4]
        if v<90: return colors[5]
        return colors[6]
    
    return getColor

class DataJSReader:
    def __init__(self):
        self.x = self.y = None
        
        #self.file = open(filename)
        #self.line_n = 0
    
    def get_line_iterator(self, filename = "data.js"):
        self.line_n = 0
        with open(filename) as f:
            for line in f:
                self.line_n+=1
                if self.line_n==1:
                    s = re.search("x=(\d+), y=(\d+)", line)
                    self.x = int(s.group(1))
                    self.y = int(s.group(2))
                    print("Loading data from", filename, "size =", self.x, "x", self.y)
                    continue
                #if self.line_n > 2 + self.y:
                #    break
                if self.line_n >= 3:
                    pixels = [float(x) for x in line.strip().split(',') if re.match(r"[\d\.]+$", x)]
                    if len(pixels)!=self.x:
                        raise IndexError("We expect %d pixels but got %d at line %d"%(self.x, len(pixels), self.line_n))
                    yield pixels

class DataReader:
    def __init__(self, filename = "image.dat"):
        self.reader = open(filename, "rb")
        meta_data = pickle.load(self.reader)
        self.x, self.y = meta_data[:2]
        self.line_n = 0
    
    def get_line_iterator(self):
        for line in pickle.load(self.reader):
            self.line_n += 1
            yield line

def draw_png(**args):
    if not args.get('color_step'):
        args['color_step'] = 1
    if 'palette_min' not in args:
        args['palette_min'] = 1
    if 'square' not in args:
        args['square'] = 1
    if 'output' not in args:
        args['output'] = "data.png"
    if not args.get('colors'):    
        #colors = ["48c06b", "8ac969", "cfd463", "fae059", "f5b74a", "da6034", "c92721"] # от зелёного к красному
        colors = ["B9FFA0", "88EFD9", "6298EA", "6C4FFF", "C030E5", "FF1000", "090909"] #бирюзовый, фиолетовый, красный, чёрный
        #colors = ["B7FFE3", "8CA8FF", "5E71FF", "9F68FF", "9F68FF", "FF1000", "090909"]
        #colors = ["8ac969", "cfd463", "fae059", "f5b74a", "da6034", "c92721", "200000"]
        args['colors'] = [RGBstring2array(x) for x in colors]
        
    if args.get('palette'):
        if args.get('find_palette_max'):
            from numpy import percentile
            def get_pixel_values_in_list(filename = "data.js"):
                res = []
                for pixels in DataReader().get_line_iterator():
                    res += pixels
                print("max is", max(res))    
                return res    
                    
            args['palette_min']=0
            args['palette_max']=percentile(get_pixel_values_in_list(), args['find_palette_max'])
            print("find_palette_max gave palette_max =", args['palette_max'])
            #exit()
            
        if not args.get('palette_max'):
            raise Exception("If you use palette you must also spesify the maximum value")
        getColor = Palette(args['palette'], args['palette_min'], args['palette_max']).getColor
    else:    
        getColor = getPaletteFixedColors(args['colors'], 0, args['color_step'])
    #getColor = getPaletteFixedColors(colors, 0, 1)   
    #getColor = getPaletteFixedColorsNonlinear(colors) ; print("Костыльная градация без учёта параметров вызова")
    #palette = Palette(r'palettes\palette-12a.png', 60*60/4., 60*60/4.*8)
    
    
    reader = DataReader()
    image = None
    
    if args['square']>1:
        square = args['square']
        print("Square = ", square)
        def put_square(image, ij, c):
            i0, j0 = ij
            for i in range(i0*square, (i0+1)*square):
                for j in range(j0*square, (j0+1)*square):
                    image.putpixel((i,j),c)
        
        for pixels in reader.get_line_iterator():
            if image is None:
                image = Image.new("RGBA", (reader.x*square, reader.y*square), (0,0,0,0))
            for i, c in enumerate(pixels):
                c = getColor(c)
                if c:
                    #image.putpixel((i,lineN-3), palette.getColor(c)+(255,))
                    put_square(image, (i, reader.line_n-3), c+(255,))
    else:
        for pixels in reader.get_line_iterator():
            if image is None:
                image = Image.new("RGBA", (reader.x, reader.y), (0,0,0,0))
            for i, c in enumerate(pixels):
                c = getColor(c)
                if c:
                    #image.putpixel((i,lineN-3), palette.getColor(c)+(255,))
                    #print(i, reader.line_n, reader.x, reader.y)
                    try:
                        image.putpixel((i, reader.line_n), c+(255,))
                    except IndexError as e:
                        print("IndexError", i, reader.line_n, reader.x, reader.y)
                        raise e
                        
    
    image.save(args['output'], "PNG")
    #image.close()

if __name__ == '__main__':
    import argparse
    
    command_arguments = argparse.ArgumentParser(description='Draws image')
    command_arguments.add_argument('--color_step', type=float, default=10, help='palette step in minutes')
    command_arguments.add_argument('--palette', help='palette file, the first row of pixels will be used')
    command_arguments.add_argument('--colors', nargs='+', help='give a list of colors like B9FFA0 88EFD9 6298EA 6C4FFF C030E5 FF1000')
    command_arguments.add_argument('--find_palette_max', nargs='?', const=100, type=float, help='sets the maximim value as a fractile of the data, default is 100, which is 100% fractile, i.e. max value')
    command_arguments.add_argument('--palette_max', type=float, help='maximum value of the palette')
    command_arguments.add_argument('--palette_min', type=float, default=0, help='minimum value of the palette')
    command_arguments.add_argument('--square', type=int, default=1, help='put each pixel as a squeare with given size')
    command_arguments.add_argument('--output', default="data.png", help='output filename')
    
    args = vars(command_arguments.parse_args()) #'-file yes.csv'.split())
    
    draw_png(**args)