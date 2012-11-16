#------------------------------------------------------------------------------------
# Knowlogic CodeReview Application
#
# This file contains the main UI functions for the Code Review application.
# The main UI is displayed. Signals emitted by the UI Objects are connected
# with slot functions which are defined here.
#
#------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Python Modules
#---------------------------------------------------------------------------------------------------
from collections import OrderedDict

import datetime
import os
import re
import socket
import sys
import subprocess
import time

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------
from PySide import QtCore
from PySide.QtGui import QApplication, QMainWindow, QMessageBox
from PySide.QtGui import QFileDialog

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
from utils import DateTime, util

from tools.pcLint.PcLint import PcLint
from tools.u4c.u4c import U4c

from CrtGui import Ui_MainWindow
from ViolationDb import ViolationDb

import ProjFile as PF

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
eVersion = 'v0.2.3'

eKsCrtIni = 'KsCrt'
eLogPc = 'PcLint'
eLogKs = 'Knowlogic'
eLogTool = 'Tool Output'

eTabAdmin = 0
eTabAnalysis = 1
eTabManual = 2
eTabProject = 3
eTabMerge = 4
eTabReport = 5

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------

#------------------------------------------------------------------------------------
# Class MainWindow
#
# The class MainWindow inherits from Ui_CRMainWindow which is imported from crmainwindow.
# The Ui_CRMainWindow and all of it's related UI objects were designed with QT Designer
# and their code was then generated. Functionality of those objects is provided here by
# defining slots/functions for those UI objects.
#
#------------------------------------------------------------------------------------
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        """Sets the window title and some default file locations.
           Connects signals from the UI objects to slots which are defined here."""

        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.baseTitle = "Knowlogic Code Review Tool %s" % eVersion
        self.setWindowTitle(self.baseTitle)

        #------------------------------------------------------------------------------
        # Declare All object attributes
        #------------------------------------------------------------------------------
        self.filterInfo = {
            'Filename':'filename',
            'Function':'function',
            'Severity':'Severity',
            'Id':'violationId',
            'DetectedBy':'detectedBy',
            'Status':'Status'
        }

        # declare object attributes
        self.userName = ''
        self.curTab = eTabAdmin
        self.db = None

        self.violationsData = []
        self.v = None

        self.programOpenedU4c = False
        self.analysisActive = False

        self.projFile = None
        self.toolRunOutput = ''

        self.analysisProcess = None

        self.timer = None

        self.ResetProject()

        #------------------------------------------------------------------------------
        # Handle Tabs of TabWidget
        #------------------------------------------------------------------------------
        self.tabWidget.currentChanged.connect(self.CurrentTabChanged)

        #------------------------------------------------------------------------------
        # Handle Admin Tab Data
        #------------------------------------------------------------------------------
        self.projectFileSelector.currentIndexChanged.connect(lambda a,
                                                             fx=self.NewProjFile: fx(a))
        self.browseProjectFile.clicked.connect(self.SelectMainProjectFile)

        self.lineEdit_userName.editingFinished.connect(self.lineEditUserNameChanged)
        self.lineEdit_userName.setFocus()

        self.runAnalysis.clicked.connect(self.RunAnalysis)
        self.abortAnalysis.clicked.connect(self.AbortAnalysis)
        self.abortAnalysis.setEnabled( False)
        self.showPcLintLog.clicked.connect(lambda x=eLogPc,fx=self.ShowLog: fx(x))
        self.showKsLog.clicked.connect(lambda x=eLogKs,fx=self.ShowLog: fx(x))
        self.showToolOutput.clicked.connect(lambda x=eLogTool,fx=self.ShowLog: fx(x))

        self.exportDb.clicked.connect( self.ExportDb)
        self.clearedDbOfRemoved.clicked.connect( self.ClearRemoved)

        #------------------------------------------------------------------------------
        # Set up the filter comboboxes and the Apply Filter pushbutton
        #------------------------------------------------------------------------------
        # the a is the index that is selected => if 0 we know they cleared this filter
        self.comboBox_Filename.currentIndexChanged.connect(lambda a,x='Filename',
                                                           fx=self.FillFilters: fx(a,x))
        self.comboBox_Function.currentIndexChanged.connect(lambda a,x='Function',
                                                           fx=self.FillFilters: fx(a,x))
        self.comboBox_Severity.currentIndexChanged.connect(lambda a,x='Severity',
                                                           fx=self.FillFilters: fx(a,x))
        self.comboBox_Id.currentIndexChanged.connect(lambda a,x='Id',
                                                     fx=self.FillFilters: fx(a,x))
        self.comboBox_DetectedBy.currentIndexChanged.connect(lambda a,x='DetectedBy',
                                                             fx=self.FillFilters: fx(a,x))
        self.comboBox_Status.currentIndexChanged.connect(lambda a,x='Status',
                                                         fx=self.FillFilters: fx(a,x))

        self.lineEditDescFilter.editingFinished.connect(self.FillFilters)

        self.lineEditDetailsFilter.editingFinished.connect(self.FillFilters)

        self.dispositioned.stateChanged.connect( lambda a,x='',
                                                 fx=self.FillFilters: fx(a,x))

        self.pushButton_ApplyFilters.clicked.connect(self.ApplyFilters)

        self.resetFilters.clicked.connect( self.ResetFilters)

        #------------------------------------------------------------------------------
        # Manage the violations horizontal slider scroll bar
        #------------------------------------------------------------------------------
        self.textBrowser_Description.Connect( self.GotoCode)
        self.textBrowser_Details.Connect( self.GotoCode)

        self.horizontalScrollBar.setMinimum(0)
        self.horizontalScrollBar.setMaximum(0)
        self.horizontalScrollBar.valueChanged.connect(self.DisplayViolationsData)

        self.pcLintPdf.clicked.connect( self.OpenPcLintManual)
        self.syncCode.setChecked(True)
        self.pushButton_GotoCode.clicked.connect(self.GotoCode)

        #------------------------------------------------------------------------------
        # Manage the Analysis Tab Widgets
        #------------------------------------------------------------------------------
        self.cannedAnalysisSelector.currentIndexChanged.connect(self.SelectAnalysisText)
        self.autoAcceptCanned = False

        self.pushButtonAddCanned.clicked.connect(self.SelectAnalysisText)

        self.pushButton_MarkReviewed.clicked.connect(lambda x='Reviewed',
                                                     fx=self.SaveAnalysis: fx(x))
        self.pushButton_MarkAccepted.clicked.connect(lambda x='Accepted',
                                                     fx=self.SaveAnalysis: fx(x))

        #------------------------------------------------------------------------------
        # Handle Project Tab Data
        #------------------------------------------------------------------------------
        self.pfSections.clicked.connect( self.GotoProjectFileIni)

        #------------------------------------------------------------------------------
        # Handle Merge Tab Data
        #------------------------------------------------------------------------------
        self.browseMergeProjectFile.clicked.connect( self.SelectMergeProjFile)
        self.performMerge.clicked.connect(self.PerformMerge)
        self.mergeProgress.setValue(0) # the first item it does not seem to listen

        #------------------------------------------------------------------------------
        # Handle GenerateReport Tab Data
        #------------------------------------------------------------------------------
        self.pushButton_BrowseSrcCode.clicked.connect(self.DisplaySrcFileBrowser)
        self.pushButton_BrowseReport.clicked.connect(self.DisplayReportFileBrowser)
        self.pushButton_GenerateReport.clicked.connect(self.GenerateReport)

    #-----------------------------------------------------------------------------------------------
    # Tab Selection and Control
    #-----------------------------------------------------------------------------------------------
    def CurrentTabChanged(self):
        """ When changing tabs perform clean up/set up conditions
        """
        newTab = self.tabWidget.currentIndex()

        # Make sure we have a username and project file before moving off config tab
        if self.curTab == eTabAdmin and newTab != eTabAdmin:
            #-----------------------------------------------------------------------
            # NOTE: this is very simple logic.  You MUST have a project file and a
            #       user name to get off the first tab.
            #-----------------------------------------------------------------------
            # see if we can move off the admin page
            errs = self.OkToMoveOffAdmin()
            if errs:
                self.tabWidget.setCurrentIndex(eTabAdmin)
                self.CrErrPopup('Please enter a valid %s' % ' and '.join(errs))
                newTab = eTabAdmin
            else:
                if newTab == eTabAnalysis:
                    if not self.analysisActive:
                        self.OpenAnalysisTab()
                    else:
                        self.tabWidget.setCurrentIndex(eTabAdmin)
                        self.CrErrPopup('You must wait for the tool analysis to complete!')

                elif newTab == eTabProject:
                    self.OpenProjectTab()

                elif newTab == eTabMerge:
                    self.OpenMergeTab()

        # moving to the Proj tab make sure the data is in there
        elif newTab == eTabProject:
            self.OpenProjectTab()

        elif newTab == eTabMerge:
            self.OpenMergeTab()

        # Coming back to the Config tab update the Stats as they may have analyzed something
        elif newTab == eTabAdmin and self.curTab != eTabAdmin:
            pfList = self.GetRecentProjFiles()
            self.projectFileSelector.clear()
            self.projectFileSelector.addItems( pfList)

            self.DisplayViolationStatistics()

        self.curTab = newTab

    #-----------------------------------------------------------------------------------------------
    def OkToMoveOffAdmin( self):
        """ here we make sure we have a project selected and a user name.  A user name could
            be their initials - 2 will do in case they hate their middle name or something
        """
        errs = []
        user = self.userName.strip()
        if self.db is None or len(user) < 2:
            if self.db is None: errs.append( 'Project File')
            if len(user) < 2: errs = ['User Name or initials (at least two characters).']
        return errs

    #-----------------------------------------------------------------------------------------------
    def OpenAnalysisTab(self):
        # see if understand is open and open it if not
        op = subprocess.check_output( 'tasklist')
        opStr = op.decode()

        if not self.programOpenedU4c or opStr.find('understand') == -1:
            # create a U4c object to get project Db info
            u4co = U4c(self.projFile)

            if opStr.find('understand') == -1:
                openIt = True
            else:
                msg  = 'Understand is currently running.\n'
                msg += 'For Code Viewing the following project should be open.\n'
                msg += '<%s>.\nWould you like this to happen.' % u4co.dbName
                rtn = QMessageBox.question( self, 'Understand Open',
                                            msg, QMessageBox.Yes, QMessageBox.No)
                if rtn == QMessageBox.Yes:
                    u4co.KillU4c()
                    openIt = True
                else:
                    openIt = False

            if openIt:
                # get path to understand from project
                undPath = self.projFile.paths[PF.ePathU4c]
                u4cPath, prog = os.path.split(undPath)
                understand = os.path.join(u4cPath, 'understand.exe')
                cmd = '%s -db "%s"' % (understand, u4co.dbName)
                subprocess.Popen( cmd)

            # indicate the user has the U4C Db open that they want open
            self.programOpenedU4c = True

    #-----------------------------------------------------------------------------------------------
    def OpenProjectTab(self):
        """ open the project file and load it into the viewer """
        self.projFileViewerLoaded = False
        if not self.projFileViewerLoaded:
            # open the select project file for display/editing
            f = open( self.projFileName, 'r')
            data = f.read()
            lines = data.split('\n')
            f.close()
            # scan the lines for all the ini groups
            self.iniGroups = OrderedDict()
            for lx, line in enumerate(lines):
                ls = line.strip()
                if ls and ls[0] == '[' and ls[-1] == ']':
                    # find the pos in the text
                    at = data.find(ls)
                    self.iniGroups[ls] = at

            iniList = list(self.iniGroups.keys())
            self.pfSections.clear()
            self.pfSections.addItems( iniList)

            text = '\n'.join(lines)
            self.pfText.setText( text)

    #-----------------------------------------------------------------------------------------------
    def OpenMergeTab( self):
        if self.projFile:
            txt = '[%s]' % self.projFileName
            self.mergeLabel.setText(txt)
            self.mergeProgress.setValue(0)

    #-----------------------------------------------------------------------------------------------
    # Admin Tab
    #-----------------------------------------------------------------------------------------------
    def NewProjFile( self, at):
        projFileName = self.projectFileSelector.currentText()
        if at > 0:
            if projFileName != self.projFileName:
                # reorder our recent PF list
                projFile = PF.ProjectFile( projFileName)
                self.ResetProject( projFile)

    #-----------------------------------------------------------------------------------------------
    def SelectProjectFile(self):
        """ Where ever the user can select a project file name this function handles that and
            keeping our known proj file list updated.

            It will only return a valid projFile object or None
        """
        pFile, selFilter = QFileDialog.getOpenFileName(self, "Select Project File")

        projFile = None

        if pFile:
            projFile = PF.ProjectFile( pFile)

        return projFile

    #-----------------------------------------------------------------------------------------------
    def ResetProject( self, projFile=None):
        """ A new project file has been selected - reset all the info in the display
        """
        self.filterUpdateInProgress = False
        self.currentFilters = []

        if projFile is None:
            projFileNames = self.GetRecentProjFiles()
            if projFileNames:
                # select the most recent
                self.projFileName = projFileNames[0]
                self.projFile = PF.ProjectFile( self.projFileName)
            else:
                self.projFile = None
                self.projFileName = ''
        else:
            self.projFile = projFile
            self.projFileName = projFile.projFileName
            # save the new proj file in the recent list on top
            self.SaveRecentProjFile( self.projFileName)

        if self.projFile and self.projFile.isValid:
            projFileNames = self.GetRecentProjFiles()

            self.setWindowTitle(self.baseTitle + '  <' + self.projFile.projFileName + '>')

            # display the recent file list
            self.projectFileSelector.clear()
            self.projectFileSelector.addItems( projFileNames)
            self.projectFileSelector.setCurrentIndex(0)

            # and on the merge tab
            self.mergeProjectFileSelector.clear()
            self.mergeProjectFileSelector.addItems( projFileNames)
            self.mergeProjectFileSelector.setCurrentIndex(0)

            # Get the canned comment data
            self.cannedAnalysisSelector.clear()
            self.cannedAnalysisSelector.addItems(self.GetAnalysisTextOptions())
            self.cannedAnalysisSelector.setCurrentIndex(0)

            #------------------------------------------------------------------------------
            # Establish a DataBase connection
            #------------------------------------------------------------------------------
            self.db = ViolationDb( self.projFile.paths[PF.ePathProject])

            self.FillFilters( 0, '', True)
            self.DisplayViolationStatistics()
            self.DisplayViolationsData()

            self.violationsData = []
            self.v = None

            self.programOpenedU4c = False
            self.analysisActive = False

            self.toolRunOutput = ''
            self.toolOutput.setText( self.toolRunOutput)

        elif self.projFile:
            msg = self.projFile.GetErrorText()
            self.projFile = None
            self.CrErrPopup( msg)

    #-----------------------------------------------------------------------------------------------
    def SelectMainProjectFile( self):
        pf = self.SelectProjectFile()
        if pf:
            self.ResetProject( pf)

    #-----------------------------------------------------------------------------------------------
    def DisplayViolationStatistics(self):
        if self.db:
            s = 'SELECT count(*) from Violations'
            total = self.db.Query(s)
        else:
            total = []

        if len(total) > 0:
            s = "SELECT count(*) from Violations where status = 'Accepted'"
            accepted = self.db.Query(s)

            s = "SELECT count(*) from Violations where status = 'Reviewed'"
            reviewed = self.db.Query(s)

            s = "SELECT count(*) from Violations where status = 'Not Reported'"
            noRep = self.db.Query(s)

            self.totalViolations.setText(str(total[0]))
            self.reviewedViolations.setText(str(reviewed[0]))
            self.acceptedViolations.setText(str(accepted[0]))
            self.removedViolations.setText(str(noRep[0]))
            self.activeViolations.setText(str(total[0].data-noRep[0].data))
            openIssues = total[0].data - (accepted[0].data + reviewed[0].data + noRep[0].data)
            self.openViolations.setText(str(openIssues))

            #-------------- KS Totals
            s = "SELECT count(*) from Violations where detectedBy = 'Knowlogic'"
            total = self.db.Query(s)

            s = "SELECT count(*) from Violations where status = 'Accepted' and detectedby = 'Knowlogic'"
            accepted = self.db.Query(s)

            s = "SELECT count(*) from Violations where status = 'Reviewed' and detectedby = 'Knowlogic'"
            reviewed = self.db.Query(s)

            s = "SELECT count(*) from Violations where status = 'Not Reported' and detectedby = 'Knowlogic'"
            noRep = self.db.Query(s)

            self.ksTotal.setText(str(total[0]))
            self.ksReviewed.setText(str(reviewed[0]))
            self.ksAccepted.setText(str(accepted[0]))
            self.ksRemoved.setText(str(noRep[0]))
            self.ksActive.setText(str(total[0].data-noRep[0].data))
            openIssues = total[0].data - (accepted[0].data + reviewed[0].data + noRep[0].data)
            self.ksOpen.setText(str(openIssues))

            #-------------- PC-LINT Totals
            s = "SELECT count(*) from Violations where detectedBy = 'PcLint'"
            total = self.db.Query(s)

            s = "SELECT count(*) from Violations where status = 'Accepted' and detectedby = 'PcLint'"
            accepted = self.db.Query(s)

            s = "SELECT count(*) from Violations where status = 'Reviewed' and detectedby = 'PcLint'"
            reviewed = self.db.Query(s)

            s = "SELECT count(*) from Violations where status = 'Not Reported' and detectedby = 'PcLint'"
            noRep = self.db.Query(s)

            self.pcTotal.setText(str(total[0]))
            self.pcReviewed.setText(str(reviewed[0]))
            self.pcAccepted.setText(str(accepted[0]))
            self.pcRemoved.setText(str(noRep[0]))
            self.pcActive.setText(str(total[0].data-noRep[0].data))
            openIssues = total[0].data - (accepted[0].data + reviewed[0].data + noRep[0].data)
            self.pcOpen.setText(str(openIssues))
        else:
            self.totalViolations.setText('0')
            self.reviewedViolations.setText('0')
            self.openViolations.setText('0')
            self.acceptedViolations.setText('0')
            self.removedViolations.setText('0')
            self.activeViolations.setText('0')

            self.ksTotal.setText('0')
            self.ksReviewed.setText('0')
            self.ksOpen.setText('0')
            self.ksAccepted.setText('0')
            self.ksRemoved.setText('0')
            self.ksActive.setText('0')

            self.pcTotal.setText('0')
            self.pcReviewed.setText('0')
            self.pcOpen.setText('0')
            self.pcAccepted.setText('0')
            self.pcRemoved.setText('0')
            self.pcActive.setText('0')

    #-----------------------------------------------------------------------------------------------
    def ExportDb( self):
        if self.db:
            fn, dummy = QFileDialog.getSaveFileName( self,
                                                     "Save DB to",
                                                     self.projFile.paths[PF.ePathProject],
                                                     "CSV File (*.csv)")
            if fn:
                self.db.Export( fn)
        else:
            self.CrErrPopup('You must select a project first')

    #-----------------------------------------------------------------------------------------------
    def ClearRemoved( self):
        if self.db:
            self.db.ClearRemoved()
            self.DisplayViolationStatistics()
        else:
            self.CrErrPopup('You must select a project first')

    #-----------------------------------------------------------------------------------------------
    def ShowLog( self, logId):
        if self.projFile:
            lines = []
            logName = ''
            if logId == eLogPc:
                pcl = PcLint( self.projFile)
                logName = pcl.GetLogName()
            elif logId == eLogKs:
                u4co = U4c(self.projFile)
                logName = u4co.GetLogName()
            elif logId == eLogTool:
                lines = [i+'\n' for i in self.toolRunOutput.split('\n')]

            if logName and os.path.isfile( logName):
                f = open(logName, 'r')
                lines = f.readlines()
                f.close()

            displayLines = ['%s Output contains %d lines\n' % (logId, len(lines))] + lines
            self.toolOutput.setText( ''.join( displayLines))
        else:
            self.CrErrPopup( 'Please select a project file.')

    #-----------------------------------------------------------------------------------------------
    # Tool Analysis
    #-----------------------------------------------------------------------------------------------
    def RunAnalysis(self):
        """ Run the analysis tools for PcLint and U4C
        """
        if self.projFile:
            # --- DO THIS FIRST ---
            # TODO can be removed when project file editing is working
            self.ResetProject( self.projFile)

            # see if understand is open they may have been edting something
            # give them a chance to save it.
            op = subprocess.check_output( 'tasklist')
            opStr = op.decode()
            if opStr.find('understand') != -1:
                msg  = 'We are about to close an open instance of Understand.\n\n'
                msg += 'If you have any unsaved work, please save the file(s) now\n'
                msg += 'or your work will be lost.'
                self.CrErrPopup(msg)

            self.runAnalysis.setEnabled(False)
            self.abortAnalysis.setEnabled(True)
            self.analysisActive = True

            self.abortRequested = False
            self.programOpenedU4c = False
            self.toolProgress = ''
            self.toolRunOutput = ''
            self.toolOutputText = []
            self.startAnalysis = DateTime.DateTime.today()

            cwd = os.getcwd()
            cmdPath = os.path.join( cwd, 'Analyze.py')
            cmd = 'c:\python32\python.exe "%s" "%s"' % (cmdPath, self.projFileName)
            rootDir = self.projFile.paths[PF.ePathProject]

            self.analysisProcess = subprocess.Popen( cmd,
                                                     cwd=rootDir,
                                                     stderr=subprocess.STDOUT,
                                                     stdout=subprocess.PIPE)

            # launch our thread to collect results
            t1 = util.ThreadSignal( self.CollectToolAnalysisOutput)
            t1.Go()

            self.toolOutput.clear()

            self.StartTimerEvent( self.AnalysisUpdate, 250)
        else:
            self.CrErrPopup('Please select a project file.')

    #-----------------------------------------------------------------------------------------------
    def AnalysisUpdate( self):
        #for line in self.analysisProcess.stdout:
        #    line = line.decode(encoding='windows-1252').strip()
        #    print(line)

        nowIs = DateTime.DateTime.today()
        elapsed = nowIs - self.startAnalysis
        elapsed.ShowMs( False)
        self.runAnalysis.setText('%s' % (elapsed))

        if self.AnalyzeActive():
            self.toolOutput.setText( self.toolRunOutput)

        else:
            self.analysisProcess = None
            self.BuildToolOutput()
            self.toolOutput.setText( self.toolRunOutput)

            self.runAnalysis.setText('Run Analysis')

            # kill the timer
            self.StopTimerEvent()

            # update things dependent on the DB
            self.FillFilters( 0, '', True)
            self.DisplayViolationStatistics()
            self.DisplayViolationsData()

            self.violationsData = []
            self.v = None

            self.programOpenedU4c = False
            self.analysisActive = False

            self.runAnalysis.setEnabled(True)
            self.abortAnalysis.setEnabled(False)

    #-----------------------------------------------------------------------------------------------
    def AnalyzeActive(self):
        """ is a review actively running
        Note the sleep is to ensure if threads are getting active status they give up control
        """
        status = False
        if self.analysisProcess is not None:
            if self.analysisProcess.poll() is None:
                status = True

        return status

    #-----------------------------------------------------------------------------------------------
    def AbortAnalysis(self):
        """ Abort the analysis process
        """
        if self.analysisProcess:
            self.abortRequested = True
            time.sleep(0.25)
            self.analysisProcess.kill()

    #-----------------------------------------------------------------------------------------------
    def CollectToolAnalysisOutput(self):
        """ This function is run as a thread to collect Tool Analysis Process outputs """
        while self.AnalyzeActive():
            line = self.analysisProcess.stdout.readline()
            line = line.decode(encoding='windows-1252').strip()
            if line.find( '^') == 0:
                self.toolProgress = line[1:] # remove the '^'
            else:
                self.toolOutputText.append( line)

            self.BuildToolOutput()
            time.sleep(0.001)

    #-----------------------------------------------------------------------------------------------
    def BuildToolOutput( self):
        text = '\n'.join(self.toolOutputText)

        text = self.toolProgress + '\n\n' + text

        if self.abortRequested:
            text = text.strip()
            text += '\n\n--- Tool Analysis ABORTED. '
            text += 'Partial tool analysis results maybe included. ---'

        self.toolRunOutput = text

    #-----------------------------------------------------------------------------------------------
    # Filter Handling
    #-----------------------------------------------------------------------------------------------
    def ResetFilters( self):
        """ Clear all the filters """
        self.FillFilters( 0, '', True)

    #-----------------------------------------------------------------------------------------------
    def FillFilters( self, index=-1, name='', reset=False):
        """ This function fills in all of the filter selection dropdowns based on the
            settings in the other filter dropdowns.

            filterUpdateInProgress - stop re-entrant calls when we update the filter lists items
                                     as it appears the selection changed
        """
        if not self.filterUpdateInProgress:
            self.filterUpdateInProgress = True

            if reset:
                self.currentFilters = []
                self.dispositioned.setCheckState( QtCore.Qt.Unchecked)
                for dd in self.filterInfo:
                    gui = getattr( self, 'comboBox_%s' % dd)
                    gui.clear()

            # don't refill the ones that have changed
            if name:
                if name not in self.currentFilters:
                    self.currentFilters.append(name)
                if index <= 0:
                    self.currentFilters.remove( name)

            whereClause = self.BuildSqlStatement()

            # now loop through each filter applying the constraint
            for dd in self.filterInfo:
                if dd not in self.currentFilters:
                    gui = getattr( self, 'comboBox_%s' % dd)
                    s = """select distinct(%s)
                           from violations
                           %s
                           order by %s""" % ( self.filterInfo[dd], whereClause, self.filterInfo[dd])
                    q = self.db.Query(s)

                    # special handling for filenames to remove the (W)
                    if dd == 'Filename':
                        comboList = [i.data for i in q if i.data.find('(W)') == -1]
                    else:
                        comboList = [i.data for i in q]

                    # put some stuff up front
                    comboList = ['Select <%s> [%d]' % (dd, len(comboList))] + comboList

                    gui.clear()
                    gui.addItems( comboList)
                    gui.setCurrentIndex(0)

            # done with the filter update
            self.filterUpdateInProgress = False

    #-----------------------------------------------------------------------------------------------
    def BuildSqlStatement(self):
        noFilterRe = re.compile('Select <[A-Za-z]+>')

        whereClause = ''
        constraints = ['reviewDate is NULL']

        if self.dispositioned.isChecked():
            constraints = []

        # get the value of all filter and make a constraint on all the queries
        for dd in self.filterInfo:
            gui = getattr( self, 'comboBox_%s' % dd)
            if gui.count() > 0:
                text = gui.currentText()
                filterOff = noFilterRe.search( text)
                if filterOff is None:
                    # ok we have something to filter on
                    filterText = "%s = '%s'" % (self.filterInfo[dd], text)
                    constraints.append( filterText)
                elif text == '':
                    # ok we want an empty string
                    filterText = "%s = ''" % (self.filterInfo[dd])
                    constraints.append( filterText)

        # check for user strings in desc/detail
        desc = self.lineEditDescFilter.text()
        detl = self.lineEditDetailsFilter.text()
        if desc.strip():
            constraints.append( "description like '%%%s%%'" % desc)
        if detl.strip():
            constraints.append( "details like '%%%s%%'" % detl)

        if constraints:
            queryConstraint = '\nand '.join( constraints)
            whereClause = 'where %s' % queryConstraint

        return whereClause

    #-----------------------------------------------------------------------------------------------
    def ApplyFilters(self):
        """ Display the violations information based on selected filters """

        # don't automatically accept the select canned analysis
        self.autoAcceptCanned = False

        # Query the database using filters selected
        s = """
            SELECT filename, function, severity, violationId, description, details,
                   lineNumber, detectedBy, firstReport, lastReport, status, analysis,
                   who, reviewDate
            FROM Violations
            %s
            order by lineNumber desc, filename, detectedBy, violationId, function, severity
            """
        whereClause = self.BuildSqlStatement()
        sql = s % whereClause

        self.violationsData = []
        self.violationsData = self.db.Query( sql)

        # Display Violations Data
        if self.violationsData:
            self.horizontalScrollBar.setMinimum(0)
            self.horizontalScrollBar.setMaximum((len(self.violationsData)-1))
            self.horizontalScrollBar.setValue(0)
        else:
            self.horizontalScrollBar.setMinimum(0)
            self.horizontalScrollBar.setMaximum(0)

        self.DisplayViolationsData()

    #-----------------------------------------------------------------------------------------------
    def DisplayViolationsData(self):
        """ Display violations data """
        at = self.horizontalScrollBar.value()
        at += 1
        total = len(self.violationsData)

        if self.violationsData:
            # Violation 'number' is one greater than scrollbar index which starts at 0
            self.groupBox_Violations.setTitle("Currently Selected Violation %d of %d" % (at,total))

            # Populate the fields in the violations groupbox
            self.v = self.violationsData[self.horizontalScrollBar.value()]
            self.textBrowser_Filename.setText(self.v.filename)
            self.textBrowser_Function.setText(self.v.function)
            self.textBrowser_Description.setText(self.v.description)
            self.textBrowser_Details.setText(self.v.details)
            self.textBrowser_Severity.setText(self.v.severity)
            self.textBrowser_Id.setText(self.v.violationId)
            self.textBrowser_DetectedBy.setText(self.v.detectedBy)
            self.lineNumber.setText(str(self.v.lineNumber))
            rd = '%s' % self.v.firstReport
            dt = DateTime.DateTime.today()
            dt = dt.Set(rd)
            dt.ShowMs( False)
            self.reportedOn.setText(str(dt))

            # Populate the fields in the Analysis groupbox
            if self.v.reviewDate:
                self.textBrowser_PrevReviewer.setText(self.v.who)
                rd = '%s' % self.v.reviewDate
                dt = DateTime.DateTime.today()
                dt = dt.Set(rd)
                dt.ShowMs( False)
                self.textBrowser_PrevDate.setText(str(dt))
                self.textBrowser_PrevStatus.setText(self.v.status)
            else:
                self.textBrowser_PrevReviewer.clear()
                self.textBrowser_PrevDate.clear()
                self.textBrowser_PrevStatus.clear()

            self.plainTextEdit_Analysis.setPlainText(self.v.analysis)

            # are we autosyncing the code with the scroll bar?
            if self.syncCode.isChecked():
                self.GotoCode()

        else:
            self.groupBox_Violations.setTitle("Currently Selected Violation 0 of 0")
            self.textBrowser_Filename.clear()
            self.textBrowser_Function.clear()
            self.textBrowser_Description.clear()
            self.textBrowser_Details.clear()
            self.textBrowser_Severity.clear()
            self.textBrowser_Id.clear()
            self.textBrowser_DetectedBy.clear()
            self.v = None

    #-----------------------------------------------------------------------------------------------
    # User Analysis
    #-----------------------------------------------------------------------------------------------
    def GetAnalysisTextOptions(self):
        """ Return list of canned analysis text to display in the combobox for user selection """
        analysisTextList = ['Analysis Text Selection']
        analysisTextList.extend(self.projFile.analysisComments)

        return analysisTextList

    #-----------------------------------------------------------------------------------------------
    def SelectAnalysisText(self):
        """ Update the Analysis Text Browser with the user's choice from the combobox """
        analysisChoice = self.cannedAnalysisSelector.currentText()

        analysisChoice = analysisChoice.replace(r'\n', '\n')

        if analysisChoice != 'Analysis Text Selection':
            # Append the canned comment to the analysis text rather than clear() it first.
            # This would allow for the case where they want to enter other information first
            self.plainTextEdit_Analysis.append(analysisChoice)

    #-----------------------------------------------------------------------------------------------
    def SaveAnalysis(self, status):
        """ Save analysis data entered and mark status as reviewed or accepted based status
            passed in
        """
        reportBlank = True
        if self.v:
            analysisText = self.plainTextEdit_Analysis.toPlainText()
            if not analysisText.strip():
                # see if a canned comment is selected
                self.SelectAnalysisText()
                analysisText = self.plainTextEdit_Analysis.toPlainText()
                if analysisText and not self.autoAcceptCanned:
                    msgBox = QMessageBox(self)
                    msgBox.setWindowTitle( 'Auto-Complete Prompt')

                    msg  = 'We have auto-populated the analysis comment.'
                    msgBox.setText(msg)

                    msg = "If you want to keep it click 'Yes'.\n"
                    msg += "\nIf you want to keep the selected comment, without being asked again\n"
                    msg += "until you 'Apply Filters' click 'Yes To All'."
                    msgBox.setInformativeText(msg)

                    msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.YesToAll | QMessageBox.No)
                    msgBox.setDefaultButton(QMessageBox.Yes)
                    rtn = msgBox.exec_()

                    if rtn not in (QMessageBox.Yes, QMessageBox.YesToAll):
                        analysisText = ''
                        self.plainTextEdit_Analysis.clear()
                        reportBlank = False

                    if rtn == QMessageBox.YesToAll:
                        self.autoAcceptCanned = True

            if analysisText:
                if self.applyToAll.isChecked():
                    tagList = self.violationsData
                else:
                    tagList = [self.v]

                updateCmd = """UPDATE Violations
                                   SET status = ?, analysis = ?, who = ?, reviewDate = ?
                                 WHERE filename = ?
                                   AND function = ?
                                   AND severity = ?
                                   AND violationId = ?
                                   AND description = ?
                                   AND details = ?
                                   AND lineNumber = ? """

                nowIs = datetime.datetime.now()

                for i in tagList:
                    self.db.Execute(updateCmd,
                                    status,
                                    analysisText,
                                    self.userName,
                                    nowIs,
                                    i.filename,
                                    i.function,
                                    i.severity,
                                    i.violationId,
                                    i.description,
                                    i.details,
                                    i.lineNumber)

                self.db.Commit()

                # ensure apply to all is cleared after each use
                self.applyToAll.setCheckState(QtCore.Qt.Unchecked)

                # remember where we are to the next issue
                at = self.horizontalScrollBar.value()

                # refresh the data in our cache, save autoAcceptCanned State
                temp = self.autoAcceptCanned

                keepState = self.syncCode.checkState()
                self.syncCode.setCheckState(QtCore.Qt.Unchecked)
                self.ApplyFilters()
                self.syncCode.setCheckState(keepState)
                self.autoAcceptCanned = temp

                # now go there - scroll bar handles setting to locations that do not exist
                # i.e., if we accepted the last violation in a set
                #       => 19 of 19 we should position ourself at 18 of 18
                if self.dispositioned.isChecked():
                    self.horizontalScrollBar.setValue(at+1)
                else:
                    self.horizontalScrollBar.setValue(at)

                if self.syncCode.isChecked():
                    self.GotoCode()
            else:
                if reportBlank:
                    QMessageBox.information( self, "Comment", 'You need to specify a comment')

    #-----------------------------------------------------------------------------------------------
    def DisplaySrcFileBrowser(self):
        # Display a file browser for the user to select the project file database directory
        srcFile = str(QFileDialog.getExistingDirectory(self, "Select Source Code Directory"))

        self.textBrowser_ReportFile.setText(srcFile)

    #-----------------------------------------------------------------------------------------------
    def DisplayReportFileBrowser(self):

        # Display a file browser for the user to select the reports file directory

        reportFile = str(QFileDialog.getExistingDirectory(self, "Select Reports Directory"))

        self.textBrowser_ReportDir.setText(reportFile)

    #-----------------------------------------------------------------------------------------------
    def OpenPcLintManual(self):
        """ open the PC-Lint PDF """
        # remove the exe
        f = open('pcLintManual.bat', 'w')
        path, exe = os.path.split(self.projFile.paths[PF.ePathPcLint])
        fn = os.path.join( path, 'PC-lint.pdf')
        cmd = 'start %s\n' % fn
        f.write( cmd)
        f.close()
        t = subprocess.Popen( 'pcLintManual.bat')

    #-----------------------------------------------------------------------------------------------
    def GotoCode(self):
        # get the filename and line number for this violation
        if self.v:
            filename = self.v.filename
            filename = filename.replace('(W)', '').strip()
            fpfn = self.projFile.FullPathName( filename)
            if fpfn:
                if len(fpfn) == 1:
                    viewerCommand = self.projFile.paths[PF.ePathViewer]

                    viewerCommand = viewerCommand.replace( '<fullPathFileName>', '"%s"' % fpfn[0])

                    linenumber = self.v.lineNumber
                    if linenumber >= 0:
                        viewerCommand = viewerCommand.replace( '<lineNumber>', str(linenumber))
                    else:
                        viewerCommand = viewerCommand.replace( '<lineNumber>', '')

                    subprocess.Popen( viewerCommand)
            else:
                if filename:
                    msg = 'Ambiguous filename (%s)\n%s' % (filename,'\n'.join(fpfn))
                    self.CrErrPopup( msg)
        else:
            msg = 'No matching violations.'
            self.CrErrPopup( msg)

    #-----------------------------------------------------------------------------------------------
    # Manual Entry Tab
    #-----------------------------------------------------------------------------------------------
    #-----------------------------------------------------------------------------------------------
    # Project Tab
    #-----------------------------------------------------------------------------------------------
    def GotoProjectFileIni( self):
        """ Goto the text for the select ini group, display its tip
            TODO: center the select group
        """
        text = self.pfSections.currentItem().text()
        newChar = -1
        for i in self.iniGroups:
            if text.find(i) != -1:
                newChar = self.iniGroups[i]
                tip = self.projFile.GetTip( text)
                break

        if newChar != -1:
            self.sectionTip.setText( tip)
            # goto that area of the proj file
            curCursor = self.pfText.textCursor()
            atChar = curCursor.position()

            curCursor.setPosition( newChar)
            self.pfText.setTextCursor(curCursor)

    #-----------------------------------------------------------------------------------------------
    # Merge Tab
    #-----------------------------------------------------------------------------------------------
    def SelectMergeProjFile( self):
        pf = self.SelectProjectFile()
        if pf:
            pfName = pf.projFileName
            pfList = self.GetRecentProjFiles()

            # save this pf name at the end of the list
            self.SaveRecentProjFile( pfName, False)
            if pfName in pfList:
                pfList.remove( pfName)

            # we display it first in our merge list though
            pfList = [pfName] + pfList
            self.mergeProjectFileSelector.clear()
            self.mergeProjectFileSelector.addItems( pfList)

    #-----------------------------------------------------------------------------------------------
    def PerformMerge( self):
        # run merge as a thread and report it's status
        # get the merge project file and validate
        # if valid merge project
        #   Merge the DB as a thread
        # else
        #   report it
        mergePf = self.mergeProjectFileSelector.currentText()
        if mergePf != self.projFileName:
            pf = PF.ProjectFile( mergePf)
            if pf.isValid:
                self.performMerge.setEnabled(False)

                mdb = ViolationDb( pf.paths[PF.ePathProject])
                mn = mdb.dbName

                self.mergeThread = util.ThreadSignal( lambda x=mn,fx=self.RunMerge: fx(x))

                self.mergeProgress.setValue( 0)

                self.mergeThread.Go()
                self.StartTimerEvent( self.UpdateMerge, 250)

            else:
                self.CrErrPopup('Merge Project File Error:\n%s' % pf.GetErrorText())
        else:
            msg  = 'You cannot merge a file with itself.\n'
            msg += "Well you can but it really doesn't do much!"
            self.CrErrPopup(msg)

    #-----------------------------------------------------------------------------------------------
    def RunMerge( self, otherDbName):
        """ DB Creation and access must occur in the same thread so we heave this little helper
            func
        """
        # now open our Db
        self.sdb = ViolationDb( self.projFile.paths[PF.ePathProject])
        self.sdb.Merge( otherDbName)

    #-----------------------------------------------------------------------------------------------
    def UpdateMerge( self):
        #
        pct = int(self.sdb.mergePct)
        self.mergeProgress.setValue( pct)
        # display merge results
        sts = self.sdb.ShowMergeStats()
        self.mergeResults.setText( sts)

        if not self.mergeThread.active:
            self.StopTimerEvent()
            self.performMerge.setEnabled(True)
            self.mergeResults.setText( sts + '\n\nDone')

    #-----------------------------------------------------------------------------------------------
    # Report Tab
    #-----------------------------------------------------------------------------------------------
    def GenerateReport(self):
        self.CrErrPopup('Not yet implemented...')

    #-----------------------------------------------------------------------------------------------
    # Utils
    #-----------------------------------------------------------------------------------------------
    def StartTimerEvent( self, handler, ms):
        if self.timer is None:
            self.timer = QtCore.QTimer(self)
            self.connect(self.timer, QtCore.SIGNAL("timeout()"), handler)
            self.timerDelay = ms
            self.timer.start( self.timerDelay)
        else:
            self.CrErrPopup("I'm busy doing something else, have some coffee.")

    #-----------------------------------------------------------------------------------------------
    def StopTimerEvent( self):
        self.timer.stop()
        self.timer = None

    #-----------------------------------------------------------------------------------------------
    def CrErrPopup(self, errText):
        """ The crErrPopup provides a popup dialog to be used for simple
            notifications to the user through the GUI """
        msgBox = QMessageBox()
        msgBox.setWindowTitle("Knowlogic Code Review")
        msgBox.setText(errText)
        msgBox.exec_()

    #-----------------------------------------------------------------------------------------------
    def lineEditDescFilterChanged(self):
        descFilter = self.lineEditDescFilter.text()

    #-----------------------------------------------------------------------------------------------
    def lineEditDetailsFilterChanged(self):
        detailsFilter = self.lineEditDetailsFilter.text()

    #-----------------------------------------------------------------------------------------------
    def lineEditUserNameChanged(self):
        tmp = self.lineEdit_userName.text().strip()
        if tmp:
            self.userName = tmp

    #-----------------------------------------------------------------------------------------------
    def GetIniFilename( self):
        """ create an init file name based on the machine the user is running from
            this is used to make unique ini files if people are workgin from a common install
        """
        if not os.path.isdir( '.ini'):
            os.makedirs( '.ini')

        host = socket.gethostname()
        fn = eKsCrtIni + '_%s.ini' % host
        fn = util.ValidFileName( fn)
        rpfn =  os.path.join( '.ini', fn)

        return rpfn

    #-----------------------------------------------------------------------------------------------
    def GetRecentProjFiles( self):
        projFileNames = []

        iniFn = self.GetIniFilename()
        if os.path.isfile( iniFn):
            # recall the last open project file
            f = open(iniFn, 'r')
            projFileNames = [i.strip() for i in f.readlines()]
            f.close()

        return projFileNames

    #-----------------------------------------------------------------------------------------------
    def SaveRecentProjFile( self, projFileName, first=True):
        """ Save a list of project file, put the name passed in on the top of the list if first
            is True, otherwise append to the end
        """
        projFileNames = self.GetRecentProjFiles()
        if projFileName in projFileNames:
            projFileNames.remove( projFileName)

        if first:
            projFileNames = [projFileName] + projFileNames
        else:
            projFileNames.append( projFileName)

        # save the results
        iniFn = self.GetIniFilename()
        f = open(iniFn, 'w')
        [f.write( i+'\n') for i in projFileNames]
        f.close()


#------------------------------------------------------------------------------------
# Main Program
#
# Instantiates the QApplication and Displays the Main Window.
#------------------------------------------------------------------------------------
def main():
    # Create Application
    app = QApplication(sys.argv)
    frame = MainWindow()

    # Launch Main Window
    frame.show()
    app.exec_()

if __name__=='__main__':
    main()

