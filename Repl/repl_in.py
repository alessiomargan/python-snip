#!/usr/bin/env python3

import yaml
import argparse

from pipe_io import PipeIO
from zmsg_io import ZmsgIO


def repl_option():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file_yaml", dest="repl_yaml", action="store", default="repl.yaml")
    parser.add_argument("-c", dest="cmd_exec_cnt", action="store", type=int, default=1)
    args = parser.parse_args()
    dict_opt = vars(args)
    return dict_opt


def gen_cmds(cmds):

    for cmd in cmds:
        if 'board_id_list' in cmd:
            id_list = cmd['board_id_list']
            del cmd['board_id_list']
            for _id in id_list:
                if 'ctrl_cmd' in cmd:
                    cmd['ctrl_cmd']['board_id'] = _id
                if 'flash_cmd' in cmd:
                    cmd['ctrl_cmd']['board_id'] = _id
                yield cmd
        else:
            yield cmd


if __name__ == '__main__':

    opts = repl_option()
    d = yaml.load(open(opts["repl_yaml"], 'r'), Loader=yaml.FullLoader)

    if ( d['use_zmq']):
        io = ZmsgIO(d['uri'])
    else:
        io = PipeIO()

    #print(d)

    cnt = opts["cmd_exec_cnt"]
    while cnt:

        print("cmd_exec_cnt", cnt)
        cnt -= 1

        #test_dict = {"type": "ECAT_MASTER_CMD", "ecat_master_cmd": {"type": "GET_SLAVES_DESCR"}}
        #io.send_to(test_dict)
        #''' wait reply ... blocking'''
        #reply = io.recv_from()

        if not 'cmds' in d:
            continue

        for cmd_dict in gen_cmds(d['cmds']):
            ''' send cmd '''
            io.send_to(cmd_dict)
            ''' wait reply ... blocking'''
            reply = io.recv_from()

            #time.sleep(0.01)

        #time.sleep(0.05)

    print("Exit")
