"""Версии и диапазоны версий в нотации NuGet."""

import re
from dataclasses import dataclass

NUM_PARTS = 4
MIN_PARTS = 3
VERSION_PARTS_RE = re.compile(r"^(\d+(?:\.\d+)*)(?:-([0-9A-Za-z.\-]+))?$")


class VersionError(ValueError):
    """Строка не является корректной версией или диапазоном."""


def _split(text):
    """Разделить версию на числовые части и метку предрелиза."""
    core = text.strip().split("+", 1)[0]
    match = VERSION_PARTS_RE.match(core)
    if not match:
        raise VersionError(f"некорректная версия: '{text}'")
    nums = [int(part) for part in match.group(1).split(".")]
    if len(nums) > NUM_PARTS:
        raise VersionError(f"слишком много частей в версии: '{text}'")
    return nums, (match.group(2) or "").lower()


def version_key(text):
    """Ключ сравнения версий: релиз старше любого своего предрелиза."""
    nums, label = _split(text)
    nums += [0] * (NUM_PARTS - len(nums))
    labels = tuple(
        (0, int(part), "") if part.isdigit() else (1, 0, part)
        for part in label.split(".")) if label else ()
    return tuple(nums), not label, labels


def is_prerelease(text):
    """Проверить, является ли версия предрелизной."""
    return bool(_split(text)[1])


def normalize(text):
    """Нормализовать версию так, как это делает NuGet (1.0 -> 1.0.0)."""
    nums, label = _split(text)
    nums += [0] * (MIN_PARTS - len(nums))
    if len(nums) == NUM_PARTS and nums[-1] == 0:
        nums = nums[:MIN_PARTS]
    result = ".".join(str(num) for num in nums)
    return f"{result}-{label}" if label else result


@dataclass
class VersionRange:
    """Диапазон версий NuGet, например [1.0,2.0)."""

    low: str = ""
    low_inclusive: bool = True
    high: str = ""
    high_inclusive: bool = False

    def contains(self, version):
        """Проверить, входит ли версия в диапазон."""
        key = version_key(version)
        if self.low:
            low = version_key(self.low)
            if key < low or (key == low and not self.low_inclusive):
                return False
        if self.high:
            high = version_key(self.high)
            if key > high or (key == high and not self.high_inclusive):
                return False
        return True

    def allows_prerelease(self):
        """Разрешены ли предрелизы (если нижняя граница — предрелиз)."""
        return bool(self.low) and is_prerelease(self.low)


def _parse_bracketed(text):
    """Разобрать диапазон в скобках: [a,b], (a,b), [a]."""
    body = text[1:-1]
    low_inc, high_inc = text[0] == "[", text[-1] == "]"
    if "," not in body:
        if not (low_inc and high_inc) or not body.strip():
            raise VersionError(f"некорректный диапазон: '{text}'")
        return VersionRange(body.strip(), True, body.strip(), True)
    low, high = (part.strip() for part in body.split(",", 1))
    for bound in (low, high):
        if bound:
            _split(bound)
    return VersionRange(low, low_inc, high, high_inc)


def parse_range(text):
    """Разобрать строку диапазона версий NuGet."""
    text = (text or "").strip()
    if not text:
        return VersionRange()
    if text[0] in "[(" and text[-1] in "])":
        return _parse_bracketed(text)
    _split(text)
    return VersionRange(low=text)


def lowest_matching(version_range, versions):
    """Минимальная подходящая версия (правило NuGet), либо None."""
    allow_pre = version_range.allows_prerelease()
    suitable = [
        ver for ver in versions
        if (allow_pre or not is_prerelease(ver))
        and version_range.contains(ver)
    ]
    return min(suitable, key=version_key) if suitable else None
