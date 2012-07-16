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
#from Analyze import Analyzer
from crappcustomiddialog import Ui_CRAppCustomIdDialog
from crmainwindow import Ui_MainWindow

from utils import util
from utils.DB.database import Query, GetAll, GetCursor
from utils.DB.sqlLite.database import DB_SQLite

from ViolationDb import eDbName, eDbRoot

import ProjFile as PF

#---------------------------------------------------------------------------------------------------
# Data
#---------------------------------------------------------------------------------------------------
eDefaultProjectFileName = r'C:\Knowlogic\tools\CR-Projs\zzzCodereviewPROJ\G4.crp'

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

        self.ResetProject()

        self.fnameFilter    =  dict(name = 'fName', value = '', comboBoxTitle = 'Select Filename')
        self.functionFilter =  dict(name = 'function', value = '', comboBoxTitle = 'Select Function')
        self.severityFilter =  dict(name = 'severityFilter', value = '', comboBoxTitle = 'Select Severity')
        self.vIdFilter      =  dict(name = 'vIdFilter', value = '', comboBoxTitle = 'Select Violation Id')
        self.detByFilter    =  dict(name = 'detByFilter', value = '', comboBoxTitle = 'Select Detected By')
        self.statusFilter   =  dict(name = 'statusFilter', value = '', comboBoxTitle = 'Select Status')

        """ Keep list of filters to iterate for building sql statement """
        self.filterList = [self.fnameFilter,
                           self.functionFilter,
                           self.severityFilter,
                           self.vIdFilter,
                           self.detByFilter,
                           self.statusFilter]

        #------------------------------------------------------------------------------
        # Handle Tabs of TabWidget
        #------------------------------------------------------------------------------
        self.tabWidget.currentChanged.connect(self.CurrentTabChanged)

        #------------------------------------------------------------------------------
        # Handle Config Tab Data
        #------------------------------------------------------------------------------
        self.lineEdit_userName.editingFinished.connect(self.lineEditUserNameChanged)
        self.pushButton_pFileBrowse.clicked.connect(self.DisplaypFileBrowser)
        self.pushButton_RunAnalysis.clicked.connect(self.RunAnalysis)
        self.pushButton_Statistics.clicked.connect(self.DisplayViolationStatistics)

        #------------------------------------------------------------------------------
        # Set up the filter comboboxes and the Apply Filter pushbutton
        #------------------------------------------------------------------------------
        # the a is the index that is selected => if 0 we know they cleared this filter
        self.comboBox_Filename.currentIndexChanged.connect(lambda a,x='Filename', fx=self.FillFilters: fx(a,x))
        self.comboBox_Function.currentIndexChanged.connect(lambda a,x='Function', fx=self.FillFilters: fx(a,x))
        self.comboBox_Severity.currentIndexChanged.connect(lambda a,x='Severity', fx=self.FillFilters: fx(a,x))
        self.comboBox_Id.currentIndexChanged.connect(lambda a,x='Id', fx=self.FillFilters: fx(a,x))
        self.comboBox_DetectedBy.currentIndexChanged.connect(lambda a,x='DetectedBy', fx=self.FillFilters: fx(a,x))
        self.comboBox_Status.currentIndexChanged.connect(lambda a,x='Status', fx=self.FillFilters: fx(a,x))
        self.pushButton_ApplyFilters.clicked.connect(self.ApplyFilters)

        #------------------------------------------------------------------------------
        # Manage the violations horizontal slider scroll bar
        #------------------------------------------------------------------------------
        self.horizontalScrollBar.setMinimum(0)
        self.horizontalScrollBar.setMaximum(0)
        self.horizontalScrollBar.valueChanged.connect(self.DisplayViolationsData)
        self.pushButton_GotoCode.clicked.connect(self.GotoCode)

        #------------------------------------------------------------------------------
        # Manage the analysis push buttons
        #------------------------------------------------------------------------------
        self.pushButton_MarkReviewed.clicked.connect(self.MarkReviewed)
        self.pushButton_MarkAccepted.clicked.connect(self.MarkAccepted)

        #------------------------------------------------------------------------------
        # Handle GenerateReport Tab Data
        #------------------------------------------------------------------------------
        self.pushButton_BrowseSrcCode.clicked.connect(self.DisplaySrcFileBrowser)
        self.pushButton_BrowseReport.clicked.connect(self.DisplayReportFileBrowser)
        self.pushButton_GenerateReport.clicked.connect(self.GenerateReport)

    #-----------------------------------------------------------------------------------------------
    def ResetProject( self, projFileName = None):
        """ A new project file has been selected - reset all the info in the display
        """
        self.filterUpdateInProgress = False
        self.currentFilters = []

        if projFileName is None:
            projFileName = eDefaultProjectFileName

        if os.path.isfile( projFileName):
            self.pFullFilename = projFileName
            self.projFile = PF.ProjectFile( projFileName)

            if self.projFile.isValid:
                self.dbFname = eDbName
                self.dbFullFilename = os.path.join( self.projFile.paths[PF.ePathProject],
                                                    eDbRoot, eDbName)

                #------------------------------------------------------------------------------
                # Establish a DataBase connection
                #------------------------------------------------------------------------------
                self.db = DB_SQLite()
                self.db.Connect(self.dbFullFilename)

                self.violationsData = []
                self.v = None

                self.FillFilters( 0, '', True)
                self.DisplayViolationStatistics()

                # display the project file name
                self.textBrowser_ProjFile.setText(projFileName)
            else:
                msg = '\n'.join( self.projFile.errors)
                self.CrErrPopup( msg)

    #-----------------------------------------------------------------------------------------------
    def CrErrPopup(self, errText):
        """ The crErrPopup provides a popup dialog to be used for simple
            notifications to the user through the GUI """
        msgBox = QMessageBox()
        msgBox.setWindowTitle("Knowlogic Code Review Application Message")
        msgBox.setText(errText)
        msgBox.exec_()

    #-----------------------------------------------------------------------------------------------
    def DisplayCRAppCustomIdDialog(self):
        dlg = CRAppCustomIdDialog()
        dlg.setWindowTitle("Knowlogic Custom Filter")
        return(dlg)

    #-----------------------------------------------------------------------------------------------
    def CurrentTabChanged(self):
        """ When moving onto any tab check conditions and perform actions
        """
        # Make sure we have a username and project file before moving off config tab
        if self.tabWidget.currentIndex() != 0:
            if self.db == None or self.userName == '':
                self.tabWidget.setCurrentIndex(0)
                self.CrErrPopup('Please enter a valid Username and Project File.')

        # Coming back to the Config tab update the Stats as they may have analyzed something
        elif self.tabWidget.currentIndex() == 0 and self.curTab != 0:
            self.DisplayViolationStatistics()

        self.curTab = self.tabWidget.currentIndex()

    #-----------------------------------------------------------------------------------------------
    def lineEditUserNameChanged(self):
        self.userName = self.lineEdit_userName.text()

    #-----------------------------------------------------------------------------------------------
    def DisplaypFileBrowser(self):

        # Display a file browser for the user to select the project file database directory

        pFile, selFilter = QFileDialog.getOpenFileName(self, "Select Project File")
        if pFile:
            self.ResetProject( pFile)

    #-----------------------------------------------------------------------------------------------
    def DisplayViolationStatistics(self):

        sqlTotal = 'SELECT status from Violations'
        q = Query(sqlTotal, self.db)

        total = 0
        numAccepted = 0
        numReviewed = 0
        for i in q:
            if i.status == 'Accepted':
                numAccepted = numAccepted + 1
            if i.status == 'Reviewed':
                numReviewed = numReviewed + 1
            total = total +1

        self.textBrowser_Total.setText(str(total))
        self.textBrowser_Accepted.setText(str(numAccepted))
        self.textBrowser_Reviewed.setText(str(numReviewed))

    #-----------------------------------------------------------------------------------------------
    def RunAnalysis(self):
        # TODO: Call Analyze Here
        # TODO: this should be launched as a thread, this way the main giu can display the
        #       output of the analyzer for status
        """
        analyzer = Analyzer(self.pFullFilename)
        if analyzer.isValid:
            analyzer.Analyze(fullAnalysis)
        """
        msg = 'Not fully integrated. Run Analysis commandline and GUI works with KsCrDb.db in working directory.'
        self.crErrPopup(msg)
        self.DisplayViolationStatistics()

    #-----------------------------------------------------------------------------------------------
    def FillFilters( self, index, name='', reset=False):
        """ This function fills in all of the filter selection dropdowns based on the
            settings in the other filter dropdowns.

            filterUpdateInProgress - stop re-entrant calls when we update the filter lists items
                                     as it appears the selection changed
        """
        if not self.filterUpdateInProgress:
            self.filterUpdateInProgress = True

            noFilterRe = re.compile('Select <[A-Za-z]+> \[[0-9]+\]')

            # don't refill the one that changed
            if name:
                if name not in self.currentFilters:
                    self.currentFilters.append(name)
                if index <= 0:
                    self.currentFilters.remove( name)

            whereClause = ''
            if not reset:
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
        constraints = []

        # get the value of all filter and make a constraint on all the queries
        for dd in self.filterInfo:
            gui = getattr( self, 'comboBox_%s' % dd)
            text = gui.currentText()
            filterOff = noFilterRe.search( text)
            if filterOff is None and text:
                # ok we have something to filter on
                filterText = "%s like '%%%s%%'" % (self.filterInfo[dd], text)
                constraints.append( filterText)

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
            self.textBrowser_PrevReviewer.setText(self.v.who)
            self.textBrowser_PrevDate.setText(self.v.reviewDate)
            self.textBrowser_PrevStatus.setText(self.v.status)

            self.plainTextEdit_Analysis.setPlainText(self.v.analysis)
            self.textBrowser_Reviewer.setText(self.userName)
            self.textBrowser_Date.setText(str(datetime.datetime.now()))

        else:
            self.groupBox_Violations.setTitle("Currently Selected Violation %d of %d" % (at,total))
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
                    viewerCommand = viewerCommand.replace( '<fullPathFileName>', fpfn[0])

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
    def SaveAnalysisData(self, status):
        """ Save analysis data entered and mark status as reviewed or accepted based status passed in """
        if self.v:
            analysisText = self.plainTextEdit_Analysis.toPlainText()

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
            self.horizontalScrollBar.setValue(at + 1)

    #-----------------------------------------------------------------------------------------------
    def MarkReviewed(self):
        """ Save analysis data entered and Mark violation as reviewed """
        self.SaveAnalysisData('Reviewed')

    #-----------------------------------------------------------------------------------------------
    def MarkAccepted(self):
        """ Save analysis data entered and Mark violation as accepted """
        self.SaveAnalysisData('Accepted')

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

