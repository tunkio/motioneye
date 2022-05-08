import json
import yaml

class MotionConfigMapper:
    motion_version = None
    motioneye_map = None
    motion_map = None

    def __init__(self, motion_version):
        self.motion_version = motion_version
        self.load_motion_map()
        self.load_motioneye_map()

    def load_motion_map(self):
        with open("motion/motion_%s.yaml" % self.motion_version, "r") as f:
            self.motion_map = yaml.load(f, Loader=yaml.SafeLoader)
    
    def load_motioneye_map(self):
        with open("motion/motioneye.yaml", "r") as f:
            self.motioneye_map = yaml.load(f, Loader=yaml.SafeLoader)

    def _format_parameter_value(self, parameter, value):
        if parameter not in self.motioneye_map['params']:
            print("_get_proper_parameter_value: invalid parameter")
            return None
        
        parameter_type = self.motioneye_map['params'][parameter]['type']
        if parameter_type == "bool":
            return 'on' if value else 'off'

        if parameter_type == "int":
            return int(value)

        return value

    def _resolve_motion_values_list(self, config_list):
        remapped_config = {}
        config = dict(x.split('=')for x in config_list.split(","))
        for mkey, mvalue in config.items():
            key, value = self._remap_param(mkey, mvalue, False)
            remapped_config[key] = value

        return remapped_config

    def _remap_param(self, key, value, handle_list=True):
        for motioneye_key, values in self.motion_map['params'].items():
            if handle_list and 'mlist_name' in values:
                if values['mlist_name'] != key:
                    continue

                return self._resolve_motion_values_list(value)

            if key != values['mname']:
                continue

            return motioneye_key, value

        return key, value

    def convert_from_ver(self, config):
        converted = {}
        for key, value in config.items():
            result = self._remap_param(key, value)
            if isinstance(result, tuple):
                converted[result[0]] = result[1]
            elif isinstance(result, dict):
                converted.update(result)
            else:
                print("Invalid conversion %s %s" % (key, value))

        return converted

    def convert_to_ver(self, params):
        converted_params = {}
        for key, value in params.items():
            if key not in self.motioneye_map['params']:
                print("Key %s not found in motioneye map" % key)
                continue

            motion_param = self.motion_map['params'].get(key, None)

            # TODO we could validate values(correct values given in mapping files)

            if not motion_param:
                converted_params[key] = self._format_parameter_value(key, value)
                continue

            # TODO need to validate if parameter type has changed?
            if 'mlist_name' in motion_param:
                key_name = key if not motion_param['mname'] else motion_param['mname']
                new_option = "%s=%s" % (key_name, self._format_parameter_value(key, value))
                if motion_param['mlist_name'] not in converted_params:
                    converted_params[motion_param['mlist_name']] = new_option
                    continue

                converted_params[motion_param['mlist_name']] += ",%s" % new_option
            else:
                converted_params[motion_param['mname']] = self._format_parameter_value(key, value)


        return converted_params


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

motions = [1, 2, 4]

for motion in motions:
    camera_config = get_camera_config("motion/camera-4.%d.conf" % motion)

    print("MOTION 4.%d" % motion)
    mc = MotionConfigMapper("4.%d" % motion)
    print("---- Conversion from motioneye to 4.%d" % motion)
    print(json.dumps(mc.convert_to_ver(conf), indent=4))
    print("---- Conversion from 4.%d to motioneye" % motion)
    print(json.dumps(mc.convert_from_ver(camera_config), indent=4))
    print("END MOTION 4.%d" % motion)


