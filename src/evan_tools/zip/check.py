import re
import struct
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple


class ZipType(Enum):
    ZIP = b"\x50\x4b\x03\x04"
    EMPTY_ZIP = b"\x50\x4b\x05\x06"
    SPANNED_ZIP = b"\x50\x4b\x07\x08"
    RAR = b"\x52\x61\x72\x21"
    GZIP = b"\x1f\x8b\x08"
    BZIP2 = b"\x42\x5a\x68"
    SEVEN_Z = b"\x37\x7a\xbc\xaf\x27\x1c"
    UNKNOWN = b""


class FileHeaderReader:

    @staticmethod
    def read_header(path: Path, size: int = 6) -> Optional[bytes]:
        if not path.exists() or not path.is_file():
            return None
        try:
            with path.open("rb") as f:
                return f.read(size)
        except Exception:
            return None


class ZipTypeIdentifier:

    def __init__(self, header_reader: FileHeaderReader):
        self._header_reader = header_reader

    def identify_by_header(self, path: Path) -> ZipType:
        header = self._header_reader.read_header(path)
        if not header:
            return ZipType.UNKNOWN

        zip_types = sorted(
            [zt for zt in ZipType if zt != ZipType.UNKNOWN],
            key=lambda x: len(x.value),
            reverse=True,
        )

        for zt in zip_types:
            if header.startswith(zt.value):
                return zt

        return ZipType.UNKNOWN


class VolumePathResolver:

    @staticmethod
    def resolve_first_volume_for_numbered(path: Path) -> Optional[Path]:
        file_name = path.name.lower()
        if re.search(r"\.\d{3,}$", file_name):
            first_vol_name = re.sub(r"\.\d{3,}$", ".001", path.name)
            return path.with_name(first_vol_name)
        return None

    @staticmethod
    def resolve_first_volume_for_part(path: Path) -> Optional[Path]:
        file_name = path.name.lower()
        if ".part" in file_name:
            first_vol_name = re.sub(
                r"\.part\d+\.rar$", ".part1.rar", path.name, flags=re.IGNORECASE
            )
            return path.with_name(first_vol_name)
        return None

    @staticmethod
    def resolve_first_volume_for_z_numbered(path: Path) -> Optional[Path]:
        file_name = path.name.lower()
        if re.search(r"\.z\d+$", file_name):
            return path.with_suffix(".zip")
        return None


class ZipTypeDetector:

    def __init__(
        self,
        identifier: ZipTypeIdentifier,
        path_resolver: VolumePathResolver,
    ):
        self._identifier = identifier
        self._path_resolver = path_resolver

    def detect(self, path: Path) -> ZipType:
        result = self._identifier.identify_by_header(path)
        if result != ZipType.UNKNOWN:
            return result

        first_volume = self._try_find_first_volume(path)
        if first_volume:
            result = self._identifier.identify_by_header(first_volume)
            if result != ZipType.UNKNOWN:
                return result

        return ZipType.UNKNOWN

    def _try_find_first_volume(self, path: Path) -> Optional[Path]:
        resolvers = [
            self._path_resolver.resolve_first_volume_for_numbered,
            self._path_resolver.resolve_first_volume_for_part,
            self._path_resolver.resolve_first_volume_for_z_numbered,
        ]

        for resolver in resolvers:
            first_vol = resolver(path)
            if first_vol:
                return first_vol

        return None


class VolumeCollector:

    @staticmethod
    def is_part_file(path: Path) -> bool:
        return path.suffix.isdigit() and len(path.suffix) >= 3

    @staticmethod
    def collect_volumes(path: Path) -> Tuple[List[Path], bool]:
        is_part = VolumeCollector.is_part_file(path)

        if is_part:
            prefix = path.name.rsplit(".", 1)[0]
            volumes = sorted(
                list(path.parent.glob(f"{prefix}.[0-9][0-9][0-9]")),
                key=lambda p: p.suffix,
            )
            return (volumes if volumes else [path], is_part)

        return ([path], is_part)


class EncryptionChecker(ABC):

    @abstractmethod
    def check(self, path: Path, is_part_file: bool, volumes: List[Path]) -> bool:
        pass


class ZipEncryptionChecker(EncryptionChecker):

    def check(self, path: Path, is_part_file: bool, volumes: List[Path]) -> bool:
        try:
            with path.open("rb") as f:
                f.seek(6)
                flag = int.from_bytes(f.read(2), "little")
                return (flag & 0x01) != 0
        except Exception:
            return False


class RarEncryptionChecker(EncryptionChecker):

    def check(self, path: Path, is_part_file: bool, volumes: List[Path]) -> bool:
        try:
            with path.open("rb") as f:
                f.seek(9)
                flag = int.from_bytes(f.read(2), "little")
                return (flag & 0x04) != 0
        except Exception:
            return False


class SevenZipEncryptionChecker(EncryptionChecker):

    def check(self, path: Path, is_part_file: bool, volumes: List[Path]) -> bool:
        try:
            header_info = self._read_header_info(volumes[0])
            if not header_info:
                return is_part_file

            next_offset, next_size = header_info

            target_file, physical_offset = self._locate_target_position(
                volumes, next_offset
            )

            return self._check_encryption_flags(
                target_file, physical_offset, next_size, is_part_file
            )

        except Exception:
            return is_part_file

    def _read_header_info(self, first_volume: Path) -> Optional[Tuple[int, int]]:
        try:
            with first_volume.open("rb") as f:
                f.seek(12)
                header_data = f.read(20)
                if len(header_data) < 20:
                    return None
                next_offset, next_size, _ = struct.unpack("<QQI", header_data)
                return (next_offset, next_size)
        except Exception:
            return None

    def _locate_target_position(
        self, volumes: List[Path], next_offset: int
    ) -> Tuple[Path, int]:
        logical_pos = 32 + next_offset
        current_logical_start = 0

        for vol in volumes:
            vol_size = vol.stat().st_size
            if current_logical_start <= logical_pos < current_logical_start + vol_size:
                physical_offset = logical_pos - current_logical_start
                return (vol, physical_offset)
            current_logical_start += vol_size

        target_file = volumes[-1]
        physical_offset = max(0, target_file.stat().st_size - 512)
        return (target_file, physical_offset)

    def _check_encryption_flags(
        self, target_file: Path, physical_offset: int, next_size: int, is_part_file: bool
    ) -> bool:
        with target_file.open("rb") as f:
            f.seek(int(physical_offset))
            first_byte = f.read(1)

            if not first_byte:
                return False

            if first_byte == b"\x17":
                return True if is_part_file else False

            if not is_part_file:
                if first_byte in (b"\x00", b"\x01"):
                    return False

            if first_byte == b"\x00":
                if not is_part_file:
                    return False
                sample = f.read(min(int(next_size) if next_size > 0 else 4096, 8192))
                return b"\x06\xf1\x07\x01" in sample or True

            sample = f.read(min(int(next_size) if next_size > 0 else 4096, 8192))
            if b"\x06\xf1\x07\x01" in sample:
                return True

            return not is_part_file


class EncryptionDetector:

    def __init__(self, volume_collector: VolumeCollector):
        self._volume_collector = volume_collector
        self._checkers = {
            ZipType.ZIP: ZipEncryptionChecker(),
            ZipType.EMPTY_ZIP: ZipEncryptionChecker(),
            ZipType.SPANNED_ZIP: ZipEncryptionChecker(),
            ZipType.RAR: RarEncryptionChecker(),
            ZipType.SEVEN_Z: SevenZipEncryptionChecker(),
        }

    def detect(self, path: Path, zip_type: ZipType) -> bool:
        if zip_type == ZipType.UNKNOWN:
            return False

        volumes, is_part_file = self._volume_collector.collect_volumes(path)

        checker = self._checkers.get(zip_type)
        if not checker:
            return False

        return checker.check(path, is_part_file, volumes)


def zip_type(path: Path) -> ZipType:
    header_reader = FileHeaderReader()
    identifier = ZipTypeIdentifier(header_reader)
    path_resolver = VolumePathResolver()
    detector = ZipTypeDetector(identifier, path_resolver)
    return detector.detect(path)


def is_encrypted(path: Path) -> bool:
    zt = zip_type(path)
    volume_collector = VolumeCollector()
    detector = EncryptionDetector(volume_collector)
    return detector.detect(path, zt)
