#!/usr/bin/python3
import glob
import os
import shutil
import sys
import logging
import datetime

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)

MOTIONEYE_DIR = '/etc/motioneye'
MOTIONEYE_BACKUP_DIR = '/etc/motioneye/backup'
MOTION_CONF = f'{MOTIONEYE_DIR}/motion.conf'

if len(sys.argv) != 3:
    print(f'\nUsage: python3 {__file__} <from_version> <to_version>\n')
    print(f'Configurations should be located at directory {MOTIONEYE_DIR}. [motion.conf, camera-1.conf ...]\n')
    print(f'Automatic backup will be taken into {MOTIONEYE_BACKUP_DIR}/<from_version>/<datetime>')
    exit(0)

syspath = os.path.join(sys.path[0], '..', '..')
sys.path.insert(1, syspath)

from motioneye.config import *
from motioneye.utils.motion_config_mapper import MotionConfigMapper

from_version = sys.argv[1]
to_version = sys.argv[2]

print(f'Updating motion configuration from {from_version} to {to_version}')

datetime_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
backup_dir = f'{MOTIONEYE_BACKUP_DIR}/{from_version}/{datetime_str}/'
print(f'Creating backup dir {backup_dir}')
os.makedirs(backup_dir, exist_ok=True)

if os.path.isfile(MOTION_CONF):
    print(f'copying {MOTION_CONF} {backup_dir}')
    shutil.copy(MOTION_CONF, backup_dir)

for camera_file in glob.glob(f'{MOTIONEYE_DIR}/camera-*.conf'):
    print(f'copying {camera_file} {backup_dir}')
    shutil.copy(camera_file, backup_dir)

print("Loading motion config")
conf = get_main(motion_version_override=from_version)
print("Updating motion config")
set_main(conf, convert_to_version=to_version)

camera_ids = get_camera_ids(filter_valid=False)
for camera_id in camera_ids:
    print(f'Loading camera config {camera_id} {from_version} {to_version}')
    camera_config = get_camera(camera_id, motion_version_override=from_version, convert_to_version=to_version)
    print(f'Updating camera config {camera_id}')
    set_camera(camera_id, camera_config, motion_version_override=from_version, convert_to_version=to_version)

print("Done")
exit(0)
