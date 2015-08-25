# Copyright (c) 2015 Ultimaker B.V.
# Uranium is released under the terms of the AGPLv3 or higher.

import configparser

from UM.Resources import Resources
from UM.Settings import SettingsError
from UM.Logger import Logger

from UM.Settings.MachineSettings import MachineSettings

class MachineInstance():
    MachineInstanceVersion = 1

    def __init__(self, machine_manager, **kwargs):
        self._machine_manager = machine_manager

        self._name = kwargs.get("name", "")
        self._machine_definition = kwargs.get("definition", None)
        self._machine_setting_overrides = {}

    def getName(self):
        return self._name

    def setName(self, name):
        if name != self._name:
            self._name = name

    def getDefinition(self):
        return self._machine_definition

    def setMachineSetting(self, setting, value):
        if not self._machine_definition.isMachineSetting(setting):
            Logger.log("w", "Tried to override setting %s that is not a machine setting", setting)
            return

        self._machine_setting_overrides[setting] = value

    def getMachineSetting(self, setting):
        if not self._machine_definition.isMachineSetting(setting):
            return

        if setting in self._machine_setting_overrides:
            return self._machine_setting_overrides[setting]

        return self._machine_definition.getSetting(setting).getDefault()

    def loadFromFile(self, path):
        config = configparser.ConfigParser()
        config.read(path, "utf-8")

        if not config.has_section("general"):
            raise SettingsError.InvalidFileError(path)

        if not config.has_option("general", "version"):
            raise SettingsError.InvalidFileError(path)

        if not config.has_option("general", "name") or not config.has_option("general", "type"):
            raise SettingsError.InvalidFileError(path)

        if int(config.get("general", "version")) != self.MachineInstanceVersion:
            raise SettingsError.InvalidVersionError(path)

        type_name = config.get("general", "type")
        variant_name = config.get("general", "variant", fallback = "")

        self._machine_definition = self._machine_manager.findMachineDefinition(type_name, variant_name)

        self._name = config.get("general", "name")

        for key, value in config["machine_settings"].items():
            self._machine_setting_overrides[key] = value

    def saveToFile(self, path):
        config = configparser.ConfigParser()

        config.add_section("general")
        config["general"]["name"] = self._name
        config["general"]["type"] = self._machine_definition.getId()
        config["general"]["version"] = str(self.MachineInstanceVersion)
        config["general"]["variant"] = self._machine_definition.getVariantName()

        config.add_section("machine_settings")
        for key, value in self._machine_setting_overrides:
            config["machine_settings"][key] = str(value)

        with open(path, "wt", -1, "utf-8") as f:
            config.write(f)