import pickle
from math import pi, cos
import math
import datetime
import time
import gzip
import re
import os
import shutil
import argparse
from draw_png import draw_png

def sq(x): return x*x

def distanceLatLon(lat1,lon1,lat2,lon2):
    grad2rad=3.141592653589/180
    lat1*=grad2rad;lat2*=grad2rad;lon1*=grad2rad;lon2*=grad2rad
    return 6372795*2*math.asin(math.sqrt(
                             sq(math.sin((lat2-lat1)/2))+math.cos(lat1)*math.cos(lat2)*sq(math.sin((lon1-lon2)/2))
                             ));

def inBounds(lat, lon, bounds):#, bounds
    if lat<bounds[0]:return False
    if lon<bounds[1]:return False
    if lat>bounds[2]:return False
    if lon>bounds[3]:return False
    return True

t_split = time.strptime("20150612", "%Y%m%d")

def save_png_and_html(bounds, zoom, folder=None, step = None, **png_args):
    (lat0, lon0, lat1, lon1) = bounds
    #exit()
    #print(r"C:\Users\mednikov\AppData\Local\Continuum\Anaconda\python draw_png.py" +step)
    draw_png(color_step=step, **png_args)
    #os.system(r"C:\Users\mednikov\AppData\Local\Continuum\Anaconda3\python draw_png.py" +step)
    #import time
    #time.sleep(5)
    #exit()

    outF_diom = open("drawImgOnMap.html", "w")
    for line in open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates", "image_on_map.html")):
        if re.search('myMap = new ymaps.Map\("YMapsID", {center: ', line):
            outF_diom.write( re.sub("center: \[[\d\.\-,]+\], zoom: \d+",
                                    "center: [%f,%f], zoom: %d"%((lat0+lat1)/2, (lon0+lon1)/2, zoom), line) )
            
            #outF_diom.write()
            continue
        if re.search('var rectangle = new ymaps.Rectangle', line):
            #print(line)
            #new ymaps.Rectangle([[55.517470,37.290977],[55.95711439750372, 38.0048169995256]]
            outF_diom.write( re.sub("ymaps.Rectangle\([\d\.\-, \[\]]+,",
                                    "ymaps.Rectangle([[%f,%f],[%f,%f]],"%(lat0,lon0, lat1,lon1), line) )
            #outF_diom.write( 
            #outF_diom.write(re.sub("center: \[([\d\.\-,])\]", "center: %f,%f"%()))
            continue
        
        outF_diom.write(line)
    outF_diom.close()
    
    if folder is not None:
        if not os.path.isdir(folder):
            os.mkdir(folder)
        shutil.move('data.png', os.path.join(folder, 'data.png'))
        shutil.move('drawImgOnMap.html', os.path.join(folder, 'map.html'))

def simple_data_reader(f, lat_pos, lon_pos):
    #insertLatLon(55.708289, 37.578597, 10); return
    for line in open(f):
        data = line.strip().split(';')
        try:
            lat = float(data[lat_pos])
            lon = float(data[lon_pos])
            #lat, lon = (float(x) for x in data[3:5])
        except ValueError:
            continue
        yield [lat, lon, 1]

def coords2merkator(lat, lon, exc = math.sqrt(1 - pow(6356752.3142/6378137, 2))):
    x = 6378137 * math.radians(lon)
    lat = math.radians(lat)
    exc_sin = exc * math.sin(lat)
    y = 6378137 * math.log(math.tan(math.pi/4 + lat/2) *
                           pow((1 - exc_sin)/(1 + exc_sin), exc/2))
    #print("adfadf", lat, lon, y, x)
    return (y, x)

class MercatorInBounds:
    def __init__(self, bounds, meters):
        y1, x1 = coords2merkator(*bounds[:2])
        y2, x2 = coords2merkator(*bounds[2:4])
        #print(x1, y1, x2, y2), bounds)
        self.x_len = int((x2-x1)/meters) + 1
        self.y_len = int((y2-y1)/meters) + 1
        self.meters = meters
        self.x1 = x1
        self.y2 = y2
    
    def get_index(self, lat, lon):
        y, x = coords2merkator(lat, lon)
        ind_x = int((x - self.x1)/self.meters)
        ind_y = int((self.y2 - y)/self.meters)
        #print("asd", ind_x, ind_y, self.x_len, self.y_len)
        if not ((0<=ind_x<self.x_len) and (0<=ind_y<self.y_len)):
            return
        return (ind_y, ind_x)

class LinearInBounds:
    def __init__(self, bounds, meters):
        (lat0, lon0, lat1, lon1) = bounds
        heightKM=(lat1-lat0)/(1/6372.795/pi*180);
        widthKM= (lon1-lon0)/(1/6372.795/pi*180/cos((lat0+lat1)/2*pi/180))
        
        yN=int(heightKM/square_size)
        xN=int(widthKM/square_size)
        
        heightKM = yN*square_size
        widthKM  = xN*square_size
        
        print (bounds, str(xN)+" x "+str(yN)+" => %.1f, %.1f"%(widthKM, heightKM), widthKM/xN, heightKM/yN )
        
        self.lat1 = lat0 + heightKM/6372.795/pi*180;
        self.lon1 = lon0 + widthKM /6372.795/pi*180/cos((lat0+lat1)/2*pi/180)
        self.lat0 = lat0
        self.lon0 = lon0
        self.k_lat = yN / (self.lat1-self.lat0)
        self.k_lon = xN / (self.lon1-self.lon0)
        self.y_len = yN
        self.x_len = xN
        #dLat = (lat1-lat0)/yN
        #dLon = (lon1-lon0)/xN

    
    def get_index(self, lat, lon):
        if (lat>=self.lat1 or lat<self.lat0) or (lon>=self.lon1 or lon<self.lon0):
            return
    
        y = int((self.lat1 - lat)*self.k_lat)
        x = int((lon - self.lon0)*self.k_lon)
        
        return (y, x)
        
def draw_density_img(bounds, data_stream, **args):
    runTime=(time.mktime(datetime.datetime.now().timetuple()))
    
    if not args.get('output'):
        args['output'] = "res"
    if not args.get('color_step'):
        args['color_step'] = 1.
    square_size = args.get('square_size', 1000)
    zoom = args.get('zoom', 16)
    projection = args.get("projection", "mercator" if zoom<=11 else "linear")
    assert projection in ["mercator", "linear"]
    recalc = not args.get("redraw")
    #print(square_size);exit()

    def insert_value(lat, lon, v=1):
        res = calc_index(lat, lon)
        if res is None:
            return
        y, x = res
        store1[y][x] += v
        store1n[y][x] += 1
    
    projection_calculator = MercatorInBounds if projection=="mercator" else LinearInBounds
    bounds_indexer = projection_calculator(bounds, square_size)
    calc_index = bounds_indexer.get_index

    total = total_n = 0
    
    if recalc:
        print("Calculating...")
        store1 = [[0 for i in range(bounds_indexer.x_len)] for j in range(bounds_indexer.y_len)]
        store1n = [[0 for i in range(bounds_indexer.x_len)] for j in range(bounds_indexer.y_len)]
        
        for lat, lon, v in data_stream:
            insert_value(lat, lon, v)
            
        #addData(r'parkings.csv')
    
        if "density_postprocess" in args:
            func = args["density_postprocess"]
            for y in range(bounds_indexer.y_len):
                for x in range(bounds_indexer.x_len):
                    store1[y][x] = func(store1[y][x], store1n[y][x])
            
        for y in range(bounds_indexer.y_len):
            total += sum(store1[y])
            total_n += sum(store1n[y])
    
        with open(r'image.dat','wb') as wf:
            pickle.dump([bounds_indexer.x_len+1, bounds_indexer.y_len+1], wf)
            pickle.dump(store1, wf)
    
    if not os.path.isdir(args['output']):
        os.mkdir(args['output'])
    #save_png_and_html(bounds, os.path.join(args['output'], region), args['color_step'])
    save_png_args = {}
    if "colors" in args:
        save_png_args["colors"] = args["colors"]
    save_png_and_html(bounds, zoom, args['output'], args['color_step'], **save_png_args)
    
    print("Done in "+str(time.mktime(datetime.datetime.now().timetuple())-runTime)+" seconds");
    print (str(total)+", N="+str(total_n));

if __name__ == '__main__':
    command_arguments = argparse.ArgumentParser(description='Draws density image on map')
    command_arguments.add_argument('--output', help='output path')
    command_arguments.add_argument('--color_step', type=float, help='palette step')
    command_arguments.add_argument('--square_size', default=10, type=int, help='palette step')
    command_arguments.add_argument('--bounds', help='bounds as a part of route url after rtext=')
    command_arguments.add_argument('--lat_position', type=int, help='Lat position in csv', default=3)
    command_arguments.add_argument('--lon_position', type=int, help='Lon position in csv', default=4)
    args = vars(command_arguments.parse_args())
    
    if not args.get("bounds"):
        bounds = [float(x) for x in re.split("%2C|~", "55.703308%2C37.570286~55.711788%2C37.5789")] #Ленинский
        print("You haven't set bounds, I'll use some default", bounds)
        
    draw_density_img(bounds,
                     simple_data_reader("parkings.csv", args["lat_position"], args["lon_postion"]),
                     **args)