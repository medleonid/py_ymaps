# -*- coding: UTF-8 -*-
import re
import requests
import json
import pandas as pd
import pickle

def get_coordinates_by_url(url):
    r = requests.get(url)
    #print(r.text)
    s = re.search(r'"coordinates":\[([\-\d\.,\[\]]+)\]', r.text)
    #s = re.search(r'("coordinates":\[([]+))', r.text)
    if s:
        #print(s.group(1))
        return json.loads(s.group(1))

def point_in_poly(x,y,poly):
    """ Determine if a point is inside a given polygon or not
    Polygon is a list of (x,y) pairs. This function
    returns True or False.  The algorithm is called
    the "Ray Casting Method" """
    n = len(poly)
    inside = False

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xints = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside

if __name__ == '__main__':
    url = "https://yandex.ru/maps/?um=constructor:rkITAZ89zBHDeFKKKVTTdEgNoiZ8Mc9j&source=constructor"
    map_id = re.search(r"um=constructor:([\w\-]+)&", url).group(1)
    coords = get_coordinates_by_url("https://api-maps.yandex.ru/services/constructor/1.0/js/?sid="+map_id)
    print(coords)


exit()
#{"type":"Polygon","coordinates":[[[37.63746566174305,55.81025884129423],[37.63574904797356,55.81025884129742],[37.63493365643304,55.80587228851932],[37.636188930252004,55.80545535890312],[37.638216680267256,55.80610190001287],[37.63877457974231,55.81004133797397],[37.63746566174305,55.81025884129423]]]
print(get_polygon_by_url("https://api-maps.yandex.ru/services/constructor/1.0/js/?sid=QAb_Aeh4Pi02zCnC_AgarskdLrh6teKX"))
