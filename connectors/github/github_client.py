from dataclasses import dataclass
import requests

@dataclass
class GitHubClient:
    token: str
    base_url: str = "https://api.github.com"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def get_pull(self, owner: str, repo: str, pull_number: int) -> dict:
        r = requests.get(f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}", headers=self._headers(), timeout=20)
        r.raise_for_status()
        return r.json()

    def merge_pull(self, owner: str, repo: str, pull_number: int, commit_title: str | None = None) -> dict:
        payload = {}
        if commit_title:
            payload["commit_title"] = commit_title
        r = requests.put(f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/merge", headers=self._headers(), json=payload, timeout=20)
        r.raise_for_status()
        return r.json()
