#
# Jason S. McMullan (c) 2019
#

import argparse
import os
import sys

import chitubox.session


def _human_value(value):
    if value < 2048:
        return str(value) + "b"
    elif value < 2048 * 1024:
        return "%.2f" % (value / 1024) + "Kb"
    elif value < 2048 * 1024 * 1024:
        return "%.2f" % (value / 1024 / 1024) + "Mb"
    else:
        return "%.2f" % (value / 1024 / 1024 / 1024) + "Gb"


def _progress(filename="", offset=0, total=1):
    sys.stdout.write("%s: %s/%s\r" %
                     (filename, _human_value(offset), _human_value(total)))
    if offset == total:
        sys.stdout.write("\n")


def cli(argv=[]):
    """Command line interface to ChuTuBox LCD Printers
    """

    parser = argparse.ArgumentParser()

    parser.add_argument("--ip", "-i", action="store", required=True)

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--list", "-L", action="store_true", default=False)
    group.add_argument("--query", "-Q", action="store_true", default=False)
    group.add_argument("--axis-z", "-Z", action="store_true", default=False)
    group.add_argument("--version", "-V", action="store_true", default=False)
    group.add_argument("--print", "-P", action="store_true", default=False)
    group.add_argument("--upload", "-U", action="store_true", default=False)
    group.add_argument("--download", "-D", action="store_true", default=False)

    parser.add_argument("files", nargs="*")

    args = parser.parse_args(argv)

    session = chitubox.session.Session(ip=args.ip)
    session.progress = _progress

    if args.list:
        fileset = session.list("/", recurse=True)
        for fname, length in fileset:
            print(fname, _human_value(length))
    elif args.query:
        config = session.query_config()
        print("Resolution: x:%.4f, y:%.4f, z:%.5f mm" %
              (config['X'], config['Y'], config['Z']))
        try:
            status = session.print_status()
            print(status)
            status = session.query_status()
            print(status)
        except:
            print("Not printing")
    elif args.axis_z:
        print(session.query_axes()['Z'])
    elif args.version:
        print(session.query_version())
    elif args.print:
        print(session.start_print(args.print))
    elif args.upload:
        for filename in args.files:
            with open(filename, "rb") as fd:
                session.upload(os.path.basename(filename), fd)
    elif args.download:
        for filename in args.files:
            with open(os.path.basename(filename), "wb") as fd:
                session.download(filename, fd)
    else:
        parser.help()
        return 255

    return 0


if __name__ == "__main__":
    sys.exit(cli(sys.argv[1:]))
