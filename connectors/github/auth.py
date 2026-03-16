from dataclasses import dataclass
import os

@dataclass(frozen=True)
class GitHubAuthConfig:
    token: str

def load_auth() -> GitHubAuthConfig:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing GITHUB_TOKEN")
    return GitHubAuthConfig(token=token)
