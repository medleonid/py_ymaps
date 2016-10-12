# -*- coding: UTF-8 -*-
import re
import time
import pickle

if 0: #color from hex 2 dec
    s = "#b4281e"
    for i in range(3):
        ss = s[i*2+1: (i+1)*2+1]
        print(ss, int(ss, 16))
    exit()        

#FILTER_WEEKDAYS = False#True

with open("heatmap/data.js", "w", encoding="utf-8") as wf:
    wf.write("var data = [\n")
    for line in open("usefull.csv", encoding="utf-8-sig"):
        data = line.strip().split(';')
        #lat, lon, text, _, dt, bad = data
        lat, lon, text, dt = data[:4] ; bad = '0'
        
        lat = re.sub(",", ".", lat)
        lon = re.sub(",", ".", lon)
        #if bad not in ['0', '1']:
        #if bad not in ['3']: #
        #    continue
        #if time.strptime(data[4][:10], "%Y-%m-%d").tm_wday>=5:
        #    continue
        if bad=='1':
            text = "***"
        else:
            date_str = dt[:10]
            #print(line)
            #print(text)
            #pass
            text = re.sub(r" [\[\(].+","", text)
            text = re.sub(r'[\\"]', "", text)
            text += "<BR>"+date_str
        wf.write('[%s,%s,"%s"],\n'%(lat, lon, text))
    wf.write("];\n")
