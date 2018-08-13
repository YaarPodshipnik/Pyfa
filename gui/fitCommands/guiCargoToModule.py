import wx
from service.fit import Fit

import gui.mainFrame
from gui import globalEvents as GE
from gui.fitCommands.calc.fitSetCharge import FitSetChargeCommand
from gui.fitCommands.calc.fitReplaceModule import FitReplaceModuleCommand
from gui.fitCommands.calc.fitRemoveCargo import FitRemoveCargoCommand
from logbook import Logger
pyfalog = Logger(__name__)

class GuiCargoToModuleCommand(wx.Command):
    """
    Moves cargo to fitting window. Can either do a copy, move, or swap with current module
    If we try to copy/move into a spot with a non-empty module, we swap instead.
    To avoid redundancy in converting Cargo item, this function does the
    sanity checks as opposed to the GUI View. This is different than how the
    normal .swapModules() does things, which is mostly a blind swap.
    """

    def __init__(self, fitID, moduleIdx, cargoIdx, copy=False):
        wx.Command.__init__(self, True, "Module State Change")
        self.mainFrame = gui.mainFrame.MainFrame.getInstance()
        self.sFit = Fit.getInstance()
        self.fitID = fitID
        self.moduleIdx = moduleIdx
        self.cargoIdx = cargoIdx
        self.copy = copy
        self.internal_history = wx.CommandProcessor()

    def Do(self):
        sFit = Fit.getInstance()
        fit = sFit.getFit(self.fitID)
        module = fit.modules[self.moduleIdx]
        cargo = fit.cargo[self.cargoIdx]
        result = None

        # We're trying to move a charge from cargo to a slot. Use SetCharge command (don't respect move vs copy)
        if sFit.isAmmo(cargo.item.ID):
            result = self.internal_history.Submit(FitSetChargeCommand(self.fitID, [module], cargo.item.ID))
        else:

            pyfalog.debug("Moving cargo item to module for fit ID: {0}", self.fitID)

            self.addCmd = FitReplaceModuleCommand(self.fitID, module.modPosition, cargo.itemID)
            result = self.internal_history.Submit(self.addCmd)
            if not result:
                # module failed
                return False

            if not self.copy:
                self.removeCmd = FitRemoveCargoCommand(self.fitID, cargo.itemID)
                result = self.internal_history.Submit(self.removeCmd)

        if result:
            wx.PostEvent(self.mainFrame, GE.FitChanged(fitID=self.fitID))
        return result

    def Undo(self):
        for _ in self.internal_history.Commands:
            self.internal_history.Undo()
        wx.PostEvent(self.mainFrame, GE.FitChanged(fitID=self.fitID))
        return True