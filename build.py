"""Packs the addon folder into an installable .nvda-addon file next to this script."""

import pathlib
import re
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
ADDON_DIR = ROOT / "addon"


def main():
	manifest = (ADDON_DIR / "manifest.ini").read_text(encoding="utf-8")
	name = re.search(r"^name\s*=\s*\"?([^\"\s]+)", manifest, re.MULTILINE).group(1)
	version = re.search(r"^version\s*=\s*\"?([^\"\s]+)", manifest, re.MULTILINE).group(1)
	outFile = ROOT / f"{name}-{version}.nvda-addon"
	with zipfile.ZipFile(outFile, "w", zipfile.ZIP_DEFLATED) as addonZip:
		for path in sorted(ADDON_DIR.rglob("*")):
			# Bytecode from local test runs would not match NVDA's Python, so leave it out.
			if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
				addonZip.write(path, path.relative_to(ADDON_DIR).as_posix())
	print(outFile)


if __name__ == "__main__":
	main()
