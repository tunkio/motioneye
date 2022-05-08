import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.motion_config_mapper import *

conf = {
    'netcam_url': "http://hihhei.com/1234123",
    'netcam_userpass': "testiuser:testipassword",
    'netcam_keepalive': 'on',
    'netcam_tolerant_check': True,
    'netcam_use_tcp': False,
    'width': 640,
    'height': 480,
    'contrast': 10,
    'power_line_frequency': 15,
    'hue': 100,
    'saturation': 50,
    'movie_quality': 80,
    'movie_extpipe': 'testiextpipe',
    'netcam_use_tcp': 'off',
    'movie_quality': 15,
    'picture_exif': 'test_picture_exif',
    'picture_quality': 75,
    'v4l2_palette': 10
}

def get_camera_config(camera_file):
    with open(camera_file, "r") as f:
        lines = f.readlines()

    camera_dict = {}

    for line in lines:
        if line.strip() == "":
            continue

        if line.startswith("#") or line.startswith(";"):
            continue

        line_split = line.strip().replace("\n", "").split(" ", 1)
        if len(line_split) != 2:
            continue

        camera_dict[line_split[0]] = line_split[1]
    return camera_dict

motions = ["4.1.0", "4.2.2", "4.4.0"]

for motion in motions:
    camera_config = get_camera_config("utils/motion/camera-%s.conf" % motion)
    print("MOTION %s" % motion)
    mc = MotionConfigMapper(motion)
    print("---- Conversion from motioneye to %s" % motion)
    print(json.dumps(mc.convert_to_ver(conf), indent=4))
    print("---- Conversion from %s to motioneye" % motion)
    print(json.dumps(mc.convert_from_ver(camera_config), indent=4))
    print("END MOTION %s" % motion)


