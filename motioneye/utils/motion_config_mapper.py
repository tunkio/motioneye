import os
import yaml
import json
import logging
from collections import OrderedDict
from typing import Any, Dict, Tuple
from motioneye import settings


class MotionConfigMapper:
    motion_version = None
    motioneye_map = None
    motion_map = None

    def __init__(self, motion_version: str='') -> None:
        if motion_version:
            self.motion_version = motion_version
            self.load_motion_map()

        self.load_motioneye_map()

    def _get_motion_conf_filepath(self, version: str):
        return os.path.join(settings.PROJECT_PATH, f'utils/motion/motion_{version}.yaml')

    def load_motion_map(self, version: str='', fallback: bool=True) -> None:
        if not version:
            version = self.motion_version

        mpath = self._get_motion_conf_filepath(version)
        if not os.path.isfile(mpath):
            logging.debug(f'load_motion_map map file {mpath} not found')
            if not fallback:
                raise Exception(f'Invalid motion config mapping {mpath} requested')

            version_split = self.motion_version.split(".")
            major_version = f'{version_split[0]}.{version_split[1]}'
            mpath = self._get_motion_conf_filepath(major_version)
            logging.debug(f'load_motion_map trying map file with major version {mpath}')
            if not os.path.isfile(mpath):
                mpath = self._get_motion_conf_filepath("4.4")
                logging.warning('Failed to resolve proper motion config mapper file. Using default 4.4')

        logging.debug(f'motion config map file {mpath}')

        self.motion_map = None
        with open(mpath, "r") as f:
            self.motion_map = yaml.load(f, Loader=yaml.SafeLoader)
    
    def load_motioneye_map(self) -> None:
        mpath = os.path.join(settings.PROJECT_PATH, 'utils/motion/motioneye.yaml')
        with open(mpath, "r") as f:
            self.motioneye_map = yaml.load(f, Loader=yaml.SafeLoader)

    def _format_parameter_value(self, parameter: Any, value: Any) -> Any:
        if parameter not in self.motioneye_map['params']:
            logging.warning(f"_get_proper_parameter_value: invalid parameter {parameter}")
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
        config = dict(x.split('=') for x in config_list.split(","))
        for mkey, mvalue in config.items():
            key, value = self._remap_param(mkey, mvalue, False)
            remapped_config[key] = value

        return remapped_config

    def _remap_param(self, key: Any, value: Any, handle_list: bool=True) -> Tuple[Any, Any]:
        for motioneye_key, values in self.motion_map['params'].items():
            if handle_list and 'mlist_name' in values:
                if values['mlist_name'] != key:
                    continue

                logging.debug(f'MotionConfigMapper:_remap_param resolve_motion_values_list {motioneye_key}')

                return self._resolve_motion_values_list(value)

            if values['mtype'] == 'none' or key != values['mname']:
                continue

            logging.debug(f'MotionConfigMapper:_remap_param key {key}->{motioneye_key}')
            return motioneye_key, value

        logging.debug(f'MotionConfigMapper:_remap_param no conversion done for key {key}')
        return key, value

    def convert_from_version(self, config: Dict[Any, Any], version: str='') -> Dict[Any, Any]:
        if version:
            self.load_motion_map(version, fallback=False)

        converted = OrderedDict()
        for key, value in config.items():
            result = self._remap_param(key, value)
            if isinstance(result, tuple):
                converted[result[0]] = result[1]
            elif isinstance(result, dict):
                converted.update(result)
            else:
                logging.warning(f'Invalid conversion {key}')

        return converted

    def convert_to_version(self, config: Dict[Any, Any], version: str='') -> Dict[Any, Any]:
        if version:
            self.load_motion_map(version, fallback=False)

        converted_params = OrderedDict()
        for key, value in config.items():
            if key.startswith('@'):
                converted_params[key] = value
                continue
            elif key not in self.motioneye_map['params']:
                logging.warning(f'MotionConfigMapper:convert_to_version Key {key} not found in motioneye map')
                continue

            motion_param = self.motion_map['params'].get(key, None)

            if not motion_param:
                logging.debug(f'MotionConfigMapper:convert_to_version mapping not found for {key}. No conversion done.')
                converted_params[key] = self._format_parameter_value(key, value)
                continue

            if motion_param['mtype'] == 'none':
                logging.warning(f'Unsupported parameter {key}. Adding it into config but it won\'t affect to anything.')
                converted_params[key] = value
                continue

            if 'mlist_name' in motion_param:
                key_name = key if not motion_param['mname'] else motion_param['mname']
                new_option = f'{key_name}={self._format_parameter_value(key, value)}'
                if motion_param['mlist_name'] not in converted_params:
                    logging.debug(f'MotionConfigMapper:convert_to_version adding new list {motion_param["mlist_name"]} option {new_option}')
                    converted_params[motion_param['mlist_name']] = new_option
                    continue

                logging.debug(f'MotionConfigMapper:convert_to_version extending list {motion_param["mlist_name"]}  with option {new_option}')
                converted_params[motion_param['mlist_name']] += f',{new_option}'
            else:
                param_value = self._format_parameter_value(key, value)
                logging.debug(f'MotionConfigMapper:convert_to_version converted {key}->{motion_param["mname"]}')
                converted_params[motion_param['mname']] = param_value

        return converted_params

