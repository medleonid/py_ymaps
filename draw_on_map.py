# -*- coding: UTF-8 -*-
import math
import re
import os

class MapInHTML:
    def __init__(self, filename, **args):
        #args may be
        #center
        #zoom
        self.template_f = open(os.path.dirname(os.path.realpath(__file__))+'/drawOnMapTemplate.html','r');
        self.result_f = open(filename, 'w', encoding='utf-8-sig'); #
        
        while True:
            line = self.template_f.readline()
            if not line:
                raise Exception("Looks like a problem in template file")
            self.result_f.write(line)
            if(re.match("//startRewriteFromHere", line)):
                break
      
        center = args.get('center')
        zoom = args.get('zoom', 12)
            
        if center:
            self.write(self.get_map_header(center, zoom))
            self.center_found = True
        else:
            self.center_found = False
            self.zoom = zoom

    def close(self):
        skipping = True
        while True:
            line = self.template_f.readline()
            if not line:
                if skipping:
                    raise Exception("Looks like a problem in template file")
                else:
                    break
            if skipping:
                if re.match("//endRewriteHere", line):
                    skipping = False
                else:
                    continue
            self.write(line)    
        self.template_f.close()
        self.result_f.close()
        self.result_f = None
    
    def __del__(self):
        if self.result_f:
            self.close()

    def find_center(self, coords):
        if self.center_found:
            return
        self.write(self.get_map_header(coords[0], self.zoom))
        self.center_found = True
    
    def write(self, code):
        self.result_f.write(code)
       
    def get_map_header(self, center_coords, zoom):
        return ('var myMap = new ymaps.Map("map", '+
                '{center: [%f, %f], zoom: %d});\n'%(
                center_coords[0], center_coords[1], zoom))
    
    def text_for_js(self, t):
        t = str(t)
        t = re.sub(r'\\','\\\\', t)
        t = re.sub('"', r"\"", t)
        return '"' + t + '"'

    def params_parser(self, params, which_color="fillColor"):
        param1 = param2 = ""

        if 'text' in params:
            param1 += 'balloonContent: %s, '%self.text_for_js(params['text'])
        if 'color' in params:
            param2 += '%s: %s, '%(which_color, self.text_for_js(params['color']))
        if 'stroke_width' in params:
            param2 += 'strokeWidth: %.0f, '%params['stroke_width']
        if 'stroke_opacity' in params:
            param2 += 'strokeOpacity: %.3f, '%params['stroke_opacity']            
            
        return (param1, param2)
    
    
    def placemark(self, coord, **params):
        self.find_center([coord])
        param1, param2 = self.params_parser(params, "iconColor")
        if 'icon_color' in params:
            param2 += "iconColor: %s, "%text_for_js(params['icon_color'])
        if 'icon_caption' in params:
            param1 += "iconCaption: %s, "%self.text_for_js(params['icon_caption'])
        if 'preset' in params:
            param2 += "preset: %s, "%self.text_for_js(params['preset'])
        if 'icon_caption_max_width' in params:
            param2 += "iconCaptionMaxWidth: %s, "%self.text_for_js(params['icon_caption_max_width'])
            
        self.write('myMap.geoObjects.add(new ymaps.Placemark([%f, %f],'%(coord[0], coord[1]) +
                   '{%s}, {%s}));\n'%(param1, param2))

    def circle(self, coord, radius, **params):
        self.find_center([coord])
        if 'stroke_width' not in params:
            params['stroke_width'] = 0
        param1, param2 = self.params_parser(params, "fillColor")
            
        self.write('myMap.geoObjects.add(new ymaps.Circle([[%f, %f], %f],'%(coord[0], coord[1], radius) +
                   '{%s}, {%s}));\n'%(param1, param2))

    def polyline(self, coords, **params):
        self.find_center(coords)
        param1, param2 = self.params_parser(params, "strokeColor")
            
        self.write('myMap.geoObjects.add(new ymaps.Polyline([%s], {%s}, {%s}));\n'%
                                 (",".join("[%f,%f]"%(c[0], c[1]) for c in coords),
                                  param1, param2))


if __name__ == '__main__':
    drawer = MapInHTML("draw_on_map_test.html", zoom=9)
    drawer.placemark([57, 35.5], text="test", color="#FF0000")
    drawer.circle([57.5, 35], 3000, text="test circle", color="#00FF00")
    drawer.polyline([[57, 35], [57.5, 35], [57, 35.5]])

    #full list of presets
    #https://tech.yandex.ru/maps/doc/jsapi/2.1/ref/reference/option.presetStorage-docpage
    drawer.placemark([57, 35], text="test", preset="islands#blueDotIconWithCaption",
                     icon_caption="Click me", icon_caption_max_width = 100)

    drawer.close()
    