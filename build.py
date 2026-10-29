"""Packs the addon folder into an installable .nvda-addon file next to this script."""

import ast
import pathlib
import re
import struct
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
ADDON_DIR = ROOT / "addon"


def compilePo(poText):
	"""Returns the contents of the .mo file for a .po file, so no gettext tools are needed."""
	# Each entry maps its keywords (msgctxt, msgid, msgid_plural, msgstr, msgstr[0]...) to their text.
	entries = []
	entry = field = None
	fuzzy = False
	for line in poText.splitlines():
		line = line.strip()
		if line.startswith("#,"):
			fuzzy = fuzzy or "fuzzy" in line
		if not line or line.startswith("#"):
			# Obsolete entries start with #~ and are left out with the other comments.
			continue
		if line.startswith('"'):
			if field is None:
				raise ValueError(f"Text without a keyword in .po file: {line}")
			entry[field] += ast.literal_eval(line)
			continue
		keyword, _sep, rest = line.partition(" ")
		if not re.fullmatch(r"msgctxt|msgid|msgid_plural|msgstr(\[\d+\])?", keyword):
			raise ValueError(f"Unexpected line in .po file: {line}")
		if keyword == "msgctxt" or (keyword == "msgid" and (entry is None or "msgid" in entry)):
			entry = {"fuzzy": fuzzy}
			fuzzy = False
			entries.append(entry)
		if entry is None:
			raise ValueError(f"Unexpected line in .po file: {line}")
		field = keyword
		entry[field] = ast.literal_eval(rest)

	messages = {}
	for entry in entries:
		key = entry.get("msgid")
		if key is None:
			raise ValueError(f"Entry without msgid in .po file: {entry}")
		# Fuzzy entries are not reviewed yet, so they stay out; the header (empty msgid) stays in.
		if entry["fuzzy"] and key:
			continue
		if "msgid_plural" in entry:
			forms = sorted((k for k in entry if k.startswith("msgstr[")), key=lambda k: int(k[7:-1]))
			value = "\0".join(entry[k] for k in forms)
			translated = bool(forms) and all(entry[k] for k in forms)
			key += "\0" + entry["msgid_plural"]
		else:
			value = entry.get("msgstr", "")
			translated = bool(value)
		# Untranslated entries stay out, so NVDA falls back to English for them.
		if not translated:
			continue
		if "msgctxt" in entry:
			key = entry["msgctxt"] + "\x04" + key
		messages[key] = value
	ids = sorted(messages, key=lambda k: k.encode("utf-8"))
	idData = b"".join(k.encode("utf-8") + b"\0" for k in ids)
	strData = b"".join(messages[k].encode("utf-8") + b"\0" for k in ids)
	tableSize = 28
	idStart = tableSize + 16 * len(ids)
	strStart = idStart + len(idData)
	idTable, strTable = [], []
	offset = 0
	for k in ids:
		length = len(k.encode("utf-8"))
		idTable += [length, idStart + offset]
		offset += length + 1
	offset = 0
	for k in ids:
		length = len(messages[k].encode("utf-8"))
		strTable += [length, strStart + offset]
		offset += length + 1
	header = struct.pack("<7I", 0x950412DE, 0, len(ids), tableSize, tableSize + 8 * len(ids), 0, 0)
	return header + struct.pack(f"<{len(idTable)}I", *idTable) + struct.pack(f"<{len(strTable)}I", *strTable) + idData + strData


def main():
	manifest = (ADDON_DIR / "manifest.ini").read_text(encoding="utf-8")
	name = re.search(r"^name\s*=\s*\"?([^\"\s]+)", manifest, re.MULTILINE).group(1)
	version = re.search(r"^version\s*=\s*\"?([^\"\s]+)", manifest, re.MULTILINE).group(1)
	outFile = ROOT / f"{name}-{version}.nvda-addon"
	with zipfile.ZipFile(outFile, "w", zipfile.ZIP_DEFLATED) as addonZip:
		for path in sorted(ADDON_DIR.rglob("*")):
			# Bytecode from local test runs would not match NVDA's Python, so leave it out.
			# A .mo file left by a translation editor may be out of date, so it is always made from the .po.
			if path.is_file() and "__pycache__" not in path.parts and path.suffix not in (".pyc", ".mo"):
				addonZip.write(path, path.relative_to(ADDON_DIR).as_posix())
				# NVDA reads translations from nvda.mo, which is made from nvda.po here.
				if path.suffix == ".po":
					moPath = path.with_suffix(".mo").relative_to(ADDON_DIR).as_posix()
					addonZip.writestr(moPath, compilePo(path.read_text(encoding="utf-8")))
	print(outFile)


if __name__ == "__main__":
	main()
