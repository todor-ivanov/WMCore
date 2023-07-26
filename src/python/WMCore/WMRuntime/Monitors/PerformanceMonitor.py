#!/usr/bin/env python

"""
__PerformanceMonitor_

Monitor object which checks the job to ensure it is working inside
the agreed limits of virtual memory and wallclock time, and terminate it
if it exceeds them.
"""


import logging
import os
import os.path
import signal
import time
import psutil

import WMCore.FwkJobReport.Report as Report
from WMCore.WMException import WMException
from WMCore.WMRuntime.Monitors.WMRuntimeMonitor import WMRuntimeMonitor
from WMCore.WMSpec.Steps.Executor import getStepSpace
from WMCore.WMSpec.WMStep import WMStepHelper

getStepName = lambda step: WMStepHelper(step).name()


def getStepPID(stepSpace, stepName):
    """
    _getStepPID_

    Find the PID for a step given its stepSpace from the file
    """
    currDir = stepSpace.location
    pidFile = os.path.join(currDir, 'process.id')
    if not os.path.isfile(pidFile):
        msg = "Could not find process ID file for step %s" % stepName
        logging.error(msg)
        return None

    with open(pidFile,'r') as filehandle:
        output = filehandle.read()

    try:
        stepPID = int(output)
    except ValueError:
        msg = "Couldn't find a number"
        logging.error(msg)
        return None

    return stepPID


def average(numbers):
    """
    Quick averaging function

    """
    return float(sum(numbers)) / len(numbers)


class PerformanceMonitorException(WMException):
    """
    _PerformanceMonitorException_

    Just a performance monitor error...nothing to see here
    """
    pass


class PerformanceMonitor(WMRuntimeMonitor):
    """
    _PerformanceMonitor_

    Monitors the performance by pinging ps and
    recording data regarding the current step
    """

    def __init__(self):
        """
        Actual variable initialization
        in initMonitor
        """

        self.pid = None
        self.uid = os.getuid()
        self.monitorCommand = None
        self.currentStepSpace = None
        self.currentStepName = None

        self.rss = []
        self.pcpu = []
        self.pmem = []

        self.maxPSS = None
        self.softTimeout = None
        self.hardTimeout = None
        self.logPath = None
        self.startTime = None
        self.killRetry = False  # will trigger a hard (SIGTERM) instead of soft kill

        self.watchStepTypes = []

        self.disableStep = False

        WMRuntimeMonitor.__init__(self)

        return

    def initMonitor(self, task, job, logPath, args=None):
        """
        _initMonitor_

        Puts together the information needed for the monitoring
        to actually find everything.
        """
        args = args or {}

        # Set the steps we want to watch
        self.watchStepTypes = args.get('WatchStepTypes', ['CMSSW', 'PerfTest'])

        self.maxPSS = args.get('maxPSS', args.get('maxRSS'))
        self.softTimeout = args.get('softTimeout', None)
        self.hardTimeout = args.get('hardTimeout', None)
        self.numOfCores = args.get('cores', None)

        self.logPath = os.path.join(logPath)

        return

    def jobStart(self, task):
        """
        _jobStart_

        Acknowledge that the job has started and initialize the time
        """
        self.startTime = time.time()

        return

    def stepStart(self, step):
        """
        _stepStart_

        Assure that the monitor is pointing at the right step
        """

        self.stepHelper = WMStepHelper(step)
        self.currentStepName = getStepName(step)
        self.currentStepSpace = None

        if not self.stepHelper.stepType() in self.watchStepTypes:
            self.disableStep = True
            logging.debug("PerformanceMonitor ignoring step of type %s", self.stepHelper.stepType())
            return
        else:
            logging.debug("Beginning PeformanceMonitor step Initialization")
            self.disableStep = False

        return

    def stepEnd(self, step, stepReport):
        """
        _stepEnd_

        Package the information and send it off
        """

        if not self.disableStep:
            # No information to correlate
            return

        self.currentStepName = None
        self.currentStepSpace = None

        return

    def periodicUpdate(self):
        """
        Run on the defined intervals.

        """
        killProc = False
        killHard = False
        reason = ''
        errorCodeLookup = {'PSS': 50660,
                           'Wallclock time': 50664,
                           '': 99999}

        if self.disableStep:
            # Then we aren't doing CPU monitoring
            # on this step
            return

        if self.currentStepName is None:
            # We're between steps
            return

        if self.currentStepSpace is None:
            # Then build the step space
            self.currentStepSpace = getStepSpace(self.stepHelper.name())

        stepPID = getStepPID(self.currentStepSpace, self.currentStepName)

        if stepPID is None:
            # Then we have no step PID, we can do nothing
            return

        # Now we run the psutil module and collate some process data.
        # We gather info about CPU system time and Memory statistics - VMS, PSS, RSS
        stepProc = psutil.Process(stepPID)
        if not stepProc.is_running():
            # The step process has vanished before we managed to finish the current periodic update
            msg = " The step process with PID: %s of STEP: %s "
            msg += "has finished execution before the last periodic resource update.\n"
            logging.warning(msg, stepPID, self.currentStepName)
            return

        with stepProc.oneshot():
            stepCmd = stepProc.cmdline()
            stepMemInfo = stepProc.memory_full_info()
            stepCpuInfo = stepProc.cpu_times()

        # NOTE: All the information from psutil.memory_*info() comes in Bytes
        #       we need to make it in MegaBytes
        pss = int(stepMemInfo.pss) // (1000**2)

        logging.info("PID: %s; VirtMEM: %s, PSS: %s; RSS: %s; SystemTime: %s;", stepPID, stepMemInfo.vms, stepMemInfo.pss, stepMemInfo.rss, stepCpuInfo.system)

        msg = 'Error in CMSSW step %s\n' % self.currentStepName
        msg += 'Number of Cores: %s\n' % self.numOfCores

        if self.maxPSS is not None and pss >= self.maxPSS:
            msg += "Job has exceeded maxPSS: %s MB\n" % self.maxPSS
            msg += "Job has PSS: %s MB\n" % pss
            killProc = True
            reason = 'PSS'
        elif self.hardTimeout is not None and self.softTimeout is not None:
            currentTime = time.time()
            if (currentTime - self.startTime) > self.softTimeout:
                killProc = True
                reason = 'Wallclock time'
                msg += "Job has been running for more than: %s\n" % str(self.softTimeout)
                msg += "Job has been running for: %s\n" % str(currentTime - self.startTime)
            if (currentTime - self.startTime) > self.hardTimeout:
                killHard = True
                msg += "Job exceeded soft timeout"

        if not killProc:
            # then job is behaving well, there is nothing to do
            return

        # make sure we persist the performance error only once
        if not self.killRetry:
            logging.error(msg)
            report = Report.Report()
            # Find the global report
            logPath = os.path.join(self.currentStepSpace.location,
                                   '../../../',
                                   os.path.basename(self.logPath))
            try:
                if os.path.isfile(logPath):
                    # We should be able to find existant job report.
                    # If not, we're in trouble
                    logging.debug("Found pre-existant error report in PerformanceMonitor termination.")
                    report.load(logPath)
                # Create a new step that won't be overridden by an exiting CMSSW
                if not report.retrieveStep(step="PerformanceError"):
                    report.addStep(reportname="PerformanceError")
                report.addError(stepName="PerformanceError", exitCode=errorCodeLookup[reason],
                                errorType="PerformanceKill", errorDetails=msg)
                report.save(logPath)
            except Exception as ex:
                # Basically, we can't write a log report and we're hosed
                # Kill anyway, and hope the logging file gets written out
                msg2 = "Exception while writing out jobReport.\n"
                msg2 += "Aborting job anyway: unlikely you'll get any error report.\n"
                msg2 += "Error: %s" % str(ex)
                logging.exception(msg2)

        try:
            if not killHard and not self.killRetry:
                logging.error("Attempting to kill step using SIGUSR2")
                os.kill(stepPID, signal.SIGUSR2)
            else:
                logging.error("Attempting to kill step using SIGTERM")
                os.kill(stepPID, signal.SIGTERM)
        except Exception:
            logging.error("Attempting to kill step using SIGTERM")
            os.kill(stepPID, signal.SIGTERM)
        finally:
            self.killRetry = True

        return
