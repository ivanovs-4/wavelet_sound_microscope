#!/usr/bin/python3
import logging
import os
import sys

from PyQt5.QtCore import QSettings, Qt, QTimer, QVariant, QFile
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction, QApplication, QFileDialog, QFrame, QLabel, QMainWindow,
    QProgressDialog,
)

from gui.composition_worker import QCompositionWorker
from gui.spectrogramqgraphicsview import SpectrogramQGraphicsView


__version__ = '1.0.0'

logging.basicConfig(format='%(levelname)s\t[%(threadName)s]\t%(filename)s:'
                    '%(lineno)d\t%(message)s')
logging.getLogger('').setLevel(logging.DEBUG)

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.progress_dialog = QProgressDialog()
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(100)

        self.composition_worker = QCompositionWorker(self.progress_dialog)

        self.composition_worker.message.connect(self.update_status)
        self.composition_worker.load_file_ok.connect(self.on_file_loaded)
        self.composition_worker.load_file_error.connect(self.stop_loading)
        self.composition_worker.process_ok.connect(self.update_spectrogram)

        self.fname = None

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
            'Open sound file'
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

        path = (os.path.dirname(self.fname)
               if self.fname is not None else '.')
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
        log.debug('MainWindow.load_file: %s', fname)

        self.fname = fname

        if self.ok_to_continue():
            self.composition_worker.load_file.emit(self.fname)

    def stop_loading(self):
        pass

    def on_file_loaded(self):
        # When file loaded immediately start process it
        self.composition_worker.process.emit()

    def update_spectrogram(self, image):
        log.debug('Run update_spectrogram %s', image)
        self.spectrogram.show_image(image)

    def load_initial_file(self):
        settings = QSettings()
        fname = settings.value('LastFile')

        if fname and QFile.exists(fname):
            self.load_file(fname)

    def update_status(self, msg):
        self.statusBar().showMessage(msg)

    def closeEvent(self, event):
        if self.ok_to_continue():
            self.composition_worker.finish()

            settings = QSettings()

            if self.fname:
                settings.setValue("LastFile", self.fname)

            settings.setValue('MainWindow/Geometry',
                              QVariant(self.saveGeometry()))

            settings.setValue('MainWindow/State',
                              QVariant(self.saveState()))
        else:
            event.ignore()

    def ok_to_continue(self):
        return True

    # Helper functions
    def create_action(self, text, slot=None, shortcut=None, icon=None,
                      tip=None, checkable=False, signal_name='triggered'):
        action = QAction(text, self)
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            getattr(action, signal_name).connect(slot)
        if checkable:
            action.setCheckable(True)
        return action

    def add_actions(self,target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)


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
