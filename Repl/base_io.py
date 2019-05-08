import math

master_cmd_stop = {"type": "ECAT_MASTER_CMD", "ecat_master_cmd": {"type": "STOP_MASTER"}}
master_cmd_start = {"type": "ECAT_MASTER_CMD", "ecat_master_cmd": {"type": "START_MASTER"}}
master_cmd_get_slave_descr = {"type": "ECAT_MASTER_CMD", "ecat_master_cmd": {"type": "GET_SLAVES_DESCR"}}

_flash_cmd_save2flash = {"type": "FLASH_CMD", "flash_cmd": {"type": "SAVE_PARAMS_TO_FLASH", "board_id": -1}}

_ctrl_cmd_start = {"type": "CTRL_CMD", "ctrl_cmd": {"type": "CTRL_CMD_START", "board_id": -1}}
_ctrl_cmd_stop  = {"type": "CTRL_CMD", "ctrl_cmd": {"type": "CTRL_CMD_STOP", "board_id": -1}}

_ctrl_cmd_fan = {"type": "CTRL_CMD", "ctrl_cmd": {"type": "CTRL_FAN", "value": 1, "board_id": -1}}
_ctrl_cmd_led = {"type": "CTRL_CMD", "ctrl_cmd": {"type": "CTRL_LED", "value": 1, "board_id": -1}}

_ctrl_cmd_set_home = {"type": "CTRL_CMD", "ctrl_cmd": {"type": "CTRL_SET_HOME", "value": 0, "board_id": -1}}
_ctrl_cmd_set_zero = {"type": "CTRL_CMD", "ctrl_cmd": {"type": "CTRL_SET_ZERO_POSITION", "value": math.pi, "board_id": -1}}
_ctrl_cmd_set_min_pos = {"type": "CTRL_CMD", "ctrl_cmd": {"type": "CTRL_SET_MIN_POSITION", "board_id": -1}}
_ctrl_cmd_set_max_pos = {"type": "CTRL_CMD", "ctrl_cmd": {"type": "CTRL_SET_MAX_POSITION", "board_id": -1}}


def gen_cmds(cmds: list):

    for cmd in cmds:
        if 'board_id_list' in cmd:
            id_list = cmd['board_id_list']
            del cmd['board_id_list']
            for _id in id_list:
                for key in ['ctrl_cmd','flash_cmd','trajectory_cmd']:
                    if key in cmd:
                        cmd[key]['board_id'] = _id
                        break
                    #else:
                        #print("no board_id key ...")
                yield cmd
        else:
            yield cmd


def ctrl_cmd_start(bId=-1):
    if bId > 0:
        _ctrl_cmd_start["ctrl_cmd"]["board_id"] = bId
    return _ctrl_cmd_start


def ctrl_cmd_stop(bId=-1):
    if bId > 0:
        _ctrl_cmd_stop["ctrl_cmd"]["board_id"] = bId
    return _ctrl_cmd_stop


def ctrl_cmd_fan(bId=-1, value=0):
    if bId > 0:
        _ctrl_cmd_fan["ctrl_cmd"]["board_id"] = bId
    _ctrl_cmd_fan["ctrl_cmd"]["value"] = value
    return _ctrl_cmd_fan


def ctrl_cmd_led(bId=-1, value=0):
    if bId > 0:
        _ctrl_cmd_led["ctrl_cmd"]["board_id"] = bId
    _ctrl_cmd_led["ctrl_cmd"]["value"] = value
    return _ctrl_cmd_led


def ctrl_cmd_set_home(bId=-1, value=0):
    if bId > 0:
        _ctrl_cmd_set_home["ctrl_cmd"]["board_id"] = bId
    _ctrl_cmd_set_home["ctrl_cmd"]["value"] = value
    return _ctrl_cmd_set_home


def ctrl_cmd_set_zero(bId=-1, value=math.pi):
    if bId > 0:
        _ctrl_cmd_set_zero["ctrl_cmd"]["board_id"] = bId
    _ctrl_cmd_set_zero["ctrl_cmd"]["value"] = value
    return _ctrl_cmd_set_zero


def ctrl_cmd_set_min_pos(bId=-1):
    if bId > 0:
        _ctrl_cmd_set_min_pos["ctrl_cmd"]["board_id"] = bId
    return _ctrl_cmd_set_min_pos


def ctrl_cmd_set_max_pos(bId=-1):
    if bId > 0:
        _ctrl_cmd_set_max_pos["ctrl_cmd"]["board_id"] = bId
    return _ctrl_cmd_set_max_pos


def flash_cmd_save2flash(bId=-1):
    if bId > 0:
        _flash_cmd_save2flash["flash_cmd"]["board_id"] = bId
    return _flash_cmd_save2flash
