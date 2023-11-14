#!/usr/bin/env python3 

### BHTOM system script
### Script allows to upload bulk FITS data to BHTOM server.
### Last modified: Nov 8, 2023
### Authors: PM
### Important: Added support for new server (!)

import os
import subprocess
import requests
import time
import argparse
import sys

bhtom2_url = "https://uploadsvc2.astrolabs.pl/upload/"

def input_arguments(): 
    global indir, inhash, inobject, infilter, intype, dryrun, inmjd, inobservat, intoken
    des = ">>> " + os.path.basename(sys.argv[0]) + " <<<\n" + \
          "Sends image data to BHTOM system\n" + \
          "Requires: Python3 with os,subprocess,requests,time,\n" + \
          "          argparse,sys packages\n" + \
          "Example: send_to_bhtom.py -d ./files_to_be_sent -o Gaia18dif -t 65u6gqiubs88d7c27083cfb51af71 -oname ROAD_QHY600M\n" + \
          "[-f filter] --dryrun"
    parser = argparse.ArgumentParser(description = des, formatter_class = argparse.RawTextHelpFormatter)
    parser.add_argument("-d", "--dir", type=str, help="directory containing FITS images or a PHOT filepath", required=True)
    parser.add_argument("-t", "--token", type=str, help="your dedicated hashtag", required=True)
    parser.add_argument("-o", "--object", type=str, help="object name", required=True)
    parser.add_argument("-oname", "--observatory", type=str, help="observatory name", required=True)
    parser.add_argument("-f", "--filter", type=str, help="matching catalogue filter name", default="GaiaSP/any")
    parser.add_argument("--dryrun", help="sends data, but does not store datapoints in BHTOM database", action="store_true") 
    args = parser.parse_args()
    
    indir       = str(args.dir)
    intoken     = str(args.token)
    inobject    = str(args.object) 
    infilter    = str(args.filter)
    inobservat  = str(args.observatory)
    dryrun      = True if args.dryrun else False

def show_arguments():
    print("$ Directory              :", indir)
    print("$ Token                  :", intoken)
    print("$ Object name            :", inobject)
    print("$ Observatory            :", inobservat)
    print("$ Matching filter        :", infilter)
    print("$ Dry run                :", dryrun)
    ## print("$ Filter                 :", infilter)

#def send_fits_file(filename,hashtag,target,flter,m_radius,dry_run):
def send_fits_file(f, tokenid, observatory_name, inobjec, filter_name, dry_run, data_product_type='fits_file', comment='None'):
    response = requests.post(
        url = bhtom2_url,
        headers={
            'Authorization': "Token " + str(tokenid)
        },
        data={
            'target': inobjec,
            'filter': filter_name,
            'data_product_type': data_product_type,
            'dry_run': dry_run,
            'observatory': observatory_name,
            'comment': comment,
        },
        files={'files': f}
    )
    if "201" in str(response):
        return 201
    elif "200" in str(response):
        return 200
    else:
        return 404

if __name__ == '__main__':
    print("")
    input_arguments()
    show_arguments() 
    try:
        number_of_files = len(os.listdir(indir))
    except FileNotFoundError:
        print("\n### There's no such directory '"+str(indir)+"'. Quitting.\n")
        sys.exit(1)
    if number_of_files > 0:
        print("\n$$$ NOW SENDING DATA TO BHTOM (https://bh-tom.astrolabs.pl) $$$\n")
    else:
        print("\n# No files present inside '" + str(indir) + "'")
        print("  Program is terminating.\n")
        sys.exit(1)
    i       = 0
    success = 0
    error   = 0
    total   = number_of_files
    
    '''
    Now looping over files    
    '''
    ## print(infilter), exit()
    for filename in os.listdir(indir):
        i += 1
        total -= 1
        prompt = "$ LEFT: " + str(total + 1) + " | SUCCESS: " + str(success) + " | ERROR: " + str(error) + " | " + \
                 "> Now uploading '" + str(filename) + "' (" + str(i) + "/" + str(number_of_files) + ")"
        print(prompt, end="\r")    

        with open(os.path.join(indir, filename), 'rb') as f:
            ## print(indir, os.path.join(indir, filename), f)
            code = send_fits_file(f, intoken, inobservat, inobject, infilter, dryrun)
        if code == 200 or code == 201:
            success += 1
            subprocess.call('mkdir success 2>/dev/null', shell=True)
            subprocess.call("mv %s/%s %s " % (indir, filename, "./success/"), shell=True)
        else:
            error += 1
            subprocess.call('mkdir error 2>/dev/null', shell=True)
            subprocess.call("cp %s/%s %s " % (indir, filename, "./error/"), shell=True)
        time.sleep(0.01)
    print("$ LEFT: " + str(total) + " | SUCCESS: " + str(success) + " | ERROR: " + str(error) + \
          "                                                              ")
    print("$ All files have been processed.")
    if success > 0:
        print("  Files processed successfully have been moved to 'success' directory.")
    if error > 0:
        print("  Files with errors have been copied to 'error' directory.")
    print("$ Thank you for using BHTOM!")
    print("  Program is terminating.\n")

    sys.exit(0)

### END
