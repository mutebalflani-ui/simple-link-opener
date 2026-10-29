# Simple Link Opener: opens the links in the clipboard in the default browser with one gesture.
# Copyright (C) 2026 Muteb Almarri <mutebalflani@gmail.com>

import os

import wx
import api
import config
import globalPluginHandler
import globalVars
import ui
from gui import guiHelper
from gui.settingsDialogs import NVDASettingsDialog, SettingsPanel
from logHandler import log
from scriptHandler import getLastScriptRepeatCount, script
import addonHandler

from .linkFinder import displayLink, findLinks
from .linksDialog import LinksDialog

addonHandler.initTranslation()

# One row per kind of link: the findLinks argument that allows it, its name in the configuration,
# whether it is opened by default, and the label of its checkbox in the settings.
# The settings, the checkboxes and the search for links all follow this table.
LINK_KINDS = (
	# Translators: Checkbox for links that start with http://
	("http", "openHttp", True, _("Links starting with &http://")),
	# Translators: Checkbox for links that start with https://
	("https", "openHttps", True, _("Links starting with http&s://")),
	# Translators: Checkbox for links that start with www. without http:// or https:// in front.
	("www", "openWww", False, _("Links starting with &www., such as www.example.com")),
	# Translators: Checkbox for TeamTalk links, which start with tt://
	("tt", "openTt", False, _("&TeamTalk links starting with tt://")),
)

config.conf.spec["simpleLinkOpener"] = {
	confKey: f"boolean(default={default})" for _kind, confKey, default, _label in LINK_KINDS
}

# Pause between links when opening several, so a browser that is still starting up receives every one.
OPEN_DELAY_MS = 400

# Opening more links than this asks for confirmation first.
CONFIRM_OVER_LINKS = 10


def _openLink(link):
	try:
		# Hands the link to Windows, which opens it in the default browser.
		os.startfile(link)
	except OSError:
		log.error(f"Could not open {displayLink(link)}", exc_info=True)
		# Translators: Announced when a link could not be opened. {link} is the link.
		ui.message(_("Could not open {link}").format(link=displayLink(link)))


def openLinks(links):
	if len(links) > CONFIRM_OVER_LINKS:
		answer = wx.MessageBox(
			# Translators: Asks before opening many links. {count} is the number of links.
			_("Open {count} links?").format(count=len(links)),
			# Translators: Title of the question that asks before opening many links.
			_("Simple Link Opener"),
			wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
		)
		if answer != wx.YES:
			return
	if len(links) == 1:
		# Translators: Announced when one link is opened.
		ui.message(_("Opening link"))
	else:
		# Translators: Announced when several links are opened. {count} is the number of links.
		ui.message(_("Opening {count} links").format(count=len(links)))
	# Even the first link waits a moment, so the browser taking focus does not cut off the announcement.
	for index, link in enumerate(links, start=1):
		wx.CallLater(index * OPEN_DELAY_MS, _openLink, link)


def getClipboardLinks(allKinds=False):
	try:
		text = api.getClipData()
	except Exception:
		# The clipboard is empty or holds something other than text.
		log.debugWarning("No text in the clipboard", exc_info=True)
		return []
	conf = config.conf["simpleLinkOpener"]
	return findLinks(text, **{kind: allKinds or conf[confKey] for kind, confKey, _default, _label in LINK_KINDS})


def disableInSecureMode(decoratedCls):
	if globalVars.appArgs.secure:
		return globalPluginHandler.GlobalPlugin
	return decoratedCls


@disableInSecureMode
class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	# Translators: Category of the add-on's command in the Input gestures dialog.
	scriptCategory = _("Simple Link Opener")

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		NVDASettingsDialog.categoryClasses.append(SimpleLinkOpenerPanel)

	def terminate(self):
		NVDASettingsDialog.categoryClasses.remove(SimpleLinkOpenerPanel)
		super().terminate()

	@script(
		# Translators: Describes the command in the Input gestures dialog.
		description=_(
			"Pressed once, says the link in the clipboard, or how many links there are. "
			"Pressed twice, opens the link, "
			"or shows a list to open one or all of the links."
		),
	)
	def script_openClipboardLinks(self, gesture):
		repeatCount = getLastScriptRepeatCount()
		if repeatCount > 1:
			# A third quick press would open the links a second time.
			return
		links = getClipboardLinks()
		if not links:
			if getClipboardLinks(allKinds=True):
				# Translators: Announced when the clipboard has links, but their kind is turned off in the settings.
				ui.message(_("The links in the clipboard are of a kind turned off in the settings"))
			else:
				# Translators: Announced when the clipboard has no link to open.
				ui.message(_("No link in clipboard"))
		elif repeatCount == 0:
			if len(links) == 1:
				ui.message(displayLink(links[0]))
			else:
				# Translators: Announced when the clipboard has several links. {count} is the number of links.
				ui.message(_("{count} links").format(count=len(links)))
		elif len(links) == 1:
			openLinks(links)
		else:
			LinksDialog.show(links, openLinks)


class SimpleLinkOpenerPanel(SettingsPanel):
	# Translators: Title of the add-on's panel in NVDA settings.
	title = _("Simple Link Opener")

	def makeSettings(self, settingsSizer):
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		conf = config.conf["simpleLinkOpener"]

		# Translators: Label of the group of checkboxes that choose which kinds of links are opened.
		groupSizer = wx.StaticBoxSizer(wx.VERTICAL, self, label=_("Kinds of links to open"))
		groupBox = groupSizer.GetStaticBox()
		group = guiHelper.BoxSizerHelper(self, sizer=groupSizer)
		sHelper.addItem(group)

		# The checkbox of each kind of link, by its name in the configuration.
		self.checkBoxes = {}
		for _kind, confKey, _default, label in LINK_KINDS:
			checkBox = wx.CheckBox(groupBox, label=label)
			checkBox.SetValue(conf[confKey])
			group.addItem(checkBox)
			self.checkBoxes[confKey] = checkBox

	def onSave(self):
		conf = config.conf["simpleLinkOpener"]
		for confKey, checkBox in self.checkBoxes.items():
			conf[confKey] = checkBox.IsChecked()
