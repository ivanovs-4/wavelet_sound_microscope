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

from PyQt5.QtCore import (Qt, SIGNAL)
from PyQt5.QtGui import (QApplication, QDialog, QDialogButtonBox,
        QGridLayout, QLabel, QSpinBox)


class ResizeDlg(QDialog):

    def __init__(self, width, height, parent=None):
        super(ResizeDlg, self).__init__(parent)

        width_label = QLabel("&Width:")
        self.width_spin_box = QSpinBox()
        width_label.setBuddy(self.width_spin_box)
        self.width_spin_box.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.width_spin_box.setRange(4, width * 4)
        self.width_spin_box.setValue(width)
        height_label = QLabel("&Height:")
        self.height_spin_box = QSpinBox()
        height_label.setBuddy(self.height_spin_box)
        self.height_spin_box.setAlignment(Qt.AlignRight|
                                        Qt.AlignVCenter)
        self.height_spin_box.setRange(4, height * 4)
        self.height_spin_box.setValue(height)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok|
                                     QDialogButtonBox.Cancel)

        layout = QGridLayout()
        layout.addWidget(width_label, 0, 0)
        layout.addWidget(self.width_spin_box, 0, 1)
        layout.addWidget(height_label, 1, 0)
        layout.addWidget(self.height_spin_box, 1, 1)
        layout.addWidget(button_box, 2, 0, 1, 2)
        self.setLayout(layout)

        self.connect(button_box, SIGNAL("accepted()"), self.accept)
        self.connect(button_box, SIGNAL("rejected()"), self.reject)

        self.setWindowTitle("Image Changer - Resize")


    def result(self):
        return self.width_spin_box.value(), self.height_spin_box.value()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    form = ResizeDlg(64, 128)
    form.show()
    app.exec_()

