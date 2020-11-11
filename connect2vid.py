'''
Requirements:
- python 2.7 or 3
- wget, unzip, and ffmpeg accessible from command line.

Examples:
python connect2vid_v2.py https://my.adobeconnect.com/pqc06mcawjgn/  --output_filename="Understanding how the Network impacts your service"

The script assumes that the .zip files contains screenshare__.flv files, which contain the screen share.

Author: Franck Dernoncourt <franck.dernoncourt@gmail.com>
'''

import shlex
import subprocess
import os
import glob
import argparse
import sys
import re


def run_command(command):
    print('running command: {0}'.format(command))
    process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE)
    while True:
        output = process.stdout.readline()
        print(output.strip())
        if output == b'' and process.poll() is not None:
            print('Done running the command.')
            break
        if output:
            print(output.strip())
    rc = process.poll()
    return rc

def create_folder_if_not_exists(directory):
    '''
    Create the folder if it doesn't exist already.
    '''
    if not os.path.exists(directory):
        os.makedirs(directory)

def extract_connect_id(parser, args):
    '''
    Function written by Aaron Hertzmann
    '''
    # ----- extract the connectID or ZIP file  -----

    if len(args.URLorIDorZIP) < 1:
    #    print('Error: No Connect recording URL provided.')
        parser.print_help()
        sys.exit(0)

    if args.URLorIDorZIP[0][-4:].lower() == '.zip':
        sourceZIP = args.URLorIDorZIP[0]
        connectID = os.path.basename(sourceZIP[:-4])
    elif len(args.URLorIDorZIP[0]) == 12:
        connectID = args.URLorIDorZIP[0]
    else:
        s = args.URLorIDorZIP[0].split('/')
        connectID = None
        for i in range(len(s)-1):
            if 'adobeconnect.com' in s[i]:
                connectID = s[i+1]
                break
        if connectID == None:
            print("Error: couldn't parse URL")
            sys.exit(1)

    return connectID


def main():
    '''
    This is the main function
    '''

    # ================ parse the arguments (part of the parsing code was written by Aaron Hertzmann) ======================

    parser = argparse.ArgumentParser(description='Download an Adobe Connect recording and convert to a video file.')
    parser.add_argument('URLorIDorZIP', nargs='*', help='URL, code, or ZIP file for the Connect recording')
    parser.add_argument('--output_folder',default='output_videos',help='Folder for output files')
    parser.add_argument('--output_filename',default='noname', help='output_filename')
    args = parser.parse_args()

    #main_output_folder = "all_videos"
    main_output_folder = args.output_folder
    output_filename = args.output_filename
    output_filename =  re.sub(r'[^\w\s]','', output_filename)
    output_filename = output_filename.replace('@', '').strip()
    print('output_filename: {0}'.format(output_filename))
    connect_id = 'pul1pgdvpr87'
    connect_id = 'p6vwxp2d0c2f'
    connect_id = extract_connect_id(parser, args)
    video_filename = 'hello'
    video_filename = output_filename

    # ================ Download video  ======================
    output_folder = connect_id
    output_zip_filename = '{0}.zip'.format(connect_id)
    create_folder_if_not_exists(output_folder)
    create_folder_if_not_exists(main_output_folder)

    # Step 1: retrieve audio and video files
    connect_zip_url = 'https://my.adobeconnect.com/{0}/output/{0}.zip?download=zip'.format(connect_id)
    wget_command = 'wget -nc -O {1} {0}'.format(connect_zip_url, output_zip_filename) # -nc, --no-clobber: skip downloads that would download to existing files.
    run_command(wget_command)
    unzip_command = 'unzip -n {0} -d {1}'.format(output_zip_filename, output_folder) # -n: Unzip only newer files.
    run_command(unzip_command)

    # Step 2: create final video output
    cameraVoip_filepaths = []
    for filepaths in sorted(glob.glob(os.path.join(output_folder, 'cameraVoip_*.flv'))):
        cameraVoip_filepaths.append(filepaths)
    print('cameraVoip_filepaths: {0}'.format(cameraVoip_filepaths))

    screenshare_filepaths = []
    for filepaths in sorted(glob.glob(os.path.join(output_folder, 'screenshare_*.flv'))):
        screenshare_filepaths.append(filepaths)

    part = 0
    output_filepaths = []
    for cameraVoip_filepath, screenshare_filepath in zip(cameraVoip_filepaths, screenshare_filepaths):
        output_filepath = os.path.join(main_output_folder, '{0}_{1:04d}.flv'.format(video_filename, part))
        #output_filepath = '{0}_{1:04d}.flv'.format(video_filename, part)
        output_filepaths.append(output_filepath)
        # ffmpeg command from Oliver Wang / Yannick Hold-Geoffroy / Aaron Hertzmann
        conversion_command = 'ffmpeg -i "%s" -i "%s" -c copy -map 0:a:0 -map 1:v:0 -shortest -y "%s"'%(cameraVoip_filepath, screenshare_filepath, output_filepath)
        # -y: override output file if exists
        run_command(conversion_command)
        part += 1

    # Concatenate all videos into one single video
    # https://stackoverflow.com/questions/7333232/how-to-concatenate-two-mp4-files-using-ffmpeg
    video_list_filename = 'video_list.txt'
    video_list_file = open(video_list_filename, 'w')
    for output_filepath in output_filepaths:
        video_list_file.write("file '{0}'\n".format(output_filepath))
    video_list_file.close()
    final_output_filepath = '{0}.flv'.format(video_filename)
    # ffmpeg command from Oliver Wang / Yannick Hold-Geoffroy / Aaron Hertzmann
    conversion_command = 'ffmpeg -safe 0 -y -f concat -i "{1}" -c copy "{0}"'.format(final_output_filepath, video_list_filename)
    run_command(conversion_command)
    #os.remove(video_list_filename)

if __name__ == "__main__":
    main()
    #cProfile.run('main()') # if you want to do some profiling