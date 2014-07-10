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

import os
import platform
import sys
from PyQt5.QtCore import (PYQT_VERSION_STR, QFile, QFileInfo, QSettings,
        QString, QT_VERSION_STR, QTimer, QVariant, Qt, SIGNAL)
from PyQt5.QtGui import (QAction, QActionGroup, QApplication,
        QDockWidget, QFileDialog, QFrame, QIcon, QImage, QImageReader,
        QImageWriter, QInputDialog, QKeySequence, QLabel, QListWidget,
        QMainWindow, QMessageBox, QPainter, QPixmap, QPrintDialog,
        QPrinter, QSpinBox)
import helpform
import newimagedlg
import resizedlg
# import qrc_resources


__version__ = "1.0.0"


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.image = QImage()
        self.dirty = False
        self.filename = None
        self.mirrored_vertically = False
        self.mirrored_horizontally = False

        self.image_label = QLabel()
        self.image_label.setMinimumSize(200, 200)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.setCentralWidget(self.image_label)

        log_dock_widget = QDockWidget("Log", self)
        log_dock_widget.setObjectName("log_dock_widget")
        log_dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea|
                                      Qt.RightDockWidgetArea)
        self.list_widget = QListWidget()
        log_dock_widget.setWidget(self.list_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, log_dock_widget)

        self.printer = None

        self.size_label = QLabel()
        self.size_label.setFrameStyle(QFrame.StyledPanel|QFrame.Sunken)
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.addPermanentWidget(self.size_label)
        status.showMessage("Ready", 5000)

        file_new_action = self.create_action("&New...", self.file_new,
                QKeySequence.New, "filenew", "Create an image file")
        file_open_action = self.create_action("&Open...", self.file_open,
                QKeySequence.Open, "fileopen",
                "Open an existing image file")
        file_save_action = self.create_action("&Save", self.file_save,
                QKeySequence.Save, "filesave", "Save the image")
        file_save_as_action = self.create_action("Save &As...",
                self.file_save_as, icon="filesaveas",
                tip="Save the image using a new name")
        file_print_action = self.create_action("&Print", self.file_print,
                QKeySequence.Print, "fileprint", "Print the image")
        file_quit_action = self.create_action("&Quit", self.close,
                "Ctrl+Q", "filequit", "Close the application")
        edit_invert_action = self.create_action("&Invert",
                self.edit_invert, "Ctrl+I", "editinvert",
                "Invert the image's colors", True, "toggled(bool)")
        edit_swap_red_and_blue_action = self.create_action(
                "Sw&ap Red and Blue", self.edit_swap_red_and_blue,
                "Ctrl+A", "editswap",
                "Swap the image's red and blue color components",
                True, "toggled(bool)")
        edit_zoom_action = self.create_action("&Zoom...", self.edit_zoom,
                "Alt+Z", "editzoom", "Zoom the image")
        edit_resize_action = self.create_action("&Resize...",
                self.edit_resize, "Ctrl+R", "editresize",
                "Resize the image")
        mirror_group = QActionGroup(self)
        edit_un_mirror_action = self.create_action("&Unmirror",
                self.edit_un_mirror, "Ctrl+U", "editunmirror",
                "Unmirror the image", True, "toggled(bool)")
        mirror_group.addAction(edit_un_mirror_action)
        edit_mirror_horizontal_action = self.create_action(
                "Mirror &Horizontally", self.edit_mirror_horizontal,
                "Ctrl+H", "editmirrorhoriz",
                "Horizontally mirror the image", True, "toggled(bool)")
        mirror_group.addAction(edit_mirror_horizontal_action)
        edit_mirror_vertical_action = self.create_action(
                "Mirror &Vertically", self.edit_mirror_vertical,
                "Ctrl+V", "editmirrorvert",
                "Vertically mirror the image", True, "toggled(bool)")
        mirror_group.addAction(edit_mirror_vertical_action)
        edit_un_mirror_action.setChecked(True)
        help_about_action = self.create_action("&About image Changer",
                self.help_about)
        help_help_action = self.create_action("&Help", self.help_help,
                QKeySequence.HelpContents)

        self.file_menu = self.menuBar().addMenu("&File")
        self.file_menu_actions = (file_new_action, file_open_action,
                file_save_action, file_save_as_action, None, file_print_action,
                file_quit_action)
        self.connect(self.file_menu, SIGNAL("aboutToShow()"),
                     self.update_file_menu)
        edit_menu = self.menuBar().addMenu("&Edit")
        self.add_actions(edit_menu, (edit_invert_action,
                edit_swap_red_and_blue_action, edit_zoom_action,
                edit_resize_action))
        mirror_menu = edit_menu.addMenu(QIcon(":/editmirror.png"),
                                      "&Mirror")
        self.add_actions(mirror_menu, (edit_un_mirror_action,
                edit_mirror_horizontal_action, edit_mirror_vertical_action))
        help_menu = self.menuBar().addMenu("&Help")
        self.add_actions(help_menu, (help_about_action, help_help_action))

        file_toolbar = self.addToolBar("File")
        file_toolbar.setObjectName("file_tool_bar")
        self.add_actions(file_toolbar, (file_new_action, file_open_action,
                                      file_save_as_action))
        edit_toolbar = self.addToolBar("Edit")
        edit_toolbar.setObjectName("edit_tool_bar")
        self.add_actions(edit_toolbar, (edit_invert_action,
                edit_swap_red_and_blue_action, edit_un_mirror_action,
                edit_mirror_vertical_action, edit_mirror_horizontal_action))
        self.zoom_spin_box = QSpinBox()
        self.zoom_spin_box.setRange(1, 400)
        self.zoom_spin_box.setSuffix(" %")
        self.zoom_spin_box.setValue(100)
        self.zoom_spin_box.setToolTip("Zoom the image")
        self.zoom_spin_box.setStatusTip(self.zoom_spin_box.toolTip())
        self.zoom_spin_box.setFocusPolicy(Qt.NoFocus)
        self.connect(self.zoom_spin_box,
                     SIGNAL("valueChanged(int)"), self.show_image)
        edit_toolbar.addWidget(self.zoom_spin_box)

        self.add_actions(self.image_label, (edit_invert_action,
                edit_swap_red_and_blue_action, edit_un_mirror_action,
                edit_mirror_vertical_action, edit_mirror_horizontal_action))

        self.resetable_actions = ((edit_invert_action, False),
                                 (edit_swap_red_and_blue_action, False),
                                 (edit_un_mirror_action, True))

        settings = QSettings()
        self.recent_files = settings.value("recent_files").toStringList()
        self.restoreGeometry(
                settings.value("MainWindow/Geometry").toByteArray())
        self.restoreState(settings.value("MainWindow/State").toByteArray())
        
        self.setWindowTitle("image Changer")
        self.update_file_menu()
        QTimer.singleShot(0, self.load_initial_file)


    def create_action(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/{0}.png".format(icon)))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action


    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)


    def close_event(self, event):
        if self.ok_to_continue():
            settings = QSettings()
            filename = (QVariant(QString(self.filename)) 
                        if self.filename is not None else QVariant())
            settings.setValue("LastFile", filename)
            recent_files = (QVariant(self.recent_files)
                           if self.recent_files else QVariant())
            settings.setValue("recent_files", recent_files)
            settings.setValue("MainWindow/Geometry", QVariant(
                              self.saveGeometry()))
            settings.setValue("MainWindow/State", QVariant(
                              self.saveState()))
        else:
            event.ignore()


    def ok_to_continue(self):
        if self.dirty:
            reply = QMessageBox.question(self,
                    "image Changer - Unsaved Changes",
                    "Save unsaved changes?",
                    QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                return self.file_save()
        return True


    def load_initial_file(self):
        settings = QSettings()
        fname = str(settings.value("LastFile").toString())
        if fname and QFile.exists(fname):
            self.load_file(fname)


    def update_status(self, message):
        self.statusBar().showMessage(message, 5000)
        self.list_widget.addItem(message)
        if self.filename is not None:
            self.setWindowTitle("image Changer - {0}[*]".format(
                                os.path.basename(self.filename)))
        elif not self.image.isNull():
            self.setWindowTitle("image Changer - Unnamed[*]")
        else:
            self.setWindowTitle("image Changer[*]")
        self.setWindowModified(self.dirty)


    def update_file_menu(self):
        self.file_menu.clear()
        self.add_actions(self.file_menu, self.file_menu_actions[:-1])
        current = (QString(self.filename)
                   if self.filename is not None else None)
        recent_files = []
        for fname in self.recent_files:
            if fname != current and QFile.exists(fname):
                recent_files.append(fname)
        if recent_files:
            self.file_menu.addSeparator()
            for i, fname in enumerate(recent_files):
                action = QAction(QIcon(":/icon.png"),
                        "&{0} {1}".format(i + 1, QFileInfo(
                        fname).file_name()), self)
                action.setData(QVariant(fname))
                self.connect(action, SIGNAL("triggered()"),
                             self.load_file)
                self.file_menu.addAction(action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.file_menu_actions[-1])


    def file_new(self):
        if not self.ok_to_continue():
            return
        dialog = newimagedlg.NewImageDlg(self)
        if dialog.exec_():
            self.add_recent_file(self.filename)
            self.image = QImage()
            for action, check in self.resetable_actions:
                action.setChecked(check)
            self.image = dialog.image()
            self.filename = None
            self.dirty = True
            self.show_image()
            self.size_label.setText("{0} x {1}".format(self.image.width(),
                                                      self.image.height()))
            self.update_status("Created new image")


    def file_open(self):
        if not self.ok_to_continue():
            return
        dir = (os.path.dirname(self.filename)
               if self.filename is not None else ".")
        formats = (["*.{0}".format(format.data().decode("ascii").lower())
                for format in QImageReader.supportedImageFormats()])
        fname = str(QFileDialog.getOpenFileName(self,
                "image Changer - Choose image", dir,
                "image files ({0})".format(" ".join(formats))))
        if fname:
            self.load_file(fname)


    def load_file(self, fname=None):
        if fname is None:
            action = self.sender()
            if isinstance(action, QAction):
                fname = str(action.data().toString())
                if not self.ok_to_continue():
                    return
            else:
                return
        if fname:
            self.filename = None
            image = QImage(fname)
            if image.isNull():
                message = "Failed to read {0}".format(fname)
            else:
                self.add_recent_file(fname)
                self.image = QImage()
                for action, check in self.resetable_actions:
                    action.setChecked(check)
                self.image = image
                self.filename = fname
                self.show_image()
                self.dirty = False
                self.size_label.setText("{0} x {1}".format(
                                       image.width(), image.height()))
                message = "Loaded {0}".format(os.path.basename(fname))
            self.update_status(message)


    def add_recent_file(self, fname):
        if fname is None:
            return
        if not self.recent_files.contains(fname):
            self.recent_files.prepend(QString(fname))
            while self.recent_files.count() > 9:
                self.recent_files.takeLast()


    def file_save(self):
        if self.image.isNull():
            return True
        if self.filename is None:
            return self.file_save_as()
        else:
            if self.image.save(self.filename, None):
                self.update_status("Saved as {0}".format(self.filename))
                self.dirty = False
                return True
            else:
                self.update_status("Failed to save {0}".format(
                                  self.filename))
                return False


    def file_save_as(self):
        if self.image.isNull():
            return True
        fname = self.filename if self.filename is not None else "."
        formats = (["*.{0}".format(format.data().decode("ascii").lower())
                for format in QImageWriter.supportedImageFormats()])
        fname = str(QFileDialog.getSaveFileName(self,
                "image Changer - Save image", fname,
                "image files ({0})".format(" ".join(formats))))
        if fname:
            if "." not in fname:
                fname += ".png"
            self.add_recent_file(fname)
            self.filename = fname
            return self.file_save()
        return False


    def file_print(self):
        if self.image.isNull():
            return
        if self.printer is None:
            self.printer = QPrinter(QPrinter.HighResolution)
            self.printer.setPageSize(QPrinter.Letter)
        form = QPrintDialog(self.printer, self)
        if form.exec_():
            painter = QPainter(self.printer)
            rect = painter.viewport()
            size = self.image.size()
            size.scale(rect.size(), Qt.KeepAspectRatio)
            painter.setViewport(rect.x(), rect.y(), size.width(),
                                size.height())
            painter.drawImage(0, 0, self.image)


    def edit_invert(self, on):
        if self.image.isNull():
            return
        self.image.invertPixels()
        self.show_image()
        self.dirty = True
        self.update_status("Inverted" if on else "Uninverted")


    def edit_swap_red_and_blue(self, on):
        if self.image.isNull():
            return
        self.image = self.image.rgbSwapped()
        self.show_image()
        self.dirty = True
        self.update_status(("Swapped Red and Blue"
                           if on else "Unswapped Red and Blue"))


    def edit_un_mirror(self, on):
        if self.image.isNull():
            return
        if self.mirrored_horizontally:
            self.edit_mirror_horizontal(False)
        if self.mirrored_vertically:
            self.edit_mirror_vertical(False)


    def edit_mirror_horizontal(self, on):
        if self.image.isNull():
            return
        self.image = self.image.mirrored(True, False)
        self.show_image()
        self.mirrored_horizontally = not self.mirrored_horizontally
        self.dirty = True
        self.update_status(("Mirrored Horizontally"
                           if on else "Unmirrored Horizontally"))


    def edit_mirror_vertical(self, on):
        if self.image.isNull():
            return
        self.image = self.image.mirrored(False, True)
        self.show_image()
        self.mirrored_vertically = not self.mirrored_vertically
        self.dirty = True
        self.update_status(("Mirrored Vertically"
                           if on else "Unmirrored Vertically"))


    def edit_zoom(self):
        if self.image.isNull():
            return
        percent, ok = QInputDialog.getInteger(self,
                "image Changer - Zoom", "percent:",
                self.zoom_spin_box.value(), 1, 400)
        if ok:
            self.zoom_spin_box.setValue(percent)


    def edit_resize(self):
        if self.image.isNull():
            return
        form = resizedlg.ResizeDlg(self.image.width(),
                                   self.image.height(), self)
        if form.exec_():
            width, height = form.result()
            if (width == self.image.width() and
                height == self.image.height()):
                self.statusBar().showMessage("Resized to the same size",
                                             5000)
            else:
                self.image = self.image.scaled(width, height)
                self.show_image()
                self.dirty = True
                size = "{0} x {1}".format(self.image.width(),
                                          self.image.height())
                self.size_label.setText(size)
                self.update_status("Resized to {0}".format(size))


    def show_image(self, percent=None):
        if self.image.isNull():
            return
        if percent is None:
            percent = self.zoom_spin_box.value()
        factor = percent / 100.0
        width = self.image.width() * factor
        height = self.image.height() * factor
        image = self.image.scaled(width, height, Qt.KeepAspectRatio)
        self.image_label.setPixmap(QPixmap.fromImage(image))


    def help_about(self):
        QMessageBox.about(self, "About image Changer",
                """<b>image Changer</b> v {0}
                <p>Copyright &copy; 2008-9 Qtrac Ltd. 
                All rights reserved.
                <p>This application can be used to perform
                simple image manipulations.
                <p>Python {1} - Qt {2} - PyQt {3} on {4}""".format(
                __version__, platform.python_version(),
                QT_VERSION_STR, PYQT_VERSION_STR,
                platform.system()))


    def help_help(self):
        form = helpform.HelpForm("index.html", self)
        form.show()


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("Qtrac Ltd.")
    app.setOrganizationDomain("qtrac.eu")
    app.setApplicationName("image Changer")
    app.setWindowIcon(QIcon(":/icon.png"))
    form = MainWindow()
    form.show()
    app.exec_()


main()

