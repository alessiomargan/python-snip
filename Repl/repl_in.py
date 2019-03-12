#!/usr/bin/env python3

import sys
import os
import time
import yaml
import json
import zmq
import argparse
import ec_boards_base_input_pb2 as repl_cmd
from protobuf_to_dict import protobuf_to_dict, dict_to_protobuf


def repl_option():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file_yaml", dest="repl_yaml", action="store", default="repl.yaml")
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

    def send_to(self, cmd: dict):
        cmd_pb = dict_to_protobuf(repl_cmd.Repl_cmd, cmd)
        serialized = cmd_pb.SerializeToString()
        msg_size = len(serialized)
        self.wr_to.write(msg_size.to_bytes(4, byteorder='little'))
        self.wr_to.write(serialized)
        self.wr_to.flush()

    def recv_from(self):
        rep_size = int.from_bytes(self.rd_from.read(4), byteorder='little')
        rep = repl_cmd.Cmd_reply()
        rep.ParseFromString(self.rd_from.read(rep_size))
        return rep


class MultiPartMessage(object):
    header = None

    @classmethod
    def recv(cls, socket):
        """Reads key-value message from socket, returns new instance."""
        return cls.from_msg(socket.recv_multipart())

    @property
    def msg(self):
        return [self.header]

    def send(self, socket, identity=None):
        """Send message to socket"""
        msg = self.msg
        if identity:
            msg = [identity] + msg
        socket.send_multipart(msg)


class HelloMessage(MultiPartMessage):
    header = b"HELLO"


class EscCmdMessage(MultiPartMessage):
    header = b"ESC_CMD"

    def __init__(self, cmd):
        self.cmd = cmd

    @property
    def msg(self):
        # returns list of all message frames as a byte-string:
        return [self.header, self.cmd]


class EcatMasterCmdMessage(MultiPartMessage):
    header = b"ECAT_MASTER_CMD"

    def __init__(self, cmd):
        self.cmd = cmd

    @property
    def msg(self):
        # returns list of all message frames as a byte-string:
        return [self.header, self.cmd]


class zmqIO(object):

    def __init__(self, uri):

        #  Prepare our context and sockets
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.REQ)
        self.socket.connect("tcp://"+uri)

    def send_to(self, cmd: dict):
        "dict -> protobuf -> serialize to string -> send through socket"
        cmd_pb = dict_to_protobuf(repl_cmd.Repl_cmd, cmd)
        # print(cmd_pb)
        if cmd['type'] == "ECAT_MASTER_CMD":
            cmd_msg = EcatMasterCmdMessage(cmd_pb.SerializeToString())
        else:
            cmd_msg = EscCmdMessage(cmd_pb.SerializeToString())
        cmd_msg.send(self.socket)

    def recv_from(self):
        rep_data = self.socket.recv()
        rep = repl_cmd.Cmd_reply()
        # fill protobuf mesg
        rep.ParseFromString(rep_data)
        print(rep)
        d = protobuf_to_dict(rep)
        yaml_msg = yaml.safe_load(d['msg'])
        json_msg = json.dumps(yaml_msg)
        print(json_msg)
        return rep


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
    d = yaml.load(open(opts["repl_yaml"], 'r'))

    if ( d['use_zmq']):
        io = zmqIO(d['uri'])
    else:
        io = PipeIO()

    #print(d)

    cnt = opts["cmd_exec_cnt"]
    while cnt:

        print("cmd_exec_cnt", cnt)
        cnt -= 1

        test_dict = {"type": "ECAT_MASTER_CMD", "ecat_master_cmd": {"type": "GET_SLAVES_DESCR"}}
        io.send_to(test_dict)
        ''' wait reply ... blocking'''
        reply = io.recv_from()

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
