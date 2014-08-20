#!/usr/bin/python3
import os
import sys
from functools import partial

from PyQt5.QtCore import QSettings, QTimer, QVariant, QFile
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QLabel, QFileDialog, QFrame

from composition import Composition
from gui.helperqmainwindow import HelperQMainWindow
from gui.spectrogramqgraphicsview import SpectrogramQGraphicsView


__version__ = '1.0.0'


class MainWindow(HelperQMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.composition = None

        self.spectrogram = SpectrogramQGraphicsView()
        self.spectrogram.setMinimumSize(200, 200)
        self.setCentralWidget(self.spectrogram)

        self.size_label = QLabel()
        self.size_label.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.addPermanentWidget(self.size_label)
        status.showMessage('Ready', 5000)

        file_open_action = self.create_action(
            '&Open...', self.file_open, QKeySequence.Open, 'fileopen',
            'Open an existing image file'
        )

        file_quit_action = self.create_action(
            '&Quit', self.close, 'Ctrl+Q', 'filequit', 'Close the application'
        )

        file_toolbar = self.addToolBar('File')
        file_toolbar.setObjectName('file_tool_bar')

        self.add_actions(file_toolbar, (
            file_open_action,
            file_quit_action,
        ))

        settings = QSettings()
        self.restoreGeometry(settings.value('MainWindow/Geometry', ''))
        self.restoreState(settings.value('MainWindow/State', ''))

        QTimer.singleShot(0, self.load_initial_file)

    def file_open(self):
        if not self.ok_to_continue():
            return

        path = (os.path.dirname(self.composition.filename)
               if self.composition is not None else '.')
        formats = ['*.wav', '*.flac']

        fname, fmts = QFileDialog.getOpenFileName(
            self,
            'Musical harmony - Choose Music file',
            path,
            'Sound files ({0})'.format(' '.join(formats))
        )

        if fname:
            self.load_file(fname)

    def load_file(self, fname):
        try:
            self.composition = Composition(fname)
        except Exception as e:
            message = repr(e)
        else:
            self.update_spectrogram()
            message = 'Loaded {0}'.format(os.path.basename(fname))

        self.update_status(message)

    def update_spectrogram(self):
        if not self.composition:
            return

        # Нужно это выполнять в отдельном потоке
        image = self.composition.get_image()

        self.spectrogram.show_image(image)

    def load_initial_file(self):
        settings = QSettings()
        fname = settings.value('LastFile')
        if fname and QFile.exists(fname):
            self.load_file(fname)

    def update_status(self, message):
        self.statusBar().showMessage(message, 5000)

    def closeEvent(self, event):
        if self.ok_to_continue():
            settings = QSettings()
            if self.composition:
                settings.setValue("LastFile", self.composition.filename)
            settings.setValue('MainWindow/Geometry',
                              QVariant(self.saveGeometry()))
            settings.setValue('MainWindow/State',
                              QVariant(self.saveState()))
        else:
            event.ignore()

    def ok_to_continue(self):
        return True


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName('Sergey Ivanov')
    app.setOrganizationDomain('')
    app.setApplicationName('Musical harmony explorer')
    form = MainWindow()
    form.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
