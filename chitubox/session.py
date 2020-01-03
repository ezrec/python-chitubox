#
# Jason S. McMullan (c) 2019
#

import struct
import os

import chitubox.network



class Session(object):
    """Start a ChiTuBox session
    """

    def __init__(self, ip=None, progress = None):
        self._net = chitubox.network.Udp()
        self._net.connect(ip=ip)
        self._progress = progress
        self._progress_interval = 32

        # Read the config
        config = self.query_config()

        # Update the network session's encoding to match the remote
        self._net.encoding(config['U'])

    def progress(self, filename="", offset=0, size=0):
        if self._progress is not None:
            if offset == size or ((offset % (0x500 * self._progress_interval)) == 0):
                self._progress(filename=filename, offset=offset, size=size)

    def _parse_value(self, val=""):
        if len(val) == 0:
            return None
        elif val.startswith("'") and val.endswith("'"):
            return val.strip("'")
        elif '/' in val:
            vals = []
            for subval in val.split("/"):
                vals.append(self._parse_value(subval))
            return vals
        elif '.' in val:
            return float(val)
        else:
            return int(val)

    def _parse_fields(self, s=""):
        fields = {}
        for field in s.split(" "):
            attr, val = field.split(":", 2)
            fields[attr] = self._parse_value(val)
        return fields

    def response(self, fields=True, comment=""):
        result = []
        fieldset = {}
        while True:
            resp = self._net.response()
            if resp == None:
                return None, {}
            resp = resp.strip()
            if resp.startswith("Error"):
                raise RuntimeError(comment + ": " + resp)
            if resp.startswith("resend "):
                offset, rest = resp.split(",")
                dummy, offset = offset.split(" ")
                fieldset["offset"] = int(offset)
                dummy, error = rest.split(":")
                fieldset["offset error"] = int(error)
                return ["resend"], fieldset
            if resp == "ok":
                break
            if resp.startswith("ok "):
                if not fields:
                    result.append(resp)
                else:
                    fieldset = self._parse_fields(resp[3:])
                break
            else:
                result.append(resp)
        return result, fieldset

    def send_gcode(self, gcode="", fields=True):
        self._net.command(gcode=gcode)
        return self.response(fields=fields, comment=gcode)

    def recv_block(self, offset=0):
        block = None
        while block is None:
            self._net.command("M3000 I%d" % (offset))
            block = self._net.recv()
        return block

    def send_block(self, block=b"", comment=""):
        result = None
        fields = {}
        while result is None:
            self._net.send(block)
            result, fields = self.response(fields=False, comment=comment)
        return result, fields

    def list(self, root="/", recurse=False):
        result, fields = self.send_gcode("M20 '" + root + "'")
        if len(result) < 2:
            raise RuntimeError("M20: Response too short")
        elif result[0] != 'Begin file list':
            raise RuntimeError("M20: Unexpected header")
        elif result[-1] != 'End file list':
            raise RuntimeError("M20: Unexpected footer")

        flist = []

        for x in result[1:-1]:
            if x.startswith("->"):
                flist += self.list(os.path.join(root, x[2:]))
            else:
                f, s = x.rsplit(" ", 2)
                s = int(s)
                flist.append((os.path.join(root, f), s))

        return flist

    def query_version(self):
        result, _ = self.send_gcode("M4002", fields=False)

        return result[-1].split(" ", 2)[1]

    def query_config(self):
        result, fields = self.send_gcode("M4001")

        return fields

    def query_status(self):
        result, fields = self.send_gcode("M4000")
        return fields

    def print_status(self):
        result, fields = self.send_gcode("M27")

        return fields

    def query_axes(self):
        result, fields = self.send_gcode("M114")
        return fields

    def start_print(self, filename=None):
        result, fields = self.send_gcode("M6030 ':" + filename + "'")
        return fields

    def delete(self, filename=None):
        result, fields = self.send_gcode("M30 " + filename)
        return result

    def download(self, filename=None, fd=None):
        # Abort any prior download
        self.send_gcode("M22")
        result, fields = self.send_gcode("M6032 :'" + filename + "'")
        print(filename, result, fields)
        length = fields['L']

        # Download data
        curr = 0
        while curr < length:
            block = self.recv_block(offset=curr)
            offset, csum, verify = struct.unpack("<LBB", block[-6:])

            check = 0
            for x in block[:-2]:
                check ^= x

            if check != csum:
                raise RuntimeError(
                    "Checksum failed (%02x != %02x) at offset %d" % (check, csum, curr))

            if verify != 0x83:
                raise RuntimeError("Verification failed at offset %d" % (curr))

            if curr != offset:
                continue

            block = block[:-6]
            curr += len(block)
            fd.write(block)

            self.progress(filename, curr, length)

        self.send_gcode("M22")

    def upload(self, filename=None, fd=None):
        # Abort any prior download
        self.send_gcode("M22")
        result, fields = self.send_gcode("M28 " + filename)

        length = fd.seek(0, 2)
        fd.seek(0)
        while True:
            offset = fd.tell()
            block = fd.read(0x500)
            if len(block) == 0:
                break

            block += struct.pack("<L", offset)

            check = 0
            for x in block:
                check ^= x

            block += struct.pack("<BB", check, 0x83)
            result, fields = self.send_block(block=block, comment="Upload @%d" % (offset))
            if len(result) > 0 and result[0] == "resend":
                fd.seek(fields["offset"])

            self.progress(filename, offset, length)

        self.progress(filename, length, length)

        result, fields = self.send_gcode("M29")
