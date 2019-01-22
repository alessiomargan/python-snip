#!/usr/bin/env python3
import io
import yaml
import ec_boards_base_input_pb2 as repl_cmd
from protobuf_to_dict import protobuf_to_dict, dict_to_protobuf


def repl_option(args):
    parser = OptionParser()
    parser.add_option("--cmd", dest="repl_cmd", action="store", type="string", default="")
    (options, args) = parser.parse_args(args=args)
    dict_opt = vars(options)


def open_pipes():
    try:
        _wr_to = open('/proc/xenomai/registry/rtipc/xddp/repl_in', 'wb')
        _rd_from = open('/proc/xenomai/registry/rtipc/xddp/repl_out', 'rb')
    except IOError as e:
        _wr_to = open('/tmp/nrt_pipes/repl_in', 'wb')
        _rd_from = open('/tmp/nrt_pipes/repl_out', 'rb')

    return _wr_to, _rd_from


def write_to_pipe(serialized, wr_fd):
    msg_size = len(serialized)
    wr_fd.write(msg_size.to_bytes(4, byteorder='little'))
    wr_fd.write(serialized)
    wr_fd.flush()


def read_from_pipe(rd_fd):
    rep_size = int.from_bytes(rd_fd.read(4), byteorder='little')
    rep = repl_cmd.Cmd_reply()
    rep.ParseFromString(rd_from.read(rep_size))
    return rep


if __name__ == '__main__':

    wr_to, rd_from = open_pipes()

    d = yaml.load(open("repl.yaml", 'r'))
    print(d)

    for cmd_dict in d['cmds']:
        ''' prepare cmd '''
        #cmd_dict = {"type": "SET_FLASH_CMD", "flash_cmd": {"type": "LOAD_DEFAULT_PARAMS", "board_id": 696}}
        cmd = dict_to_protobuf(repl_cmd.Repl_cmd, cmd_dict)
        print(cmd)
        write_to_pipe(cmd.SerializeToString(), wr_to)

        ''' wait reply ... blocking'''
        reply = read_from_pipe(rd_from)
        print(reply)

    print("Exit")
