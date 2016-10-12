# -*- coding: UTF-8 -*-
import math
import re
import os
import sys

def utf8reader(filename, **args):
    if sys.version_info[0]>=3:
        args["encoding"] = "utf-8"
        for line in open(filename, **args):
            yield line
    else:
        for line in open(filename, **args):
            yield line.decode("utf-8")

class Utf8Writer:
    def __init__(self, filename, **args):
        if sys.version_info[0]>=3:
            args["encoding"] = "utf-8"
        self.file = open(filename, "w", **args)
    
    def write(self, v):
        if sys.version_info[0]>=3:
            self.file.write(v)
        else:
            self.file.write(v.encode("utf-8"))
    
    def close(self):
        self.file.close()


class MapInHTML:
    def __init__(self, filename, **args):
        #args may be
        #center
        #zoom
        #if 'my_template' in args:
        #    raise Exception("Please change 'my_template' to 'template' arg name")
        self.result_f = None #нужно, чтобы если следующая строка вылетит с Exception в __del__ всё же был self.result_f
        
        templates_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates")
        template_filename = (args['my_template'] if 'my_template' in args
                        else os.path.join(templates_dir, args['template']) if 'template' in args
                        else os.path.join(templates_dir, 'general.html'))
            
        self.template_f = utf8reader(template_filename)
        self.result_f = Utf8Writer(filename)
        
        for line in self.template_f:
            self.result_f.write(line)
            if(re.match("//startRewriteFromHere", line)):
                break
        else:
            raise Exception("Looks like a problem in template file")
      
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
        for line in self.template_f:
            if skipping:
                if re.match("//endRewriteHere", line):
                    skipping = False
                else:
                    continue
            self.write(line)
        if skipping:
            raise Exception("Looks like a problem in template file")
            
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
        if sys.version_info[0]>=3:
            t = str(t)
        else:
            t = unicode(t)    
        #t = str(t)
        t = re.sub('[\r\n]+',' ', t)
        t = re.sub(r'\\','\\\\', t)
        t = re.sub('"', r"\"", t)
        return '"' + t + '"'

    def params_parser(self, params, which_color="fillColor"):
        param1 = param2 = ""

        if 'text' in params:
            param1 += 'balloonContent: %s, '%self.text_for_js(params['text'])
        if 'balloon_content' in params:
            param1 += 'balloonContent: %s, '%self.text_for_js(params['balloon_content'])
        if 'hint_content' in params:
            param1 += 'hintContent: %s, '%self.text_for_js(params['hint_content'])
        if 'icon_content' in params:
            param1 += 'iconContent: %s, '%self.text_for_js(params['icon_content'])
        if 'icon_caption' in params:
            param1 += 'iconCaption: %s, '%self.text_for_js(params['icon_caption'])

        if 'color' in params:
            param2 += '%s: %s, '%(which_color, self.text_for_js(params['color']))
        if 'stroke_width' in params:
            param2 += 'strokeWidth: %.0f, '%params['stroke_width']
        if 'stroke_opacity' in params:
            param2 += 'strokeOpacity: %.3f, '%params['stroke_opacity']            
        if 'stroke_color' in params:
            param2 += 'strokeColor: %s, '%self.text_for_js(params['stroke_color'])
        if 'fill_opacity' in params:
            param2 += 'fillOpacity: %.3f, '%params['fill_opacity']            
        if 'fill_color' in params:
            param2 += 'fillColor: %s, '%self.text_for_js(params['fill_color'])
            
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

    def rectangle(self, coords, **params):
        self.find_center(coords)
        param1, param2 = self.params_parser(params, "fillColor")
        self.write('myMap.geoObjects.add(new ymaps.Rectangle([%s], {%s}, {%s}));\n'%
                                 (",".join("[%f,%f]"%(c[0], c[1]) for c in coords),
                                  param1, param2))


if __name__ == '__main__':
    drawer = MapInHTML("draw_on_map_test.html", zoom=9)
    drawer.placemark([57, 35.5], text="test", color="#FF0000")
    drawer.circle([57.5, 35], 3000, text=u"русский test circle", color="#0000FF40")
    drawer.polyline([[57, 35], [57.5, 35], [57, 35.5]])

    s = 'Full list of icon style presets <A href="https://tech.yandex.ru/maps/doc/jsapi/2.1/ref/reference/option.presetStorage-docpage" target="blank">here</A>'
    drawer.placemark([57, 35], text=s, preset="islands#greenDotIconWithCaption",
                     icon_caption="Click me", icon_caption_max_width = 100)

    drawer.close()
    