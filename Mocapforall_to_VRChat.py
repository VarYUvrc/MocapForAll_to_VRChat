import argparse
import math
# import time
from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import udp_client

def quaternion_to_euler(q):
    sinX = 2 * q[1] * q[2] - 2 * q[0] * q[3]
    absSinX = abs(sinX)
    e = 0.001

    if absSinX < e:
        sinX = 0

    x = math.asin(-sinX)
    if math.isnan(x) or abs(abs(x) - math.pi / 2) < e:
        x = math.copysign(-sinX, 1) * (math.pi / 2)
        return to_euler_angles_zimbal_lock(x, q)

    cosX = math.cos(x)
    sinY = (2 * q[0] * q[2] + 2 * q[1] * q[3]) / cosX
    cosY = (2 * math.pow(q[3], 2) + 2 * math.pow(q[2], 2) - 1) / cosX
    y = math.atan2(sinY, cosY)

    sinZ = (2 * q[0] * q[1] + 2 * q[2] * q[3]) / cosX
    cosZ = (2 * math.pow(q[3], 2) + 2 * math.pow(q[1], 2) - 1) / cosX
    z = math.atan2(sinZ, cosZ)

    angles = [x, y, z]
    angles = [x * 180 / math.pi for x in angles]
    return [
        normalize(angles[0]),
        normalize(angles[1]),
        normalize(angles[2])
    ]

def normalize(x):
    return (x if x > 0 else 360 + x) % 360

def to_euler_angles_zimbal_lock(x, q):
    sinY = 2 * q[0] * q[1] + 2 * q[3] * q[2]
    cosY = 2 * math.pow(q[3], 2) + 2 * math.pow(q[1], 2) - 1
    y = math.atan2(sinY, cosY)
    sinZ = 2 * q[0] * q[2] + 2 * q[1] * q[3]
    cosZ = 2 * math.pow(q[3], 2) + 2 * math.pow(q[2], 2) - 1
    z = math.atan2(sinZ, cosZ)

    return [
        x * 180 / math.pi,
        y * 180 / math.pi,
        z * 180 / math.pi
    ]

def handle_message(address, *args):
    # MocapForAllのOSCメッセージをVRChat形式に変換する
    client = udp_client.SimpleUDPClient("192.168.0.xxx", 9000) # 自身のMeta QuestのIPアドレスに要変更
    address = address.replace("/VMT/Room/Unity", "/tracking/trackers")
    if int(args[0]) == 9:
        new_address_position = '/tracking/trackers/head/position'
        new_address_rotation = '/tracking/trackers/head/rotation'
    else:
        new_address_position = '/tracking/trackers/' + str(int(args[0])+1) + '/position'
        new_address_rotation = '/tracking/trackers/' + str(int(args[0])+1) + '/rotation'
    
    # Quaternionからオイラー角に変換
    args = list(args)
    quaternion = args[6:] # x, y, z, w = quaternion
    euler = quaternion_to_euler(quaternion)
    args[6:] = euler 
    # print(new_address_rotation, args[6:]) # debug
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
        # time.sleep(10) # 実行間隔(要調整)
    except KeyboardInterrupt:
        print("Exit")
