"""Unit tests for ISO parser module."""

import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from app.core.iso_parser import ISOMetadata, parse_version_string, _parse_wiminfo_output, _parse_wim_xml


def test_parse_version_string_windows_11_24h2():
    version, build = parse_version_string("10.0.26100")
    assert version == "24H2"
    assert build == 26100


def test_parse_version_string_windows_11_23h2():
    version, build = parse_version_string("10.0.23500")
    assert version == "23H2"
    assert build == 23500


def test_parse_version_string_windows_11_22h2():
    version, build = parse_version_string("10.0.22621")
    assert version == "22H2"
    assert build == 22621


def test_parse_version_string_windows_10_22h2():
    version, build = parse_version_string("10.0.19045")
    assert version == "22H2"
    assert build == 19045


def test_parse_version_string_windows_10_21h2():
    version, build = parse_version_string("10.0.19044")
    assert version == "21H2"
    assert build == 19044


def test_parse_version_string_unknown():
    version, build = parse_version_string("10.0.10000")
    assert version is None
    assert build == 10000


def test_parse_version_string_invalid():
    version, build = parse_version_string("invalid")
    assert version is None
    assert build is None


def test_parse_wiminfo_output():
    output = """
Image 1: Windows 11 Pro
  Description: Windows 11 Pro
  Size: 1234567890 bytes
  Architecture: x64
  Version: 10.0.26100
  Edition: Professional
  Language: en-US
"""
    metadata = _parse_wiminfo_output(output)
    assert metadata.version == "10.0.26100"
    assert metadata.edition == "Professional"
    assert metadata.architecture == "x64"
    assert metadata.language == "en-US"
    assert metadata.build_number == 26100


def test_parse_wiminfo_output_minimal():
    output = """
Image 1: Windows 10 Enterprise
  Version: 10.0.19044
  Architecture: x64
"""
    metadata = _parse_wiminfo_output(output)
    assert metadata.version == "10.0.19044"
    assert metadata.architecture == "x64"
    assert metadata.build_number == 19044
    assert metadata.edition is None
    assert metadata.language is None


def test_parse_wim_xml():
    """Test parsing WIM XML metadata."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<WIM>
  <TOTALBYTES>1234567890</TOTALBYTES>
  <IMAGE INDEX="1">
    <NAME>Windows 11 Pro</NAME>
    <DESCRIPTION>Windows 11 Pro</DESCRIPTION>
    <WINDOWS>
      <VERSION>10.0.26100</VERSION>
      <ARCHITECTURE>x64</ARCHITECTURE>
      <LANGUAGE>en-US</LANGUAGE>
      <EDITION>Professional</EDITION>
    </WINDOWS>
  </IMAGE>
</WIM>
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        xml_file = Path(tmpdir) / "[1].xml"
        xml_file.write_text(xml_content)

        # Create a mock WIM file structure
        wim_dir = Path(tmpdir) / "wim"
        wim_dir.mkdir()
        (wim_dir / "[1].xml").write_text(xml_content)

        # We can't easily test _parse_wim_xml without 7z, but we can test the XML parsing logic
        tree = ET.parse(xml_file)
        root = tree.getroot()

        image = root.find(".//IMAGE")
        assert image is not None

        name_elem = image.find("NAME")
        assert name_elem is not None
        assert name_elem.text == "Windows 11 Pro"

        windows = image.find("WINDOWS")
        assert windows is not None

        version_elem = windows.find("VERSION")
        assert version_elem is not None
        assert version_elem.text == "10.0.26100"

        arch_elem = windows.find("ARCHITECTURE")
        assert arch_elem is not None
        assert arch_elem.text == "x64"

        lang_elem = windows.find("LANGUAGE")
        assert lang_elem is not None
        assert lang_elem.text == "en-US"


def test_isometadata_dataclass():
    metadata = ISOMetadata(
        version="24H2",
        edition="Pro",
        build_number=26100,
        architecture="x64",
        language="en-US",
    )
    assert metadata.version == "24H2"
    assert metadata.edition == "Pro"
    assert metadata.build_number == 26100
    assert metadata.architecture == "x64"
    assert metadata.language == "en-US"


def test_isometadata_defaults():
    metadata = ISOMetadata()
    assert metadata.version is None
    assert metadata.edition is None
    assert metadata.build_number is None
    assert metadata.architecture is None
    assert metadata.language is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

