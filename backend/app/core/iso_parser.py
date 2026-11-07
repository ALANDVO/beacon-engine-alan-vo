"""ISO image parsing utilities for Windows ISO metadata extraction."""

import asyncio
import logging
import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


@dataclass
class ISOMetadata:
    """Extracted metadata from a Windows ISO."""
    version: Optional[str] = None
    edition: Optional[str] = None
    build_number: Optional[int] = None
    architecture: Optional[str] = None
    language: Optional[str] = None


class ISOParserError(Exception):
    """Raised when ISO parsing fails."""
    pass


async def validate_iso_file(iso_path: str) -> bool:
    """
    Validate that a file is a valid ISO 9660 or UDF image.

    Checks for ISO 9660 Primary Volume Descriptor (CD001) or
    UDF Beginning Extended Area Descriptor (BEA01) at sector 16 (offset 32768).
    """
    try:
        with open(iso_path, "rb") as f:
            f.seek(32768)
            signature = f.read(5)
            return signature in (b"CD001", b"BEA01")
    except (OSError, IOError):
        return False


async def extract_iso_metadata(iso_path: str) -> ISOMetadata:
    """
    Extract metadata from a Windows ISO file.

    Uses 7z to extract boot.wim/install.wim and wiminfo to parse metadata.
    Falls back to direct XML parsing if wiminfo is unavailable.
    """
    metadata = ISOMetadata()

    # Try to find and extract WIM files from the ISO
    wim_path = await _find_wim_in_iso(iso_path)
    if not wim_path:
        logger.warning("No WIM file found in ISO: %s", iso_path)
        raise ISOParserError("No WIM file found in ISO")

    # Parse WIM metadata
    wim_metadata = await _parse_wim_metadata(wim_path)
    metadata.version = wim_metadata.version
    metadata.edition = wim_metadata.edition
    metadata.build_number = wim_metadata.build_number
    metadata.architecture = wim_metadata.architecture
    metadata.language = wim_metadata.language

    logger.info("Extracted ISO metadata: version=%s edition=%s build=%s arch=%s lang=%s",
                metadata.version, metadata.edition, metadata.build_number,
                metadata.architecture, metadata.language)
    return metadata


async def _find_wim_in_iso(iso_path: str) -> Optional[str]:
    """Find and extract a WIM file (boot.wim or install.wim) from the ISO."""
    import shutil

    # Check if 7z is available
    if not shutil.which("7z"):
        logger.warning("7z not found, cannot extract WIM from ISO")
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        # List ISO contents to find WIM files
        try:
            result = await asyncio.create_subprocess_exec(
                "7z", "l", iso_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()
            if result.returncode != 0:
                logger.warning("Failed to list ISO contents: %s", stderr.decode())
                return None

            output = stdout.decode()
            wim_files = []
            for line in output.splitlines():
                if ".wim" in line.lower() and ("boot.wim" in line.lower() or "install.wim" in line.lower()):
                    # Extract filename from 7z output (last column)
                    parts = line.split()
                    if parts:
                        wim_files.append(parts[-1])

            # Prefer install.wim over boot.wim
            wim_files.sort(key=lambda x: 0 if "install.wim" in x.lower() else 1)

            if not wim_files:
                logger.warning("No boot.wim or install.wim found in ISO")
                return None

            # Extract the first WIM file found
            wim_name = wim_files[0]
            extract_dir = os.path.join(tmpdir, "wim")
            os.makedirs(extract_dir, exist_ok=True)

            result = await asyncio.create_subprocess_exec(
                "7z", "x", iso_path, f"-o{extract_dir}", wim_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()
            if result.returncode != 0:
                logger.warning("Failed to extract WIM from ISO: %s", stderr.decode())
                return None

            extracted_path = os.path.join(extract_dir, wim_name)
            if os.path.exists(extracted_path):
                return extracted_path

        except Exception as e:
            logger.warning("Error extracting WIM from ISO: %s", e)
            return None

    return None


async def _parse_wim_metadata(wim_path: str) -> ISOMetadata:
    """Parse metadata from a WIM file using wiminfo or XML fallback."""
    # Try wiminfo first (part of wimlib)
    import shutil

    if shutil.which("wiminfo"):
        try:
            result = await asyncio.create_subprocess_exec(
                "wiminfo", wim_path, "1",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()
            if result.returncode == 0:
                return _parse_wiminfo_output(stdout.decode())
        except Exception as e:
            logger.warning("wiminfo failed, falling back to XML parsing: %s", e)

    # Fallback to XML parsing using 7z
    return await _parse_wim_xml(wim_path)


def _parse_wiminfo_output(output: str) -> ISOMetadata:
    """Parse wiminfo command output."""
    metadata = ISOMetadata()

    # Parse version (e.g., "10.0.26100")
    version_match = re.search(r"Version\s*:\s*(\d+\.\d+\.\d+)", output)
    if version_match:
        version_str = version_match.group(1)
        metadata.version, metadata.build_number = parse_version_string(version_str)

    # Parse edition (e.g., "Windows 11 Pro")
    edition_match = re.search(r"Edition\s*:\s*(.+)", output)
    if edition_match:
        metadata.edition = edition_match.group(1).strip()

    # Parse architecture (e.g., "x64" or "arm64")
    arch_match = re.search(r"Architecture\s*:\s*(.+)", output)
    if arch_match:
        metadata.architecture = arch_match.group(1).strip()

    # Parse language (e.g., "en-US")
    lang_match = re.search(r"Language\s*:\s*(.+)", output)
    if lang_match:
        metadata.language = lang_match.group(1).strip()

    return metadata


async def _parse_wim_xml(wim_path: str) -> ISOMetadata:
    """Extract and parse WIM XML metadata using 7z."""
    import shutil

    if not shutil.which("7z"):
        logger.warning("7z not found, cannot parse WIM XML")
        return ISOMetadata()

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Extract [1].xml from WIM (index 1 metadata)
            result = await asyncio.create_subprocess_exec(
                "7z", "x", wim_path, f"-o{tmpdir}", "[1].xml",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await result.communicate()
            if result.returncode != 0:
                logger.warning("Failed to extract WIM XML: %s", stderr.decode())
                return ISOMetadata()

            xml_path = os.path.join(tmpdir, "[1].xml")
            if not os.path.exists(xml_path):
                logger.warning("WIM XML not found at expected path")
                return ISOMetadata()

            tree = ET.parse(xml_path)
            root = tree.getroot()

            metadata = ISOMetadata()

            # Parse version
            version_elem = root.find(".//VERSION")
            if version_elem is not None and version_elem.text:
                metadata.version, metadata.build_number = parse_version_string(version_elem.text)

            # Parse edition
            edition_elem = root.find(".//EDITION")
            if edition_elem is not None and edition_elem.text:
                metadata.edition = edition_elem.text.strip()

            # Parse architecture
            arch_elem = root.find(".//ARCHITECTURE")
            if arch_elem is not None and arch_elem.text:
                metadata.architecture = arch_elem.text.strip()

            # Parse language
            lang_elem = root.find(".//LANGUAGE")
            if lang_elem is not None and lang_elem.text:
                metadata.language = lang_elem.text.strip()

            return metadata

        except Exception as e:
            logger.warning("Error parsing WIM XML: %s", e)
            return ISOMetadata()


def parse_version_string(version: str) -> tuple[str | None, int | None]:
    """
    Parse Windows version string to marketing version and build number.

    Examples:
        "10.0.26100" -> ("24H2", 26100)
        "10.0.23500" -> ("23H2", 23500)
        "10.0.22621" -> ("22H2", 22621)
        "10.0.19045" -> ("22H2", 19045)
        "10.0.19044" -> ("21H2", 19044)
    """
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not match:
        return None, None

    major, minor, build = map(int, match.groups())

    if major != 10:
        return None, build

    # Windows 11 versions
    if build >= 26100:
        return "24H2", build
    if build >= 23500:
        return "23H2", build
    if build >= 22621:
        return "22H2", build

    # Windows 10 versions
    if build >= 19045:
        return "22H2", build
    if build >= 19044:
        return "21H2", build
    if build >= 19043:
        return "21H1", build
    if build >= 19042:
        return "20H2", build
    if build >= 19041:
        return "2004", build

    return None, build
