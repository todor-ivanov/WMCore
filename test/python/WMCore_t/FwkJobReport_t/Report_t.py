#!/usr/bin/env python
"""
_Report_t_

Unit tests for the Report class.
"""

import unittest
import os
import time

from WMCore.Algorithms import BasicAlgos
from WMCore.Configuration import ConfigSection
from WMCore.FwkJobReport.Report import Report
from WMCore.WMBase import getTestBase
from WMQuality.TestInitCouchApp import TestInitCouchApp

class ReportTest(unittest.TestCase):
    """
    _ReportTest_

    Unit tests for the Report class.
    """
    def setUp(self):
        """
        _setUp_

        Figure out the location of the XML report produced by CMSSW.
        """
        self.testInit = TestInitCouchApp(__file__)
        self.testInit.setLogging()
        self.testInit.setDatabaseConnection(destroyAllDatabase=True)
        self.testInit.setupCouch("report_t/fwjrs", "FWJRDump")

        self.xmlPath = os.path.join(getTestBase(),
                                    "WMCore_t/FwkJobReport_t/CMSSWProcessingReport.xml")
        self.badxmlPath = os.path.join(getTestBase(),
                                       "WMCore_t/FwkJobReport_t/CMSSWFailReport2.xml")
        self.skippedFilesxmlPath = os.path.join(getTestBase(),
                                                "WMCore_t/FwkJobReport_t/CMSSWSkippedNonExistentFile.xml")
        self.skippedAllFilesxmlPath = os.path.join(getTestBase(),
                                                   "WMCore_t/FwkJobReport_t/CMSSWSkippedAll.xml")
        self.fallbackXmlPath = os.path.join(getTestBase(),
                                            "WMCore_t/FwkJobReport_t/CMSSWInputFallback.xml")
        self.twoFileFallbackXmlPath = os.path.join(getTestBase(),
                                                   "WMCore_t/FwkJobReport_t/CMSSWTwoFileRemote.xml")
        self.pileupXmlPath = os.path.join(getTestBase(),
                                          "WMCore_t/FwkJobReport_t/CMSSWPileup.xml")

        self.testDir = self.testInit.generateWorkDir()
        return

    def tearDown(self):
        """
        _tearDown_

        Cleanup the databases.
        """
        self.testInit.tearDownCouch()
        self.testInit.clearDatabase()
        self.testInit.delWorkDir()
        return

    def verifyInputData(self, report):
        """
        _verifyInputData_

        Verify that the input file in the Report class matches the input file in
        the XML generated by CMSSW.
        """
        inputFiles = report.getInputFilesFromStep("cmsRun1")

        assert len(inputFiles) == 1, \
               "Error: Wrong number of input files."
        assert inputFiles[0]["lfn"] == "/store/data/BeamCommissioning09/MinimumBias/RAW/v1/000/122/023/142F3F42-C5D6-DE11-945D-000423D94494.root", \
               "Error: Wrong LFN on input file."
        assert inputFiles[0]["pfn"] == "dcap://cmsdca.fnal.gov:24137/pnfs/fnal.gov/usr/cms/WAX/11/store/data/BeamCommissioning09/MinimumBias/RAW/v1/000/122/023/142F3F42-C5D6-DE11-945D-000423D94494.root", \
               "Error: Wrong PFN on input file."

        inputRun = list(inputFiles[0]["runs"])
        assert len(inputRun) == 1, \
               "Error: Wrong number of runs in input."
        assert inputRun[0].run == 122023, \
               "Error: Wrong run number on input file."
        assert len(inputRun[0].lumis) == 1, \
               "Error: Wrong number of lumis in input file."
        assert 215 in inputRun[0].lumis, \
               "Error: Input file is missing lumis."

        assert inputFiles[0]["events"] == 2, \
               "Error: Wrong number of events in input file."
        assert inputFiles[0]["size"] == 0, \
               "Error: Wrong size in input file."

        assert inputFiles[0]["catalog"] == "trivialcatalog_file:/uscmst1/prod/sw/cms/SITECONF/T1_US_FNAL/PhEDEx/storage.xml?protocol=dcap", \
               "Error: Catalog on input file is wrong."
        assert inputFiles[0]["guid"] == "142F3F42-C5D6-DE11-945D-000423D94494", \
               "Error: GUID of input file is wrong."

        return

    def verifyRecoOutput(self, report):
        """
        _verifyRecoOutput_

        Verify that all the metadata in the RECO output module is correct.
        """
        outputFiles = report.getFilesFromOutputModule("cmsRun1", "outputRECORECO")

        assert len(outputFiles) == 1, \
               "Error: Wrong number of output files."
        assert outputFiles[0]["lfn"] == "/store/backfill/2/unmerged/WMAgentCommissioining10/MinimumBias/RECO/rereco_GR09_R_34X_V5_All_v1/0000/outputRECORECO.root", \
               "Error: Wrong LFN on output file: %s" % outputFiles[0]["lfn"]
        assert outputFiles[0]["pfn"] == "outputRECORECO.root", \
               "Error: Wrong PFN on output file."

        outputRun = list(outputFiles[0]["runs"])
        assert len(outputRun) == 1, \
               "Error: Wrong number of runs in output."
        assert outputRun[0].run == 122023, \
               "Error: Wrong run number on output file."
        assert len(outputRun[0].lumis) == 1, \
               "Error: Wrong number of lumis in output file."
        assert 215 in outputRun[0].lumis, \
               "Error: Output file is missing lumis."

        assert outputFiles[0]["events"] == 2, \
               "Error: Wrong number of events in output file."
        assert outputFiles[0]["size"] == 0, \
               "Error: Wrong size in output file."

        assert len(outputFiles[0]["input"]) == 1, \
               "Error: Wrong number of input files."
        assert outputFiles[0]["input"][0] == "/store/data/BeamCommissioning09/MinimumBias/RAW/v1/000/122/023/142F3F42-C5D6-DE11-945D-000423D94494.root", \
               "Error: LFN of input file is wrong."

        assert len(outputFiles[0]["checksums"]) == 0, \
               "Error: There should be no checksums in output file."
        assert outputFiles[0]["catalog"] == "", \
               "Error: Catalog on output file is wrong."
        assert outputFiles[0]["guid"] == "7E3359C8-222E-DF11-B2B0-001731230E47", \
               "Error: GUID of output file is wrong: %s" % outputFiles[0]["guid"]
        assert outputFiles[0]["module_label"] == "outputRECORECO", \
               "Error: Module label of output file is wrong."
        assert outputFiles[0]["branch_hash"] == "cf37adeb60b427f4ccd0e21b5771146b", \
               "Error: Branch has on output file is wrong."

        return

    def verifyAlcaOutput(self, report):
        """
        _verifyAlcaOutput_

        Verify that all of the meta data in the ALCARECO output module is
        correct.
        """
        outputFiles = report.getFilesFromOutputModule("cmsRun1", "outputALCARECORECO")
        assert len(outputFiles) == 1, \
               "Error: Wrong number of output files."
        assert outputFiles[0]["lfn"] == "/store/backfill/2/unmerged/WMAgentCommissioining10/MinimumBias/ALCARECO/rereco_GR09_R_34X_V5_All_v1/0000/B8F849C9-222E-DF11-B2B0-001731230E47.root", \
               "Error: Wrong LFN on output file: %s" % outputFiles[0]["lfn"]
        assert outputFiles[0]["pfn"] == "outputALCARECORECO.root", \
               "Error: Wrong PFN on output file."

        outputRun = list(outputFiles[0]["runs"])
        assert len(outputRun) == 1, \
               "Error: Wrong number of runs in output."
        assert outputRun[0].run == 122023, \
               "Error: Wrong run number on output file."
        assert len(outputRun[0].lumis) == 1, \
               "Error: Wrong number of lumis in output file."
        assert 215 in outputRun[0].lumis, \
               "Error: Output file is missing lumis."

        assert outputFiles[0]["events"] == 2, \
               "Error: Wrong number of events in output file."
        assert outputFiles[0]["size"] == 0, \
               "Error: Wrong size in output file."

        assert len(outputFiles[0]["input"]) == 1, \
               "Error: Wrong number of input files."
        assert outputFiles[0]["input"][0] == "/store/data/BeamCommissioning09/MinimumBias/RAW/v1/000/122/023/142F3F42-C5D6-DE11-945D-000423D94494.root", \
               "Error: LFN of input file is wrong."

        assert len(outputFiles[0]["checksums"]) == 0, \
               "Error: There should be no checksums in output file."
        assert outputFiles[0]["catalog"] == "", \
               "Error: Catalog on output file is wrong."
        assert outputFiles[0]["guid"] == "B8F849C9-222E-DF11-B2B0-001731230E47", \
               "Error: GUID of output file is wrong: %s" % outputFiles[0]["guid"]
        assert outputFiles[0]["module_label"] == "outputALCARECORECO", \
               "Error: Module label of output file is wrong."
        assert outputFiles[0]["branch_hash"] == "cf37adeb60b427f4ccd0e21b5771146b", \
               "Error: Branch has on output file is wrong."

        return

    def testXMLParsing(self):
        """
        _testParsing_

        Verify that the parsing of a CMSSW XML report works correctly.
        """
        myReport = Report("cmsRun1")
        myReport.parse(self.xmlPath)

        self.verifyInputData(myReport)
        self.verifyRecoOutput(myReport)
        self.verifyAlcaOutput(myReport)

        return

    def testBadXMLParsing(self):
        """
        _testBadXMLParsing_

        Verify that the parsing of a CMSSW XML report works correctly even if
        the XML is malformed.

        This should raise a FwkJobReportException, which in CMSSW will be caught
        """
        myReport = Report("cmsRun1")
        from WMCore.FwkJobReport.Report import FwkJobReportException
        self.assertRaises(FwkJobReportException, myReport.parse, self.badxmlPath)
        self.assertEqual(myReport.getStepErrors("cmsRun1")['error0'].type, 'BadFWJRXML')
        self.assertEqual(myReport.getStepErrors("cmsRun1")['error0'].exitCode, 50115)
        return

    def testErrorReporting(self):
        """
        _testErrorReporting_

        Verify that errors are correctly transfered from the XML report to the
        python report.
        """
        cmsException = \
"""cms::Exception caught in cmsRun
---- EventProcessorFailure BEGIN
EventProcessingStopped
---- ScheduleExecutionFailure BEGIN
ProcessingStopped
---- NoRecord BEGIN
No "CastorDbRecord" record found in the EventSetup.
 Please add an ESSource or ESProducer that delivers such a record.
cms::Exception going through module CastorRawToDigi/castorDigis run: 121849 lumi: 1 event: 23
---- NoRecord END
Exception going through path raw2digi_step
---- ScheduleExecutionFailure END
an exception occurred during current event processing
cms::Exception caught in EventProcessor and rethrown
---- EventProcessorFailure END"""

        xmlPath = os.path.join(getTestBase(),
                               "WMCore_t/FwkJobReport_t/CMSSWFailReport.xml")

        myReport = Report("cmsRun1")
        myReport.parse(xmlPath)

        assert hasattr(myReport.data.cmsRun1, "errors"), \
               "Error: Error section missing."
        assert getattr(myReport.data.cmsRun1.errors, "errorCount") == 1, \
               "Error: Error count is wrong."
        assert hasattr(myReport.data.cmsRun1.errors, "error0"), \
               "Error: Error0 section is missing."
        assert myReport.data.cmsRun1.errors.error0.type == "CMSException", \
               "Error: Wrong error type."
        assert myReport.data.cmsRun1.errors.error0.exitCode == "8001", \
               "Error: Wrong exit code."
        assert myReport.data.cmsRun1.errors.error0.details == cmsException, \
               "Error: Error details are wrong:\n|%s|\n|%s|" % (myReport.data.cmsRun1.errors.error0.details,
                                                                cmsException)

        # Test getStepErrors
        self.assertEqual(myReport.getStepErrors("cmsRun1")['error0'].type, "CMSException")

        return

    def testMultipleInputs(self):
        """
        _testMultipleInputs_

        Verify that parsing XML reports with multiple inputs works correctly.
        """
        xmlPath = os.path.join(getTestBase(),
                               "WMCore_t/FwkJobReport_t/CMSSWMultipleInput.xml")
        myReport = Report("cmsRun1")
        myReport.parse(xmlPath)

        assert hasattr(myReport.data.cmsRun1.input, "source"), \
               "Error: Report missing input source."

        inputFiles = myReport.getInputFilesFromStep("cmsRun1")

        assert len(inputFiles) == 2, \
               "Error: Wrong number of input files."

        for inputFile in inputFiles:
            assert inputFile["input_type"] == "primaryFiles", \
                   "Error: Wrong input type."
            assert inputFile["module_label"] == "source", \
                   "Error: Module label is wrong"
            assert inputFile["catalog"] == "trivialcatalog_file:/uscmst1/prod/sw/cms/SITECONF/T1_US_FNAL/PhEDEx/storage.xml?protocol=dcap", \
                   "Error: Catalog is wrong."
            assert inputFile["events"] == 2, \
                   "Error: Wrong number of events."
            assert inputFile["input_source_class"] == "PoolSource", \
                   "Error: Wrong input source class."

            if inputFile["guid"] == "F0875ECD-3347-DF11-9FE0-003048678A80":
                assert inputFile["lfn"] == "/store/backfill/2/unmerged/WMAgentCommissioining10/MinimumBias/RECO/rereco_GR10_P_V4_All_v1/0000/F0875ECD-3347-DF11-9FE0-003048678A80.root", \
                       "Error: Input LFN is wrong."
                assert inputFile["pfn"] == "dcap://cmsdca3.fnal.gov:24142/pnfs/fnal.gov/usr/cms/WAX/11/store/backfill/2/unmerged/WMAgentCommissioining10/MinimumBias/RECO/rereco_GR10_P_V4_All_v1/0000/F0875ECD-3347-DF11-9FE0-003048678A80.root", \
                       "Error: Input PFN is wrong."
                assert len(inputFile["runs"]) == 1, \
                       "Error: Wrong number of runs."
                assert list(inputFile["runs"])[0].run == 124216, \
                       "Error: Wrong run number."
                assert 1 in list(inputFile["runs"])[0], \
                       "Error: Wrong lumi sections in input file."
            else:
                assert inputFile["guid"] == "626D74CE-3347-DF11-9363-0030486790C0", \
                       "Error: Wrong guid."
                assert inputFile["lfn"] == "/store/backfill/2/unmerged/WMAgentCommissioining10/MinimumBias/RECO/rereco_GR10_P_V4_All_v1/0000/626D74CE-3347-DF11-9363-0030486790C0.root", \
                       "Error: Input LFN is wrong."
                assert inputFile["pfn"] == "dcap://cmsdca3.fnal.gov:24142/pnfs/fnal.gov/usr/cms/WAX/11/store/backfill/2/unmerged/WMAgentCommissioining10/MinimumBias/RECO/rereco_GR10_P_V4_All_v1/0000/626D74CE-3347-DF11-9363-0030486790C0.root", \
                       "Error: Input PFN is wrong."
                assert len(inputFile["runs"]) == 1, \
                       "Error: Wrong number of runs."
                assert list(inputFile["runs"])[0].run == 124216, \
                       "Error: Wrong run number."
                assert 2 in list(inputFile["runs"])[0], \
                       "Error: Wrong lumi sections in input file."

        return

    def testJSONEncoding(self):
        """
        _testJSONEncoding_

        Verify that turning the FWJR into a JSON object works correctly.
        """
        xmlPath = os.path.join(getTestBase(),
                               "WMCore_t/FwkJobReport_t/CMSSWProcessingReport.xml")
        myReport = Report("cmsRun1")
        myReport.parse(xmlPath)

        jsonReport = myReport.__to_json__(None)

        assert "task" in jsonReport.keys(), \
               "Error: Task name missing from report."

        assert len(jsonReport["steps"].keys()) == 1, \
               "Error: Wrong number of steps in report."
        assert "cmsRun1" in jsonReport["steps"].keys(), \
               "Error: Step missing from json report."

        cmsRunStep = jsonReport["steps"]["cmsRun1"]

        jsonReportSections = ["status", "errors", "logs", "parameters", "site",
                              "analysis", "cleanup", "input", "output", "start"]
        for jsonReportSection in jsonReportSections:
            assert jsonReportSection in cmsRunStep.keys(), \
                "Error: missing section: %s" % jsonReportSection

        return

    def testTimeSetting(self):
        """
        _testTimeSetting_

        Can we set the times correctly?
        """
        stepName = "cmsRun1"
        timeDiff = 0.01
        myReport = Report(stepName)
        localTime = time.time()
        myReport.setStepStartTime(stepName)
        myReport.setStepStopTime(stepName)
        repTime = myReport.getTimes(stepName)

        self.assertTrue(repTime["startTime"] - localTime < timeDiff)
        self.assertTrue(repTime["stopTime"] - localTime < timeDiff)


        myReport = Report("cmsRun1")
        myReport.addStep("cmsRun2")
        myReport.addStep("cmsRun3")

        step = myReport.retrieveStep("cmsRun1")
        step.startTime = 1
        step.stopTime = 8
        step = myReport.retrieveStep("cmsRun2")
        step.startTime = 2
        step.stopTime = 9
        step = myReport.retrieveStep("cmsRun3")
        step.startTime = 3
        step.stopTime = 10

        self.assertEqual(myReport.getFirstStartLastStop()['stopTime'], 10)
        self.assertEqual(myReport.getFirstStartLastStop()['startTime'], 1)

        return


    def testTaskJobID(self):
        """
        _testTaskJobID_

        Test the basic task and jobID functions
        """


        report = Report('fake')
        self.assertEqual(report.getTaskName(), None)
        self.assertEqual(report.getJobID(), None)
        report.setTaskName('silly')
        report.setJobID(100)
        self.assertEqual(report.getTaskName(), 'silly')
        self.assertEqual(report.getJobID(), 100)

        return


    def test_PerformanceReport(self):
        """
        _PerformanceReport_

        Test the performance report part of the job report
        """

        report = Report("cmsRun1")
        report.setStepVSize(stepName="cmsRun1", min=100, max=800, average=244)
        report.setStepRSS(stepName="cmsRun1", min=100, max=800, average=244)
        report.setStepPCPU(stepName="cmsRun1", min=100, max=800, average=244)
        report.setStepPMEM(stepName="cmsRun1", min=100, max=800, average=244)

        perf = report.retrieveStep("cmsRun1").performance
        for section in perf.dictionary_().values():
            d = section.dictionary_()
            self.assertEqual(d['min'], 100)
            self.assertEqual(d['max'], 800)
            self.assertEqual(d['average'], 244)
        return

    def testPerformanceSummary(self):
        """
        _testPerformanceSummary_

        Test whether or not we can pull performance information
        out of a Timing/SimpleMemoryCheck jobReport
        """

        xmlPath = os.path.join(getTestBase(),
                               "WMCore_t/FwkJobReport_t/PerformanceReport.xml")

        myReport = Report("cmsRun1")
        myReport.parse(xmlPath)

        # Do a brief check of the three sections
        perf = myReport.data.cmsRun1.performance

        self.assertEqual(perf.memory.PeakValueRss, '492.293')
        self.assertEqual(perf.cpu.TotalJobCPU, '9.16361')
        self.assertEqual(perf.storage.writeTotalMB, 5.22226)
        self.assertEqual(perf.storage.writeTotalSecs, 60317.4)
        self.assertEqual(perf.storage.readPercentageOps, 0.98585512216030857)

        return

    def testPerformanceJSON(self):
        """
        _testPerformanceJSON_

        Verify that the performance section of the report is correctly converted
        to JSON.
        """
        xmlPath = os.path.join(getTestBase(),
                               "WMCore_t/FwkJobReport_t/PerformanceReport.xml")

        myReport = Report("cmsRun1")
        myReport.parse(xmlPath)

        perfSection = myReport.__to_json__(thunker=None)["steps"]["cmsRun1"]["performance"]

        self.assertTrue("storage" in perfSection,
                        "Error: Storage section is missing.")
        self.assertTrue("memory" in perfSection,
                        "Error: Memory section is missing.")
        self.assertTrue("cpu" in perfSection,
                        "Error: CPU section is missing.")

        self.assertEqual(perfSection["cpu"]["AvgEventCPU"], "0.626105",
                         "Error: AvgEventCPU is wrong.")
        self.assertEqual(perfSection["cpu"]["TotalJobTime"], "23.5703",
                         "Error: TotalJobTime is wrong.")
        self.assertEqual(perfSection["storage"]["readTotalMB"], 39.6166,
                         "Error: readTotalMB is wrong.")
        self.assertEqual(perfSection["storage"]["readMaxMSec"], 320.653,
                         "Error: readMaxMSec is wrong")
        self.assertEqual(perfSection["memory"]["PeakValueRss"], "492.293",
                         "Error: PeakValueRss is wrong.")
        self.assertEqual(perfSection["memory"]["PeakValueVsize"], "643.281",
                         "Error: PeakValueVsize is wrong.")
        return


    def testExitCode(self):
        """
        _testExitCode_

        Test and see if we can get an exit code out of a report

        Note: Errors without a return code return 99999
        """

        report = Report("cmsRun1")
        self.assertEqual(report.getExitCode(), 0)
        report.addError(stepName="cmsRun1", exitCode=None, errorType="test", errorDetails="test")
        self.assertEqual(report.getExitCode(), 99999)
        self.assertEqual(report.getStepExitCode(stepName="cmsRun1"), 99999)
        report.addError(stepName="cmsRun1", exitCode='12345', errorType="test", errorDetails="test")
        self.assertEqual(report.getExitCode(), 12345)
        self.assertEqual(report.getStepExitCode(stepName="cmsRun1"), 12345)

    def testProperties(self):
        """
        _testProperties_

        Test data fields for the properties information for DBS
        """

        myReport = Report("cmsRun1")
        myReport.parse(self.xmlPath)

        name = "ThisIsASillyString"

        myReport.setValidStatus(name)
        myReport.setGlobalTag(name)
        myReport.setAcquisitionProcessing(acquisitionEra='NULL', processingVer=name)
        myReport.setInputDataset(inputPath='/lame/path')

        for f in myReport.getAllFilesFromStep("cmsRun1"):
            self.assertEqual(f['globalTag'], name)
            self.assertEqual(f['validStatus'], name)
            self.assertEqual(f['processingVer'], name)
            self.assertEqual(f['acquisitionEra'], 'NULL')
            self.assertEqual(f['inputPath'], '/lame/path')

        return

    def testOutputFiles(self):
        """
        _testOutputFiles_

        Test some basic manipulation of output files
        """

        myReport = Report("cmsRun1")
        myReport.parse(self.xmlPath)

        files = myReport.getAllFilesFromStep(step="cmsRun1")

        f1 = files[0]
        f2 = files[1]

        self.assertEqual(f1['outputModule'], 'outputRECORECO')
        self.assertEqual(f1['pfn'], 'outputRECORECO.root')

        self.assertEqual(f2['outputModule'], 'outputALCARECORECO')
        self.assertEqual(f2['pfn'], 'outputALCARECORECO.root')

        for f in files:
            self.assertEqual(f['events'], 2)
            self.assertEqual(f['configURL'], None)
            self.assertEqual(f['merged'], False)
            self.assertEqual(f['validStatus'], None)
            self.assertEqual(f['first_event'], 0)

        return

    def testGetAdlerChecksum(self):
        """
        _testGetAdlerChecksum_

        Test the function that sees if all files
        have an adler checksum.

        For some reason, our default XML report doesn't have checksums
        Therefore it should fail.
        """

        myReport = Report("cmsRun1")
        myReport.parse(self.xmlPath)

        myReport.checkForAdlerChecksum(stepName="cmsRun1")

        self.assertFalse(myReport.stepSuccessful(stepName="cmsRun1"))
        self.assertEqual(myReport.getExitCode(), 60451)

        # Now see what happens if the adler32 is set to None
        myReport2 = Report("cmsRun1")
        myReport2.parse(self.xmlPath)
        fRefs = myReport2.getAllFileRefsFromStep(step="cmsRun1")
        for fRef in fRefs:
            fRef.checksums = {'adler32': None}
        myReport2.checkForAdlerChecksum(stepName="cmsRun1")
        self.assertFalse(myReport2.stepSuccessful(stepName="cmsRun1"))
        self.assertEqual(myReport2.getExitCode(), 60451)

        myReport3 = Report("cmsRun1")
        myReport3.parse(self.xmlPath)
        fRefs = myReport3.getAllFileRefsFromStep(step="cmsRun1")
        for fRef in fRefs:
            fRef.checksums = {'adler32': 100}

        myReport3.checkForAdlerChecksum(stepName="cmsRun1")
        self.assertTrue(myReport3.getExitCode() != 60451)

        return

    def testCheckLumiInformation(self):
        """
        _testCheckLumiInformation_

        Test the function that checks if all files
        have run lumi information
        """

        myReport = Report("cmsRun1")
        myReport.parse(self.xmlPath)

        myReport.checkForRunLumiInformation(stepName="cmsRun1")

        self.assertNotEqual(myReport.getExitCode(), 70452)

        # Remove the lumi information on purpose
        myReport2 = Report("cmsRun1")
        myReport2.parse(self.xmlPath)
        fRefs = myReport2.getAllFileRefsFromStep(step="cmsRun1")
        for fRef in fRefs:
            fRef.runs = ConfigSection()
        myReport2.checkForRunLumiInformation(stepName="cmsRun1")
        self.assertFalse(myReport2.stepSuccessful(stepName="cmsRun1"))
        self.assertEqual(myReport2.getExitCode(), 70452)

        return


    def testTaskSuccessful(self):
        """
        _testTaskSuccessful_

        Test whether or not the report marks the task successful
        """

        myReport = Report("cmsRun1")
        myReport.parse(self.xmlPath)

        # First, the report should fail
        self.assertFalse(myReport.taskSuccessful())

        # Second, if we ignore cmsRun, the task
        # should succeed
        self.assertTrue(myReport.taskSuccessful(ignoreString='cmsRun'))
        return

    def testStripReport(self):
        """
        _testStripReport_

        Test whether or not we can strip input file information
        from a FWJR and create a smaller object.
        """

        myReport = Report("cmsRun1")
        myReport.parse(self.xmlPath)

        path1 = os.path.join(self.testDir, 'testReport1.pkl')
        path2 = os.path.join(self.testDir, 'testReport2.pkl')

        myReport.save(path1)
        info = BasicAlgos.getFileInfo(filename=path1)
        self.assertEqual(info['Size'], 7101)

        inputFiles = myReport.getAllInputFiles()
        self.assertEqual(len(inputFiles), 1)
        myReport.stripInputFiles()
        self.assertEqual(len(myReport.getAllInputFiles()), 0)

        myReport.save(path2)
        info = BasicAlgos.getFileInfo(filename=path2)
        self.assertEqual(info['Size'], 6210)

        return

    def testDuplicatStep(self):
        """
        _testDuplicateStep_

        If the same step is added twice, it should act
        as a replacement, and raise an appropriate message
        """

        baseReport = Report("cmsRun1")
        baseReport.parse(self.xmlPath)

        modReport = Report("cmsRun1")
        modReport.parse(self.xmlPath)
        setattr(modReport.data.cmsRun1, 'testVar', 'test01')

        report = Report()
        report.setStep(stepName='cmsRun1', stepSection=baseReport.retrieveStep('cmsRun1'))
        report.setStep(stepName='cmsRun1', stepSection=modReport.retrieveStep('cmsRun1'))

        self.assertEqual(report.listSteps(), ['cmsRun1'])
        self.assertEqual(report.data.cmsRun1.testVar, 'test01')

        return

    def testDeleteOutputModule(self):
        """
        _testDeleteOutputModule_

        If asked delete an output module, if it doesn't
        exist then do nothing
        """
        originalReport = Report("cmsRun1")
        originalReport.parse(self.xmlPath)

        self.assertTrue(originalReport.getOutputModule("cmsRun1", "outputALCARECORECO"),
                        "Error: Report XML doesn't have the module for the test, invalid test")

        originalOutputModules = len(originalReport.retrieveStep("cmsRun1").outputModules)
        originalReport.deleteOutputModuleForStep("cmsRun1", "outputALCARECORECO")
        self.assertFalse(originalReport.getOutputModule("cmsRun1", "outputALCARECORECO"),
                         "Error: The output module persists after deletion")
        self.assertEqual(len(originalReport.retrieveStep("cmsRun1").outputModules), originalOutputModules - 1,
                         "Error: The number of output modules is incorrect after deletion")

    def testSkippedFiles(self):
        """
        _testSkippedFiles_

        Test that skipped files are translated from FWJR into report
        """
        # Check a report where some files were skipped but not all
        originalReport = Report("cmsRun1")
        originalReport.parse(self.skippedFilesxmlPath)
        self.assertEqual(originalReport.getAllSkippedFiles(),
                         ['/store/data/Run2012D/Cosmics/RAW/v1/000/206/379/1ED243E7-A611-E211-A851-0019B9F581C9.root'])

        # For negative control, check a good report with no skipped files
        goodReport = Report("cmsRun1")
        goodReport.parse(self.xmlPath)
        self.assertEqual(goodReport.getAllSkippedFiles(), [])

        # Check a report where all files were skipped
        badReport = Report("cmsRun1")
        badReport.parse(self.skippedAllFilesxmlPath)
        self.assertEqual(sorted(badReport.getAllSkippedFiles()),
                         ['/store/data/Run2012D/Cosmics/RAW/v1/000/206/379/1ED243E7-A611-E211-A851-0019B9F581C9.root',
                          '/store/data/Run2012D/Cosmics/RAW/v1/000/206/379/1ED243E7-A622-E211-A851-0019B9F581C.root'])

        return

    def testSkippedFilesJSON(self):
        """
        _testSkippedFilesJSON_

        Test that skipped files are translated properly into JSON
        """
        # Check a report where some files were skipped but not all
        originalReport = Report("cmsRun1")
        originalReport.parse(self.skippedFilesxmlPath)
        originalJSON = originalReport.__to_json__(None)
        self.assertEqual(len(originalJSON['skippedFiles']), 1)

        # For negative control, check a good report with no skipped files
        goodReport = Report("cmsRun1")
        goodReport.parse(self.xmlPath)
        goodJSON = goodReport.__to_json__(None)
        self.assertEqual(goodJSON['skippedFiles'], [])

        # Check a report where all files were skipped
        badReport = Report("cmsRun1")
        badReport.parse(self.skippedAllFilesxmlPath)
        badJSON = badReport.__to_json__(None)
        self.assertEqual(len(badJSON['skippedFiles']), 2)

        return

    def testFallbackFiles(self):
        """
        _testFallbackFiles_

        Test that fallback files end up in the report
        """

        # For negative control, check a good report with no fallback files
        goodReport = Report("cmsRun1")
        goodReport.parse(self.xmlPath)
        self.assertEqual(goodReport.getAllFallbackFiles(), [])

        # Check a report where the file was a fallback
        badReport = Report("cmsRun1")
        badReport.parse(self.fallbackXmlPath)
        self.assertEqual(sorted(badReport.getAllFallbackFiles()),
                         ['/store/data/Run2012D/SingleElectron/AOD/PromptReco-v1/000/207/279/D43A5B72-1831-E211-895D-001D09F24763.root'])

        twoReport = Report("cmsRun1")
        twoReport.parse(self.twoFileFallbackXmlPath)
        self.assertEqual(len(twoReport.getAllFallbackFiles()), 2)

        return

    def testPileupFiles(self):
        """
        _testPileupFiles_

        Test that alll the pileup files end up in the report
        """

        report = Report("cmsRun1")
        report.parse(self.pileupXmlPath)
        self.assertEqual(len(report.getAllInputFiles()), 14)

        primaryCount = 0
        secondaryCount = 0
        mixingCount = 0

        for fileEntry in report.getAllInputFiles():
            if fileEntry['input_type'] == 'mixingFiles':
                mixingCount += 1
            elif fileEntry['input_type'] == 'primaryFiles':
                primaryCount += 1
            elif fileEntry['input_type'] == 'secondaryFiles':
                secondaryCount += 1

        self.assertEqual(primaryCount, 1)
        self.assertEqual(secondaryCount, 0)
        self.assertEqual(mixingCount, 13)
        self.assertEqual(len(report.getAllFallbackFiles()), 1)

        return

    def testFallbackFilesJSON(self):
        """
        _testFallbackFilesJSON_

        Test that fallback attempt files are translated properly into JSON
        """

        # For negative control, check a good report with no skipped files
        goodReport = Report("cmsRun1")
        goodReport.parse(self.xmlPath)
        goodJSON = goodReport.__to_json__(None)
        self.assertEqual(goodJSON['fallbackFiles'], [])

        # Check a report where all files were skipped
        badReport = Report("cmsRun1")
        badReport.parse(self.fallbackXmlPath)
        badJSON = badReport.__to_json__(None)
        self.assertEqual(len(badJSON['fallbackFiles']), 1)

        return

    def testOutputCheck(self):
        """
        _testOutputCheck_

        Check that we can identify bad reports with no output files
        """
        badReport = Report("cmsRun1")
        badReport.parse(self.skippedAllFilesxmlPath)
        badReport.checkForOutputFiles("cmsRun1")
        self.assertFalse(badReport.stepSuccessful(stepName="cmsRun1"))
        self.assertEqual(badReport.getExitCode(), 60450)
        return

if __name__ == "__main__":
    unittest.main()
