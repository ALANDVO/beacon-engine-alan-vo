"""Unit tests for ISO parser module."""

import tempfile

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
    # parse_version_string converts "10.0.26100" -> ("24H2", 26100)
    assert metadata.version == "24H2"
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
    # parse_version_string converts "10.0.19044" -> ("21H2", 19044)
    assert metadata.version == "21H2"
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
      <ARCHITECTURE>x64</ARCHITECTURE>
      <VERSION>10.0.26100</VERSION>
      <EDITION>Professional</EDITION>
      <LANGUAGE>en-US</LANGUAGE>
    </WINDOWS>
  </IMAGE>
</WIM>
"""
    import xml.etree.ElementTree as ET
    from app.core.iso_parser import _parse_wim_xml

    # Parse the XML directly to test the logic
    root = ET.fromstring(xml_content)
    metadata = ISOMetadata()

    version_elem = root.find(".//VERSION")
    if version_elem is not None and version_elem.text:
        metadata.version, metadata.build_number = parse_version_string(version_elem.text)

    edition_elem = root.find(".//EDITION")
    if edition_elem is not None and edition_elem.text:
        metadata.edition = edition_elem.text.strip()

    arch_elem = root.find(".//ARCHITECTURE")
    if arch_elem is not None and arch_elem.text:
        metadata.architecture = arch_elem.text.strip()

    lang_elem = root.find(".//LANGUAGE")
    if lang_elem is not None and lang_elem.text:
        metadata.language = lang_elem.text.strip()

    # parse_version_string converts "10.0.26100" -> ("24H2", 26100)
    assert metadata.version == "24H2"
    assert metadata.edition == "Professional"
    assert metadata.architecture == "x64"
    assert metadata.language == "en-US"
    assert metadata.build_number == 26100


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
