# Finds web links and TeamTalk links in plain text.
# This module imports nothing from NVDA, so it can be tested with ordinary Python.

import re

# A link starts with http://, https://, tt:// or www. and runs until a space
# or a character that cannot be in a link.
# Every start listed here needs its own branch in findLinks, which treats any other match as a www. link.
# A www. link must not follow a letter, slash, dot, @ or hyphen, so the www. inside https://www.example.com
# or inside an email address is not counted as a second link.
_LINK_RE = re.compile(r"(?:\b(?:https?|tt)://|(?<![\w/.@-])www\.)[^\s<>\"]+", re.IGNORECASE)

# The values of the server and channel passwords inside a TeamTalk link.
_TT_PASSWORD_RE = re.compile(r"([?&](?:password|chanpasswd)=)[^&]*", re.IGNORECASE)

# Characters that usually end the sentence around a link rather than the link itself.
_TRAILING_PUNCTUATION = ".,;:!?'\"*،؛؟。、，！？…”’»"

# A closing bracket at the end is kept only when the link also contains the matching opening bracket,
# as in https://en.wikipedia.org/wiki/Python_(programming_language)
_CLOSING_BRACKETS = {")": "(", "]": "[", "}": "{"}


def _trimEnd(link):
	while link:
		last = link[-1]
		if last in _TRAILING_PUNCTUATION:
			link = link[:-1]
		elif last in _CLOSING_BRACKETS and link.count(last) > link.count(_CLOSING_BRACKETS[last]):
			link = link[:-1]
		else:
			break
	return link


def displayLink(link):
	"""Returns the link as it may be spoken, shown or logged: a TeamTalk link without its passwords."""
	if link.lower().startswith("tt://"):
		return _TT_PASSWORD_RE.sub(r"\1", link)
	return link


def findLinks(text, http=True, https=True, www=False, tt=False):
	"""Returns the links in text whose kind is allowed, in the order they appear, without duplicates.
	Links starting with tt:// are TeamTalk links, opened as they are by the TeamTalk client.
	Links starting with www. are returned with https:// in front (http:// when https links are turned off),
	so the browser can open them.
	"""
	links = []
	if not text:
		return links
	for match in _LINK_RE.finditer(text):
		link = match.group()
		lowerLink = link.lower()
		# A TeamTalk link that is the whole text was copied as a link, not as part of a sentence,
		# so its last character belongs to it: a password or channel name may end in punctuation.
		if not (lowerLink.startswith("tt://") and link == text.strip()):
			link = _trimEnd(link)
			lowerLink = link.lower()
		if lowerLink.startswith("https://"):
			allowed = https and len(link) > len("https://")
		elif lowerLink.startswith("http://"):
			allowed = http and len(link) > len("http://")
		elif lowerLink.startswith("tt://"):
			allowed = tt and len(link) > len("tt://")
		else:
			# Needs a dot after www., so a lone "www." in a sentence is not a link.
			allowed = www and "." in link[len("www."):]
			# Follows the https setting, so a site that only works over http can still be opened.
			link = ("https://" if https else "http://") + link
		if allowed and link not in links:
			links.append(link)
	return links
