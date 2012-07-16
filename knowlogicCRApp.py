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

        self.userName = ''

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
        self.tabWidget.currentChanged.connect(self.currentTabChanged)

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
        self.comboBox_Filename.setCurrentIndex(0)
        self.comboBox_Filename.addItems([self.fnameFilter['comboBoxTitle']])
        self.comboBox_Filename.addItems(self.GetFilenames())
        self.comboBox_Filename.currentIndexChanged.connect(self.FilenameComboBoxIndexChanged)

        self.comboBox_Function.setCurrentIndex(0)
        self.comboBox_Function.addItems([self.functionFilter['comboBoxTitle']])
        self.comboBox_Function.currentIndexChanged.connect(self.FunctionComboBoxIndexChanged)

        self.comboBox_Severity.setCurrentIndex(0)
        self.comboBox_Severity.addItems(self.GetSeverity())
        self.comboBox_Severity.currentIndexChanged.connect(self.SeverityComboBoxIndexChanged)

        self.comboBox_Id.setCurrentIndex(0)
        self.comboBox_Id.addItems(self.GetIds())
        self.comboBox_Id.currentIndexChanged.connect(self.IdComboBoxIndexChanged)

        self.comboBox_DetectedBy.setCurrentIndex(0)
        self.comboBox_DetectedBy.addItems(self.GetDetectedBy())
        self.comboBox_DetectedBy.currentIndexChanged.connect(self.DetectedByComboBoxIndexChanged)

        self.comboBox_Status.setCurrentIndex(0)
        self.comboBox_Status.addItems(self.GetStatus())
        self.comboBox_Status.currentIndexChanged.connect(self.StatusComboBoxIndexChanged)

        self.pushButton_ApplyFilters.clicked.connect(self.ApplyFilters)

        #------------------------------------------------------------------------------
        # Manage the violations horizontal slider scroll bar
        #------------------------------------------------------------------------------
        self.horizontalScrollBar.setMinimum(0)
        self.horizontalScrollBar.setMaximum(0)

        self.horizontalScrollBar.valueChanged.connect(self.ViolationsSliderChanged)

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
        if projFileName is None:
            projFileName = eDefaultProjectFileName

        if os.path.isfile( projFileName):
            self.pFullFilename = projFileName
            self.projFile = PF.ProjectFile( projFileName)

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

            # display the project file name
            self.textBrowser_ProjFile.setText(projFileName)

    #-----------------------------------------------------------------------------------------------
    def crErrPopup(self, errText):
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
    def currentTabChanged(self):
        """ If moving onto any tab other than config tab"""
        if self.tabWidget.currentIndex() != 0:
            """ Make sure they enter a username and project file before moving off config tab """
            if self.db == None or self.userName == '':
                self.crErrPopup('Please enter a valid Username and Project File.')
                self.tabWidget.setCurrentIndex(0)
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

    def RunAnalysis(self):
        # TODO: Call Analyze Here
        # TODO: this should be launched as a thread, this way the main giu can display the
        #       output of the analyzer for status
        """
        analyzer = Analyzer(self.pFullFilename)
        if analyzer.isValid:
            analyzer.Analyze(fullAnalysis)
        """
        self.crErrPopup('Not fully integrated. Run Analysis commandline and GUI works with KsCrDb.db in working directory.')
        self.DisplayViolationStatistics()


    def UpdateFunctionsComboBox(self):
        self.comboBox_Function.setCurrentIndex(0)
        self.comboBox_Function.clear()
        self.comboBox_Function.addItems([self.functionFilter['comboBoxTitle']])
        self.comboBox_Function.addItems(self.GetFunctions())
        self.FunctionComboBoxIndexChanged()


    def UpdateFileNameFilter(self):

        curSel = self.comboBox_Filename.currentText()
        if curSel == self.fnameFilter['comboBoxTitle']:
            self.fnameFilter['value'] = ''
        else:
            self.fnameFilter['value'] = """filename = '%s' """ % self.comboBox_Filename.currentText()

    def GetFilenames(self):
        """ GetFilenames returns list of filenames to display in the combobox for user selection"""
        sql = 'SELECT DISTINCT filename from Violations'
        q = Query(sql, self.db)
        #filenameList = [self.fnameFilter['comboBoxTitle']]
        filenameList = []
        for i in q:
            filenameList.append(str(i))

        self.UpdateFileNameFilter()

        """ If filename changed, update function combobox"""
        #self.UpdateFunctionsComboBox()

        return filenameList


    def UpdateFunctionsFilter(self):
        curSel = self.comboBox_Function.currentText()
        if (curSel == self.functionFilter['comboBoxTitle']) or (curSel == 'N/A'):
            self.functionFilter['value'] = ''
        else:
            self.functionFilter['value'] = """function = '%s' """ % self.comboBox_Function.currentText()


    def GetFunctions(self):
        """ GetFunctions returns list of functions to display in the combobox for user selection"""
        sql = ("""SELECT DISTINCT function
                   FROM Violations
                   WHERE filename =  '%s'""" % self.comboBox_Filename.currentText())
        q = Query(sql, self.db)
        #functionList = [self.functionFilter['comboBoxTitle']]
        functionList = []
        for i in q:
            functionList.append(str(i))

        self.UpdateFunctionsFilter()

        return functionList

    def UpdateSeverityFilter(self):

        curSel = self.comboBox_Severity.currentText()
        if curSel == self.severityFilter['comboBoxTitle']:
            self.severityFilter['value'] = ''
        else:
            self.severityFilter['value'] = """severity = '%s' """ % self.comboBox_Severity.currentText()

    def GetSeverity(self):
        """ GetSeverity returns list of severity choices to display in the combobox for user selection"""

        sql = 'SELECT DISTINCT severity from Violations'
        q = Query(sql, self.db)
        severityList = [self.severityFilter['comboBoxTitle']]
        for i in q:
            severityList.append(str(i))
        print('SeverityList:')
        print (severityList)

        #self.UpdateSeverityFilter()

        return severityList

    def UpdatevIdFilter(self):

        curSel = self.comboBox_Id.currentText()
        if curSel == self.vIdFilter['comboBoxTitle']:
            self.vIdFilter['value'] = ''
        else:
            if self.vIdCustom:
                """ Custom vIdFilter """
                filterStr = """violationId LIKE '"""+"%"+self.comboBox_Id.currentText()+"%"+"""'"""
                self.vIdFilter['value'] = filterStr
            else:
                self.vIdFilter['value'] = """violationId = '%s' """ % self.comboBox_Id.currentText()

    def GetIds(self):
        """ GetIds returns list of violationId choices to display in the combobox for user selection"""

        """ Initialize custom vidfilter to false """
        self.vIdCustom = 0

        sql = 'SELECT DISTINCT violationId from Violations'
        q = Query(sql, self.db)

        vIdList = [self.vIdFilter['comboBoxTitle'], 'Custom']
        for i in q:
            vIdList.append(str(i))

        print('vIdList:')
        print (vIdList)
        return vIdList

    def UpdatedetectedByFilter(self):

        curSel = self.comboBox_DetectedBy.currentText()
        if curSel == self.detByFilter['comboBoxTitle']:
            self.detByFilter['value'] = ''
        else:
            self.detByFilter['value'] = """detectedBy = '%s' """ % self.comboBox_DetectedBy.currentText()

    def GetDetectedBy(self):
        """ GetDetectedBy returns list of detectedBy choices to display in the combobox for user selection"""

        sql = 'SELECT DISTINCT detectedBy from Violations'
        q = Query(sql, self.db)

        detectedByList = [self.detByFilter['comboBoxTitle']]
        for i in q:
            detectedByList.append(str(i))

        print('detectedByList:')
        print (detectedByList)
        return detectedByList

    def UpdateStatusFilter(self):
        curSel = self.comboBox_Status.currentText()
        if curSel == self.statusFilter['comboBoxTitle']:
            self.statusFilter['value'] = ''
        else:
            self.statusFilter['value'] = """status = '%s' """ % self.comboBox_Status.currentText()

    def GetStatus(self):
        """ GetStatus returns list of status choices to display in the combobox for user selection"""
        statusList = []
        statusList = [self.statusFilter['comboBoxTitle'], 'Reviewed', 'Accepted', 'Not Reported']

        return statusList

    def FilenameComboBoxIndexChanged(self):
        """ Filename choice changed """
        """ Update filter """
        self.UpdateFileNameFilter()
        """ Update functions combobox """
        """ If filename changed, update function combobox"""
        self.UpdateFunctionsComboBox()

    def FunctionComboBoxIndexChanged(self):
        """ Function choice changed """
        """ Update filter """
        self.UpdateFunctionsFilter()

    def SeverityComboBoxIndexChanged(self):
        """ Severity choice changed """
        """ Update filter """
        self.UpdateSeverityFilter()

    def IdComboBoxIndexChanged(self):
        """ ViolationId choice changed """
        """ Update filter """
        if self.comboBox_Id.currentText() == 'Custom':
            self.vIdCustom = 1
            """ Add custom dialog here """
            dlg = self.DisplayCRAppCustomIdDialog()
            if dlg.exec_():
                customText = dlg.getValue()
                self.comboBox_Id.setItemText(self.comboBox_Id.currentIndex(), customText)
        self.UpdatevIdFilter()

    def DetectedByComboBoxIndexChanged(self):
        """ DetectedBy choice changed """
        """ Update filter """
        self.UpdatedetectedByFilter()

    def StatusComboBoxIndexChanged(self):
        """ Status choice changed """
        """ Update filter """
        self.UpdateStatusFilter()

    def BuildSqlStatement(self):
        sql = ("""SELECT filename,
                         function,
                         severity,
                         violationId,
                         description,
                         details,
                         lineNumber,
                         detectedBy,
                         firstReport,
                         lastReport,
                         status,
                         analysis,
                         who,
                         reviewDate
                    FROM Violations """)
        numFilters = 0
        for f in self.filterList:
            if f['value']:
                if numFilters == 0:
                    sql = sql + "WHERE "
                else:
                    sql = sql + "AND "
                sql = sql + f['value']
                numFilters = numFilters + 1

        sql += '\norder by filename, detectedBy, violationId, function, severity '

        print("Built sql statement:")
        print(sql)
        return(sql)


    def DisplayViolationsData(self):
        """ Display violations data """
        if self.violationsData:
            """ Violation 'number' is one greater than scrollbar index which starts at 0 """
            self.groupBox_Violations.setTitle("Currently Selected Violation %d of %d" % ((self.horizontalScrollBar.value()+1),len(self.violationsData)))

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
            self.groupBox_Violations.setTitle("Currently Selected Violation %d of %d" % (self.horizontalScrollBar.value(),len(self.violationsData)))
            self.textBrowser_Filename.clear()
            self.textBrowser_Function.clear()
            self.textBrowser_Description.clear()
            self.textBrowser_Details.clear()
            self.textBrowser_Severity.clear()
            self.textBrowser_Id.clear()
            self.textBrowser_DetectedBy.clear()
            self.v = None


    def ViolationsSliderChanged(self):
        """ Slider changed, so redisplay  violations data """
        self.DisplayViolationsData()

    def ApplyFilters(self):
        """ Display the violations information based on selected filters """

        """ Query the database using filters selected """
        sql = ''
        sql = self.BuildSqlStatement()

        self.violationsData = []
        self.violationsData = Query(sql, self.db)

        """ Display Violations Data """
        if self.violationsData:
            self.horizontalScrollBar.setMinimum(0)
            self.horizontalScrollBar.setMaximum((len(self.violationsData)-1))
        else:
            self.horizontalScrollBar.setMinimum(0)
            self.horizontalScrollBar.setMaximum(0)


        self.DisplayViolationsData()

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
                # TODO: alert user of ambiguous filename in project
                pass
        else:
            # TODO warn no violations match the filter criteria
            pass

    def SaveAnalysisData(self, status):
        """ Save analysis data entered and mark status as reviewed or accepted based status passed in """

        if self.v:
            analysisText = self.plainTextEdit_Analysis.toPlainText()

            updateCmd = ("""UPDATE Violations
                               SET status = '%s',
                                   analysis = '%s',
                                   who = '%s',
                                   reviewDate = '%s'
                             WHERE filename = '%s'
                               AND function = '%s'
                               AND severity = '%s'
                               AND violationId = '%s'
                               AND description = '%s'
                               AND details = '%s'
                               AND lineNumber = %d """ % (status,
                                                          analysisText,
                                                          self.userName,
                                                          datetime.datetime.now(),
                                                          self.v.filename,
                                                          self.v.function,
                                                          self.v.severity,
                                                          self.v.violationId,
                                                          self.v.description,
                                                          self.v.details,
                                                          self.v.lineNumber))
            print('updateCmd:')
            print(updateCmd)
            self.db.Execute(updateCmd)

            self.db.Commit()

            """ Need to get new Query object now that the database has been changed """
            sql = ''
            sql = self.BuildSqlStatement()

            self.violationsData = []
            self.violationsData = Query(sql, self.db)

            """ Redisplay violations data. """
            self.DisplayViolationsData()


    def MarkReviewed(self):
        """ Save analysis data entered and Mark violation as reviewed """
        self.SaveAnalysisData('Reviewed')
    def MarkAccepted(self):
        """ Save analysis data entered and Mark violation as accepted """
        self.SaveAnalysisData('Accepted')

    def DisplaySrcFileBrowser(self):

        # Display a file browser for the user to select the project file database directory

        srcFile = str(QFileDialog.getExistingDirectory(self, "Select Source Code Directory"))

        self.textBrowser_ReportFile.setText(srcFile)

    def DisplayReportFileBrowser(self):

        # Display a file browser for the user to select the reports file directory

        reportFile = str(QFileDialog.getExistingDirectory(self, "Select Reports Directory"))

        self.textBrowser_ReportDir.setText(reportFile)


    def GenerateReport(self):
        self.crErrPopup('Not yet implemented...')


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

