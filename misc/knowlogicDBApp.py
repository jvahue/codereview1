#--------------------------------------------------------------------------
# Knowlogic TestResults Database Application
#
# This file contains the main UI functions for the Test Results application.
# The main UI is displayed.  Signals emitted by the UI Objects are connected
# with slot functions which are defined here.
#
#--------------------------------------------------------------------------

#--------------------------------------------------------------------------
# Python imports
#--------------------------------------------------------------------------
import sys

#--------------------------------------------------------------------------
# Third Party imports
#--------------------------------------------------------------------------
from PySide.QtGui import QApplication, QFileDialog, QMainWindow, QTableWidgetItem, QTextEdit, QPushButton, QMessageBox
                                
#--------------------------------------------------------------------------
# Knowlogic Module imports
#--------------------------------------------------------------------------
from dbAppMainGui import Ui_MainWindow
from dbAppDataManager import dataManager

#--------------------------------------------------------------------------
# Class MainWindow
#
# The class MainWindow inherits from Ui_MainWindow which is imported from
# dbAppMainGui. The Ui_MainWindow and all of it's related UI objects were
# designed with QT Designer and their code was then generated. Functionality
# of those objects is provided here by defining slots/functions for those UI
# objects.
#
# The MainWindow consists of a QTabWidget which contains the following tabs:
#    View Database
#    Merge Data
#    Data Analysis
#    Code Coverage
#    Database Administration
# 
# NOTE: The Ui_MainWindow code in the dbAppMainGui should not be altered.  
# If changes to the UI are required, it should be done with QT Designer and 
# then regenerated.
#
#--------------------------------------------------------------------------
class MainWindow(QMainWindow, Ui_MainWindow):
    #---------------------------------------------------------------------------
    #
    # MainWindow __init__
    # 
    # Sets the window title and some default file locations.
    # Builds the database if it doesn't already exist.
    # Creates a dataManager object (module imported above) to handle the data 
    # management. 
    # Connects signals from the UI objects to slots which are defined here.
    # 
    #---------------------------------------------------------------------------
   
    def __init__(self, parent=None):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("PySTE Results DB Application")
 
        self.dm = dataManager()
        self.textBrowser_dbLocation.setText(self.dm.testResultsDir)
             
        self.pushButton_ViewTestResults.clicked.connect(self.displayTestResultsTable)
        self.pushButton_dbFileBrowse.clicked.connect(self.displayDBFileBrowser)
   
   
    #---------------------------------------------------------------------------
    # Slot displayDBFileBrowser
    # This function is triggered by self.pushButton_dbFileBrowse.clicked.connect
    # It displays a QTextBrowser file browser for the user to select the 
    # database directory.
    #---------------------------------------------------------------------------
    
    def displayDBFileBrowser(self):
        
        # Display a file browser for the user to select the database directory
        
        dbFile = str(QFileDialog.getExistingDirectory(self, "Select DB Directory"))
        if (not dbFile):
            dbFile = self.defaultDBLocation
   
        self.textBrowser_dbLocation.setText(dbFile)
        
        # Set the datamanager object dbFile based on the user's browse choice
        self.dm.db_filename = dbFile

    #---------------------------------------------------------------------------
    # Slot displayTestResultsTable
    # This function is triggered by self.pushButton_ViewTestResults.clicked.connect
    # It displays a QTableWidget table populated with data from the testResults
    # database.
    #---------------------------------------------------------------------------
           
    def displayTestResultsTable(self):
        
        # Extract testResults from the database
        
        self.dm.dmExtractTestResults()
        
        # Display the testResults in the UI test results table
        
        self.tableWidget_testResults.setRowCount(len(self.dm.testResultData))
        self.tableWidget_testResults.setColumnCount(len(self.dm.testResultData[0]))
        for i, row in enumerate(self.dm.testResultData):
            #print '*****', i, row
            for j, col in enumerate(row):
                item = QTableWidgetItem(str(col))
                #print i,j, col
                self.tableWidget_testResults.setItem(i, j, item)     
  
#-------------------------------------------------------------------------
# Main Program
#
# Instantiates the QApplication and Displays the Main Window.
#-------------------------------------------------------------------------
def main():
    # Create Qt Application
    app = QApplication(sys.argv)
    frame = MainWindow()
    
    # Launch the Main Window
    frame.show()
    app.exec_()
           
if __name__=='__main__':
    main()
