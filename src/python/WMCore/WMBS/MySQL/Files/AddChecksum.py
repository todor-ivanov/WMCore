#!/usr/bin/env python

"""
MySQL implementation of AddChecksum
"""


__revision__ = "$Id: AddChecksum.py,v 1.1 2009/12/02 19:34:36 mnorman Exp $"
__version__  = "$Revision: 1.1 $"

from WMCore.Database.DBFormatter import DBFormatter

class AddChecksum(DBFormatter):
    sql = """INSERT INTO wmbs_file_checksums (fileid, typeid, cksum)
             SELECT :fileid, (SELECT id FROM wmbs_checksum_type WHERE type = :cktype), :cksum FROM dual
             WHERE NOT EXISTS (SELECT fileid FROM wmbs_file_checksums WHERE
                               fileid = :fileid AND typeid = (SELECT id FROM wmbs_checksum_type WHERE type = :cktype))"""
                
    def execute(self, fileid = None, cktype = None, cksum = None, bulkList = None, conn = None,
                transaction = False):

        if bulkList:
            binds = bulkList
        else:
            binds = {'fileid': fileid, 'cktype': cktype, 'cksum': cksum}

        result = self.dbi.processData(self.sql, binds, 
                         conn = conn, transaction = transaction)

        return
