#!/usr/bin/python

from  IPython import embed


class WMCoreTool(object):
    """
    """
    def __init__(self):
        self.ident = "WMCoreTool"

    def restClient(self, subsys):
        print("will connect to %s" % subsys)


class RucioClient(WMCoreTool):
    """
    """
    def __init__(self):
        self.ident = "RucioClient"


def main():
    embed()
    wmcoreTool = WMCoreTool()
    return wmcoreTool
