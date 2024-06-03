# imports
import os
import numpy as np
import datetime
import pandas as pd
#import BCI_analysis
from pathlib import Path
import subprocess

# generate a csv file and collect data in folders if necessary.
metadata_dir = '/home/jupyter/bucket/Metadata/' 
dlc_base_dir = os.path.abspath("/home/jupyter/bucket/Data/Behavior_videos/DLC_output/Bergamo-2P-Photostim/")
bpod_path = os.path.abspath("/home/jupyter/bucket/Data/Behavior/BCI_exported/Bergamo-2P-Photostim/")
suite2p_path = os.path.abspath("/home/jupyter/bucket/Data/Calcium_imaging/suite2p/Bergamo-2P-Photostim/")
raw_imaging_path = os.path.abspath("/home/jupyter/bucket/Data/Calcium_imaging/raw/Bergamo-2P-Photostim/")

sessionwise_data_path = os.path.abspath("/home/jupyter/bucket/Data/Calcium_imaging/sessionwise_tba/")

face_rhythm_base_dir = '/home/jupyter/bucket/Data/Behavior_videos/FaceRhythm/'
motion_energy_base_dir = os.path.abspath("/home/jupyter/bucket/Data/Behavior_videos/MotionEnergy/Bergamo-2P-Photostim/")
raw_video_path = os.path.abspath("/home/jupyter/bucket/Data/Behavior_videos/raw/Bergamo-2P-Photostim/")

CO_save_path = "/home/jupyter/bucket/CodeOcean_transfer/"

sessions_with_errors = [] # sessions that are skipped collected in this list
no_cn_sessions = []
invalid_neurons = [] # with inf
blacklist = []
mat_files = []
session_dates = {}
kept_files = []
files_thrown_away = []
only_csv_metadata = False
for mouse_id in os.listdir(raw_imaging_path):
    
    if 'BCI' not in mouse_id:
       # print('{} is not a proper subject name, skipping'.format(mouse_id))
        continue
    for session in os.listdir(os.path.join(raw_imaging_path,mouse_id)):
        try:
            datetime.datetime.strptime(session,'%m%d%y')
        except:
            #print('{} is not a proper session folder, skipping'.format(session))
            continue
        if mouse_id not in session_dates.keys():
            session_dates[mouse_id] = {}
        session_dates[mouse_id][datetime.datetime.strptime(session,'%m%d%y')]  = [session]
        
        
        
upload_dict = {'platform':[],
                'acq_datetime':[],
                'subject_id':[],
                's3_bucket':[],
                'modality0':[],
                'modality0.source':[],
                'modality1':[],
                'modality1.source':[],
                'modality2':[],
                'modality2.source':[]}
#asdsa
platform = 'single-plane-ophys'
s3_bucket = 'aind-ophys-data'
df_metadata=pd.read_csv(os.path.join(metadata_dir,'Surgeries-BCI.csv'))
for mouse_id in session_dates.keys():
    mouseid = mouse_id
    while mouseid.find('_')>-1:
        mouseid = mouseid[:mouseid.find('_')]+mouseid[mouseid.find('_')+1:]
    for session_date in np.sort(list(session_dates[mouse_id].keys())):
        [session] = session_dates[mouse_id][session_date]
        # load metadata to find subject_id
        try:
            try:
                subject_id = int(df_metadata.loc[df_metadata['ID']==mouse_id,'animal#'].values[0])
            except:
                subject_id = int(df_metadata.loc[df_metadata['ID']==mouseid,'animal#'].values[0])    
        except:
            subject_id = None
            print('missing subject id for {} ..  skipping'.format(mouse_id))
            break
        
        # load exported bpod data to find acq datetime
        behavior_fname = os.path.join(bpod_path,mouse_id, f"{session}-bpod_zaber.npy")
        try:
            bpod_dict = np.load(behavior_fname,allow_pickle = True).tolist()
        except:
            print('no behavior found, skipping {} - {}'.format(mouse_id,session))
            continue
        print('starting {} - {}'.format(mouse_id,session))
        idx = -1
        tiffheader = np.nan
        while np.abs(idx)<len(bpod_dict['scanimage_tiff_headers']):
            try:
                tiffheader = bpod_dict['scanimage_tiff_headers'][idx].tolist()[0]
                break
            except:
                idx-=1
        last_trial_time = tiffheader['movie_start_time'] + datetime.timedelta(seconds = float(tiffheader['description_first_frame']['frameTimestamps_sec']))
        
        gotit = False
        i_ = 0
        while not gotit:
            i_-=1
            try:
                last_residual_tiff_time = bpod_dict['residual_tiff_files']['scanimage_tiff_headers'][i_]['movie_start_time']+ datetime.timedelta(seconds = float(bpod_dict['residual_tiff_files']['scanimage_tiff_headers'][i_]['description_first_frame']['frameTimestamps_sec']))
                gotit = True
            except:
                pass
        session_end_time = np.max([last_trial_time,last_residual_tiff_time])
        
        acq_datetime = datetime.datetime.strftime(session_end_time, '%Y-%m-%d %H-%M-%S')
        
        # locate raw imaging data (no copy required, only folder name)
        modality0 = 'ophys'
        modality0_source = os.path.join(raw_imaging_path,mouse_id,session)
        
        
        #copy behavior stuff in a folder
        modality1 = 'trained_behavior'
        modality1_source = Path(os.path.join(CO_save_path,'{}-{}'.format(mouse_id,session),'behavior'))
        modality1_source.mkdir(parents=True, exist_ok=True)
        copy_command = 'gsutil cp {} {} '.format(behavior_fname,str(modality1_source)+'/'+f"{session}-bpod_zaber.npy")
        #reply = os.system(copy_command)
        if not only_csv_metadata:
            subprocess.run(copy_command,shell=True)
        bpod_file_names = np.unique(bpod_dict['bpod_file_names'])
        
        command_list = []
        for f in bpod_file_names:
            copy_command = 'gsutil -m cp -r {} {} '.format('/home/jupyter/bucket/Data/Behavior/raw/KayvonScope/BCI/experiments/BCI/setups/KayvonScope/sessions/'+f[:-4],
                                                     str(modality1_source)+'/')
            command_list.append(copy_command)

        bash_command = r" && ".join(command_list)
        #os.system(bash_command)
        if not only_csv_metadata:
            for bash_command in command_list:
                subprocess.run(bash_command,shell=True)

        
        #copy camera data in a single folder under side & bottom
        modality2 = 'behavior_videos'
        modality2_source = Path(os.path.join(CO_save_path,'{}-{}'.format(mouse_id,session),'behavior_videos'))
        modality2_source.mkdir(parents=True, exist_ok=True)
        modality2_source_side = Path(os.path.join(CO_save_path,'{}-{}'.format(mouse_id,session),'behavior_videos','side'))
        modality2_source_side.mkdir(parents=True, exist_ok=True)
        modality2_source_bottom = Path(os.path.join(CO_save_path,'{}-{}'.format(mouse_id,session),'behavior_videos','bottom'))
        modality2_source_bottom.mkdir(parents=True, exist_ok=True)
        
        side_folders = []
        bottom_folders = []
        
        for m in bpod_dict['behavior_movie_name_list']:
            if type(m) == np.ndarray:
                for movie_name in m:
                    if 'side' in movie_name:
                        side_folders.append(os.path.join('/home/jupyter/bucket/Data/Behavior_videos/raw/Bergamo-2P-Photostim',*movie_name.split('/')[5:-1]))
                    elif 'bottom' in movie_name:
                        bottom_folders.append(os.path.join('/home/jupyter/bucket/Data/Behavior_videos/raw/Bergamo-2P-Photostim',*movie_name.split('/')[5:-1]))
                    else:
                        wtf
        side_folders = np.unique(side_folders)
        command_list = []
        for s in side_folders:
            dest  = Path(os.path.join(modality2_source_side,s.split('/')[-1]))
            dest.mkdir(parents=True, exist_ok=True)
            copy_command = 'gsutil -m rsync {} {} '.format(s,
                                                     str(dest)+'/')
            command_list.append(copy_command)
        bottom_folders = np.unique(bottom_folders)
        for b in bottom_folders:
            dest  = Path(os.path.join(modality2_source_bottom,b.split('/')[-1]))
            dest.mkdir(parents=True, exist_ok=True)
            copy_command = 'gsutil -m rsync {} {} '.format(b,
                                                     str(dest)+'/')
            command_list.append(copy_command)

        bash_command = r" && ".join(command_list)
        #os.system(bash_command)
        if not only_csv_metadata:
            for bash_command in command_list:
                subprocess.run(bash_command,shell=True)
        #asd
        
        
        upload_dict['platform'].append(platform)
        upload_dict['acq_datetime'].append(acq_datetime)
        upload_dict['subject_id'].append(subject_id)
        upload_dict['s3_bucket'].append(s3_bucket)
        upload_dict['modality0'].append(modality0)
        upload_dict['modality0.source'].append(modality0_source)
        upload_dict['modality1'].append(modality1)
        upload_dict['modality1.source'].append(modality1_source)
        upload_dict['modality2'].append(modality2)
        upload_dict['modality2.source'].append(modality2_source)

output_df = pd.DataFrame.from_dict(upload_dict)
output_df.to_csv(os.path.join(CO_save_path,'uplpoad_job_ALL.csv'))
        
        
        
        
    
        
            


