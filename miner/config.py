"""Configuration. Secrets come from environment, never from this file."""
import os
from dataclasses import dataclass, field


@dataclass
class Config:
    wallet: str = "0x61810117d55a7ec1256D0FaE20f19858452564e5"
    agent_name: str = "Ize capitals"
    api_key: str = field(default_factory=lambda: os.environ.get("DELPHI_API_KEY", ""))
    api_base: str = field(default_factory=lambda: os.environ.get(
        "DELPHI_API_BASE", "https://api.delphi.org"))  # placeholder, real base from Nov 23 docs
    max_submissions_per_market: int = 3
    max_files_per_submission: int = 3
    dry_run: bool = True  # True until the API spike on Nov 23 passes its checks

    def require_live(self):
        if not self.api_key:
            raise RuntimeError("DELPHI_API_KEY not set")
