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

from analyze.media.sound import SoundFromSoundFile
from gui.composition_worker import QCompositionWorker
from gui.play_worker import QPlayWorker
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

        self.composition_worker = QCompositionWorker()
        self.composition_worker.message.connect(self.status_show)
        self.composition_worker.process_ok.connect(
            self.on_composition_processed
        )
        self.composition_worker.process_error.connect(
            self.on_composition_process_error
        )

        self.play_worker = QPlayWorker()

        self.fname = None

        self.spectrogram_view = SpectrogramQGraphicsView()

        self.spectrogram_view.reseted.connect(
            lambda: self.play_fragment_action.setEnabled(False)
        )
        self.spectrogram_view.reseted.connect(
            lambda: self.play_fragment_fb_action.setEnabled(False)
        )

        self.spectrogram_view.fragment_selected.connect(
            self.on_sound_fragment_selected
        )
        self.spectrogram_view.setMinimumSize(200, 200)
        self.setCentralWidget(self.spectrogram_view)

        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.showMessage('Ready', 5000)

        # self.size_label = QLabel()
        # self.size_label.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        # status.addPermanentWidget(self.size_label)

        status.addPermanentWidget(self.progress_dialog)

        file_open_action = self.create_action(
            '&Open...', self.file_open, QKeySequence.Open, 'fileopen',
            'Open sound file'
        )

        # Play
        self.play_fragment_action = self.create_action(
            'Play fra&gment', self.play_fragment, shortcut='g',
            tip='Play fragment'
        )
        self.play_fragment_action.setEnabled(False)

        self.play_fragment_fb_action = self.create_action(
            'Play full&band fragment', self.play_fragment_fb, shortcut='b',
            tip='Play fullband fragment'
        )
        self.play_fragment_fb_action.setEnabled(False)
        # /Play

        file_quit_action = self.create_action(
            '&Quit', self.close, 'Ctrl+Q', 'filequit', 'Close the application'
        )

        file_toolbar = self.addToolBar('File')
        file_toolbar.setObjectName('file_tool_bar')

        self.add_actions(file_toolbar, (
            file_open_action,
            self.play_fragment_action,
            self.play_fragment_fb_action,
            file_quit_action,
        ))

        settings = QSettings()
        self.restoreGeometry(settings.value('MainWindow/Geometry', ''))
        self.restoreState(settings.value('MainWindow/State', ''))

        QTimer.singleShot(0, self.load_initial_file)

    def on_sound_fragment_selected(self, fragment):
        self.status_show(repr(fragment))
        self.fragment = fragment
        self.play_fragment()
        self.play_fragment_action.setEnabled(True)
        self.play_fragment_fb_action.setEnabled(True)

    def play_fragment(self):
        if not getattr(self, 'fragment', False):
            return

        if not self.play_worker.busy:
            self.play_worker.play.emit(self.fragment)

    def play_fragment_fb(self):
        if not getattr(self, 'fragment', False):
            return

        if not self.play_worker.busy:
            self.play_worker.play.emit(self.fragment.full_band_sound)

    def file_open(self):
        if not self.ok_to_continue:
            return

        path = (os.path.dirname(self.fname)
                if self.fname is not None
                else '.')
        formats = ['*.wav', '*.flac', '*.ogg']

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

        if not self.ok_to_continue:
            log.debug('Not self.ok_to_continue')

            return

        self.fname = None
        self.spectrogram_view.reset()

        try:
            sound = SoundFromSoundFile(fname)

        except Exception as e:
            log.exception('Load file error %s', e)
            self.status_show(repr(e))

            return

        self.fname = fname
        log.debug('Loaded %s', os.path.basename(fname))
        self.status_show('Loaded {0}'.format(os.path.basename(fname)))

        self.composition_worker.process.emit(sound, self.progress_dialog)

    def on_composition_processed(self, spectrogram):
        log.debug('Run update_spectrogram %s', spectrogram)
        self.status_show('Processed')
        self.spectrogram_view.update_spectrogram(spectrogram)

    def on_composition_process_error(self, msg):
        self.fname = None
        self.status_show(msg)

    def load_initial_file(self):
        settings = QSettings()
        fname = settings.value('LastFile')

        if fname and QFile.exists(fname):
            self.load_file(fname)

    def status_show(self, msg):
        self.statusBar().showMessage(msg)

    def closeEvent(self, event):
        if self.ok_to_continue:
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

    @property
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
