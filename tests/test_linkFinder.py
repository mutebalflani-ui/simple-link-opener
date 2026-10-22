"""Tests for linkFinder. Run with: python -B -m unittest discover tests"""

import pathlib
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "addon" / "globalPlugins" / "simpleLinkOpener"))

from linkFinder import findLinks  # noqa: E402


class FindLinksTests(unittest.TestCase):
	def test_emptyText(self):
		self.assertEqual(findLinks(""), [])
		self.assertEqual(findLinks(None), [])

	def test_noLinks(self):
		self.assertEqual(findLinks("Just some words, no address here."), [])

	def test_singleLink(self):
		self.assertEqual(findLinks("https://example.com"), ["https://example.com"])

	def test_linkInsideSentenceWithTrailingPeriod(self):
		self.assertEqual(findLinks("See https://example.com/page."), ["https://example.com/page"])

	def test_trailingPunctuation(self):
		self.assertEqual(findLinks("Links: https://a.com, http://b.org; done!"), ["https://a.com", "http://b.org"])

	def test_balancedParenthesesKept(self):
		link = "https://en.wikipedia.org/wiki/Python_(programming_language)"
		self.assertEqual(findLinks(f"({link})"), [link])

	def test_unbalancedClosingParenthesisRemoved(self):
		self.assertEqual(findLinks("(see https://example.com)"), ["https://example.com"])

	def test_queryStringKept(self):
		link = "https://www.youtube.com/watch?v=abc123&t=42s"
		self.assertEqual(findLinks(link), [link])

	def test_duplicatesRemovedInOrder(self):
		text = "https://b.com https://a.com https://b.com"
		self.assertEqual(findLinks(text), ["https://b.com", "https://a.com"])

	def test_caseInsensitiveScheme(self):
		self.assertEqual(findLinks("HTTPS://Example.com"), ["HTTPS://Example.com"])

	def test_httpUnchecked(self):
		text = "http://a.com https://b.com"
		self.assertEqual(findLinks(text, http=False), ["https://b.com"])

	def test_httpsUnchecked(self):
		text = "http://a.com https://b.com"
		self.assertEqual(findLinks(text, https=False), ["http://a.com"])

	def test_wwwOffByDefault(self):
		self.assertEqual(findLinks("Visit www.example.com today"), [])

	def test_wwwOn(self):
		self.assertEqual(findLinks("Visit www.example.com today", www=True), ["https://www.example.com"])

	def test_wwwInsideHttpsNotCountedTwice(self):
		self.assertEqual(findLinks("https://www.example.com", www=True), ["https://www.example.com"])

	def test_wwwInsideHttpsWithHttpsUnchecked(self):
		self.assertEqual(findLinks("https://www.example.com", https=False, www=True), [])

	def test_wwwInsideEmailIgnored(self):
		self.assertEqual(findLinks("mail me at muteb@www.example.com", www=True), [])

	def test_loneWwwIgnored(self):
		self.assertEqual(findLinks("the www. prefix", www=True), [])

	def test_schemeOnlyIgnored(self):
		self.assertEqual(findLinks("type https:// then the address"), [])

	def test_allUnchecked(self):
		self.assertEqual(findLinks("http://a.com https://b.com www.c.com", http=False, https=False, www=False), [])

	def test_linksOnSeparateLines(self):
		text = "first\r\nhttps://a.com\r\nhttps://b.com/x\n"
		self.assertEqual(findLinks(text), ["https://a.com", "https://b.com/x"])

	def test_nonAsciiTrailingPunctuation(self):
		self.assertEqual(findLinks("شاهد https://a.com، ثم"), ["https://a.com"])
		self.assertEqual(findLinks("https://b.com。"), ["https://b.com"])
		self.assertEqual(findLinks("“https://c.com”"), ["https://c.com"])

	def test_wwwFollowsHttpsSetting(self):
		self.assertEqual(findLinks("www.example.com", https=False, www=True), ["http://www.example.com"])

	def test_linkInAngleBrackets(self):
		self.assertEqual(findLinks("<https://example.com>"), ["https://example.com"])


if __name__ == "__main__":
	unittest.main()
