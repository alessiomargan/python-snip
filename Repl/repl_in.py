#!/usr/bin/env python3

import sys
import os
import time
import yaml
import zmq
import argparse
import ec_boards_base_input_pb2 as repl_cmd
from protobuf_to_dict import protobuf_to_dict, dict_to_protobuf


def repl_option():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file_yaml", dest="repl_yaml", action="store", default="")
    parser.add_argument("-c", dest="cmd_exec_cnt", action="store", type=int, default=1)
    args = parser.parse_args()
    dict_opt = vars(args)
    return dict_opt


class PipeIO(object):

    nrt_pipe_path = '/proc/xenomai/registry/rtipc/xddp/'
    rt_pipe_path = '/tmp/nrt_pipes/'

    def __init__(self):

        self.wr_to, self.rd_from = self._open_pipes()

    def _open_pipes(self):
        for dir_path in [self.rt_pipe_path, self.nrt_pipe_path]:
            if os.path.isdir(dir_path):
                try:
                    _wr_to = open(os.path.join(dir_path, 'repl_in'), 'wb')
                    _rd_from = open(os.path.join(dir_path, 'repl_out'), 'rb')
                    return _wr_to, _rd_from
                except IOError as e:
                    print(e)
                    raise e

    def send_to(self, serialized):
        msg_size = len(serialized)
        self.wr_to.write(msg_size.to_bytes(4, byteorder='little'))
        self.wr_to.write(serialized)
        self.wr_to.flush()

    def recv_from(self):
        rep_size = int.from_bytes(self.rd_from.read(4), byteorder='little')
        rep = repl_cmd.Cmd_reply()
        rep.ParseFromString(self.rd_from.read(rep_size))
        return rep

class SocketIO(object):

    def __init__(self):

        #  Prepare our context and sockets
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")

    def send_to(self, serialized):
        #msg_size = len(serialized)
        #self.socket.send_multipart(msg_size.to_bytes(4, byteorder='little'), serialized)
        self.socket.send(serialized)

    def recv_from(self):
        rep_data = self.socket.recv()
        rep = repl_cmd.Cmd_reply()
        rep.ParseFromString(rep_data)
        print(rep)
        return rep


if __name__ == '__main__':

    opts = repl_option()

    #io = PipeIO()
    io = SocketIO()

    d = yaml.load(open(opts["repl_yaml"], 'r'))
    #print(d)

    cnt = opts["cmd_exec_cnt"]
    while cnt:

        print("cmd_exec_cnt", cnt)
        cnt -= 1

        for cmd_dict in d['cmds']:
            ''' prepare cmd '''
            # cmd_dict = {"type": "SET_FLASH_CMD", "flash_cmd": {"type": "LOAD_DEFAULT_PARAMS", "board_id": 696}}
            cmd = dict_to_protobuf(repl_cmd.Repl_cmd, cmd_dict)
            # print(cmd)
            io.send_to(cmd.SerializeToString())

            ''' wait reply ... blocking'''
            reply = io.recv_from()

            time.sleep(0.01)

        time.sleep(0.05)

    print("Exit")
