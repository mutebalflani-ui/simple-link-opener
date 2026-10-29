"""Tests for the .po compiler in build.py. Run with: python -B -m unittest discover tests"""

import gettext
import io
import pathlib
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from build import compilePo  # noqa: E402

HEADER = (
	'msgid ""\n'
	'msgstr ""\n'
	'"Content-Type: text/plain; charset=UTF-8\\n"\n'
	'"Plural-Forms: nplurals=2; plural=(n != 1);\\n"\n'
	"\n"
)


def load(poBody):
	return gettext.GNUTranslations(io.BytesIO(compilePo(HEADER + poBody)))


class CompilePoTests(unittest.TestCase):
	def test_plainEntry(self):
		catalog = load('msgid "Opening link"\nmsgstr "Abriendo enlace"\n')
		self.assertEqual(catalog.gettext("Opening link"), "Abriendo enlace")

	def test_multiLineEntry(self):
		catalog = load('msgid ""\n"One "\n"two"\nmsgstr ""\n"Uno "\n"dos"\n')
		self.assertEqual(catalog.gettext("One two"), "Uno dos")

	def test_untranslatedEntryLeftOut(self):
		catalog = load('msgid "Open"\nmsgstr ""\n')
		self.assertEqual(catalog.gettext("Open"), "Open")

	def test_fuzzyEntryLeftOut(self):
		catalog = load('#, fuzzy\nmsgid "Open"\nmsgstr "Cerrar"\n\nmsgid "Close"\nmsgstr "Cerrar"\n')
		self.assertEqual(catalog.gettext("Open"), "Open")
		self.assertEqual(catalog.gettext("Close"), "Cerrar")

	def test_obsoleteEntryLeftOut(self):
		catalog = load('#~ msgid "Old"\n#~ msgstr "Viejo"\n')
		self.assertEqual(catalog.gettext("Old"), "Old")

	def test_context(self):
		catalog = load('msgctxt "button"\nmsgid "Open"\nmsgstr "Abrir"\n')
		self.assertEqual(catalog.pgettext("button", "Open"), "Abrir")
		self.assertEqual(catalog.gettext("Open"), "Open")

	def test_plural(self):
		catalog = load(
			'msgid "{count} link"\nmsgid_plural "{count} links"\n'
			'msgstr[0] "{count} enlace"\nmsgstr[1] "{count} enlaces"\n'
		)
		self.assertEqual(catalog.ngettext("{count} link", "{count} links", 1), "{count} enlace")
		self.assertEqual(catalog.ngettext("{count} link", "{count} links", 3), "{count} enlaces")

	def test_unknownLineIsAnError(self):
		with self.assertRaises(ValueError):
			compilePo(HEADER + 'msgid "Open"\nmsgtsr "Abrir"\n')

	def test_spanishTranslationCompiles(self):
		poText = (ROOT / "addon" / "locale" / "es" / "LC_MESSAGES" / "nvda.po").read_text(encoding="utf-8")
		catalog = gettext.GNUTranslations(io.BytesIO(compilePo(poText)))
		self.assertEqual(catalog.gettext("Open {count} links?"), "¿Abrir {count} enlaces?")


if __name__ == "__main__":
	unittest.main()
