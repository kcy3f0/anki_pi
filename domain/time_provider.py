# domain/time_provider.py
from __future__ import annotations
from datetime import datetime, timezone, timedelta
import re
from domain.protocols import TimeProvider

__all__ = ["TimeProvider", "SystemTimeProvider", "FixedTimeProvider"]


class SystemTimeProvider:
    """生產環境：真實系統時間。"""

    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)

    def day_cutoff_utc(
        self, tz_offset_hours: int = 8, rollover_hour: int = 4
    ) -> datetime:
        now_utc = self.now_utc()
        local_tz = timezone(timedelta(hours=tz_offset_hours))
        now_local = now_utc.astimezone(local_tz)
        if now_local.hour < rollover_hour:
            cutoff_local = now_local.replace(
                hour=rollover_hour, minute=0, second=0, microsecond=0
            )
        else:
            cutoff_local = (now_local + timedelta(days=1)).replace(
                hour=rollover_hour, minute=0, second=0, microsecond=0
            )
        return cutoff_local.astimezone(timezone.utc)

    def parse_iso(self, text: str) -> datetime | None:
        """完整複製原 parse_db_datetime 邏輯：時區後綴、微秒截斷、多格式嘗試。"""
        if not text:
            return None
        text = text.strip()
        tz_match = re.search(r"([+-]\d{2}:?\d{2}|Z)$", text)
        tz_part = tz_match.group(1) if tz_match else ""
        if tz_part:
            text = text[: -len(tz_part)]
        if "." in text:
            base, micro = text.split(".")
            micro = micro[:6]
            text = f"{base}.{micro}"
        dt = None
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            try:
                dt = datetime.fromisoformat(text.replace(" ", "T"))
            except ValueError:
                for fmt in (
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d %H:%M:%S.%f",
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d",
                ):
                    try:
                        dt = datetime.strptime(text, fmt)
                        break
                    except ValueError:
                        continue
        if dt is None:
            return None
        if tz_part == "Z" or tz_part == "+00:00" or tz_part == "-00:00" or not tz_part:
            return dt.replace(tzinfo=timezone.utc)
        else:
            tz_info = datetime.fromisoformat(f"2020-01-01T00:00:00{tz_part}").tzinfo
            return dt.replace(tzinfo=tz_info).astimezone(timezone.utc)

    def format_iso(self, dt: datetime | str | None) -> str:
        if not dt:
            return ""
        if isinstance(dt, str):
            return dt
        return dt.isoformat()


class FixedTimeProvider:
    """測試環境：固定/可控制時間。"""

    def __init__(self, now: datetime | None = None):
        self._now = now or datetime.now(timezone.utc)

    def now_utc(self) -> datetime:
        return self._now

    def set_now(self, dt: datetime) -> None:
        self._now = dt

    def advance(self, td: timedelta) -> None:
        self._now += td

    def day_cutoff_utc(
        self, tz_offset_hours: int = 8, rollover_hour: int = 4
    ) -> datetime:
        local_tz = timezone(timedelta(hours=tz_offset_hours))
        now_local = self._now.astimezone(local_tz)
        if now_local.hour < rollover_hour:
            cutoff_local = now_local.replace(
                hour=rollover_hour, minute=0, second=0, microsecond=0
            )
        else:
            cutoff_local = (now_local + timedelta(days=1)).replace(
                hour=rollover_hour, minute=0, second=0, microsecond=0
            )
        return cutoff_local.astimezone(timezone.utc)

    def parse_iso(self, text: str) -> datetime | None:
        return SystemTimeProvider().parse_iso(text)

    def format_iso(self, dt: datetime | None) -> str:
        return SystemTimeProvider().format_iso(dt)
