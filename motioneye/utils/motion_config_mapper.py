import os
import yaml
from collections import OrderedDict
from typing import Any, Dict, Tuple
from motioneye import settings

class MotionConfigMapper:
    motion_version = None
    motioneye_map = None
    motion_map = None

    def __init__(self, motion_version: str) -> None:
        self.motion_version = motion_version
        self.load_motion_map()
        self.load_motioneye_map()

    def load_motion_map(self) -> None:
        mpath = os.path.join(settings.PROJECT_PATH, f'utils/motion/motion_{self.motion_version}.yaml')
        with open(mpath, "r") as f:
            self.motion_map = yaml.load(f, Loader=yaml.SafeLoader)
    
    def load_motioneye_map(self) -> None:
        mpath = os.path.join(settings.PROJECT_PATH, 'utils/motion/motioneye.yaml')
        with open(mpath, "r") as f:
            self.motioneye_map = yaml.load(f, Loader=yaml.SafeLoader)

    def _format_parameter_value(self, parameter: Any, value: Any) -> Any:
        if parameter not in self.motioneye_map['params']:
            print(f"_get_proper_parameter_value: invalid parameter {parameter} {value}")
            return None
        
        parameter_type = self.motioneye_map['params'][parameter]['type']
        if parameter_type == "bool":
            if isinstance(value, bool):
                return 'on' if value else 'off'

            return value

        if parameter_type == "int":
            return int(value)

        return value

    def _resolve_motion_values_list(self, config_list: list) -> Dict[str, Any]:
        remapped_config = {}
        config = dict(x.split('=')for x in config_list.split(","))
        for mkey, mvalue in config.items():
            key, value = self._remap_param(mkey, mvalue, False)
            remapped_config[key] = value

        return remapped_config

    def _remap_param(self, key: Any, value: Any, handle_list: bool=True) -> Tuple[Any, Any]:
        for motioneye_key, values in self.motion_map['params'].items():
            if handle_list and 'mlist_name' in values:
                if values['mlist_name'] != key:
                    continue

                return self._resolve_motion_values_list(value)

            if key != values['mname']:
                continue

            return motioneye_key, value

        return key, value

    def convert_from_ver(self, config: Dict[Any, Any]) -> Dict[Any, Any]:
        converted = OrderedDict()
        for key, value in config.items():
            result = self._remap_param(key, value)
            if isinstance(result, tuple):
                converted[result[0]] = result[1]
            elif isinstance(result, dict):
                converted.update(result)
            else:
                print(f'Invalid conversion {key} {value}')

        return converted

    def convert_to_ver(self, params: Dict[Any, Any]) -> Dict[Any, Any]:
        converted_params = OrderedDict()
        for key, value in params.items():
            if key.startswith("@"):
                converted_params[key] = value
                continue
            elif key not in self.motioneye_map['params']:
                print(f'Key {key} not found in motioneye map')
                continue

            motion_param = self.motion_map['params'].get(key, None)

            # TODO we could validate values(correct values given in mapping files)

            if not motion_param:
                converted_params[key] = self._format_parameter_value(key, value)
                continue

            # TODO need to validate if parameter type has changed?
            if 'mlist_name' in motion_param:
                key_name = key if not motion_param['mname'] else motion_param['mname']
                new_option = f'{key_name}={self._format_parameter_value(key, value)}'
                if motion_param['mlist_name'] not in converted_params:
                    converted_params[motion_param['mlist_name']] = new_option
                    continue

                converted_params[motion_param['mlist_name']] += f',{new_option}'
            else:
                converted_params[motion_param['mname']] = self._format_parameter_value(key, value)


        return converted_params
