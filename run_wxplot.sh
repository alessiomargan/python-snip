#! /bin/sh

#ZPUB="alessio-IIT-lap.local:6666"
#ZPUB="amargan-desktop.local:6666"
#ZPUB="amargan-desktop.local:6666"
#ZPUB="10.255.32.91:5555"
#ZPUB="pc104-alessio.local:5555"
#ZPUB="ccub-embedded.local:5555"
#ZPUB="ccub-deb-test.local:6666"
#ZPUB="10.0.0.99:6666"
#ZPUB="carm-deb.local:6666"
ZPUB="ccub-deb-test.local:6666"


#MSG_ID="board_0,board_1,board_2,board_3"
MSG_ID="board_1"
#MSG_ID="pc104"

#SIGNALS="Piezo_out,Position,TT_2,TT_3"
#SIGNALS="Torque"
#SIGNALS="Position,Torque,Target_Pos,PID_out,PID_err"
#SIGNALS="sine,saw,square,triangle"
#SIGNALS="fx,fy,fz"
SIGNALS="Position,Target_pos"
python wx_mpl_dynamic_graph.py --zmq-pub tcp://$ZPUB  --zmq-msg-sub $MSG_ID --signals $SIGNALS --max-samples 4000 --draw-event-freq-ms 500 &

MSG_ID="board_1"
SIGNALS="Delta_tor,PID_err"
python wx_mpl_dynamic_graph.py --zmq-pub tcp://$ZPUB  --zmq-msg-sub $MSG_ID --signals $SIGNALS --max-samples 4000 --draw-event-freq-ms 500 &

MSG_ID="board_2"
SIGNALS="Hip_pos"
python wx_mpl_dynamic_graph.py --zmq-pub tcp://$ZPUB  --zmq-msg-sub $MSG_ID --signals $SIGNALS --max-samples 4000 --draw-event-freq-ms 500 &

MSG_ID="board_2"
SIGNALS="Height"
python wx_mpl_dynamic_graph.py --zmq-pub tcp://$ZPUB  --zmq-msg-sub $MSG_ID --signals $SIGNALS --max-samples 4000 --draw-event-freq-ms 500 &


MSG_ID="board_2"
SIGNALS="Position"
#python wx_mpl_dynamic_graph.py --zmq-pub tcp://$ZPUB  --zmq-msg-sub $MSG_ID --signals $SIGNALS --max-samples 2000 --draw-event-freq-ms 500 &

MSG_ID="board_2"
SIGNALS="Torque"
#python wx_mpl_dynamic_graph.py --zmq-pub tcp://$ZPUB  --zmq-msg-sub $MSG_ID --signals $SIGNALS --max-samples 2000 --draw-event-freq-ms 500 &
