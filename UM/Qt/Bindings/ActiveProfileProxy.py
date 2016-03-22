# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, QVariant, QUrl

from UM.Application import Application
from UM.PluginRegistry import PluginRegistry

from . import ContainerProxy

import copy

class ActiveProfileProxy(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._setting_values = {}
        self._container_proxy = ContainerProxy.ContainerProxy(self._setting_values)
        self._active_profile = None
        self._manager = Application.getInstance().getMachineManager()
        self._manager.activeProfileChanged.connect(self._onActiveProfileChanged)
        self._onActiveProfileChanged()

    activeProfileChanged = pyqtSignal()

    @pyqtProperty(bool, notify = activeProfileChanged)
    def valid(self):
        return self._active_profile != None

    ## Check if the currently selected profile (not the working profile) is readonly
    @pyqtProperty(bool, notify = activeProfileChanged)
    def readOnly(self):
        profile = self._manager.getActiveProfile()
        if profile:
            return profile.isReadOnly()

    settingValuesChanges = pyqtSignal()

    @pyqtProperty(bool, notify = settingValuesChanges)
    def hasCustomisedValues(self):
        return self._active_profile.hasChangedSettings() == True

    @pyqtProperty(QObject, notify = settingValuesChanges)
    def settingValues(self):
        return self._container_proxy

    @pyqtSlot(str, "QVariant")
    def setSettingValue(self, key, value):
        self._active_profile.setSettingValue(key, value)

    ## Show any settings that have a value in the current profile but are not visible.
    @pyqtSlot(str)
    def showHiddenValues(self, category_id):
        category = Application.getInstance().getMachineManager().getActiveMachineInstance().getMachineDefinition().getSettingsCategory(category_id)
        for setting in category.getAllSettings():
            if not setting.isVisible() and self._active_profile.hasSettingValue(setting.getKey(), filter_defaults = False):
                setting.setVisible(True)
        category.visibleChanged.emit(category)

    ## Reload a clean copy of the currently selected profile.
    @pyqtSlot()
    def discardChanges(self):
        self._active_profile.setChangedSettings({})
        self._manager.setActiveProfile(self._manager.getActiveProfile(), force = True)

    ## Update the currently selected profile with the settings from the working profile and reselect it.
    @pyqtSlot()
    def updateProfile(self):
        changed_settings = copy.deepcopy(self._active_profile.getChangedSettings())
        self._manager.getActiveProfile().setChangedSettings(changed_settings)
        self._active_profile.setChangedSettings({})
        self._manager.setActiveProfile(self._manager.getActiveProfile(), force = True)

    def _onActiveProfileChanged(self):
        if self._active_profile:
            self._active_profile.settingValueChanged.disconnect(self._onSettingValuesChanged)

        self._active_profile = Application.getInstance().getMachineManager().getWorkingProfile()
        self.activeProfileChanged.emit()

        if self._active_profile:
            self._active_profile.settingValueChanged.connect(self._onSettingValuesChanged)
            self._onSettingValuesChanged()

    def _onSettingValuesChanged(self, setting = None):
        self._setting_values.update(self._active_profile.getAllSettingValues())
        self.settingValuesChanges.emit()

def createActiveProfileProxy(engine, script_engine):
    return ActiveProfileProxy()

