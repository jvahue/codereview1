# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\PWES\FASTTesting\CodeReview1\crmainwindow.ui'
#
# Created: Wed Jul 18 19:53:05 2012
#      by: pyside-uic 0.2.14 running on PySide 1.1.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(855, 772)
        self.centralWidget = QtGui.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.verticalLayout_13 = QtGui.QVBoxLayout(self.centralWidget)
        self.verticalLayout_13.setObjectName("verticalLayout_13")
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(self.centralWidget)
        font = QtGui.QFont()
        font.setFamily("Cambria")
        font.setPointSize(16)
        font.setWeight(75)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.label_2 = QtGui.QLabel(self.centralWidget)
        font = QtGui.QFont()
        font.setFamily("Cambria")
        font.setPointSize(12)
        font.setItalic(True)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.tabWidget = QtGui.QTabWidget(self.centralWidget)
        self.tabWidget.setObjectName("tabWidget")
        self.tab_Config = QtGui.QWidget()
        self.tab_Config.setMinimumSize(QtCore.QSize(829, 440))
        self.tab_Config.setObjectName("tab_Config")
        self.verticalLayout_9 = QtGui.QVBoxLayout(self.tab_Config)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.groupBox_2 = QtGui.QGroupBox(self.tab_Config)
        self.groupBox_2.setMinimumSize(QtCore.QSize(621, 211))
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_6 = QtGui.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.horizontalLayout_4 = QtGui.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.label_7 = QtGui.QLabel(self.groupBox_2)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_4.addWidget(self.label_7)
        self.lineEdit_userName = QtGui.QLineEdit(self.groupBox_2)
        self.lineEdit_userName.setMaximumSize(QtCore.QSize(133, 20))
        self.lineEdit_userName.setObjectName("lineEdit_userName")
        self.horizontalLayout_4.addWidget(self.lineEdit_userName)
        spacerItem = QtGui.QSpacerItem(388, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem)
        self.verticalLayout_6.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_5 = QtGui.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.label_5 = QtGui.QLabel(self.groupBox_2)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_5.addWidget(self.label_5)
        self.projectFileNameEditor = QtGui.QLineEdit(self.groupBox_2)
        self.projectFileNameEditor.setObjectName("projectFileNameEditor")
        self.horizontalLayout_5.addWidget(self.projectFileNameEditor)
        self.pushButton_pFileBrowse = QtGui.QPushButton(self.groupBox_2)
        self.pushButton_pFileBrowse.setObjectName("pushButton_pFileBrowse")
        self.horizontalLayout_5.addWidget(self.pushButton_pFileBrowse)
        self.verticalLayout_6.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_6 = QtGui.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.toolOutput = QtGui.QTextEdit(self.groupBox_2)
        self.toolOutput.setReadOnly(True)
        self.toolOutput.setObjectName("toolOutput")
        self.horizontalLayout_6.addWidget(self.toolOutput)
        self.verticalLayout_5 = QtGui.QVBoxLayout()
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        spacerItem1 = QtGui.QSpacerItem(20, 58, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_5.addItem(spacerItem1)
        self.verticalLayout_4 = QtGui.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.pushButton_RunAnalysis = QtGui.QPushButton(self.groupBox_2)
        self.pushButton_RunAnalysis.setMaximumSize(QtCore.QSize(81, 31))
        self.pushButton_RunAnalysis.setObjectName("pushButton_RunAnalysis")
        self.verticalLayout_4.addWidget(self.pushButton_RunAnalysis)
        self.pushButtonAbortAnalysis = QtGui.QPushButton(self.groupBox_2)
        self.pushButtonAbortAnalysis.setMaximumSize(QtCore.QSize(81, 31))
        self.pushButtonAbortAnalysis.setObjectName("pushButtonAbortAnalysis")
        self.verticalLayout_4.addWidget(self.pushButtonAbortAnalysis)
        self.verticalLayout_5.addLayout(self.verticalLayout_4)
        spacerItem2 = QtGui.QSpacerItem(20, 48, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_5.addItem(spacerItem2)
        self.horizontalLayout_6.addLayout(self.verticalLayout_5)
        self.verticalLayout_6.addLayout(self.horizontalLayout_6)
        self.verticalLayout_9.addWidget(self.groupBox_2)
        self.groupBox = QtGui.QGroupBox(self.tab_Config)
        self.groupBox.setMinimumSize(QtCore.QSize(621, 171))
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_15 = QtGui.QVBoxLayout(self.groupBox)
        self.verticalLayout_15.setObjectName("verticalLayout_15")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label_9 = QtGui.QLabel(self.groupBox)
        self.label_9.setObjectName("label_9")
        self.gridLayout.addWidget(self.label_9, 0, 0, 1, 1)
        self.label_10 = QtGui.QLabel(self.groupBox)
        self.label_10.setObjectName("label_10")
        self.gridLayout.addWidget(self.label_10, 4, 0, 1, 1)
        self.label_11 = QtGui.QLabel(self.groupBox)
        self.label_11.setObjectName("label_11")
        self.gridLayout.addWidget(self.label_11, 2, 0, 1, 1)
        self.reviewedViolations = QtGui.QLineEdit(self.groupBox)
        self.reviewedViolations.setReadOnly(True)
        self.reviewedViolations.setObjectName("reviewedViolations")
        self.gridLayout.addWidget(self.reviewedViolations, 2, 1, 1, 1)
        self.totalViolations = QtGui.QLineEdit(self.groupBox)
        self.totalViolations.setReadOnly(True)
        self.totalViolations.setObjectName("totalViolations")
        self.gridLayout.addWidget(self.totalViolations, 0, 1, 1, 1)
        self.label_8 = QtGui.QLabel(self.groupBox)
        self.label_8.setObjectName("label_8")
        self.gridLayout.addWidget(self.label_8, 3, 0, 1, 1)
        self.acceptedViolations = QtGui.QLineEdit(self.groupBox)
        self.acceptedViolations.setReadOnly(True)
        self.acceptedViolations.setObjectName("acceptedViolations")
        self.gridLayout.addWidget(self.acceptedViolations, 3, 1, 1, 1)
        self.removedViolations = QtGui.QLineEdit(self.groupBox)
        self.removedViolations.setReadOnly(True)
        self.removedViolations.setObjectName("removedViolations")
        self.gridLayout.addWidget(self.removedViolations, 4, 1, 1, 1)
        self.label_4 = QtGui.QLabel(self.groupBox)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 0, 2, 1, 1)
        self.ksTotal = QtGui.QLineEdit(self.groupBox)
        self.ksTotal.setReadOnly(True)
        self.ksTotal.setObjectName("ksTotal")
        self.gridLayout.addWidget(self.ksTotal, 0, 3, 1, 1)
        self.Reviewed = QtGui.QLabel(self.groupBox)
        self.Reviewed.setObjectName("Reviewed")
        self.gridLayout.addWidget(self.Reviewed, 2, 2, 1, 1)
        self.label_13 = QtGui.QLabel(self.groupBox)
        self.label_13.setObjectName("label_13")
        self.gridLayout.addWidget(self.label_13, 3, 2, 1, 1)
        self.label_14 = QtGui.QLabel(self.groupBox)
        self.label_14.setObjectName("label_14")
        self.gridLayout.addWidget(self.label_14, 4, 2, 1, 1)
        self.label_12 = QtGui.QLabel(self.groupBox)
        self.label_12.setObjectName("label_12")
        self.gridLayout.addWidget(self.label_12, 0, 4, 1, 1)
        self.ksReviewed = QtGui.QLineEdit(self.groupBox)
        self.ksReviewed.setReadOnly(True)
        self.ksReviewed.setObjectName("ksReviewed")
        self.gridLayout.addWidget(self.ksReviewed, 2, 3, 1, 1)
        self.ksAccepted = QtGui.QLineEdit(self.groupBox)
        self.ksAccepted.setReadOnly(True)
        self.ksAccepted.setObjectName("ksAccepted")
        self.gridLayout.addWidget(self.ksAccepted, 3, 3, 1, 1)
        self.ksRemoved = QtGui.QLineEdit(self.groupBox)
        self.ksRemoved.setReadOnly(True)
        self.ksRemoved.setObjectName("ksRemoved")
        self.gridLayout.addWidget(self.ksRemoved, 4, 3, 1, 1)
        self.pcReviewed = QtGui.QLineEdit(self.groupBox)
        self.pcReviewed.setReadOnly(True)
        self.pcReviewed.setObjectName("pcReviewed")
        self.gridLayout.addWidget(self.pcReviewed, 2, 5, 1, 1)
        self.label_15 = QtGui.QLabel(self.groupBox)
        self.label_15.setObjectName("label_15")
        self.gridLayout.addWidget(self.label_15, 2, 4, 1, 1)
        self.label_16 = QtGui.QLabel(self.groupBox)
        self.label_16.setObjectName("label_16")
        self.gridLayout.addWidget(self.label_16, 3, 4, 1, 1)
        self.label_17 = QtGui.QLabel(self.groupBox)
        self.label_17.setObjectName("label_17")
        self.gridLayout.addWidget(self.label_17, 4, 4, 1, 1)
        self.pcTotal = QtGui.QLineEdit(self.groupBox)
        self.pcTotal.setReadOnly(True)
        self.pcTotal.setObjectName("pcTotal")
        self.gridLayout.addWidget(self.pcTotal, 0, 5, 1, 1)
        self.pcAccepted = QtGui.QLineEdit(self.groupBox)
        self.pcAccepted.setReadOnly(True)
        self.pcAccepted.setObjectName("pcAccepted")
        self.gridLayout.addWidget(self.pcAccepted, 3, 5, 1, 1)
        self.pcRemoved = QtGui.QLineEdit(self.groupBox)
        self.pcRemoved.setReadOnly(True)
        self.pcRemoved.setObjectName("pcRemoved")
        self.gridLayout.addWidget(self.pcRemoved, 4, 5, 1, 1)
        self.verticalLayout_15.addLayout(self.gridLayout)
        self.verticalLayout_9.addWidget(self.groupBox)
        self.tabWidget.addTab(self.tab_Config, "")
        self.tab_Analysis = QtGui.QWidget()
        self.tab_Analysis.setObjectName("tab_Analysis")
        self.verticalLayout_10 = QtGui.QVBoxLayout(self.tab_Analysis)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.groupBox_Filters = QtGui.QGroupBox(self.tab_Analysis)
        self.groupBox_Filters.setMinimumSize(QtCore.QSize(809, 91))
        self.groupBox_Filters.setObjectName("groupBox_Filters")
        self.verticalLayout_23 = QtGui.QVBoxLayout(self.groupBox_Filters)
        self.verticalLayout_23.setObjectName("verticalLayout_23")
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.comboBox_Filename = QtGui.QComboBox(self.groupBox_Filters)
        self.comboBox_Filename.setObjectName("comboBox_Filename")
        self.horizontalLayout.addWidget(self.comboBox_Filename)
        self.comboBox_Function = QtGui.QComboBox(self.groupBox_Filters)
        self.comboBox_Function.setObjectName("comboBox_Function")
        self.horizontalLayout.addWidget(self.comboBox_Function)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.comboBox_Severity = QtGui.QComboBox(self.groupBox_Filters)
        self.comboBox_Severity.setObjectName("comboBox_Severity")
        self.horizontalLayout_2.addWidget(self.comboBox_Severity)
        self.comboBox_Id = QtGui.QComboBox(self.groupBox_Filters)
        self.comboBox_Id.setObjectName("comboBox_Id")
        self.horizontalLayout_2.addWidget(self.comboBox_Id)
        self.comboBox_DetectedBy = QtGui.QComboBox(self.groupBox_Filters)
        self.comboBox_DetectedBy.setObjectName("comboBox_DetectedBy")
        self.horizontalLayout_2.addWidget(self.comboBox_DetectedBy)
        self.comboBox_Status = QtGui.QComboBox(self.groupBox_Filters)
        self.comboBox_Status.setObjectName("comboBox_Status")
        self.horizontalLayout_2.addWidget(self.comboBox_Status)
        self.dispositioned = QtGui.QCheckBox(self.groupBox_Filters)
        self.dispositioned.setObjectName("dispositioned")
        self.horizontalLayout_2.addWidget(self.dispositioned)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3.addLayout(self.verticalLayout_2)
        self.pushButton_ApplyFilters = QtGui.QPushButton(self.groupBox_Filters)
        self.pushButton_ApplyFilters.setMaximumSize(QtCore.QSize(75, 23))
        self.pushButton_ApplyFilters.setObjectName("pushButton_ApplyFilters")
        self.horizontalLayout_3.addWidget(self.pushButton_ApplyFilters)
        self.verticalLayout_23.addLayout(self.horizontalLayout_3)
        self.verticalLayout_10.addWidget(self.groupBox_Filters)
        self.groupBox_Violations = QtGui.QGroupBox(self.tab_Analysis)
        self.groupBox_Violations.setMinimumSize(QtCore.QSize(809, 150))
        self.groupBox_Violations.setObjectName("groupBox_Violations")
        self.horizontalLayout_22 = QtGui.QHBoxLayout(self.groupBox_Violations)
        self.horizontalLayout_22.setObjectName("horizontalLayout_22")
        self.verticalLayout_8 = QtGui.QVBoxLayout()
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.horizontalLayout_10 = QtGui.QHBoxLayout()
        self.horizontalLayout_10.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.label_Filename = QtGui.QLabel(self.groupBox_Violations)
        self.label_Filename.setObjectName("label_Filename")
        self.horizontalLayout_10.addWidget(self.label_Filename)
        self.textBrowser_Filename = QtGui.QLineEdit(self.groupBox_Violations)
        self.textBrowser_Filename.setReadOnly(True)
        self.textBrowser_Filename.setObjectName("textBrowser_Filename")
        self.horizontalLayout_10.addWidget(self.textBrowser_Filename)
        self.label_Function = QtGui.QLabel(self.groupBox_Violations)
        self.label_Function.setObjectName("label_Function")
        self.horizontalLayout_10.addWidget(self.label_Function)
        self.textBrowser_Function = QtGui.QLineEdit(self.groupBox_Violations)
        self.textBrowser_Function.setReadOnly(True)
        self.textBrowser_Function.setObjectName("textBrowser_Function")
        self.horizontalLayout_10.addWidget(self.textBrowser_Function)
        self.verticalLayout_8.addLayout(self.horizontalLayout_10)
        self.horizontalLayout_11 = QtGui.QHBoxLayout()
        self.horizontalLayout_11.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.label_6 = QtGui.QLabel(self.groupBox_Violations)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_11.addWidget(self.label_6)
        self.textBrowser_Severity = QtGui.QLineEdit(self.groupBox_Violations)
        self.textBrowser_Severity.setReadOnly(True)
        self.textBrowser_Severity.setObjectName("textBrowser_Severity")
        self.horizontalLayout_11.addWidget(self.textBrowser_Severity)
        self.label_Id = QtGui.QLabel(self.groupBox_Violations)
        self.label_Id.setObjectName("label_Id")
        self.horizontalLayout_11.addWidget(self.label_Id)
        self.textBrowser_Id = QtGui.QLineEdit(self.groupBox_Violations)
        self.textBrowser_Id.setReadOnly(True)
        self.textBrowser_Id.setObjectName("textBrowser_Id")
        self.horizontalLayout_11.addWidget(self.textBrowser_Id)
        self.label_DetectedBy = QtGui.QLabel(self.groupBox_Violations)
        self.label_DetectedBy.setObjectName("label_DetectedBy")
        self.horizontalLayout_11.addWidget(self.label_DetectedBy)
        self.textBrowser_DetectedBy = QtGui.QLineEdit(self.groupBox_Violations)
        self.textBrowser_DetectedBy.setReadOnly(True)
        self.textBrowser_DetectedBy.setObjectName("textBrowser_DetectedBy")
        self.horizontalLayout_11.addWidget(self.textBrowser_DetectedBy)
        self.verticalLayout_8.addLayout(self.horizontalLayout_11)
        self.verticalLayout_7 = QtGui.QVBoxLayout()
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.textBrowser_Description = QtGui.QTextEdit(self.groupBox_Violations)
        self.textBrowser_Description.setReadOnly(True)
        self.textBrowser_Description.setObjectName("textBrowser_Description")
        self.verticalLayout_7.addWidget(self.textBrowser_Description)
        self.textBrowser_Details = QtGui.QTextEdit(self.groupBox_Violations)
        self.textBrowser_Details.setReadOnly(True)
        self.textBrowser_Details.setObjectName("textBrowser_Details")
        self.verticalLayout_7.addWidget(self.textBrowser_Details)
        self.verticalLayout_8.addLayout(self.verticalLayout_7)
        self.horizontalLayout_13 = QtGui.QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.horizontalScrollBar = QtGui.QScrollBar(self.groupBox_Violations)
        self.horizontalScrollBar.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalScrollBar.setObjectName("horizontalScrollBar")
        self.horizontalLayout_13.addWidget(self.horizontalScrollBar)
        self.pushButton_GotoCode = QtGui.QPushButton(self.groupBox_Violations)
        self.pushButton_GotoCode.setMaximumSize(QtCore.QSize(75, 23))
        self.pushButton_GotoCode.setObjectName("pushButton_GotoCode")
        self.horizontalLayout_13.addWidget(self.pushButton_GotoCode)
        self.verticalLayout_8.addLayout(self.horizontalLayout_13)
        self.horizontalLayout_22.addLayout(self.verticalLayout_8)
        self.verticalLayout_10.addWidget(self.groupBox_Violations)
        self.groupBox_Analysis = QtGui.QGroupBox(self.tab_Analysis)
        self.groupBox_Analysis.setMinimumSize(QtCore.QSize(811, 129))
        self.groupBox_Analysis.setObjectName("groupBox_Analysis")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.groupBox_Analysis)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_9 = QtGui.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.comboBoxAnalysisTextOptions = QtGui.QComboBox(self.groupBox_Analysis)
        self.comboBoxAnalysisTextOptions.setObjectName("comboBoxAnalysisTextOptions")
        self.horizontalLayout_9.addWidget(self.comboBoxAnalysisTextOptions)
        self.pushButtonAddCanned = QtGui.QPushButton(self.groupBox_Analysis)
        self.pushButtonAddCanned.setMaximumSize(QtCore.QSize(75, 23))
        self.pushButtonAddCanned.setObjectName("pushButtonAddCanned")
        self.horizontalLayout_9.addWidget(self.pushButtonAddCanned)
        self.verticalLayout_3.addLayout(self.horizontalLayout_9)
        self.plainTextEdit_Analysis = QtGui.QTextEdit(self.groupBox_Analysis)
        self.plainTextEdit_Analysis.setObjectName("plainTextEdit_Analysis")
        self.verticalLayout_3.addWidget(self.plainTextEdit_Analysis)
        self.horizontalLayout_16 = QtGui.QHBoxLayout()
        self.horizontalLayout_16.setContentsMargins(-1, 0, -1, -1)
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        self.label_3 = QtGui.QLabel(self.groupBox_Analysis)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_16.addWidget(self.label_3)
        self.textBrowser_PrevReviewer = QtGui.QLineEdit(self.groupBox_Analysis)
        self.textBrowser_PrevReviewer.setMinimumSize(QtCore.QSize(30, 0))
        self.textBrowser_PrevReviewer.setReadOnly(True)
        self.textBrowser_PrevReviewer.setObjectName("textBrowser_PrevReviewer")
        self.horizontalLayout_16.addWidget(self.textBrowser_PrevReviewer)
        self.label_PrevDate = QtGui.QLabel(self.groupBox_Analysis)
        self.label_PrevDate.setObjectName("label_PrevDate")
        self.horizontalLayout_16.addWidget(self.label_PrevDate)
        self.textBrowser_PrevDate = QtGui.QLineEdit(self.groupBox_Analysis)
        self.textBrowser_PrevDate.setMinimumSize(QtCore.QSize(20, 0))
        self.textBrowser_PrevDate.setReadOnly(True)
        self.textBrowser_PrevDate.setObjectName("textBrowser_PrevDate")
        self.horizontalLayout_16.addWidget(self.textBrowser_PrevDate)
        self.label_PrevStatus = QtGui.QLabel(self.groupBox_Analysis)
        self.label_PrevStatus.setObjectName("label_PrevStatus")
        self.horizontalLayout_16.addWidget(self.label_PrevStatus)
        self.textBrowser_PrevStatus = QtGui.QLineEdit(self.groupBox_Analysis)
        self.textBrowser_PrevStatus.setMinimumSize(QtCore.QSize(20, 0))
        self.textBrowser_PrevStatus.setReadOnly(True)
        self.textBrowser_PrevStatus.setObjectName("textBrowser_PrevStatus")
        self.horizontalLayout_16.addWidget(self.textBrowser_PrevStatus)
        self.pushButton_MarkReviewed = QtGui.QPushButton(self.groupBox_Analysis)
        self.pushButton_MarkReviewed.setObjectName("pushButton_MarkReviewed")
        self.horizontalLayout_16.addWidget(self.pushButton_MarkReviewed)
        self.pushButton_MarkAccepted = QtGui.QPushButton(self.groupBox_Analysis)
        self.pushButton_MarkAccepted.setObjectName("pushButton_MarkAccepted")
        self.horizontalLayout_16.addWidget(self.pushButton_MarkAccepted)
        self.verticalLayout_3.addLayout(self.horizontalLayout_16)
        self.verticalLayout_10.addWidget(self.groupBox_Analysis)
        self.tabWidget.addTab(self.tab_Analysis, "")
        self.tab_Reports = QtGui.QWidget()
        self.tab_Reports.setObjectName("tab_Reports")
        self.verticalLayout_12 = QtGui.QVBoxLayout(self.tab_Reports)
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self.verticalLayout_11 = QtGui.QVBoxLayout()
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.horizontalLayout_7 = QtGui.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.label_srcCode = QtGui.QLabel(self.tab_Reports)
        self.label_srcCode.setObjectName("label_srcCode")
        self.horizontalLayout_7.addWidget(self.label_srcCode)
        self.textBrowser_ReportFile = QtGui.QTextBrowser(self.tab_Reports)
        self.textBrowser_ReportFile.setMinimumSize(QtCore.QSize(0, 32))
        self.textBrowser_ReportFile.setMaximumSize(QtCore.QSize(16777215, 32))
        self.textBrowser_ReportFile.setObjectName("textBrowser_ReportFile")
        self.horizontalLayout_7.addWidget(self.textBrowser_ReportFile)
        self.pushButton_BrowseSrcCode = QtGui.QPushButton(self.tab_Reports)
        self.pushButton_BrowseSrcCode.setObjectName("pushButton_BrowseSrcCode")
        self.horizontalLayout_7.addWidget(self.pushButton_BrowseSrcCode)
        self.verticalLayout_11.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_8 = QtGui.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.label_reportDir = QtGui.QLabel(self.tab_Reports)
        self.label_reportDir.setObjectName("label_reportDir")
        self.horizontalLayout_8.addWidget(self.label_reportDir)
        self.textBrowser_ReportDir = QtGui.QTextBrowser(self.tab_Reports)
        self.textBrowser_ReportDir.setMinimumSize(QtCore.QSize(0, 32))
        self.textBrowser_ReportDir.setMaximumSize(QtCore.QSize(16777215, 32))
        self.textBrowser_ReportDir.setObjectName("textBrowser_ReportDir")
        self.horizontalLayout_8.addWidget(self.textBrowser_ReportDir)
        self.pushButton_BrowseReport = QtGui.QPushButton(self.tab_Reports)
        self.pushButton_BrowseReport.setObjectName("pushButton_BrowseReport")
        self.horizontalLayout_8.addWidget(self.pushButton_BrowseReport)
        self.verticalLayout_11.addLayout(self.horizontalLayout_8)
        spacerItem3 = QtGui.QSpacerItem(728, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_11.addItem(spacerItem3)
        self.horizontalLayout_21 = QtGui.QHBoxLayout()
        self.horizontalLayout_21.setObjectName("horizontalLayout_21")
        spacerItem4 = QtGui.QSpacerItem(638, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_21.addItem(spacerItem4)
        self.pushButton_GenerateReport = QtGui.QPushButton(self.tab_Reports)
        self.pushButton_GenerateReport.setObjectName("pushButton_GenerateReport")
        self.horizontalLayout_21.addWidget(self.pushButton_GenerateReport)
        self.verticalLayout_11.addLayout(self.horizontalLayout_21)
        self.verticalLayout_12.addLayout(self.verticalLayout_11)
        self.tabWidget.addTab(self.tab_Reports, "")
        self.verticalLayout.addWidget(self.tabWidget)
        self.verticalLayout_13.addLayout(self.verticalLayout)
        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QtGui.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 855, 21))
        self.menuBar.setObjectName("menuBar")
        MainWindow.setMenuBar(self.menuBar)
        self.mainToolBar = QtGui.QToolBar(MainWindow)
        self.mainToolBar.setObjectName("mainToolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.mainToolBar)
        self.statusBar = QtGui.QStatusBar(MainWindow)
        self.statusBar.setObjectName("statusBar")
        MainWindow.setStatusBar(self.statusBar)

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtGui.QApplication.translate("MainWindow", "CRMainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MainWindow", "Knowlogic Software", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("MainWindow", "Code Review Tool", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_2.setTitle(QtGui.QApplication.translate("MainWindow", "Code Review Administration", None, QtGui.QApplication.UnicodeUTF8))
        self.label_7.setText(QtGui.QApplication.translate("MainWindow", "User Name", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setText(QtGui.QApplication.translate("MainWindow", "Project File", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_pFileBrowse.setText(QtGui.QApplication.translate("MainWindow", "Browse...", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_RunAnalysis.setText(QtGui.QApplication.translate("MainWindow", "Run Analysis", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonAbortAnalysis.setText(QtGui.QApplication.translate("MainWindow", "Abort Analysis", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox.setTitle(QtGui.QApplication.translate("MainWindow", "Code Review Statistics", None, QtGui.QApplication.UnicodeUTF8))
        self.label_9.setText(QtGui.QApplication.translate("MainWindow", "Total Violations", None, QtGui.QApplication.UnicodeUTF8))
        self.label_10.setText(QtGui.QApplication.translate("MainWindow", "Removed Violations", None, QtGui.QApplication.UnicodeUTF8))
        self.label_11.setText(QtGui.QApplication.translate("MainWindow", "Reviewed Violations", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setText(QtGui.QApplication.translate("MainWindow", "Accepted Violations", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("MainWindow", "Knowlogic", None, QtGui.QApplication.UnicodeUTF8))
        self.Reviewed.setText(QtGui.QApplication.translate("MainWindow", "Reviewed", None, QtGui.QApplication.UnicodeUTF8))
        self.label_13.setText(QtGui.QApplication.translate("MainWindow", "Accepted", None, QtGui.QApplication.UnicodeUTF8))
        self.label_14.setText(QtGui.QApplication.translate("MainWindow", "Removed", None, QtGui.QApplication.UnicodeUTF8))
        self.label_12.setText(QtGui.QApplication.translate("MainWindow", "PC-Lint", None, QtGui.QApplication.UnicodeUTF8))
        self.label_15.setText(QtGui.QApplication.translate("MainWindow", "Reviewed", None, QtGui.QApplication.UnicodeUTF8))
        self.label_16.setText(QtGui.QApplication.translate("MainWindow", "Accepted", None, QtGui.QApplication.UnicodeUTF8))
        self.label_17.setText(QtGui.QApplication.translate("MainWindow", "Removed", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_Config), QtGui.QApplication.translate("MainWindow", "Config", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_Filters.setTitle(QtGui.QApplication.translate("MainWindow", "Select Filters", None, QtGui.QApplication.UnicodeUTF8))
        self.dispositioned.setText(QtGui.QApplication.translate("MainWindow", "Include Dispositioned", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_ApplyFilters.setText(QtGui.QApplication.translate("MainWindow", "Apply Filters", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_Violations.setTitle(QtGui.QApplication.translate("MainWindow", "View Violations", None, QtGui.QApplication.UnicodeUTF8))
        self.label_Filename.setText(QtGui.QApplication.translate("MainWindow", "Filename:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_Function.setText(QtGui.QApplication.translate("MainWindow", "Function:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_6.setText(QtGui.QApplication.translate("MainWindow", "Error Severity:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_Id.setText(QtGui.QApplication.translate("MainWindow", "Violation Id:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_DetectedBy.setText(QtGui.QApplication.translate("MainWindow", "Detected By:", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_GotoCode.setText(QtGui.QApplication.translate("MainWindow", "Go To Code", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBox_Analysis.setTitle(QtGui.QApplication.translate("MainWindow", "Enter Analysis", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonAddCanned.setText(QtGui.QApplication.translate("MainWindow", "Add", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("MainWindow", "Previous Reviewer", None, QtGui.QApplication.UnicodeUTF8))
        self.label_PrevDate.setText(QtGui.QApplication.translate("MainWindow", "Previous Date", None, QtGui.QApplication.UnicodeUTF8))
        self.label_PrevStatus.setText(QtGui.QApplication.translate("MainWindow", "Previous Status", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_MarkReviewed.setText(QtGui.QApplication.translate("MainWindow", "Mark Reviewed", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_MarkAccepted.setText(QtGui.QApplication.translate("MainWindow", "Mark Accepted", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_Analysis), QtGui.QApplication.translate("MainWindow", "Analysis", None, QtGui.QApplication.UnicodeUTF8))
        self.label_srcCode.setText(QtGui.QApplication.translate("MainWindow", "Source Code Filename:", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_BrowseSrcCode.setText(QtGui.QApplication.translate("MainWindow", "Browse...", None, QtGui.QApplication.UnicodeUTF8))
        self.label_reportDir.setText(QtGui.QApplication.translate("MainWindow", "Report Directory:", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_BrowseReport.setText(QtGui.QApplication.translate("MainWindow", "Browse...", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton_GenerateReport.setText(QtGui.QApplication.translate("MainWindow", "Generate Report", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_Reports), QtGui.QApplication.translate("MainWindow", "Generate Report", None, QtGui.QApplication.UnicodeUTF8))

