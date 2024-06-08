import os
import requests
from bs4 import BeautifulSoup
import struct
import numpy as np
import cv2
import matplotlib.pyplot as plt
import re
import os
import shutil
import time

import colour
from colour_demosaicing import demosaicing_CFA_Bayer_Malvar2004,demosaicing_CFA_Bayer_Menon2007


import urllib3, socket
from urllib3.connection import HTTPConnection
    

def download_data(url , output_folder): 
   

    new_raw_IMG_folder_path = os.path.join(output_folder, "IMGs")
    os.mkdir(new_raw_IMG_folder_path)

    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    for d in soup.find_all('a'):

        substrings = ["ZL0","ZR0"]  
        fullstring = d['href']

        if not any(x in fullstring for x in substrings):
            continue

        if(d['href'].split(".")[-1] == "IMG"):
        
            image_url = url + d['href']

            with open(new_raw_IMG_folder_path + "/" + d['href'], 'wb') as f:
                try:
                    im = requests.get(image_url)
                
                except :
                    current_time = time.time()
                    retry_time = current_time + (60 * 3)
                    while(time.time() < retry_time):
                        im = requests.get(image_url)       

                f.write(im.content)
      

#############  convert image to png  #############

def readHeader(file):
    # print("Calling readHeader")
    f = open(file,'rb')
    continuing = 1
    count = 0
    
    h_bytes = -1
    h_lines = -1
    h_line_samples = -1
    h_sample_type = 'UNSET' #MSB_INTEGER, IEEE_REAL
    h_sample_bits = -1
    h_bands = -1
    while continuing == 1:
        line = f.readline()
        count = count + 1
        arr = str(line, 'utf8').split("=")
        arr[0] = str(arr[0]).strip()
        if 'BYTES' == arr[0] and len(arr[0])>1:
            h_bytes=int(str(arr[1]).strip())
        elif 'LINES' == arr[0] and len(arr[0])>1: 
            h_lines=int(str(arr[1]).strip())
        elif 'LINE_SAMPLES' == arr[0] and len(arr[0])>1:
            h_line_samples=int(str(arr[1]).strip())
        elif 'SAMPLE_TYPE' == arr[0] and len(arr[0])>1:
            h_sample_type=str(arr[1]).strip()
        elif 'SAMPLE_BITS' == arr[0] and len(arr[0])>1:
            h_sample_bits = int(str(arr[1]).strip())
        elif 'BANDS' == arr[0] and len(arr[0])>1: 
            h_bands=int(str(arr[1]).strip())
        if (line.endswith(b'END\r\n') or count>600):
            continuing = 0
    f.close()
    print(str(arr))
    return h_bytes, h_lines,h_line_samples,h_sample_type,h_sample_bits,h_bands



def lin2rgb(im):
    """ Convert im from "Linear sRGB" to sRGB - apply Gamma. """
    # sRGB standard applies gamma = 2.4, Break Point = 0.00304 (and computed Slope = 12.92)    
    # lin2rgb MATLAB functions uses the exact formula [we may approximate it to power of (1/gamma)].
    g = 2.4
    bp = 0.00304
    inv_g = 1/g
    sls = 1 / (g/(bp**(inv_g - 1)) - g*bp + bp)
    fs = g*sls / (bp**(inv_g - 1))
    co = fs*bp**(inv_g) - sls*bp

    srgb = im.copy()
    srgb[im <= bp] = sls * im[im <= bp]
    srgb[im > bp] = np.power(fs*im[im > bp], inv_g) - co
    return srgb



def readImage(file, pixelbytes, sample_type,sample_bits, lines, line_samples, bands,new_png_folder_path,image_label):
    # print("Calling Read image")
    f = open(file,'rb')
    filesize = os.fstat(f.fileno()).st_size
    h_bytes = filesize - pixelbytes
    f.seek(h_bytes) # skip past the header bytes
    
    fmt = '{endian}{pixels}{fmt}'.format(endian='>', pixels=lines*line_samples*bands, fmt=getFmt(sample_type,sample_bits))
    
    if (bands==3):
        # print(pixelbytes,lines,line_samples,fmt)
        img = np.array(struct.unpack(fmt,f.read(pixelbytes))).reshape(bands,lines,line_samples)    
        
        m = np.max(np.max(img, axis=1))
        img = np.clip(img/m,0,1)  #normalize and clip so values are between 0 and 1
        img = np.stack([img[0,:,:],img[1,:,:],img[2,:,:]],axis=2)
        # print(np.amin(img))
        # print(np.amax(img))

        plt.imsave(new_png_folder_path + "/" + image_label + '.png',img)


    elif (bands==1):
        # print(pixelbytes,lines,line_samples,fmt)
        data = f.read(pixelbytes)  # Read raw data bytes
        img = np.frombuffer(data, np.uint16).reshape(lines, line_samples)  # Convert to uint16 NumPy array and reshape to image dimensions.
        img = (img >> 8) + (img << 8)  # Convert from big endian to little endian
      
        img = cv2.cvtColor(img, cv2.COLOR_BAYER_BG2BGR)  # Apply demosaicing (convert from Bayer to BGR).
        img_in_range_0to1 = img.astype(np.float32) / (2**16-1)  # Convert to type float32 in range [0, 1] (before applying gamma correction).
        gamma_img = lin2rgb(img_in_range_0to1)
        gamma_img = np.round(gamma_img * 255).astype(np.uint8)  # Convert from range [0, 1] to uint8 in range [0, 255].
        kernel = np.array([[0, -1, 0],
                   [-1, 5,-1],
                   [0, -1, 0]])
        image_sharp = cv2.filter2D(src=gamma_img, ddepth=-1, kernel=kernel)
        img = image_sharp
        cv2.fastNlMeansDenoisingColored(img,None,15,15,7,21)

        cv2.imwrite(new_png_folder_path + "/" + image_label + '.png', img)

    # return img
    
    
# fmtMap - converts sample_type from header to python format fmt. 
def getFmt(sample_type, samplebits):
    # print("Calling getFM funtion")
    if (sample_type=='IEEE_REAL'):
        return 'f'
    elif (sample_type=='MSB_INTEGER'):
        return 'H'
    elif (sample_type=='UNSIGNED_INTEGER'):
        return 'B'
    else:
        return 'X'



def convert_to_png(solFolderName):
    sol_folder_path ="F:\\mars2020\\radhika_work\\MARS-PHOTOGRAMMETRY\\DATA\\ZCAM\\" + solFolderName + "\\CALI"
    new_png_folder_path = os.path.join(sol_folder_path, "PNGs+XMPs")
    os.mkdir(new_png_folder_path)


    for path in os.listdir(os.path.join(sol_folder_path, "IMGs")):
        full_path = os.path.join(sol_folder_path + "/IMGs", path)
        if os.path.isfile(full_path):

            image_label = full_path.split("\\")[-1].split(".")[0]
            
            hbytes,hlines,hline_samples,hsample_type,hsample_bits,hbands = readHeader(full_path)
            numpixels = hlines * hline_samples * hbands
            pixelbytes = numpixels*hsample_bits//8 # // is for integer division
            readImage(full_path, pixelbytes, hsample_type,hsample_bits, hlines, hline_samples, hbands,new_png_folder_path,image_label)
            # img_in_range_0to1 = img.astype(np.float32) / (2**16-1)  # Convert to type float32 in range [0, 1] (before applying gamma correction).
            # gamma_img = lin2rgb(img_in_range_0to1)
            # gamma_img = np.round(gamma_img * 255).astype(np.uint8)  # Convert from range [0, 1] to uint8 in range [0, 255].
            # print(img.dtype)
            # cv2.imwrite(new_png_folder_path + "/" + image_label + '.png', img)  # Save image after demosaicing and gamma correction.

            # plt.imsave(new_png_folder_path + "/" + image_label + '.png',img)


############  extract xmp ###################
def img_to_xmp(filename):

    # print("Calling xmp function")

    new_xmp_folder_path = os.path.join(filename, "PNGs+XMPs")
    INPUTDIR = os.path.join(filename, "IMGs") 
    OUTPUTDIR = new_xmp_folder_path
    countt=1000
    counttR=1000





    for filename in os.listdir(INPUTDIR): #for every IMG img in the given filename path

        # print(filename)
        if not filename.endswith(".IMG"):
            continue
        with open(INPUTDIR+'/'+filename,'rb') as f:



            hbytes,hlines,hline_samples,hsample_type,hsample_bits,hbands = readHeader(INPUTDIR+'/'+filename)



            # print(hbytes,hlines,hline_samples,hsample_type,hsample_bits,hbands)
            continuing = 1
            count = 0
            while continuing == 1:
                line = f.readline()
                count = count + 1
                arr = str(line, 'utf8').split("=")
                arr[0] = str(arr[0]).strip()
                if 'MODEL_COMPONENT_1'== arr[0] and len(arr[0])>1:
                    s = arr[1]
                    s = s.replace('(','')
                    s = s.replace(')','')
                    tmp = np.array(s.split(','))
                    cC = np.asfarray(tmp,float)
                    #print('hey model ' + cahvor_C[0]+',' +cahvor_C[1] +',' + cahvor_C[2])
                elif 'MODEL_COMPONENT_2'== arr[0] and len(arr[0])>1:
                    s = arr[1]
                    s = s.replace('(','')
                    s = s.replace(')','')
                    tmp = np.array(s.split(','))
                    cA = np.asfarray(tmp,float)
                elif 'MODEL_COMPONENT_3'== arr[0] and len(arr[0])>1:
                    s = arr[1]
                    s = s.replace('(','')
                    s = s.replace(')','')
                    tmp = np.array(s.split(','))
                    cH = np.asfarray(tmp,float)
                elif 'MODEL_COMPONENT_4'== arr[0] and len(arr[0])>1:
                    s = arr[1]
                    s = s.replace('(','')
                    s = s.replace(')','')
                    tmp = np.array(s.split(','))
                    cV = np.asfarray(tmp,float)
                elif 'MODEL_COMPONENT_5'== arr[0] and len(arr[0])>1:
                    s = arr[1]
                    s = s.replace('(','')
                    s = s.replace(')','')
                    tmp = np.array(s.split(','))
                    cO = np.asfarray(tmp,float)
                elif 'MODEL_COMPONENT_6'== arr[0] and len(arr[0])>1:
                    s = arr[1]
                    s = s.replace('(','')
                    s = s.replace(')','')
                    tmp = np.array(s.split(','))
                    cR = np.asfarray(tmp,float)

                elif 'FOCAL_LENGTH'== arr[0] and len(arr[0])>1:
                    s = arr[1]
                    s = s.replace('(','')
                    s = s.replace(')','')
                    # f = np.asfarray(tmp,float)
                    focal_len = float(s.split(" ")[1])  #paper says use hs hs = f or f = hs *1.5 to convert into 35mm equivalent
                elif 'IMAGE_DATA_SIZE'== arr[0] and len(arr[0])>1:
                    s = arr[1]
                    s = s.replace('(','')
                    s = s.replace(')','')
                    IMAGE_DATA_SIZE = float(s.split(" ")[1])
                if (line.endswith(b'END\r\n') or count>600):
                    continuing = 0

            f.close()
            #print(str(cA[0]) + "," +str(cA[1]) + "," +str(cA[2])+","+str(cH[0])+","+str(cH[1])+","+str(cH[2])+","+str(cV[0])+","+str(cV[1])+","+str(cV[2]))
            #CAHVOR vars: cC, cA, cH, cV, cO, cR
            hc = np.dot(cA,cH)
            vc = np.dot(cA,cV)
            hs = np.linalg.norm(np.cross(cA,cH))
            vs = np.linalg.norm(np.cross(cA,cV))
            #hc = 375.79086289445047 
            #vc = 259.0237731229597
            #hs = 5,984.766050054407
            #vs = 5,984.766050054407


            print("ca"+str(cA))
            print("ch"+str(cH))
            print("cv"+str(cV))

            Hprime = (cH-(hc*cA))*(1/hs)
            Vprime = (cV - (vc*cA))*(1/vs)

            r11 = str(Hprime[0]) #yaw 
            r12 = str(Hprime[1]) 
            r13 = str(Hprime[2])
            r21 = str(-Vprime[0]) #pitch
            r22 = str(-Vprime[1])
            r23 = str(-Vprime[2]) 
            r31 = str(-cA[0]) #roll
            r32 = str(-cA[1])
            r33 = str(-cA[2]) 
            #invert Y
            #r13 = str(-r13)
            #r23 = str(-r23)
            #r33 = str(-r33)
            p0 = str(-cC[0]) #x
            p1 = str(-cC[1]) #y
            p2 = str(-cC[2]) #z In rover coord system z is down
            rx = r11 + " "+r12 +" "+r13 
            ry =  r21 +" "+ r22 +" "+ r23
            rz = r31 +" "+ r32 +" "+ r33
            
            x0 = 0.0
            y0 = 0.0
            #CF=diag35mm / diagsensor.
            #width = 11.84 cf = #36/11.84 
            #diagonal = 14.8 cf =  #43.3/14.8 #
            crop_factor = 36/11.84
            #focal_len/width x 36
            focal_len_35mm = (crop_factor * focal_len) #focal_len/11.84* 36 #equation from RC support 
            #focal_len_35mm = (focal_len/11.84) * 36
            print("crop factor = "+ str(crop_factor)+ "focal_len = "+ str(focal_len_35mm))

            #middle * 35mm?
            #x0 = (float(hc) - float(hline_samples/ 2.0)) *Dx #*0.0074 #pixel size #*0.2645833333 /1000 # (((float(focal_len_35mm)/float(hs)) * 
            #y0 =  ((float(hlines/ 2.0))-float(vc)) *Dy #*0.0074 #*0.2645833333 /1000 #-((float(focal_len_35mm)/float(vs)) *

            hc = (float(hline_samples/ 2.0) + float(hc+1))
            vc = (float(hlines/ 2.0) - float(vc+1))
            #hc = (float(hc+1) - float(hline_samples/ 2.0))
            #vc = (float(hlines/ 2.0) - float(vc+1)) #tried: float(vc) - float(hlines/ 2.0) #
            
            #            pixel_size = 0.0074
            #active image size https://www.onsemi.com/pdf/datasheet/kai-2020-d.pdf
            #Finding the PPI of an image: Number of pixels ÷ size of the image in inches = pixels per inch.
            #Number of Effective Pixels 1608 (H) × 1208 (V)
            #Number of Active Pixels 1600 (H) × 1200 (V)

            image_size_in = 4.13934081792 
            total_num_pixels = 1990960
            IMAGE_DATA_SIZE = 1977664
            active_px = 1920000              #53 pixels off in RC ###########which do I use###
            effective_px = 1942464
            width_times_height = 1977600
            #todo- READ IMAGE_DATA_SIZE 1977664 (number of  pixels) #try other image data sizes
            ppi = total_num_pixels / image_size_in
            hc_mm = hc * (25.4/ ppi)  # = .00005467mm same as multiplying by pixel size 7.4 microns squared 
            vc_mm = vc * (25.4/ ppi)
            print("25.4/ppi = " + str(25.4/ppi))
            #convert pixel ppu.ppv to 35mm
            x0 = hc_mm #/11.84   #* crop_factor #* 36 #(hc_mm / (11.84/36)) #focal = xcr:FocalLength35mm * w/36
            y0 = vc_mm #/11.84  #* crop_factor #* 36 #(vc_mm / (11.84/36))

            #x0 = hc_mm #/36 #- removed the *36 on 4_17... not good ppu results
            #y0 = vc_mm #/36
            print("hcmm"+str(hc_mm) + "vcmm"+str(vc_mm))
            print(x0)
            print(y0)

#Radial Distortion Coefficients
            dc0 = "{:.10f}".format(cR[0]) #/ (float(focal_len_35mm)**2))
            dc1 = "{:.10f}".format(cR[1]) #/ (float(focal_len_35mm)**4))
            dc2 = "{:.10f}".format(cR[2]) #/ (float(focal_len_35mm)**6))

            #print(dc0)
            #print(dc1)
            #print(dc2)


            xmp_data = """
                    
            <x:xmpmeta xmlns:x="adobe:ns:meta/">
            <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
            <rdf:Description xcr:Version="3" xcr:PosePrior="exact" xcr:Coordinates="absolute"
            xcr:DistortionModel="brown3" xcr:FocalLength35mm=""" +  str(focal_len_35mm) + """
            xcr:Skew="0" xcr:AspectRatio="1.33" xcr:PrincipalPointU=""" + str(x0) + """
            xcr:PrincipalPointV="""+ str(y0) + """ xcr:CalibrationPrior="locked"
            xcr:CalibrationGroup="-1" xcr:DistortionGroup="-1" xcr:InTexturing="1"
            xcr:InColoring="0" xcr:InMeshing="1" xmlns:xcr="http://www.capturingreality.com/ns/xcr/1.1#">
            <xcr:Rotation>""" + rx + " "+ ry + " " + rz + """</xcr:Rotation> 
            <xcr:Position>""" + p0 +" " + p1+ " "+ p2 + """</xcr:Position>
            <xcr:DistortionCoeficients>""" + dc0 + " "+ dc1 + " " + dc2 + """ 0 0 0</xcr:DistortionCoeficients>
            </rdf:Description>
            </rdf:RDF>
            </x:xmpmeta>



        """



        
        filename2 = filename[0:3]+filename[0:2]
        if (filename[0:2].startswith("ZL")):
            #outfile = OUTPUTDIR+'/'+str(countt)+'_'+filename2+'.xmp'
            outfile = OUTPUTDIR + '/' + filename[:len(filename)-4] + '.xmp'
            countt = countt + 1
            #print(outfile)
        else:
            #outfile = OUTPUTDIR+'/'+str(counttR)+'R_'+filename2+'.xmp'
            outfile = OUTPUTDIR + '/' + filename[:len(filename)-4] + '.xmp'
            counttR = counttR + 1
            #print(outfile)
        text_file = open(outfile, "w")
        n = text_file.write(xmp_data)
        text_file.close()


