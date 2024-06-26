

from datetime import datetime
from pathlib import Path

from aind_metadata_mapper.bergamo.session import (
    BergamoEtl,
    JobSettings,
    RawImageInfo,
)

import pandas as pd
import os,datetime,json
import numpy as np
version = 5#4
# version 5 - tiff file list added to stimulusepoch and tiff file stem to streams
# version 4 - updated rig json matching (Mekhla) and imaging wavelength customized
overwrite_metadata = False
extracted_data_folders = '/home/jupyter/bucket/CodeOcean_transfer/'
upload_job_pd = pd.read_csv(os.path.join(extracted_data_folders,'uplpoad_job.csv'))
# wavelenght dictionary: the default is 920 nm, for given mice, wavelength can be changed
imaging_wavelength_dict = {'980':[650921,683842,685615,685613,685611,688405,687399,695205,
                                  686681,698158,687408,705363,705360,708792,706604,711604,715261],
                          '990':[710358,716537,714729,716539,716540,716542,729854,692996,
                                 693001,693010,710355,693011,696202,706952,706957,706956,
                                 696198,619081,693011,633069]}
for session_row in upload_job_pd.iterrows():
    session_row = session_row[1]
    
    
        # check if metadata is already done
    
    ophys_dir = ''
    behavior_dir = ''
    behavior_video_dir = ''
    behavior_data = ''
    goodtrials = []
    hittrials = []
    is_side_camera_active = False
    is_bottom_camera_active = False
    for modality_i in np.arange(10):
        if 'modality{}'.format(modality_i) not in session_row.keys():
            break
        if session_row['modality{}'.format(modality_i)] == 'ophys':
            ophys_dir =  session_row['modality{}.source'.format(modality_i)]
        elif session_row['modality{}'.format(modality_i)] == 'trained_behavior':
            behavior_dir =  session_row['modality{}.source'.format(modality_i)]
        elif session_row['modality{}'.format(modality_i)] == 'behavior_videos':
            behavior_video_dir =  session_row['modality{}.source'.format(modality_i)]
    
    
    
    try:    
        with open(Path('/'.join(behavior_dir.split('/')[:-1]),'session.json')) as json_data:
            d = json.load(json_data)
            json_data.close()
        version_now = int(d['notes'][d['notes'].find('version')+7:])
    except:
        version_now = 0
    if version_now == version and overwrite_metadata==False:
        print('metadata already exist with same version, skipping {}'.format(behavior_dir.split('/')[-2]))
    else:
        print('extracting metadata for {}'.format(behavior_dir.split('/')[-2]))
        
        
    
    behavior_files = os.listdir(behavior_dir)
    for behavior_file in behavior_files:
        if'bpod_zaber.npy' in behavior_file:
            behavior_data=np.load(os.path.join(behavior_dir,behavior_file),allow_pickle = True).tolist()
            break

    for r,sfn in zip(behavior_data['reward_L'],behavior_data['scanimage_file_names']):
        if type(sfn) == str:
            goodtrials.append(False)
        else:
            goodtrials.append(True)
        if len(r)==0:
            hittrials.append(False)
        else:
            hittrials.append(True)
    goodtrials = np.asarray(goodtrials)    
    hittrials = np.asarray(hittrials)    
    
    for movienames in behavior_data['behavior_movie_name_list'][goodtrials]:
        for moviename in movienames:
            if 'side' in moviename:
                is_side_camera_active = True
            if 'bottom' in moviename:
                is_bottom_camera_active = True
            if is_bottom_camera_active and is_side_camera_active:
                break
        if is_bottom_camera_active and is_side_camera_active:
                break
    cn_num = []
    for cn_now in behavior_data['scanimage_roi_outputChannelsRoiNames']:
        cn_num.append(len(cn_now))
    cn_num = int(np.mean(np.asarray(cn_num)[goodtrials]))
    if cn_num ==1:
        behavior_task_name = "single neuron BCI conditioning"
    elif cn_num ==2:
        behavior_task_name = "two neuron BCI conditioning"
    elif cn_num>2:
        behavior_task_name = "multi-neuron BCI conditioning"
    else:
        print('how many CNs??')
        asdasd
    print(behavior_task_name)
    #ry:
    imaging_laser_wavelength = 920
    for wl in imaging_wavelength_dict.keys():
        if int(session_row['subject_id']) in imaging_wavelength_dict[wl]:
            imaging_laser_wavelength = int(wl)
            print('imaging wavelength is {} nm'.format(wl))
    user_settings = JobSettings(input_source=Path(ophys_dir),
                                output_directory=Path('/'.join(behavior_dir.split('/')[:-1])),
                                experimenter_full_name=["Kayvon Daie", "Marton Rozsa"],
                                subject_id=str(int(session_row['subject_id'])),
                                imaging_laser_wavelength = imaging_laser_wavelength,
                                fov_imaging_depth= 200,
                                fov_targeted_structure= 'Primary Motor Cortex',
                                notes= 'This metadata was generated from old data post-hoc on {} - version {}'.format(datetime.datetime.now(),version),
                                session_type= "BCI",
                                iacuc_protocol=  "2109",
                                rig_id=  "442_Bergamo_2p_photostim",
                                behavior_camera_names= np.asarray(["Side Face Camera","Bottom Face Camera"])[np.asarray([is_side_camera_active,is_bottom_camera_active])].tolist(),
                                imaging_laser_name= "Chameleon Laser",
                                photostim_laser_name= "Monaco Laser",
                                photostim_laser_wavelength=  1035,
                                starting_lickport_position= [0,
                                                             -1*np.abs(np.median(behavior_data['zaber_reward_zone']-behavior_data['zaber_limit_far'])),
                                                             0],
                                behavior_task_name=  behavior_task_name,
                                hit_rate_trials_0_10= np.nanmean(hittrials[goodtrials][:10]),
                                hit_rate_trials_20_40=  np.nanmean(hittrials[goodtrials][20:40]),
                                total_hits= sum(hittrials[goodtrials]),
                                average_hit_rate=  sum(hittrials[goodtrials])/sum(goodtrials),
                                trial_num=sum(goodtrials))
    etl_job = BergamoEtl(job_settings=user_settings,)
    session_metadata = etl_job.run_job()
#     try:
#         session_metadata = etl_job.run_job()
#     except:
#         print('error during generating metadata.. skipping')
        
    # except:
    #     print('error, could not extract metadata')
    
            
    #asd

