#!/usr/bin/env python
from __future__ import print_function, absolute_import, division

import logging

from errno import ENOENT

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn


class webfs(LoggingMixIn, Operations):
    '''
    A simple webfs filesystem.
    '''

    def __init__(self, url):
        self.url = url

    def getattr(self, path):
        try:
            st = self.sftp.lstat(path)
        except IOError:
            raise FuseOSError(ENOENT)

        return dict((key, getattr(st, key)) for key in (
            'st_atime', 'st_gid', 'st_mode', 'st_mtime', 'st_size', 'st_uid'))

    def read(self, path, size, offset):
        f = self.sftp.open(path)
        f.seek(offset, 0)
        buf = f.read(size)
        f.close()
        return buf

    def readdir(self, path):
        return ['.', '..'] + [name.encode('utf-8')
                              for name in self.sftp.listdir(path)]

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('mount')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)


    fuse = FUSE(
        webfs(args.url),
        args.mount,
        foreground=True,
        nothreads=True,
        allow_other=True)
