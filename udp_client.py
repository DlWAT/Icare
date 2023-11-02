#udp_client.py
import socket

target_host = '192.168.237.221'
target_port = 7210

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
nBytes = client.sendto('ABCDEF'.encode('utf-8'), (target_host, target_port))
print(nBytes, 'Bytes', 'Send OK')
data, addr = client.recvfrom(4096)
print(data.decode('utf-8'), addr[0], ':', addr[1])