#
# Copyright 2019, Jason S. McMullan <jason.mcmullan@gmail.com>
#

import socket


class Udp(object):
    """Create a UDP socket connection to a ChiTuBox LCD printer (Anycubic Photon, EPAX X1, etc)
    """

    def __init__(self):
        self._socket = None
        self._send_ip = None
        self._send_port = 3000
        self._bind_port = 3001
        self._encoding = "utf-8"

    def __del__(self):
        self.disconnect()

    def connect(self, ip=None):
        """Connect to a remote printer
        :param ip: IP address
        """

        if not ip:
            self._send_ip = None
            self._socket = None
            self._mtu = 0
        else:
            self._send_ip = ip

            sock = socket.socket(family=socket.AF_INET,
                                 type=socket.SOCK_DGRAM, proto=0)
            sock.connect((self._send_ip, self._send_port))
            sock.settimeout(0.25) # 250ms
            self._socket = sock
            self._mtu = 1500

        return True

    def disconnect(self):
        """Disconnect from a remote printer
        """

        if self._socket is not None:
            self._socket.close()
        self._socket = None
        self._send_ip = None
        self._mtu = 0

    def encoding(self, encode=None):
        current_encoding = self._encoding

        if encode:
            self._encoding = encode

        return current_encoding

    def recv(self):
        if not self._socket:
            raise RuntimeError("No remote session to printer")

        try:
            resp = self._socket.recv(self._mtu)
        except socket.timeout as e:
            return None

        return resp

    def send(self, data=b''):
        if not self._socket:
            raise RuntimeError("No remote session to printer")

        return self._socket.send(data)

    def command(self, gcode=""):

        data = gcode.encode(self._encoding)

        self.send(data + b'\x00\x00')

    def response(self):
        resp = self.recv()
        if resp is None:
            return None

        return resp.decode(self._encoding)
