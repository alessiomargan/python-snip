#!/usr/bin/env python3

import yaml
import json
import zmq
import repl_cmd_pb2 as repl_cmd
from protobuf_to_dict import protobuf_to_dict, dict_to_protobuf


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


class ZmsgIO(object):

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

