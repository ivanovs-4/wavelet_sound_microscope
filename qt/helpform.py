#!/usr/bin/env python3
# Copyright (c) 2008-9 Qtrac Ltd. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.

from PyQt5.QtCore import (QUrl, Qt, pyqtSignal, pyqtSlot)
from PyQt5.QtWidgets import (
    QApplication, QLabel, QAction, QActionGroup, QDockWidget,
    QListWidget, QFileDialog, QFrame, QInputDialog,
    QMainWindow, QMessageBox, QSpinBox, QDialog,
    QTextBrowser, QToolBar, QVBoxLayout,
)

from PyQt5.QtGui import (QIcon, QKeySequence)
# import qrc_resources


class HelpForm(QDialog):

    def __init__(self, page, parent=None):
        super(HelpForm, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_GroupLeader)

        back_action = QAction(QIcon(":/back.png"), "&Back", self)
        back_action.setShortcut(QKeySequence.Back)
        home_action = QAction(QIcon(":/home.png"), "&Home", self)
        home_action.setShortcut("Home")
        self.page_label = QLabel()

        tool_bar = QToolBar()
        tool_bar.addAction(back_action)
        tool_bar.addAction(home_action)
        tool_bar.addWidget(self.page_label)
        self.text_browser = QTextBrowser()

        layout = QVBoxLayout()
        layout.addWidget(tool_bar)
        layout.addWidget(self.text_browser, 1)
        self.setLayout(layout)

        # self.connect(back_action, SIGNAL("triggered()"), self.text_browser, SLOT("backward()"))
        # self.connect(home_action, SIGNAL("triggered()"), self.text_browser, SLOT("home()"))
        # self.connect(self.text_browser, SIGNAL("sourceChanged(QUrl)"), self.update_page_title)

        self.text_browser.setSearchPaths([":/help"])
        self.text_browser.setSource(QUrl(page))
        self.resize(400, 600)
        self.setWindowTitle("{0} Help".format(
            QApplication.applicationName()))

    def update_page_title(self):
        self.page_label.setText(self.text_browser.documentTitle())


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    form = HelpForm("index.html")
    form.show()
    app.exec_()
