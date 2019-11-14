"""
Workflow class provides all the workflow data
required by MS Transferor
"""
from __future__ import division, print_function

import operator
from WMCore.DataStructs.LumiList import LumiList
from WMCore.MicroService.Unified.Common import getMSLogger, gigaBytes


class Workflow(object):
    """
    Class to represent a workflow and some helpers to access
    its information within MS
    """

    def __init__(self, reqName, reqData, logger=None, verbose=False):
        self.reqName = reqName
        self.data = reqData
        self.logger = getMSLogger(verbose, logger)

        self.inputDataset = ""
        self.parentDataset = ""
        self.pileupDatasets = set()
        self.campaigns = set()
        self.dataCampaignMap = []
        # these blocks structure will be key'ed by the block name and value'd by the block size
        self.primaryBlocks = {}
        self.parentBlocks = {}
        # sort of duplicate info, but we need to have a way to link input to parent block(s)
        self.childToParentBlocks = {}
        # pileup don't need to get resolved into blocks, store only their total size
        self.secondarySummaries = {}

        self.setDataCampaignMap()
        self.setInputData()

    def __str__(self):
        """
        Write out useful information for this object
        :return:
        """
        res = {'reqName': self.reqName, 'inputDataset': self.inputDataset,
               'parentDataset': self.parentDataset, 'pileupDatasets': self.pileupDatasets,
               'campaigns': self.campaigns, 'dataCampaignMap': self.dataCampaignMap}
        return str(res)

    def getName(self):
        """
        Get this request name
        """
        return self.reqName

    def getDbsUrl(self):
        """
        Get the DbsUrl defined in this request
        """
        return self.data['DbsUrl']

    def getReqType(self):
        """
        Return the request type for this workflow
        """
        return self.data['RequestType']

    def getSitelist(self):
        """
        Get the SiteWhitelist minus the black list for this request
        """
        return sorted(list(set(self.data['SiteWhitelist']) - set(self.data['SiteBlacklist'])))

    def getRunlist(self):
        """
        Get the RunWhitelist minus the black list for this request
        """
        res = set(self._getValue('RunWhitelist', [])) - set(self._getValue('RunBlacklist', []))
        return sorted(list(res))

    def getLumilist(self):
        """
        Get the LumiList parameter and return a LumiList object,
        in case the LumiList is not empty.
        """
        lumiDict = self._getValue('LumiList', {})
        if not lumiDict:
            return {}
        return LumiList(compactList=lumiDict)

    def setDataCampaignMap(self):
        """
        Set the association between input data, data type and campaign name
        in the format of:
        {"type": "type of input data", "name": "dataset name", "campaign": "campaign name"}
        Also set a flat set of campaign names
        """
        inputMap = {"InputDataset": "primary", "MCPileup": "secondary", "DataPileup": "secondary"}

        if "TaskChain" in self.data or "StepChain" in self.data:
            innerDicts = []
            for i in range(1, self.data.get("TaskChain", self.data.get("StepChain")) + 1):
                innerDicts.append(self.data.get("Task%d" % i, self.data.get("Step%d" % i)))
        else:
            # ReReco and DQMHarvesting
            innerDicts = [self.data]

        data = {}
        for item in innerDicts:
            for key in inputMap:
                if key in item and item[key]:
                    # use top level campaign if not available in the inner dict
                    data[item[key]] = dict(type=inputMap[key], name=item[key],
                                           campaign=item.get('Campaign', self.data.get('Campaign')))
            # also create a flat list of campaign names
            if "Campaign" in item and item["Campaign"]:
                self.campaigns.add(item["Campaign"])

        self.dataCampaignMap = data.values()

    def getDataCampaignMap(self):
        """
        Retrieve map of campaign, dataset, dataset type
        :return: list of dictionaries
        """
        return self.dataCampaignMap

    def getCampaigns(self):
        """
        Get a set of campaign names used within this request
        """
        return self.campaigns

    def setInputData(self):
        """
        Parse the request data and set the primary and secondary datasets
        """
        for item in self.getDataCampaignMap():
            if item["type"] == "primary":
                self.inputDataset = item["name"]
            elif item["type"] == "secondary":
                self.pileupDatasets.add(item["name"])

    def getInputDataset(self):
        """
        Get this request's input dataset name
        """
        return self.inputDataset

    def getPileupDatasets(self):
        """
        Get this request's secondary dataset names
        """
        return self.pileupDatasets

    def hasParents(self):
        """
        Check whether the request has IncludeParents
        :return:
        """
        if not self.inputDataset:
            return False
        return self._getValue("IncludeParents", False)

    def setParentDataset(self, parent):
        """
        Set the parent dataset name and update the data/campaign map
        :param parent: string corresponding to the parent dataset name
        """
        self.parentDataset = parent
        self._updateDataCampaignMap(parent)

    def getParentDataset(self):
        """
        Return the parent dataset name
        :return: parent dataset name string
        """
        return self.parentDataset

    def getBlockWhitelist(self):
        """
        Fetch the BlockWhitelist for this workflow
        :return: a list data type with the blocks white listed
        """
        return self._getValue("BlockWhitelist", [])

    def getBlockBlacklist(self):
        """
        Fetch the BlockBlacklist for this workflow
        :return: a list data type with the blocks white listed
        """
        return self._getValue("BlockBlacklist", [])

    def setPrimaryBlocks(self, blocksDict):
        """
        Sets a list of primary input blocks taking into consideration
        the BlockWhitelist and BlockBlacklist
        :param blocksDict: flat dict of block name and block size
        """
        self.primaryBlocks = blocksDict

    def getPrimaryBlocks(self):
        """
        Retrieve list of input primary blocks
        """
        return self.primaryBlocks

    def setSecondarySummary(self, dsetName, dsetSize):
        """
        Sets the secondary dataset name and its total size, in bytes
        :param dsetName: string with the secondary dataset name
        :param dsetSize: integer with the secondary dataset size
        """
        self.secondarySummaries[dsetName] = dsetSize

    def getSecondarySummary(self):
        """
        Retrieve list of input secondary datasets and their sizes
        """
        return self.secondarySummaries

    def setParentBlocks(self, blocksDict):
        """
        Sets a list of parent input blocks and their size.
        NOTE: this list is solely based on the parent dataset, without
        considering what are the actual input primary blocks
        :param blocksDict: flat dict of block name and block size
        """
        self.parentBlocks = blocksDict

    def getParentBlocks(self):
        """
        Retrieve list of input parent blocks
        """
        return self.parentBlocks

    def setChildToParentBlocks(self, blocksDict):
        """
        Sets a relationship between input primary block and its parent block(s)
        This method guarantees that only parent blocks with valid replicas are
        kept around (and later transferred)
        :param blocksDict: dict key'ed by the primary block, with a list of parent blocks
        """
        # flat list with the final parent blocks
        parentBlocks = set()
        # remove parent blocks without any valid replica (only invalid files)
        for child, parents in blocksDict.items():
            if child not in self.getPrimaryBlocks():
                # then we don't need this child+parent data
                continue

            for parent in list(parents):
                if parent not in self.getParentBlocks():
                    # then drop this block
                    parents.remove()
            self.childToParentBlocks[child] = blocksDict[child]
            parentBlocks = parentBlocks | blocksDict[child]

        # Now remove any parent block that don't need to be transferred
        for block in list(self.getParentBlocks()):
            if block not in parentBlocks:
                self.parentBlocks.pop(block, None)

    def getChildToParentBlocks(self):
        """
        Returns a dictionary of blocks and its correspondent list of parents
        """
        return self.childToParentBlocks

    def getChunkBlocks(self, numChunks=1):
        """
        Break down the input and parent blocks by a given number
        of chunks (usually the amount of sites available for data
        placement).
        :param numChunks: integer representing the number of chunks to be created
        :return: it returns two lists:
          * a list of sets, where each set corresponds to a set of blocks to be
            transferred to a single location;
          * and a list integers, which references the total size of each chunk in
            the list above (same order).
        """
        if numChunks <= 1:
            thisChunk = set()
            thisChunk.update(self.getPrimaryBlocks().keys())
            thisChunkSize = sum(self.getPrimaryBlocks().values())
            if self.getParentDataset():
                thisChunk.update(self.getParentBlocks().keys())
                thisChunkSize += sum(self.getParentBlocks().values())
            # keep same data structure as multiple chunks, so list of lists
            return [thisChunk], [thisChunkSize]

        # create a descendant list of blocks according to their sizes
        sortedPrimary = sorted(self.getPrimaryBlocks().items(), key=operator.itemgetter(1), reverse=True)
        chunkSize = sum(item[1] for item in sortedPrimary) // numChunks

        self.logger.info("Found %d blocks and the avg chunkSize is: %s GB",
                         len(sortedPrimary), gigaBytes(chunkSize))
        # list of sets with the block names
        blockChunks = []
        # list of integers with the total block sizes in each chunk (same order as above)
        sizeChunks = []
        for i in range(numChunks):
            thisChunk = set()
            thisChunkSize = 0
            idx = 0
            while True:
                self.logger.debug("Chunk: %d and idx: %s and length: %s", i, idx, len(sortedPrimary))
                if not sortedPrimary or idx >= len(sortedPrimary):
                    # then all blocks have been distributed
                    break
                elif thisChunkSize + sortedPrimary[idx][1] <= chunkSize:
                    thisChunk.add(sortedPrimary[idx][0])
                    thisChunkSize += sortedPrimary[idx][1]
                    sortedPrimary.pop(idx)
                else:
                    idx += 1
            blockChunks.append(thisChunk)
            sizeChunks.append(thisChunkSize)

        # now take care of the leftovers... in a round-robin style....
        while sortedPrimary:
            for chunkNum in range(numChunks):
                blockChunks[chunkNum].add(sortedPrimary[0][0])
                sizeChunks[chunkNum] += sortedPrimary[0][1]
                sortedPrimary.pop(0)
                if not sortedPrimary:
                    break
        self.logger.info("Created %d primary data chunks out of %d chunks",
                         len(blockChunks), numChunks)
        self.logger.info("    with chunk size distribution: %s", sizeChunks)

        if not self.getParentDataset():
            return blockChunks, sizeChunks

        # now add the parent blocks, considering that input blocks were evenly
        # distributed, I'd expect the same to automatically happen to the parents...
        childParent = self.getChildToParentBlocks()
        parentsSize = self.getParentBlocks()
        for chunkNum in range(numChunks):
            parentSet = set()
            for child in blockChunks[chunkNum]:
                parentSet.update(childParent[child])

            # now with the final list of parents in hand, update the list
            # of blocks within the chunk and update the chunk size as well
            blockChunks[chunkNum].update(parentSet)
            for parent in parentSet:
                sizeChunks[chunkNum] += parentsSize[parent]
        self.logger.info("Created %d primary+parent data chunks out of %d chunks",
                         len(blockChunks), numChunks)
        self.logger.info("    with chunk size distribution: %s", sizeChunks)
        return blockChunks, sizeChunks

    def _getValue(self, keyName, defaultValue=None):
        """
        Provide a property/keyName, return its valid value if any
        :param property: dictionary key name
        :param defaultValue: default value in case the key is not found
        :return: valid value (non-empty/false) or None
        """
        resp = defaultValue
        if keyName in self.data and self.data[keyName]:
            resp = self.data[keyName]
        elif keyName in self.data.get("Task1", {}):
            resp = self.data["Task1"][keyName]
        elif keyName in self.data.get("Step1", {}):
            resp = self.data["Step1"][keyName]
        return resp

    def _updateDataCampaignMap(self, parentName):
        """
        Update the data/campaign map with a newly discovered parent dataset
        :param parentName: the parent dataset name
        """
        for item in self.getDataCampaignMap():
            if item["type"] == "primary":
                # this is the campaign name we're looking for
                newItem = dict(type="parent", name=parentName, campaign=item["campaign"])
                break
        self.dataCampaignMap.append(newItem)
