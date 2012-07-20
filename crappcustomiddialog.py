# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'crappcustomiddialog.ui'
#
# Created: Thu Jul 19 21:00:45 2012
#      by: pyside-uic 0.2.13 running on PySide 1.1.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_CRAppCustomIdDialog(object):
    def setupUi(self, CRAppCustomIdDialog):
        CRAppCustomIdDialog.setObjectName("CRAppCustomIdDialog")
        CRAppCustomIdDialog.resize(265, 167)
        self.lineEdit_customText = QtGui.QLineEdit(CRAppCustomIdDialog)
        self.lineEdit_customText.setGeometry(QtCore.QRect(10, 100, 241, 20))
        self.lineEdit_customText.setObjectName("lineEdit_customText")
        self.buttonBox = QtGui.QDialogButtonBox(CRAppCustomIdDialog)
        self.buttonBox.setGeometry(QtCore.QRect(100, 130, 156, 23))
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtGui.QLabel(CRAppCustomIdDialog)
        self.label.setGeometry(QtCore.QRect(10, 80, 111, 16))
        self.label.setObjectName("label")
        self.label_2 = QtGui.QLabel(CRAppCustomIdDialog)
        self.label_2.setGeometry(QtCore.QRect(10, 10, 251, 16))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtGui.QLabel(CRAppCustomIdDialog)
        self.label_3.setGeometry(QtCore.QRect(10, 30, 241, 16))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtGui.QLabel(CRAppCustomIdDialog)
        self.label_4.setGeometry(QtCore.QRect(10, 50, 231, 16))
        self.label_4.setObjectName("label_4")

        self.retranslateUi(CRAppCustomIdDialog)
        QtCore.QMetaObject.connectSlotsByName(CRAppCustomIdDialog)

    def retranslateUi(self, CRAppCustomIdDialog):
        CRAppCustomIdDialog.setWindowTitle(QtGui.QApplication.translate("CRAppCustomIdDialog", "CRAppCustomIdDialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("CRAppCustomIdDialog", "Violation ID Contains:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("CRAppCustomIdDialog", "Enter text that the violationId filter should contain.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("CRAppCustomIdDialog", "( For example, by entering the word Metric, any  ", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("CRAppCustomIdDialog", "violation with the word Metric will be selected.)", None, QtGui.QApplication.UnicodeUTF8))

