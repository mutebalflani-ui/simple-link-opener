# Finds web links in plain text.
# This module imports nothing from NVDA, so it can be tested with ordinary Python.

import re

# A link starts with http://, https:// or www. and runs until a space or a character that cannot be in a link.
# A www. link must not follow a letter, slash, dot, @ or hyphen, so the www. inside https://www.example.com
# or inside an email address is not counted as a second link.
_LINK_RE = re.compile(r"(?:\bhttps?://|(?<![\w/.@-])www\.)[^\s<>\"]+", re.IGNORECASE)

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


def findLinks(text, http=True, https=True, www=False):
	"""Returns the links in text whose kind is allowed, in the order they appear, without duplicates.
	Links starting with www. are returned with https:// in front (http:// when https links are turned off),
	so the browser can open them.
	"""
	links = []
	if not text:
		return links
	for match in _LINK_RE.finditer(text):
		link = _trimEnd(match.group())
		lowerLink = link.lower()
		if lowerLink.startswith("https://"):
			allowed = https and len(link) > len("https://")
		elif lowerLink.startswith("http://"):
			allowed = http and len(link) > len("http://")
		else:
			# Needs a dot after www., so a lone "www." in a sentence is not a link.
			allowed = www and "." in link[len("www."):]
			# Follows the https setting, so a site that only works over http can still be opened.
			link = ("https://" if https else "http://") + link
		if allowed and link not in links:
			links.append(link)
	return links
