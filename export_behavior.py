import argparse
import BCI_analysis
from pathlib import Path
args = parser.parse_args()
subject_names = [args.arg1]
calcium_imaging_raw_session_dir = args.arg2
save_dir = args.arg3
calcium_imaging_raw_session_dir

raw_behavior_dirs = ['/home/jupyter/bucket/Data/Behavior/raw/KayvonScope/BCI']
zaber_root_folder = '/home/jupyter/bucket/Data/Behavior/BCI_Zaber_data'


BCI_analysis.pipeline_bpod.export_single_pybpod_session(session =Path(calcium_imaging_raw_session_dir).name,
                                                         subject_names = subject_names,
                                                         save_dir= save_dir,
                                                         calcium_imaging_raw_session_dir = calcium_imaging_raw_session_dir,
                                                         raw_behavior_dirs = raw_behavior_dirs,
                                                         zaber_root_folder = zaber_root_folder)
