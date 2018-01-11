#!/usr/bin/python

import sys
sys.path.append('/home/amargan/work/code/ecat_dev/ec_master_test/build/protobuf')
import ec_boards_base_input_pb2
from protobuf_to_dict import protobuf_to_dict


if __name__ == '__main__' :
    
    zz = ec_boards_base_input_pb2.Ec_board_base_input
    zz