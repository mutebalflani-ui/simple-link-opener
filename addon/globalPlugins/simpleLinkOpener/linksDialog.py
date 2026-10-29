# The dialog that lists the links found in the clipboard when there is more than one.

import wx
import gui
from gui import guiHelper
import addonHandler

from .linkFinder import displayLink

addonHandler.initTranslation()

OPEN_AFTER_CLOSE_DELAY_MS = 300


class LinksDialog(wx.Dialog):
	"""Lists links. Enter opens the selected link; the "Open N links" button opens all of them.
	openLinks is called with the list of links to open, after the dialog has closed.
	"""

	# The dialog currently shown, so there is never more than one.
	instance = None

	@classmethod
	def show(cls, links, openLinks):
		if cls.instance:
			cls.instance._close()
		gui.mainFrame.prePopup()
		cls.instance = cls(gui.mainFrame, links, openLinks)
		cls.instance.CentreOnScreen()
		cls.instance.Show()
		cls.instance.Raise()
		cls.instance.linksList.SetFocus()
		gui.mainFrame.postPopup()

	def __init__(self, parent, links, openLinks):
		# Translators: Title of the dialog that lists the links found in the clipboard.
		super().__init__(parent, title=_("Links in clipboard"))
		self.links = links
		self.openLinks = openLinks
		self.closing = False

		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.linksList = sHelper.addLabeledControl(
			# Translators: Label of the list of links in the clipboard.
			_("&Links:"),
			wx.ListBox,
			# The list shows TeamTalk links without their passwords; the full links are opened.
			choices=[displayLink(link) for link in links],
			size=(550, 220),
		)

		buttons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: Button that opens the selected link.
		openButton = buttons.addButton(self, label=_("&Open"))
		# Translators: Button that opens every link in the list. {count} is the number of links.
		openAllButton = buttons.addButton(self, label=_("Open {count} links").format(count=len(links)))
		# Translators: Button that closes the dialog without opening anything.
		buttons.addButton(self, id=wx.ID_CANCEL, label=_("&Close"))
		sHelper.addDialogDismissButtons(buttons)

		mainSizer.Add(sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL | wx.EXPAND)
		self.SetSizer(mainSizer)
		mainSizer.Fit(self)

		openButton.Bind(wx.EVT_BUTTON, self.onOpenSelected)
		openAllButton.Bind(wx.EVT_BUTTON, self.onOpenAll)
		self.linksList.Bind(wx.EVT_LISTBOX_DCLICK, self.onOpenSelected)
		# Escape, Alt+F4 and the Close button all arrive here.
		self.Bind(wx.EVT_BUTTON, lambda evt: self._close(), id=wx.ID_CANCEL)
		self.Bind(wx.EVT_CHAR_HOOK, self.onCharHook)

		self.linksList.SetSelection(0)
		self.linksList.SetFocus()

	def onCharHook(self, evt):
		# A list box does not reliably pass Enter on to the dialog, so handle it here.
		if evt.GetKeyCode() in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and self.FindFocus() is self.linksList:
			self.onOpenSelected(evt)
		else:
			evt.Skip()

	def onOpenSelected(self, evt):
		index = self.linksList.GetSelection()
		if index == wx.NOT_FOUND:
			return
		self._closeAndOpen([self.links[index]])

	def onOpenAll(self, evt):
		self._closeAndOpen(self.links)

	def _closeAndOpen(self, links):
		# Destroy is deferred, so a quick second Enter could arrive before the dialog is gone.
		if self.closing:
			return
		self._close()
		# Wait until focus is back on the window behind the dialog,
		# otherwise that focus change cuts off the "Opening link" announcement.
		wx.CallLater(OPEN_AFTER_CLOSE_DELAY_MS, self.openLinks, links)

	def _close(self):
		self.closing = True
		LinksDialog.instance = None
		self.Destroy()
