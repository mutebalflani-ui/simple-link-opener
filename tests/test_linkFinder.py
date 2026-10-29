"""Tests for linkFinder. Run with: python -B -m unittest discover tests"""

import pathlib
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "addon" / "globalPlugins" / "simpleLinkOpener"))

from linkFinder import displayLink, findLinks  # noqa: E402


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

	def test_ttLinkNeedsTtSetting(self):
		link = "tt://example.com?tcpport=10333&udpport=10333&encrypted=0&username=guest&password=guest&channel=%2F"
		self.assertEqual(findLinks(link), [])
		self.assertEqual(findLinks("Join " + link + " now", tt=True), [link])
		self.assertEqual(findLinks("https://a.com " + link, https=False, tt=True), [link])

	def test_ttLinkEdgeCases(self):
		self.assertEqual(findLinks("tt://", tt=True), [])
		self.assertEqual(findLinks("Type tt:// first.", tt=True), [])
		self.assertEqual(findLinks("TT://Example.com?tcpport=1", tt=True), ["TT://Example.com?tcpport=1"])
		# Letters before tt:// make it part of another word, not a TeamTalk link.
		self.assertEqual(findLinks("att://example.com", tt=True), [])

	def test_ttLinkAloneKeepsItsLastCharacter(self):
		link = "tt://example.com?tcpport=10333&username=me&password=secret!"
		self.assertEqual(findLinks(link + "\r\n", tt=True), [link])
		self.assertEqual(findLinks("Join " + link, tt=True), [link[:-1]])
		self.assertEqual(findLinks("(tt://example.com?tcpport=10333).", tt=True), ["tt://example.com?tcpport=10333"])

	def test_displayLinkHidesTtPasswords(self):
		link = "TT://example.com?tcpport=10333&username=me&Password=secret&channel=%2F&chanpasswd=door"
		self.assertEqual(
			displayLink(link),
			"TT://example.com?tcpport=10333&username=me&Password=&channel=%2F&chanpasswd=",
		)
		self.assertEqual(displayLink("https://example.com/?password=x"), "https://example.com/?password=x")

	def test_linkInAngleBrackets(self):
		self.assertEqual(findLinks("<https://example.com>"), ["https://example.com"])


if __name__ == "__main__":
	unittest.main()
