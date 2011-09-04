#!/usr/bin/env python
"""
WorkQueue splitting by block

"""
__all__ = []



from WMCore.WorkQueue.Policy.Start.StartPolicyInterface import StartPolicyInterface
from math import ceil
from WMCore.WorkQueue.WorkQueueExceptions import WorkQueueWMSpecError
from WMCore.WorkQueue.DataStructs.ACDCBlock import ACDCBlock
from WMCore.ACDC.DataCollectionService import DataCollectionService

class ResubmitBlock(StartPolicyInterface):
    """Split elements into blocks"""
    def __init__(self, **args):
        StartPolicyInterface.__init__(self, **args)
        self.args.setdefault('SliceType', 'NumberOfFiles')
        self.args.setdefault('SliceSize', 1)

    def split(self):
        """Apply policy to spec"""
        for block in self.validBlocks(self.initialTask):
            parents = []
            if self.initialTask.parentProcessingFlag():
                parentFlag = True
            else:
                parentFlag = False
            self.newQueueElement(Inputs = {block['Name'] : block['Sites']},
                                 ParentFlag = parentFlag,
                                 Jobs = ceil(float(block[self.args['SliceType']]) /
                                             float(self.args['SliceSize'])),
                                 ACDC = block['ACDC'],
                                 )


    def validate(self):
        """Check args and spec work with block splitting"""
        StartPolicyInterface.validateCommon(self)

    def validBlocks(self, task):
        """Return blocks that pass the input data restriction"""
        validBlocks = []
        # TODO take the chunk size from parameter
        chunkSize = 200
        
        acdcInfo = task.getInputACDC()
        acdc = DataCollectionService(acdcInfo["server"], acdcInfo["database"])
        if self.data:
            acdcBlockSplit = ACDCBlock.splitBlockName(self.data)
        else:
            #if self.data is not passed, assume the the data is input dataset
            # from the spec
            acdcBlockSplit = False

        if acdcBlockSplit:
            dbsBlock = {}
            dbsBlock['Name'] = self.data
            block = acdc.getChunkInfo(acdcInfo['collection'],
                                      acdcBlockSplit['TaskName'],
                                      acdcBlockSplit['Offset'],
                                      acdcBlockSplit['NumOfFiles'],
                                      user = self.wmspec.getOwner().get("name"),
                                      group = self.wmspec.getOwner().get("group"))
            dbsBlock['NumberOfFiles'] = block['files']
            dbsBlock['NumberOfEvents'] = block['events']
            #TODO: needs this for lumi splitting
            dbsBlock['NumberOfLumis'] = block['lumis']
            dbsBlock["Sites"] = block["locations"]
            validBlocks.append(dbsBlock)
        else:
            acdcBlocks = acdc.chunkFileset(acdcInfo['collection'],
                                           acdcInfo['fileset'],
                                           chunkSize,
                                           user = self.wmspec.getOwner().get("name"),
                                           group = self.wmspec.getOwner().get("group"))
            for block in acdcBlocks:
                dbsBlock = {}
                dbsBlock['Name'] = ACDCBlock.name(self.wmspec.name(),
                                                  acdcInfo["fileset"],
                                                  block['offset'], block['files'])
                dbsBlock['NumberOfFiles'] = block['files']
                dbsBlock['NumberOfEvents'] = block['events']
                #TODO: needs this for lumi splitting
                dbsBlock['NumberOfLumis'] = block['lumis']
                dbsBlock["Sites"] = block["locations"]
                dbsBlock['ACDC'] = acdcInfo
                validBlocks.append(dbsBlock)
            
        return validBlocks
