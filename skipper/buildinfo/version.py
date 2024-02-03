import os

if "RELEASE_VERSION" in os.environ:
  import re
  release_version = os.environ["RELEASE_VERSION"]
  match = re.match(r"([^\.]+)\.([^\.]+)\.([^\.\-]+)(-.+)?", release_version)
  if match is None:
    raise AssertionError(f"bad RELEASE_VERSION env var {release_version}")
  
  major_version = match.group(1)
  minor_version = match.group(2)
  patch_version = match.group(3)
  suffix_version = match.group(4)
  if suffix_version is None:
    suffix_version = ""
else:
  major_version = "2"
  minor_version = "1"
  patch_version = "0"
  suffix_version = "-beta"


major_version_string = f"{major_version}{suffix_version}"
minor_version_string = f"{major_version}.{minor_version}{suffix_version}"
patch_version_string = f"{major_version}.{minor_version}.{patch_version}{suffix_version}"

version_string = patch_version_string
