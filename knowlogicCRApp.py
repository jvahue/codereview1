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
import datetime
import os
import sys
import subprocess
import re

#---------------------------------------------------------------------------------------------------
# Third Party Modules
#---------------------------------------------------------------------------------------------------
from PySide import QtCore
from PySide.QtGui import QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QFileDialog, QDialog

import sqlite3

#---------------------------------------------------------------------------------------------------
# Knowlogic Modules
#---------------------------------------------------------------------------------------------------
from utils import DateTime, util
from utils.DB.database import Query, GetAll, GetCursor
from utils.DB.sqlLite.database import DB_SQLite

from tools.pcLint.PcLint import PcLint
from tools.u4c.u4c import U4c

from Analyze import Analyzer
from crappcustomiddialog import Ui_CRAppCustomIdDialog
from crmainwindow import Ui_MainWindow
from ViolationDb import eDbName, eDbRoot

import ProjFile as PF

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
eKsCrIni = 'KsCr.ini'
eLogPc = 'PcLint'
eLogKs = 'Knowlogic'
eLogTool = 'Tool Output'

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------
# Class CRAppCustomIdDialog
#
# The CRAppCustomIdDialog consists of one QLineEdit object.
#
# There is also a QDialogButtonBox:
#    OK
#    Cancel
#
# NOTE: The Ui_CustomIdDialog code in the CRAppCustomIdDialog should not
# be altered.  If changes to the UI are required, it should be done with
# QT Designer and then regenerated.
#--------------------------------------------------------------------------
class CRAppCustomIdDialog(QDialog, Ui_CRAppCustomIdDialog):
    """ This dialog pops up when the user selects the custom option from the violationId Filter comboBox.
        It allows the user to enter custom text for a the violationId filter. """

    def __init__(self, parent=None):
        super(CRAppCustomIdDialog, self).__init__()
        self.setupUi(self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def getValue(self):
        text = self.lineEdit_customText.text()
        return (text)

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
        self.setWindowTitle("Knowlogic Code Review Application")

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
        self.curTab = 0
        self.db = None

        self.violationsData = []
        self.v = None

        self.programOpenedU4c = False
        self.analysisActive = False

        self.projFile = None
        self.toolRunOutput = ''

        self.ResetProject()

        #------------------------------------------------------------------------------
        # Handle Tabs of TabWidget
        #------------------------------------------------------------------------------
        self.tabWidget.currentChanged.connect(self.CurrentTabChanged)

        #------------------------------------------------------------------------------
        # Handle Config Tab Data
        #------------------------------------------------------------------------------
        self.projectFileNameEditor.currentIndexChanged.connect(self.NewProjFile)
        self.pushButton_pFileBrowse.clicked.connect(self.SelectProjectFile)

        self.lineEdit_userName.editingFinished.connect(self.lineEditUserNameChanged)

        self.pushButton_RunAnalysis.clicked.connect(self.RunAnalysis)
        self.pushButtonAbortAnalysis.clicked.connect(self.AbortAnalysis)
        self.showPcLintLog.clicked.connect(lambda x=eLogPc,fx=self.ShowLog: fx(x))
        self.showKsLog.clicked.connect(lambda x=eLogKs,fx=self.ShowLog: fx(x))
        self.showToolOutput.clicked.connect(lambda x=eLogTool,fx=self.ShowLog: fx(x))

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

        #------------------------------------------------------------------------------
        # Manage the violations horizontal slider scroll bar
        #------------------------------------------------------------------------------
        self.horizontalScrollBar.setMinimum(0)
        self.horizontalScrollBar.setMaximum(0)
        self.horizontalScrollBar.valueChanged.connect(self.DisplayViolationsData)
        self.pushButton_GotoCode.clicked.connect(self.GotoCode)

        #------------------------------------------------------------------------------
        # Manage the Analysis Tab Widgets
        #------------------------------------------------------------------------------

        self.comboBoxAnalysisTextOptions.currentIndexChanged.connect(self.SelectAnalysisText)

        self.pushButtonAddCanned.clicked.connect(self.SelectAnalysisText)

        self.pushButton_MarkReviewed.clicked.connect(lambda x='Reviewed',
                                                     fx=self.SaveAnalysis: fx(x))
        self.pushButton_MarkAccepted.clicked.connect(lambda x='Accepted',
                                                     fx=self.SaveAnalysis: fx(x))

        #------------------------------------------------------------------------------
        # Handle GenerateReport Tab Data
        #------------------------------------------------------------------------------
        self.pushButton_BrowseSrcCode.clicked.connect(self.DisplaySrcFileBrowser)
        self.pushButton_BrowseReport.clicked.connect(self.DisplayReportFileBrowser)
        self.pushButton_GenerateReport.clicked.connect(self.GenerateReport)

    #-----------------------------------------------------------------------------------------------
    def NewProjFile( self, at):
        projFileName = self.projectFileNameEditor.currentText()
        if at > 0:
            self.ResetProject( projFileName)

    #-----------------------------------------------------------------------------------------------
    def ResetProject( self, projFileName = ''):
        """ A new project file has been selected - reset all the info in the display
        """
        self.filterUpdateInProgress = False
        self.currentFilters = []

        projFileNames = []
        if os.path.isfile( eKsCrIni):
            # recall the last open project file
            f = open(eKsCrIni, 'r')
            projFileNames = [i.strip() for i in f.readlines()]
            f.close()

        if not projFileName and projFileNames:
            projFileName = projFileNames[0]

        if os.path.isfile( projFileName):
            self.pFullFilename = projFileName
            self.projFile = PF.ProjectFile( projFileName)

            if self.projFile.isValid:
                # save the current project file for next startup
                f = open(eKsCrIni, 'w')

                # put it in the list at the top
                if projFileName in projFileNames:
                    projFileNames.remove( projFileName)

                projFileNames = [projFileName] + projFileNames
                [f.write( i+'\n') for i in projFileNames]
                f.close()

                # display the reordered list
                self.projectFileNameEditor.clear()
                self.projectFileNameEditor.addItems( projFileNames)
                self.projectFileNameEditor.setCurrentIndex(0)

                self.dbFname = eDbName
                self.dbFullFilename = os.path.join( self.projFile.paths[PF.ePathProject],
                                                    eDbRoot, eDbName)

                # Get the canned comment data
                self.comboBoxAnalysisTextOptions.clear()
                self.comboBoxAnalysisTextOptions.addItems(self.GetAnalysisTextOptions())
                self.comboBoxAnalysisTextOptions.setCurrentIndex(0)

                #------------------------------------------------------------------------------
                # Establish a DataBase connection
                #------------------------------------------------------------------------------
                if os.path.isfile(self.dbFullFilename):
                    self.OpenDb( True)

                else:
                    self.toolOutput.setText('No Database exists for this project yet.')

                self.violationsData = []
                self.v = None

                self.programOpenedU4c = False
                self.analysisActive = False

                # clear out the display fields
                self.DisplayViolationsData()

            else:
                self.projFile = None
                msg = '\n'.join( self.projFile.errors)
                self.CrErrPopup( msg)

    #-----------------------------------------------------------------------------------------------
    def OpenDb(self, forceOpen = False):
        if forceOpen:
            del self.db
            self.db = None

        if self.db is None:
            self.db = DB_SQLite()
            self.db.Connect(self.dbFullFilename)

            self.FillFilters( 0, '', True)
            self.DisplayViolationStatistics()

    #-----------------------------------------------------------------------------------------------
    def CrErrPopup(self, errText):
        """ The crErrPopup provides a popup dialog to be used for simple
            notifications to the user through the GUI """
        msgBox = QMessageBox()
        msgBox.setWindowTitle("Knowlogic Code Review")
        msgBox.setText(errText)
        msgBox.exec_()

    #-----------------------------------------------------------------------------------------------
    def CurrentTabChanged(self):
        """ When changing tabs perform clean up/set up conditions
        """
        newTab = self.tabWidget.currentIndex()

        # Make sure we have a username and project file before moving off config tab
        if newTab != 0:
            if self.db is None or self.userName == '':
                self.tabWidget.setCurrentIndex(0)
                if self.userName:
                    errs = []
                else:
                    errs = ['Username']
                if self.db is None:
                    errs.append( 'Project File')

                self.CrErrPopup('Please enter a valid %s' % ' and '.join(errs))

            if newTab == 1 and not self.programOpenedU4c and not self.analysisActive:
                # see if understand is open and open it if not
                op = subprocess.check_output( 'tasklist')
                opStr = op.decode()

                # create a U4c object ot get project Db info
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
                        u4co.IsReadyToAnalyze( True)
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
                    self.programOpenedU4c = True

        # Coming back to the Config tab update the Stats as they may have analyzed something
        elif newTab == 0 and self.curTab != 0:
            self.DisplayViolationStatistics()

        self.curTab = newTab

    #-----------------------------------------------------------------------------------------------
    def lineEditUserNameChanged(self):
        self.userName = self.lineEdit_userName.text()

    #-----------------------------------------------------------------------------------------------
    def SelectProjectFile(self):
        """ Display a file browser for the user to select the project file """
        pFile, selFilter = QFileDialog.getOpenFileName(self, "Select Project File")
        if pFile:
            self.ResetProject( pFile)

    #-----------------------------------------------------------------------------------------------
    def DisplayViolationStatistics(self):
        s = 'SELECT count(*) from Violations'
        total = self.db.Query(s)
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

    #-----------------------------------------------------------------------------------------------
    def RunAnalysis(self):
        """ Run the analysis in a thread so we can display its status
        """
        if not self.analysisActive:
            self.analysisActive = True

            # refresh the project file incase they changed anything
            # TODO: remove this when we have Cfg file editing
            self.ResetProject( self.pFullFilename)

            analyzer = Analyzer(self.pFullFilename)

            if analyzer.isValid:

                self.analyzerThread = util.ThreadSignal( analyzer.Analyze, analyzer)
                self.analyzerThread.Go()

                self.timer = QtCore.QTimer(self)
                self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.AnalysisUpdate)
                self.timer.start(500)
                self.toolRunOutput = ''
                self.startAnalysis = DateTime.DateTime.today()
            else:
                self.CrErrPopup(analyzer.status)
                self.analysisActive = False

    #-----------------------------------------------------------------------------------------------
    def AbortAnalysis(self):
        """ Abort the analysis process
        """
        self.analyzerThread.classRef.abortRequest = True

    #-----------------------------------------------------------------------------------------------
    def AnalysisUpdate( self):
        sts = self.analyzerThread.classRef.status
        if self.analyzerThread.active:
            # use the project file for status display while it's running
            self.toolOutput.setText(sts)

            nowIs = DateTime.DateTime.today()
            elapsed = nowIs - self.startAnalysis
            elapsed.ShowMs( False)
            self.pushButton_RunAnalysis.setText('%s' % elapsed)
        else:
            sts += '\n\nDone.'
            self.toolOutput.setText(sts)
            self.pushButton_RunAnalysis.setText('Run Analysis')

            # save this for recall
            self.toolRunOutput = sts

            # kill the timer
            self.timer.stop()

            self.OpenDb()

            # populate the display data
            self.FillFilters( 0, '', True)
            self.DisplayViolationStatistics()

            self.analysisActive = False

    #-----------------------------------------------------------------------------------------------
    def RunAnalysis1(self):
        if not self.analysisActive:
            self.analysisActive = True
            self.toolOutputText = []
            cwd = os.getcwd()
            cmdPath = os.path.join( cwd, 'Analyze.py')
            cmd = 'c:\python32\python.exe %s "%s"' % (cmdPath, self.pFullFilename)
            rootDir = self.projFile.paths[PF.ePathProject]
            self.analysisProcess = subprocess.Popen( cmd,
                                                     bufsize=-1,
                                                     cwd=rootDir,
                                                     stderr=subprocess.STDOUT,
                                                     stdout=subprocess.PIPE)

            self.timer = QtCore.QTimer(self)
            self.connect(self.timer, QtCore.SIGNAL("timeout()"), self.AnalysisUpdate)
            self.timer.start(500)
            self.toolRunOutput = ''
            self.startAnalysis = DateTime.DateTime.today()

    #-----------------------------------------------------------------------------------------------
    def AnalysisUpdate1( self):
        for line in self.analysisProcess.stdout:
            line = line.decode(encoding='windows-1252').strip()
            print(line)

        if self.AnalyzeActive():
            for line in self.analysisProcess.stdout:
                line = line.decode(encoding='windows-1252').strip()
                if line.find( '^') == 0:
                    self.toolOutputText = self.toolOutputText[:-1]

                self.toolOutputText.append( line)

                self.toolOutput.setText('\n'.join(self.toolOutputText))

                nowIs = DateTime.DateTime.today()
                elapsed = nowIs - self.startAnalysis
                elapsed.ShowMs( False)
                self.pushButton_RunAnalysis.setText('%s' % elapsed)

        else:
            self.toolOutputText.append(  '\n\nDone.')
            sts = '\n'.join(self.toolOutputText)
            self.toolOutput.setText(sts)
            self.pushButton_RunAnalysis.setText('Run Analysis')

            # save this for recall
            self.toolRunOutput = sts

            # kill the timer
            self.timer.stop()

            self.OpenDb()

            # populate the display data
            self.FillFilters( 0, '', True)
            self.DisplayViolationStatistics()

            self.analysisActive = False

    #-----------------------------------------------------------------------------------------------
    def AnalyzeActive(self):
        """ is a review actively running
        Note the sleep is to ensure if threads are getting active status they give up control
        """
        status = False
        if self.analysisProcess is not None:
            print('Analysis Process exists')
            if self.analysisProcess.poll() is None:
                status = True
            else:
                print( 'Analysis done')
        else:
            print('No analysis process')

        return status

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

            noFilterRe = re.compile('Select <[A-Za-z]+> \[[0-9]+\]')

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
    def lineEditDescFilterChanged(self):
        descFilter = self.lineEditDescFilter.text()
        # TODO : Handle the description filter

    #-----------------------------------------------------------------------------------------------
    def lineEditDetailsFilterChanged(self):
        detailsFilter = self.lineEditDetailsFilter.text()
        # TODO : Handle the details filter

    #-----------------------------------------------------------------------------------------------
    def ApplyFilters(self):
        """ Display the violations information based on selected filters """

        """ Query the database using filters selected """
        s = """
            SELECT filename, function, severity, violationId, description, details,
                   lineNumber, detectedBy, firstReport, lastReport, status, analysis,
                   who, reviewDate
            FROM Violations
            %s
            order by filename, detectedBy, violationId, function, severity
            """
        whereClause = self.BuildSqlStatement()
        sql = s % whereClause

        self.violationsData = []
        self.violationsData = self.db.Query( sql)

        """ Display Violations Data """
        if self.violationsData:
            self.horizontalScrollBar.setMinimum(0)
            self.horizontalScrollBar.setMaximum((len(self.violationsData)-1))
            self.horizontalScrollBar.setValue(0)
        else:
            self.horizontalScrollBar.setMinimum(0)
            self.horizontalScrollBar.setMaximum(0)

        self.DisplayViolationsData()

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
                    filterText = "%s like '%%%s%%'" % (self.filterInfo[dd], text)
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
    def DisplayViolationsData(self):
        """ Display violations data """
        at = self.horizontalScrollBar.value()
        at += 1
        total = len(self.violationsData)

        if self.violationsData:
            """ Violation 'number' is one greater than scrollbar index which starts at 0 """
            self.groupBox_Violations.setTitle("Currently Selected Violation %d of %d" % (at,total))

            """ Populate the fields in the violations groupbox """
            self.v = self.violationsData[self.horizontalScrollBar.value()]
            self.textBrowser_Filename.setText(self.v.filename)
            self.textBrowser_Function.setText(self.v.function)
            self.textBrowser_Description.setText(self.v.description)
            self.textBrowser_Details.setText(self.v.details)
            self.textBrowser_Severity.setText(self.v.severity)
            self.textBrowser_Id.setText(self.v.violationId)
            self.textBrowser_DetectedBy.setText(self.v.detectedBy)

            """ Populate the fields in the Analysis groupbox """
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
    def GotoCode(self):
        viewerCommand = self.projFile.paths[PF.ePathViewer]
        # get the filename and line number for this violation
        if self.v:
            filename = self.v.filename
            filename = filename.replace('(W)', '').strip()
            fpfn = self.projFile.FullPathName( filename)
            if fpfn:
                if len(fpfn) == 1:
                    viewerCommand = viewerCommand.replace( '<fullPathFileName>', '"%s"' % fpfn[0])

                    linenumber = self.v.lineNumber
                    if linenumber >= 0:
                        viewerCommand = viewerCommand.replace( '<lineNumber>', str(linenumber))
                    else:
                        viewerCommand = viewerCommand.replace( '<lineNumber>', '')

                    subprocess.Popen( viewerCommand)
            else:
                msg = 'Ambiguous filename\n%s' % '\n'.join(fpfn)
                self.CrErrPopup( msg)
        else:
            msg = 'No matching violations.'
            self.CrErrPopup( msg)

    #-----------------------------------------------------------------------------------------------
    def GetAnalysisTextOptions(self):
        """ Return list of canned analysis text to display in the combobox for user selection """

        analysisTextList = ['Analysis Text Selection']
        analysisTextList.extend(self.projFile.analysisComments)

        return analysisTextList

    #-----------------------------------------------------------------------------------------------
    def SelectAnalysisText(self):
        """ Update the Analysis Text Browser with the user's choice from the combobox """
        analysisChoice = self.comboBoxAnalysisTextOptions.currentText()

        analysisChoice = analysisChoice.replace(r'\n', '\n')

        if analysisChoice != 'Analysis Text Selection':
            """ Append the canned comment to the analysis text rather than clear() it first.
                This would allow for the case where they want to enter other information first """
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
                if analysisText:
                    msg = 'We have auto-populated the analysis comment.\nDo you want to keep it?'
                    rtn = QMessageBox.question( self, 'Auto-Complete',
                                                msg, QMessageBox.Yes, QMessageBox.No)
                    if rtn != QMessageBox.Yes:
                        analysisText = ''
                        self.plainTextEdit_Analysis.clear()
                        reportBlank = False

            if analysisText:
                updateCmd = """UPDATE Violations
                                   SET status = ?, analysis = ?, who = ?, reviewDate = ?
                                 WHERE filename = ?
                                   AND function = ?
                                   AND severity = ?
                                   AND violationId = ?
                                   AND description = ?
                                   AND details = ?
                                   AND lineNumber = ? """

                self.db.Execute(updateCmd,
                                status,
                                analysisText,
                                self.userName,
                                datetime.datetime.now(),
                                self.v.filename,
                                self.v.function,
                                self.v.severity,
                                self.v.violationId,
                                self.v.description,
                                self.v.details,
                                self.v.lineNumber)

                self.db.Commit()

                # remember where we are to the next issue
                at = self.horizontalScrollBar.value()

                # refresh the data in our cache
                self.ApplyFilters()

                # now go there
                if self.dispositioned.isChecked():
                    self.horizontalScrollBar.setValue(at+1)
                else:
                    self.horizontalScrollBar.setValue(at)
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
    def GenerateReport(self):
        self.CrErrPopup('Not yet implemented...')


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

