#!/usr/bin/env python
from __future__ import print_function, absolute_import, division

import logging

import requests, os, re

from errno import ENOENT

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn


class webfs(LoggingMixIn, Operations):
    '''
    A simple webfs filesystem.
    '''

    def __init__(self, url):
        self.url = url
        self.fd = 0

    def getattr(self, path, fh=None):
        wh = self.getwebheader(path)
        if "Content-Length" in wh:
            st_size = int(wh["Content-Length"])
        else:
            st_size = 0
        tplist = path.split("/")
        ppath = "/".join([i for i in tplist if i != ""][0:-1]) + "/"
        w = self.getweb(ppath)
        if re.search('a href="' + path.lstrip("/") + '/"', w) or path == "/":
            st_mode = 0o40555
        else:
            st_mode = 0o100444
        attr_dict = {
            "st_mode": st_mode,
            "st_size": st_size,
                 }
        return attr_dict

    getxattr = None
    listxattr = None
    
    def open(self, path, flags):
        self.fd += 1
        return self.fd

    def read(self, path, size, offset, fh):
        w = self.getweb(path, size, offset)
        return w

    def readdir(self, path, fh):
        nulldir = ['.', '..']
        w = self.getweb(path)
        allfiles = re.findall('a href="(.*)"', w)
        dirs = [fs[0:-1] for fs in allfiles if fs.endswith("/")]
        files = [fs for fs in allfiles if not fs.endswith("/")]
        rsdir = files + dirs + nulldir
        return rsdir

    def getweb(self, path, size=None, offset=None):
        if size != None:
            headers = {"Range": "bytes=%d-%d" % (offset, offset + size)}
        else:
            headers = {}
        r = requests.get(self.url + path, headers=headers)
        return r.content

    def getwebheader(self, path):
        r = requests.head(self.url + path)
        return r.headers

    def release(self, path, fh):
        return os.close(fh)

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
