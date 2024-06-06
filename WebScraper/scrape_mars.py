#FEATURES THAT CAN BE ADDED
# --progress bar for download
# -- every step message





# import dependencies
import os
import requests
from bs4 import BeautifulSoup
import struct
import numpy as np
import cv2
import matplotlib.pyplot as plt
import re
import os




#CONSTANTS FOR IMAGE CONVERSION TO png
LINES=1196
LINE_SAMPLES = 1594
SAMPLE_BITS=32
BANDS=3
HEADERBYTES=44632
ENCODING='IEEE_REAL' #
# RAWINPUTDIRECTORY =  file
# OUTPUTDIRECTORY = output


#IMAGE CONSTANTS - given in ZCAM tech specs
img_height = 1600
img_width = 1200
pixel_size = 0.0074 #in mm



def build_url(cam,sol):

    start_url = "https://pds-imaging.jpl.nasa.gov/data/mars2020/" 

    if(cam == "zcam"):
        # mid_url = "mars2020_mastcamz_ops_raw/data/sol/"
        mid_url = "mars2020_mastcamz_sci_calibrated/data/"
    elif(cam == "ncam"):
        mid_url = "mars2020_navcam_ops_raw/data/sol/"
            
    elif(cam == "rcam"):   
            mid_url = "mars2020_hazcam_ops_raw/data/sol/"
            
    elif(cam == "zcam"):   
            mid_url = "mars2020_hazcam_ops_raw/data/sol/"
            
    # end_url = "/ids/edr/"
    end_url = "/rad"

    return start_url + mid_url + sol + end_url + "/"


def download_data(url , output_folder): #Scraper
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    data = soup.find_all('a')


    new_raw_IMG_folder_path = os.path.join(output_folder, "IMGs")
    os.mkdir(new_raw_IMG_folder_path)



    for d in data:
        # if((d['href'].split(".")[-1] == "IMG") or (d['href'].split(".")[-1] == "xml")):
        if(d['href'].split(".")[-1] == "IMG"):
            # print(d['href'])
            image_url = url + d['href']
            with open(new_raw_IMG_folder_path + "/" + d['href'] , 'wb') as f:
                im = requests.get(image_url)
                f.write(im.content)

#############  convert image to png  #############

def readHeader(file):

    f = open(file,'rb')
    #filesize = os.fstat(f.fileno()).st_size
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
    return h_bytes, h_lines,h_line_samples,h_sample_type,h_sample_bits,h_bands

def readImage(file, pixelbytes, sample_type,sample_bits, lines, line_samples, bands):
    f = open(file,'rb')
    filesize = os.fstat(f.fileno()).st_size
    h_bytes = filesize - pixelbytes
    f.seek(h_bytes) # skip past the header bytes
    
    fmt = '{endian}{pixels}{fmt}'.format(endian='>', pixels=lines*line_samples*bands, fmt=getFmt(sample_type,sample_bits))
    
    if (bands==3):
        img = np.array(struct.unpack(fmt,f.read(pixelbytes))).reshape(bands,lines,line_samples)    
        m = np.max(np.max(img, axis=1))
        print('m='+str(m))
        img = np.clip(img/m,0,1) #normalize and clip so values are between 0 and 1
        img = np.stack([img[0,:,:],img[1,:,:],img[2,:,:]],axis=2)
    elif (bands==1):
        img = np.array(struct.unpack(fmt,f.read(pixelbytes))).reshape(lines,line_samples)
        #m = np.max(np.max(img, axis=1))
        #print('m='+str(m))
        m=0.05631782487034798
        img = np.clip(img/m*255,0,255) #normalize and clip so values are between 0 and 1
        #img = np.stack([img[0,:,:],img[0,:,:],img[0,:,:]],axis=2)
        img = np.array(img, dtype=np.uint8)
        img2= cv2.cvtColor(img, cv2.COLOR_BayerRG2BGR)
        img = img2
        #img = cv2.merge([img,img,img])
    return img
    
    
# fmtMap - converts sample_type from header to python format fmt. 
def getFmt(sample_type, samplebits):
    if (sample_type=='IEEE_REAL'):
        return 'f'
    elif (sample_type=='MSB_INTEGER'):
        return 'H'
    elif (sample_type=='UNSIGNED_INTEGER'):
        return 'B'
    else:
        return 'X'



def convert_to_png(sol_folder_path):
    
    new_png_folder_path = os.path.join(sol_folder_path, "PNGs")
    os.mkdir(new_png_folder_path)


    for path in os.listdir(os.path.join(sol_folder_path, "IMGs")):
        full_path = os.path.join(sol_folder_path + "/IMGs", path)
        if os.path.isfile(full_path):
            # print(full_path)

            # OUTPUTDIRECTORY = output_folder_name
            image_label = full_path.split("\\")[-1].split(".")[0]
            hbytes,hlines,hline_samples,hsample_type,hsample_bits,hbands = readHeader(full_path)
            numpixels = hlines * hline_samples * hbands
            pixelbytes = numpixels*hsample_bits//8 # // is for integer division
            print(hsample_type +":"+str(hsample_bits)+":"+str(hlines)+":"+str(hline_samples)+":"+str(hbands)+":"+str(hbytes) )
            img = readImage(full_path, pixelbytes, hsample_type,hsample_bits, hlines, hline_samples, hbands)
            plt.imsave(new_png_folder_path + "/" + image_label + '.png',img)


 




############  extract xmp ###################
def img_to_xmp(filename):

  

    new_xmp_folder_path = os.path.join(filename, "XMPs")
    os.mkdir(new_xmp_folder_path)
    INPUTDIR = os.path.join(filename, "IMGs") 
    OUTPUTDIR = new_xmp_folder_path
    countt=1000
    counttR=1000





    for filename in os.listdir(INPUTDIR): #for every IMG img in the given filename path

        print(filename)
        if not filename.endswith(".IMG"):
            continue
        with open(INPUTDIR+'/'+filename,'rb') as f:

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
                    focal_len = s.split(" ")[1]

                if (line.endswith(b'END\r\n') or count>600):
                    continuing = 0
            f.close()

            #CAHVOR vars: cC, cA, cH, cV, cO, cR
            hc = np.dot(cA,cH)
            vc = np.dot(cA,cV)
            hs = np.linalg.norm(np.cross(cA,cH))
            vs = np.linalg.norm(np.cross(cA,cV))

            Hprime = (cH-hc*cA)*(1/hs)
            Vprime = (cV - vc*cA)*(1/vs)

            r11 = str(Hprime[0])
            r12 = str(Hprime[1])
            r13 = str(Hprime[2])
            r21 = str(-Vprime[0])
            r22 = str(-Vprime[1])
            r23 = str(-Vprime[2])
            r31 = str(-cA[0])
            r32 = str(-cA[1])
            r33 = str(-cA[2])
            p0 = str(cC[0])
            p1 = str(cC[1])
            p2 = str(cC[2])
            rx = r11 + " "+r12 +" "+r13
            ry =  r21 +" "+ r22 +" "+ r23
            rz = r31 +" "+ r32 +" "+ r33

            # Princal Point U V

            x0 = pixel_size * (hc - (img_width / 2))

            y0 = - pixel_size * (vc - (img_height / 2))

        # print(x0)
        # print(y0)

#Radial Distortion Coefficients
            dc0 = "{:.10f}".format(cR[0])
            dc1 = "{:.10f}".format((cR[1]/ (float(focal_len) **2)))
            dc2 = "{:.10f}".format((cR[2]/ (float(focal_len) **4)))







            sss = """ 
   <x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description xmlns:xcr="http://www.capturingreality.com/ns/xcr/1.1#" xcr:Version="3"
       xcr:PosePrior="exact" xcr:Coordinates="absolute" xcr:DistortionModel="brown3"
       xcr:CalibrationPrior="initial" xcr:CalibrationGroup="-1" xcr:DistortionGroup="-1"
       xcr:InTexturing="1" xcr:InMeshing="1">
    <xcr:Rotation>""" + rx + " "+ ry + " " + rz + """</xcr:Rotation>
      <xcr:Position>""" + p0 +" " + p1+ " "+ p2 + """</xcr:Position>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>"""
        #       xcr:PrincipalPointU="0.0262408324441762" xcr:PrincipalPointV="0.0369566504120667"
        #       xcr:FocalLength35mm="25.59" xcr:Skew="0" xcr:AspectRatio="1"

        #      <xcr:DistortionCoeficients>-0.18404382962295 -7.80482228958343 78.5386574619506 0 0 0</xcr:DistortionCoeficients>

        #print(sss)

            xmp_data = """
                    
            <x:xmpmeta xmlns:x="adobe:ns:meta/">
            <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
            <rdf:Description xcr:Version="3" xcr:PosePrior="exact" xcr:Coordinates="absolute"
            xcr:DistortionModel="brown3" xcr:FocalLength35mm=""" +  focal_len + """
            xcr:Skew="0" xcr:AspectRatio="1" xcr:PrincipalPointU=""" + str(x0) + """
            xcr:PrincipalPointV=""" + str(y0) + """ xcr:CalibrationPrior="locked"
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
            outfile = OUTPUTDIR + '/' + filename + '.xmp'
            countt = countt + 1
            print(outfile)
        else:
            #outfile = OUTPUTDIR+'/'+str(counttR)+'R_'+filename2+'.xmp'
            outfile = OUTPUTDIR + '/' + filename + '.xmp'
            counttR = counttR + 1
            print(outfile)
        text_file = open(outfile, "w")
        n = text_file.write(xmp_data)
        text_file.close()




##############       RUNNER        ###################

if __name__ == "__main__":

    
    print("#########################")
    print("##### MARS CAM DATA #####")
    print("#########################")
    print()


    # Zcam ---> zcam
    # Hazcam front ---> fcam
    # Hazcam rear ---> rcamzcam
    # # Navcam ---> ncam

    cam = input("Enter camera name \n Zcam ---> zcam \n Hazcam front ---> fcam \n Hazcam rear ---> rcam \n Navcam ---> ncam \n")
    print()
    sol = input("Enter Sol \n Pass the right format 89 --> 00089  \n")
    url = build_url(cam,sol) #creates the url based on inputs given
    print(url)

    root_path = os.getcwd() 
    new_sol_folder_path = os.path.join(root_path, "sol" + sol)
    os.mkdir(new_sol_folder_path)

    download_data(url,new_sol_folder_path) #downloads the data from the url created


    print("######## CONVERTING TO PNG ##########")



    convert_to_png(new_sol_folder_path)
    # convert_to_png(r"F:\mars2020\radhika_work\zcam-images\sol00103")

    
    print("######## GENERATING TO XMPs ##########")


    # # filename = r"F:\mars2020\radhika_work\zcam-images\input_img"
    img_to_xmp(new_sol_folder_path)
    # # img_to_xmp(r"F:\mars2020\radhika_work\zcam-images\sol00103")
