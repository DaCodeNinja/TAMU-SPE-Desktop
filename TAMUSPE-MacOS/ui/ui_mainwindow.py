# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.5.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QMainWindow, QMenuBar,
    QPushButton, QSizePolicy, QSpacerItem, QStatusBar,
    QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout,
    QWidget)
import src.resources_rc

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(850, 443)
        font = QFont()
        font.setFamilies([u"Futura"])
        font.setBold(False)
        MainWindow.setFont(font)
        icon = QIcon()
        icon.addFile(u":/Images/images/TAMUSPE_Square.png", QSize(), QIcon.Normal, QIcon.Off)
        MainWindow.setWindowIcon(icon)
        MainWindow.setIconSize(QSize(32, 32))
        MainWindow.setToolButtonStyle(Qt.ToolButtonIconOnly)
        MainWindow.setAnimated(True)
        MainWindow.setDocumentMode(False)
        MainWindow.setDockNestingEnabled(False)
        MainWindow.setDockOptions(QMainWindow.AllowTabbedDocks|QMainWindow.AnimatedDocks)
        MainWindow.setUnifiedTitleAndToolBarOnMac(False)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(5, 0, 5, 0)
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(-1, -1, -1, 0)
        self.table = QTableWidget(self.centralwidget)
        self.table.setObjectName(u"table")
        self.table.setLineWidth(1)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setShowGrid(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setProperty("showSortIndicator", True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)

        self.verticalLayout.addWidget(self.table)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, 0)
        self.logo = QPushButton(self.centralwidget)
        self.logo.setObjectName(u"logo")
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.logo.sizePolicy().hasHeightForWidth())
        self.logo.setSizePolicy(sizePolicy)
        self.logo.setMaximumSize(QSize(101, 100))
        icon1 = QIcon()
        icon1.addFile(u":/Images/images/SPE_A_M_RGB_border.png", QSize(), QIcon.Normal, QIcon.Off)
        self.logo.setIcon(icon1)
        self.logo.setIconSize(QSize(92, 72))
        self.logo.setFlat(True)

        self.horizontalLayout.addWidget(self.logo)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.date = QLabel(self.centralwidget)
        self.date.setObjectName(u"date")
        self.date.setMinimumSize(QSize(0, 25))
        self.date.setMargin(3)
        self.date.setIndent(-1)

        self.horizontalLayout.addWidget(self.date, 0, Qt.AlignBottom)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(-1, 5, -1, -1)
        self.offline_label = QLabel(self.centralwidget)
        self.offline_label.setObjectName(u"offline_label")
        self.offline_label.setMaximumSize(QSize(16777215, 12))
        font1 = QFont()
        font1.setFamilies([u"Futura"])
        font1.setPointSize(9)
        font1.setBold(False)
        self.offline_label.setFont(font1)

        self.verticalLayout_2.addWidget(self.offline_label, 0, Qt.AlignHCenter|Qt.AlignTop)

        self.offline_notification = QLabel(self.centralwidget)
        self.offline_notification.setObjectName(u"offline_notification")
        self.offline_notification.setFont(font1)

        self.verticalLayout_2.addWidget(self.offline_notification, 0, Qt.AlignHCenter|Qt.AlignTop)

        self.verticalSpacer = QSpacerItem(20, 23, QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(-1, 0, 1, 6)
        self.refresh = QToolButton(self.centralwidget)
        self.refresh.setObjectName(u"refresh")
        icon2 = QIcon()
        icon2.addFile(u":/Images/images/icons8-refresh-50.png", QSize(), QIcon.Normal, QIcon.Off)
        self.refresh.setIcon(icon2)
        self.refresh.setIconSize(QSize(16, 16))

        self.horizontalLayout_4.addWidget(self.refresh)

        self.settings = QToolButton(self.centralwidget)
        self.settings.setObjectName(u"settings")
        icon3 = QIcon()
        icon3.addFile(u":/Images/images/icons8-settings-50.png", QSize(), QIcon.Normal, QIcon.Off)
        self.settings.setIcon(icon3)
        self.settings.setIconSize(QSize(16, 16))
        self.settings.setPopupMode(QToolButton.DelayedPopup)
        self.settings.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.settings.setAutoRaise(False)
        self.settings.setArrowType(Qt.NoArrow)

        self.horizontalLayout_4.addWidget(self.settings)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)


        self.horizontalLayout.addLayout(self.verticalLayout_2)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 850, 24))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"TAMU-SPE Schedule v1.0.0", None))
#if QT_CONFIG(statustip)
        self.logo.setStatusTip(QCoreApplication.translate("MainWindow", u"www.tamuspe.org -- Click here to visit our website", None))
#endif // QT_CONFIG(statustip)
        self.date.setText(QCoreApplication.translate("MainWindow", u"Date", None))
        self.offline_label.setText("")
        self.offline_notification.setText("")
#if QT_CONFIG(statustip)
        self.refresh.setStatusTip(QCoreApplication.translate("MainWindow", u"Refresh Event -- CMD + R", None))
#endif // QT_CONFIG(statustip)
        self.refresh.setText(QCoreApplication.translate("MainWindow", u"...", None))
#if QT_CONFIG(shortcut)
        self.refresh.setShortcut(QCoreApplication.translate("MainWindow", u"Ctrl+R", None))
#endif // QT_CONFIG(shortcut)
#if QT_CONFIG(statustip)
        self.settings.setStatusTip(QCoreApplication.translate("MainWindow", u"Settings", None))
#endif // QT_CONFIG(statustip)
        self.settings.setText(QCoreApplication.translate("MainWindow", u"Settings", None))
    # retranslateUi

