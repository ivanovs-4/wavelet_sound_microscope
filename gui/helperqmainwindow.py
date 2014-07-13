from PyQt5.QtWidgets import QMainWindow, QAction


class HelperQMainWindow(QMainWindow):
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
