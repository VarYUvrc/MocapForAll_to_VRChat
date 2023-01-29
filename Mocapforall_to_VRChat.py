import argparse
import math
import time
from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import udp_client

def quaternion_to_euler(x, y, z, w):
    t0 = 2 * (w * x + y * z)
    t1 = 1 - 2 * (x**2 + y**2)
    X = math.atan2(t0, t1)

    t2 = 2 * (w * y - z * x)
    t2 = 1 if t2 > 1 else t2
    t2 = -1 if t2 < -1 else t2
    Y = math.asin(t2)

    t3 = 2 * (w * z + x * y)
    t4 = 1 - 2 * (y**2 + z**2)
    Z = math.atan2(t3, t4)

    return X, Y, Z

def handle_message(address, *args):
    # MocapForAllのOSCメッセージをVRChat形式に変換する
    client = udp_client.SimpleUDPClient("192.168.xxx.xxx", 9000) # 自身のMeta QuestのIPアドレスに要変更
    address = address.replace("/VMT/Room/Unity", "/tracking/trackers")
    if int(args[0]) == 9:
        new_address_position = '/tracking/trackers/head/position'
        new_address_rotation = '/tracking/trackers/head/rotation'
    else:
        new_address_position = '/tracking/trackers/' + str(int(args[0])+1) + '/position'
        new_address_rotation = '/tracking/trackers/' + str(int(args[0])+1) + '/rotation'
    
    # Quaternionからオイラー角に変換
    args = list(args)
    quaternion = args[6:]
    x, y, z, w = quaternion
    euler = quaternion_to_euler(x, y, z, w)
    args[6:] = euler

    client.send_message(new_address_position, args[3:6])
    client.send_message(new_address_rotation, args[6:])

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port",
                        type=int, default=39570, help="The port to listen on")
    args = parser.parse_args()

    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/*", handle_message)

    server = osc_server.ThreadingOSCUDPServer(
        (args.ip, args.port), dispatcher)
    print("Serving on {}".format(server.server_address))
    try:
        server.serve_forever()
        time.sleep(0.02) # 実行間隔(要調整)
    except KeyboardInterrupt:
        print("Exit")
