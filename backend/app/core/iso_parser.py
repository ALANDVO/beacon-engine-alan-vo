"""ISO image parsing utilities for Windows ISO metadata extraction."""

import asyncio
import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


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
        raise ISOParserError("No WIM file found in ISO")

    # Parse WIM metadata
    wim_metadata = await _parse_wim_metadata(wim_path)
    metadata.version = wim_metadata.version
    metadata.edition = wim_metadata.edition
    metadata.build_number = wim_metadata.build_number
    metadata.architecture = wim_metadata.architecture
    metadata.language = wim_metadata.language

    return metadata


async def _find_wim_in_iso(iso_path: str) -> Optional[str]:
    """Find and extract a WIM file (boot.wim or install.wim) from the ISO."""
    # List ISO contents to find WIM files
    try:
        result = await asyncio.create_subprocess_exec(
            "7z", "l", iso_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await result.communicate()
        if result.returncode != 0:
            return None

        output = stdout.decode("utf-8", errors="ignore")

        # Look for boot.wim or install.wim in sources directory
        wim_files = []
        for line in output.splitlines():
            if "boot.wim" in line or "install.wim" in line:
                # Extract the path from 7z output
                parts = line.split()
                if len(parts) >= 6:
                    wim_path = " ".join(parts[5:])
                    wim_files.append(wim_path)

        if not wim_files:
            return None

        # Prefer install.wim over boot.wim as it has more complete metadata
        wim_files.sort(key=lambda x: 0 if "install.wim" in x else 1)
        target_wim = wim_files[0]

        # Extract the WIM file
        with tempfile.TemporaryDirectory() as tmpdir:
            extract_dir = Path(tmpdir) / "extracted"
            result = await asyncio.create_subprocess_exec(
                "7z", "x", iso_path, f"-o{extract_dir}", target_wim,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.communicate()

            if result.returncode != 0:
                return None

            # Find the extracted WIM
            extracted_wim = extract_dir / target_wim
            if extracted_wim.exists():
                # Copy to a stable location for parsing
                stable_path = Path(tmpdir) / Path(target_wim).name
                extracted_wim.rename(stable_path)
                return str(stable_path)

    except FileNotFoundError:
        # 7z not available
        pass
    except Exception:
        pass

    return None


async def _parse_wim_metadata(wim_path: str) -> ISOMetadata:
    """Parse metadata from a WIM file using wiminfo or XML fallback."""
    metadata = ISOMetadata()

    # Try wiminfo first
    try:
        result = await asyncio.create_subprocess_exec(
            "wiminfo", wim_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await result.communicate()
        if result.returncode == 0:
            return _parse_wiminfo_output(stdout.decode("utf-8", errors="ignore"))
    except FileNotFoundError:
        pass

    # Fallback: extract and parse WIM XML metadata
    try:
        return await _parse_wim_xml(wim_path)
    except Exception:
        pass

    return metadata


def _parse_wiminfo_output(output: str) -> ISOMetadata:
    """Parse wiminfo command output."""
    metadata = ISOMetadata()

    # Example wiminfo output:
    # Image 1: Windows 11 Pro
    #   Description: Windows 11 Pro
    #   Size: 1234567890 bytes
    #   Architecture: x64
    #   Version: 10.0.26100
    #   Edition: Professional
    #   Language: en-US

    lines = output.splitlines()
    for line in lines:
        line = line.strip()
        if line.startswith("Version:") or line.startswith("  Version:"):
            metadata.version = line.split(":", 1)[1].strip()
        elif line.startswith("Edition:") or line.startswith("  Edition:"):
            metadata.edition = line.split(":", 1)[1].strip()
        elif line.startswith("Architecture:") or line.startswith("  Architecture:"):
            metadata.architecture = line.split(":", 1)[1].strip()
        elif line.startswith("Language:") or line.startswith("  Language:"):
            metadata.language = line.split(":", 1)[1].strip()
        # Try to extract build number from version
        if metadata.version and metadata.build_number is None:
            match = re.search(r"(\d{5,})", metadata.version)
            if match:
                metadata.build_number = int(match.group(1))

    return metadata


async def _parse_wim_xml(wim_path: str) -> ISOMetadata:
    """Extract and parse WIM XML metadata using 7z."""
    metadata = ISOMetadata()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Extract [1].xml from WIM (contains image metadata)
        result = await asyncio.create_subprocess_exec(
            "7z", "x", wim_path, f"-o{tmpdir}", "[1].xml",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await result.communicate()

        if result.returncode != 0:
            return metadata

        xml_file = Path(tmpdir) / "[1].xml"
        if not xml_file.exists():
            return metadata

        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Parse WIM XML structure
        # Namespace handling
        ns = {"wim": "http://schemas.microsoft.com/wim/2008/01"}

        # Find IMAGE elements
        for image in root.findall(".//wim:IMAGE", ns) or root.findall(".//IMAGE"):
            # Get edition from NAME or DESCRIPTION
            name_elem = image.find("wim:NAME", ns) or image.find("NAME")
            if name_elem is not None and name_elem.text:
                metadata.edition = name_elem.text.strip()

            desc_elem = image.find("wim:DESCRIPTION", ns) or image.find("DESCRIPTION")
            if desc_elem is not None and desc_elem.text and not metadata.edition:
                metadata.edition = desc_elem.text.strip()

            # Get version/build from WINDOWS element
            windows = image.find("wim:WINDOWS", ns) or image.find("WINDOWS")
            if windows is not None:
                version_elem = windows.find("wim:VERSION", ns) or windows.find("VERSION")
                if version_elem is not None and version_elem.text:
                    metadata.version = version_elem.text.strip()
                    # Extract build number
                    match = re.search(r"(\d{5,})", metadata.version)
                    if match:
                        metadata.build_number = int(match.group(1))

                arch_elem = windows.find("wim:ARCHITECTURE", ns) or windows.find("ARCHITECTURE")
                if arch_elem is not None and arch_elem.text:
                    metadata.architecture = arch_elem.text.strip()

                lang_elem = windows.find("wim:LANGUAGE", ns) or windows.find("LANGUAGE")
                if lang_elem is not None and lang_elem.text:
                    metadata.language = lang_elem.text.strip()

            # Only need first image
            break

    return metadata


def parse_version_string(version: str) -> tuple[str | None, int | None]:
    """
    Parse Windows version string into marketing version and build number.

    Examples:
        "10.0.26100" -> ("24H2", 26100)
        "10.0.22621" -> ("22H2", 22621)
        "10.0.19045" -> ("22H2", 19045)
    """
    match = re.search(r"10\.0\.(\d{5})", version)
    if not match:
        return None, None

    build = int(match.group(1))

    # Map build numbers to marketing versions
    if build >= 26100:
        marketing = "24H2"
    elif build >= 23500:
        marketing = "23H2"
    elif build >= 22621:
        marketing = "22H2"
    elif build >= 22000:
        marketing = "21H2"
    elif build >= 19045:
        marketing = "22H2"
    elif build >= 19044:
        marketing = "21H2"
    elif build >= 19043:
        marketing = "21H1"
    elif build >= 19042:
        marketing = "20H2"
    elif build >= 19041:
        marketing = "2004"
    else:
        marketing = None

    return marketing, build

