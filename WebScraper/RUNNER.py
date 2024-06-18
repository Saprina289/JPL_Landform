import scrape_mars_Zcam as zc
import scrape_mars_NAVcam as nc
import scrape_mars_HAZcam as hzc
import scrape_mars_HELIcam as hlc
import scrape_zcam_xyz as zc_xyz

import os
import shutil
from pathlib import Path


name_camera_names_labels = {"zcam" : "ZCAM" , "ncam" : "NAVCAM" , "fcam" : "F_HAZCAM",  "rcam" : "R_HAZCAM" , "heli" : "HELICAM"}
num_camera_names_labels = {"1" : "ZCAM" , "2" : "NAVCAM" , "3" : "HAZCAM",  "4" : "HELICAM"}
raw_cali_label = {1 : "RAW" , 2 : "CALI" , 3: "STEREO"}
########### FOLDERS
code_folder = "CODE\\"
data_folder = "DATA\\"



zcam_url = ""
ncam_url = ""
f_hazcam_url = ""
r_hazcam_url = ""
helicam_url = ""
zc_xyz_url = ""


def build_url_RAW(cam,sol):

    start_url = "https://pds-imaging.jpl.nasa.gov/data/mars2020/" 

    if(cam == "zcam"):
        mid_url = "mars2020_mastcamz_ops_raw/data/sol/"
        end_url = "/ids/edr/zcam"
        sol = (5-len(sol)) * "0" + sol 

    elif(cam == "ncam"):
        mid_url = "mars2020_navcam_ops_raw/data/sol/"
        end_url = "/ids/edr/ncam"
        sol = (5-len(sol)) * "0" + sol 

    elif(cam == "rcam"):   
        mid_url = "mars2020_hazcam_ops_raw/data/sol/"
        end_url = "/ids/edr/rcam"
        sol = (5-len(sol)) * "0" + sol

    elif(cam == "fcam"):   
        mid_url = "mars2020_hazcam_ops_raw/data/sol/"
        end_url = "/ids/edr/fcam"
        sol = (5-len(sol)) * "0" + sol



    return start_url + mid_url + sol + end_url + "/"


def build_url_Calibrated(cam,sol, file_type='rad'):

    start_url = "https://pds-imaging.jpl.nasa.gov/data/mars2020/" 

    if(cam == "zcam"):
            if file_type == "rad":
                mid_url = "mars2020_mastcamz_sci_calibrated/data/"
                end_url = "/rad"
                sol = (4-len(sol)) * "0" + sol 
            else:
                mid_url = "mars2020_mastcamz_ops_calibrated/data/sol/"
                end_url = "/ids/rdr/zcam"
                sol = (5-len(sol)) * "0" + sol 

    elif(cam == "ncam"):
        #mid_url = "mars2020_navcam_ops_raw/data/sol/"
        mid_url =  "mars2020_navcam_ops_calibrated/data/sol/"
        end_url = "/ids/fdr/ncam/"
        sol = (5-len(sol)) * "0" + sol 
            
    elif(cam == "rcam"):   
        mid_url = "mars2020_hazcam_ops_calibrated/data/sol/"
        end_url = "/ids/fdr/fcam"
        sol = (5-len(sol)) * "0" + sol

    elif(cam == "fcam"):   
        mid_url = "mars2020_hazcam_ops_calibrated/data/sol/"
        end_url = "/ids/fdr/fcam"   
        sol = (5-len(sol)) * "0" + sol
 
    elif(cam == "heli"):
        mid_url = "/mars2020_helicam/data/sol/"
        end_url = "/ids/edr/heli/"
        sol = (5-len(sol)) * "0" + sol
       
    return start_url + mid_url + sol + end_url + "/"

def build_url_Stereo(cam,sol):

    start_url = "https://pds-imaging.jpl.nasa.gov/data/mars2020/" 

    if(cam == "zcam"):
        mid_url = "mars2020_mastcamz_ops_stereo/data/sol/"
        end_url = "/ids/rdr/zcam"
        sol = (5-len(sol)) * "0" + sol

    return start_url + mid_url + sol + end_url + "/"


def zcam_xyz_process(zcam_url, new_sol_folder_path,sol_num):
    try:
        zc_xyz.download_data(zcam_url,new_sol_folder_path) #downloads the data from the url created
        print("########DOWNLOADING XYZ ##########")

        print("######## CONVERTING TO PNG ##########")

        #zc_xyz.convert_to_png(new_sol_folder_path)
        
        #print("######## PLOTTING DATA ##########")

        #zc_xyz.plot(zcam_url,new_sol_folder_path)

    except KeyError:
        print(f"Sol {sol_num} is not present for MastCamZ.")
        shutil.rmtree(new_sol_folder_path)

def zcam_process(zcam_url, new_sol_folder_path,sol_num):
    try:
        zc.download_data(zcam_url,new_sol_folder_path, new_sol_folder_path.split("\\")[-1]) #downloads the data from the url created

        print("######## CONVERTING TO PNG ##########")

        zc.convert_to_png(new_sol_folder_path)

        print("######## GENERATING TO XMPs ##########")

        zc.img_to_xmp(new_sol_folder_path)

    except KeyError:
        print(f"Sol {sol_num} is not present for MastCamZ.")
        shutil.rmtree(new_sol_folder_path)


def ncam_process(ncam_url, new_sol_folder_path,sol_num):

    try:
        nc.download_data(ncam_url,new_sol_folder_path) #downloads the data from the url created

        print("######## CONVERTING TO PNG ##########")

        nc.convert_to_png(new_sol_folder_path)

        print("######## GENERATING TO XMPs ##########")

        nc.img_to_xmp(new_sol_folder_path)

    except KeyError:

        print(f"Sol {sol_num} is not present for MastCamZ.")
        shutil.rmtree(new_sol_folder_path)



def hzcam_process(hzcam_url, new_sol_folder_path,sol_num):
    try:
                hzc.download_data(hzcam_url,new_sol_folder_path) #downloads the data from the url created

                print("######## CONVERTING TO PNG ##########")

                hzc.convert_to_png(new_sol_folder_path)

                print("######## GENERATING TO XMPs ##########")

                hzc.img_to_xmp(new_sol_folder_path)

    except KeyError:
        print(f"Sol {sol_num} is not present for MastCamZ.")
        shutil.rmtree(new_sol_folder_path, ignore_errors=True)



def hlcam_process(hlcam_url, new_sol_folder_path,sol_num):
    try:
                hlc.download_data(hlcam_url,new_sol_folder_path) #downloads the data from the url created

                print("######## CONVERTING TO PNG ##########")

                hlc.convert_to_png(new_sol_folder_path)

                print("######## GENERATING TO XMPs ##########")

                hlc.img_to_xmp(new_sol_folder_path)

    except KeyError:
        print(f"Sol {sol_num} is not present for MastCamZ.")
        shutil.rmtree(new_sol_folder_path)





def choices_merged(camera_choice, raw_cali_choice,sol_num,new_sol_folder_path):

    if(camera_choice == 1):

        if(raw_cali_choice == 1):
            zcam_url = build_url_RAW("zcam",sol)
            zcam_process(zcam_url, new_sol_folder_path + "\\",sol_num)
            
        elif(raw_cali_choice == 2):
            # Download 'rad' files
            zcam_rad_url = build_url_Calibrated("zcam",sol,"rad")
            print(zcam_rad_url)
            rad_folder_path = new_sol_folder_path + "\\RAD"
            os.mkdir(rad_folder_path)
            print("RAD Folder: ", rad_folder_path)
            zcam_process(zcam_rad_url, rad_folder_path,sol_num)

            # Download 'ras' files in a separate folder
            zcam_ras_url = build_url_Calibrated("zcam",sol,"ras")
            print(zcam_ras_url)
            ras_folder_path = new_sol_folder_path + "\\RAS"
            os.mkdir(ras_folder_path)
            print("RAS folder:", ras_folder_path)
            zcam_process(zcam_ras_url, ras_folder_path,sol_num)

        elif(raw_cali_choice == 3):
            zcam_url = build_url_Stereo("zcam",sol)
            print(zcam_url)
            zcam_xyz_process(zcam_url, new_sol_folder_path, sol_num)

           
    elif(camera_choice == 2):
        if(raw_cali_choice == 1): 
            ncam_url = build_url_RAW("ncam",sol)
            ncam_process(ncam_url, new_sol_folder_path,sol_num)

        elif(raw_cali_choice == 2):
            ncam_url = build_url_Calibrated("ncam",sol)
            print(ncam_url)
            ncam_process(ncam_url, new_sol_folder_path,sol_num)

    elif(camera_choice == 3):

        #DOWNLOADING Front Hazcam Image Data
        fhazcam = build_url_Calibrated("fcam",sol)
        print(fhazcam)
        hzcam_process(fhazcam, new_sol_folder_path,sol_num)

        # #DOWNLOADING Rear Hazcam Image Data
        # fhazcam = build_url_Calibrated("rcam",sol)
        # print(fhazcam)
        # hzcam_process(fhazcam, new_sol_folder_path+"\\REAR",sol_num)

    elif(camera_choice == 4):
        helicam_url = build_url_Calibrated("heli",sol)
        print(helicam_url)
        hlcam_process(helicam_url, new_sol_folder_path,sol_num)

if __name__ == "__main__":


    print("********************************")
    print("********************************")
    print("**** MARS SCRAPER MAIN MENU ****")
    print("********************************")
    print("********************************")
    print()
    print()

    zcam_video_sols = [31,33,47,48,49,50,55,58,61,64,66,67,68,69,74,76,193,322,397,524,530]
    camera_choice = int(input("Enter Camera number. \n1 --> ZCAM\n2 --> NAVCAM\n3 --> HAZCAM\n4 --> HELICAM \n"))

    if(camera_choice == 4):
        raw_cali_choice = int("2")

        print("There is only Raw Helicam Data.")
    else:
        raw_cali_choice = int(input("Enter 1 for RAW data \nEnter 2 for Calibrated data \nEnter 3 for Stereo data \n"))
    

    range_or_single = input("Enter 1 to scrape a single sol or Enter 2 to scrape a range of sols \n")

    
    if (range_or_single == '1'):

       sol = input("Enter Sol \n")

       root_path = "." #os.getcwd() 
       new_sol_folder_path = root_path + "\\" +  data_folder + num_camera_names_labels[str(camera_choice)] + "\\sol_" + sol + "_" +  num_camera_names_labels[str(camera_choice)] + "\\" +raw_cali_label[raw_cali_choice] 

       print(new_sol_folder_path)

       if os.path.exists(new_sol_folder_path):
            shutil.rmtree(new_sol_folder_path)
           
       Path(new_sol_folder_path).mkdir(parents=True, exist_ok=True)

       print(f"DOWNLOADING SOL : {sol}")

       choices_merged(camera_choice, raw_cali_choice,sol,new_sol_folder_path)

    elif(range_or_single == '2'):

        start_range = int(input("Enter start range \n"))
        end_range = int(input("Enter end range \n "))

        for sol in range(start_range,end_range+1):

            if(sol in zcam_video_sols and camera_choice == 1):
                print("This Sol has huge data possibly a video file")
                continue

            sol = str(sol)

            root_path = "." #os.getcwd() 
            new_sol_folder_path = root_path + "\\" +  data_folder + num_camera_names_labels[str(camera_choice)] + "\\sol_" + sol + "_" +  num_camera_names_labels[str(camera_choice)] + "\\" + raw_cali_label[raw_cali_choice] + "\\"

            print(new_sol_folder_path)

            if os.path.exists(new_sol_folder_path):
                shutil.rmtree(new_sol_folder_path)
                # print(f"Sol {sol} has already been scraped")

            # os.mkdir(new_sol_folder_path)
            Path(new_sol_folder_path).mkdir(parents=True, exist_ok=True)

            print(f"DOWNLOADING SOL : {sol}")

            choices_merged(camera_choice, raw_cali_choice,str(sol),new_sol_folder_path)