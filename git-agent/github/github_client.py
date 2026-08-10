from __future__ import annotations

import importlib
import json
import logging
import sys
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

load_dotenv(override=True)
import requests
import os

from models.schemas import (
    BranchInfo,
    CodeStatistics,
    CommitInfo,
    ContributorInfo,
    DependencyItem,
    IssueInfo,
    PullRequestInfo,
    QualityIndicators,
    ReleaseInfo,
    RepositoryInfo,
    RepositorySnapshot,
    StructureItem,
    TechnologyEvidence,
)

LOGGER = logging.getLogger(__name__)


def _load_external_module(module_name: str) -> Any | None:
    local_root = Path(__file__).resolve().parents[1]
    original_module = sys.modules.get(module_name)
    original_path = list(sys.path)
    try:
        sys.modules.pop(module_name, None)
        sys.path = [entry for entry in sys.path if Path(entry or ".").resolve() != local_root]
        return importlib.import_module(module_name)
    except Exception:
        return None
    finally:
        sys.path = original_path
        if original_module is not None:
            sys.modules[module_name] = original_module


_PYGITHUB = _load_external_module("github")


@dataclass(slots=True)
class GitHubClient:
    token: str | None = field(default_factory=lambda: os.getenv("GITHUB_TOKEN"))
    base_url: str = "https://api.github.com"
    timeout: int = 30
    per_page: int = 100
    session: requests.Session = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "git-repository-agent",
            }
        )
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"
            LOGGER.info("GitHub authentication enabled")
        else:
            LOGGER.warning("No GitHub token found. Requests will be unauthenticated")

    def _request(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = self.session.get(f"{self.base_url}{path}", params=params, timeout=self.timeout)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            if response.status_code == 403 and "rate limit" in response.text.lower():
                raise RuntimeError(
                    "GitHub API rate limit exceeded. Set GITHUB_TOKEN or GH_TOKEN to enable authenticated analysis."
                ) from exc
            raise
        return response.json()

    def _paginate(self, path: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        collected: list[dict[str, Any]] = []
        page = 1
        while True:
            page_params = dict(params or {})
            page_params.update({"per_page": self.per_page, "page": page})
            payload = self._request(path, page_params)
            if not payload:
                break
            if isinstance(payload, dict):
                return [payload]
            collected.extend(payload)
            if len(payload) < self.per_page:
                break
            page += 1
        return collected

    def _pygithub_repo(self, full_name: str) -> Any | None:
        if _PYGITHUB is None or self.token is None:
            return None
        try:
            github_client = _PYGITHUB.Github(self.token)
            return github_client.get_repo(full_name)
        except Exception:
            LOGGER.debug("PyGithub fallback unavailable for %s", full_name, exc_info=True)
            return None

    @staticmethod
    def _parse_datetime(value: str | None) -> str | None:
        if not value:
            return None
        return value.replace("Z", "+00:00")

    # --- Helpers pour la méthode principale ---
    def _merge_languages(self, languages_list: list[dict[str, int]]) -> dict[str, int]:
        merged = {}
        for lang_dict in languages_list:
            for lang, bytes_size in lang_dict.items():
                merged[lang] = merged.get(lang, 0) + bytes_size
        return merged

    def _unique_commits(self, commits: list[CommitInfo]) -> list[CommitInfo]:
        seen = set()
        unique = []
        for commit in commits:
            if commit.hash not in seen:
                seen.add(commit.hash)
                unique.append(commit)
        return unique

    def _unique_structure(self, structure: list[StructureItem]) -> list[StructureItem]:
        seen = set()
        unique = []
        for item in structure:
            if item.path not in seen:
                seen.add(item.path)
                unique.append(item)
        return unique

    def _unique_dependencies(self, deps: list[DependencyItem]) -> list[DependencyItem]:
        seen = set()
        unique = []
        for dep in deps:
            key = (dep.name, dep.version, dep.specifier)
            if key not in seen:
                seen.add(key)
                unique.append(dep)
        return unique

    def _contributors_from_commits(self, commits: list[CommitInfo]) -> list[ContributorInfo]:
        counts: dict[tuple[str, str | None], list[str]] = {}
        for commit in commits:
            counts.setdefault((commit.author, commit.email), []).append(commit.date)
        ordered = sorted(counts.items(), key=lambda item: len(item[1]), reverse=True)
        contributors: list[ContributorInfo] = []
        for index, ((name, email), dates) in enumerate(ordered, start=1):
            contributors.append(
                ContributorInfo(
                    name=name,
                    email=email,
                    commits=len(dates),
                    last_contribution=max(dates) if dates else None,
                    ranking=index,
                )
            )
        return contributors

    def _get_languages_for_branch(self, full_name: str, branch: str) -> dict[str, int]:
        """
        Récupère les langages utilisés par une branche.
        """
        structure = self.list_structure(full_name, branch)
        languages: dict[str, int] = {}
        for item in structure:
            if item.kind != "blob":
                continue
            suffix = Path(item.path).suffix.lower()
            language_map = {
                ".py": "Python",
                ".js": "JavaScript",
                ".jsx": "JavaScript",
                ".ts": "TypeScript",
                ".tsx": "TypeScript",
                ".java": "Java",
                ".go": "Go",
                ".rs": "Rust",
                ".cs": "C#",
                ".php": "PHP",
                ".rb": "Ruby",
            }
            language = language_map.get(suffix)
            if language:
                languages[language] = languages.get(language, 0) + (item.size_bytes or 0)
        return languages

    # --- Méthodes principales ---
    def get_repository_snapshot(
        self,
        full_name: str,
        analyzed_branches: list[str] | None = None,
    ) -> RepositorySnapshot:
        repo_payload = self._request(f"/repos/{full_name}")
        default_branch = repo_payload.get("default_branch")

        # Branches à analyser
        if analyzed_branches:
            branches_to_analyze = list(dict.fromkeys(analyzed_branches))
        else:
            branches_to_analyze = []
            if default_branch:
                branches_to_analyze.append(default_branch)
            machine_branch = "MAIF-Solife"
            if machine_branch not in branches_to_analyze:
                branches_to_analyze.append(machine_branch)

        LOGGER.info("Analyzing repository %s on branches: %s", full_name, branches_to_analyze)

        available_branches = {branch.name for branch in self.list_branches(full_name)}
        branches_to_analyze = [
            branch for branch in branches_to_analyze if branch in available_branches
        ]
        LOGGER.info("Available branches selected for analysis: %s", branches_to_analyze)

        # Informations générales du repository
        languages = self._merge_languages(
            [self._get_languages_for_branch(full_name, branch) for branch in branches_to_analyze]
        )
        branches = self.list_branches(full_name)

        # Agrégation des données des branches
        commits: list[CommitInfo] = []
        contributors: list[ContributorInfo] = []
        pull_requests: list[PullRequestInfo] = []
        issues: list[IssueInfo] = []
        releases: list[ReleaseInfo] = []
        structure: list[StructureItem] = []
        dependencies: list[DependencyItem] = []

        for branch in branches_to_analyze:
            LOGGER.info("Collecting GitHub data for branch '%s'", branch)

            branch_commits = self.list_commits(full_name, branch=branch)
            commits.extend(branch_commits)

            branch_structure = self.list_structure(full_name, branch)
            structure.extend(branch_structure)

            branch_dependencies = self.extract_dependencies_from_structure(
                full_name, branch_structure, branch
            )
            dependencies.extend(branch_dependencies)

        # Supprimer les doublons
        commits = self._unique_commits(commits)
        structure = self._unique_structure(structure)
        dependencies = self._unique_dependencies(dependencies)

        # Contributors calculés sur tous les commits analysés
        contributors = self._contributors_from_commits(commits)

        # PR / Issues / Releases restent repository-level
        pull_requests = self.list_pull_requests(full_name)
        issues = self.list_issues(full_name)
        releases = self.list_releases(full_name)

        quality = self._quality_indicators_from_remote(repo_payload, structure)
        technologies = self.detect_technologies(repo_payload, languages, structure, dependencies)
        statistics = self.compute_code_statistics(structure, languages)

        repository = RepositoryInfo(
            name=repo_payload.get("name", full_name.split("/")[-1]),
            description=repo_payload.get("description"),
            owner=repo_payload.get("owner", {}).get("login", full_name.split("/")[0]),
            visibility=repo_payload.get("visibility", "public"),
            created_at=self._parse_datetime(repo_payload.get("created_at")),
            updated_at=self._parse_datetime(repo_payload.get("updated_at")),
            default_branch=default_branch,
            size_kb=repo_payload.get("size"),
            license=(repo_payload.get("license") or {}).get("spdx_id"),
            url=repo_payload.get("html_url", f"https://github.com/{full_name}"),
            stars=repo_payload.get("stargazers_count", 0),
            forks=repo_payload.get("forks_count", 0),
            watchers=repo_payload.get("subscribers_count", repo_payload.get("watchers_count", 0)),
            open_issues_count=repo_payload.get("open_issues_count", 0),
            topics=list(repo_payload.get("topics", [])),
            homepage=repo_payload.get("homepage"),
            languages=languages,
            age_days=self._repository_age_days(repo_payload.get("created_at")),
            archived=repo_payload.get("archived", False),
        )

        return RepositorySnapshot(
            source="github",
            repository=repository,
            analyzed_branches=branches_to_analyze,
            branches=branches,
            commits=commits,
            contributors=contributors,
            pull_requests=pull_requests,
            issues=issues,
            releases=releases,
            structure=structure,
            dependencies=dependencies,
            technologies=technologies,
            quality_indicators=quality,
            code_statistics=statistics,
        )

    def _repository_age_days(self, created_at: str | None) -> int | None:
        if not created_at:
            return None
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return max((datetime.now(timezone.utc) - created).days, 0)

    def list_branches(self, full_name: str) -> list[BranchInfo]:
        repo_payload = self._request(f"/repos/{full_name}")
        default_branch = repo_payload.get("default_branch")
        payload = self._paginate(f"/repos/{full_name}/branches")
        branches: list[BranchInfo] = []
        for item in payload:
            commit = item.get("commit", {})
            commit_info = commit.get("commit", {})
            commit_date = self._parse_datetime(commit_info.get("committer", {}).get("date"))
            branches.append(
                BranchInfo(
                    name=item.get("name", "unknown"),
                    default_branch=item.get("name") == default_branch,
                    protected=item.get("protected"),
                    last_commit=commit.get("sha"),
                    last_update=commit_date,
                    active=self._is_recent(commit_date),
                )
            )
        return branches

    def list_commits(self, full_name: str, branch: str | None = None) -> list[CommitInfo]:
        params = {"sha": branch} if branch else None
        payload = self._paginate(f"/repos/{full_name}/commits", params)
        commits: list[CommitInfo] = []
        for item in payload:
            detail = self._request(f"/repos/{full_name}/commits/{item.get('sha')}")
            commit = detail.get("commit", {})
            stats = detail.get("stats", {})
            files = [
                entry.get("filename")
                for entry in detail.get("files", [])
                if entry.get("filename")
            ]
            commits.append(
                CommitInfo(
                    hash=detail.get("sha", item.get("sha", "")),
                    author=(commit.get("author", {}) or {}).get("name", "unknown"),
                    email=(commit.get("author", {}) or {}).get("email"),
                    date=self._parse_datetime((commit.get("author", {}) or {}).get("date")) or "",
                    message=commit.get("message", ""),
                    files_modified=files,
                    insertions=stats.get("additions", 0),
                    deletions=stats.get("deletions", 0),
                    merge_commit=len(item.get("parents", [])) > 1,
                    statistics={
                        "total": stats.get("total", 0),
                        "additions": stats.get("additions", 0),
                        "deletions": stats.get("deletions", 0),
                    },
                )
            )
        return commits

    def list_contributors(self, full_name: str) -> list[ContributorInfo]:
        # Note: cette méthode n'est pas appelée dans le code original, seule _contributors_from_commits l'est.
        payload = self.list_commits(full_name)
        counts: dict[tuple[str, str | None], list[str]] = {}
        for commit in payload:
            counts.setdefault((commit.author, commit.email), []).append(commit.date)
        ordered = sorted(counts.items(), key=lambda item: len(item[1]), reverse=True)
        contributors: list[ContributorInfo] = []
        for index, ((name, email), dates) in enumerate(ordered, start=1):
            contributors.append(
                ContributorInfo(
                    name=name,
                    email=email,
                    commits=len(dates),
                    last_contribution=max(dates) if dates else None,
                    ranking=index,
                )
            )
        return contributors

    def list_pull_requests(self, full_name: str) -> list[PullRequestInfo]:
        payload = self._paginate(f"/repos/{full_name}/pulls", {"state": "all"})
        pull_requests: list[PullRequestInfo] = []
        for item in payload:
            merged_at = self._parse_datetime(item.get("merged_at"))
            created_at = self._parse_datetime(item.get("created_at"))
            closed_at = self._parse_datetime(item.get("closed_at"))
            merge_duration = None
            if created_at and merged_at:
                merge_duration = (
                    datetime.fromisoformat(merged_at) - datetime.fromisoformat(created_at)
                ).total_seconds() / 3600
            pull_requests.append(
                PullRequestInfo(
                    title=item.get("title", ""),
                    description=item.get("body"),
                    author=(item.get("user") or {}).get("login"),
                    state=item.get("state", "open"),
                    open=item.get("state") == "open",
                    closed=item.get("state") == "closed",
                    merged=bool(item.get("merged_at")),
                    created_at=created_at,
                    merged_at=merged_at,
                    closed_at=closed_at,
                    reviewers=[
                        reviewer.get("login")
                        for reviewer in item.get("requested_reviewers", [])
                        if reviewer.get("login")
                    ],
                    comments=item.get("comments", 0),
                    labels=[
                        label.get("name")
                        for label in item.get("labels", [])
                        if label.get("name")
                    ],
                    merge_duration_hours=merge_duration,
                )
            )
        return pull_requests

    def list_issues(self, full_name: str) -> list[IssueInfo]:
        payload = self._paginate(f"/repos/{full_name}/issues", {"state": "all"})
        issues: list[IssueInfo] = []
        for item in payload:
            if item.get("pull_request"):
                continue
            issues.append(
                IssueInfo(
                    title=item.get("title", ""),
                    state=item.get("state", "open"),
                    labels=[
                        label.get("name")
                        for label in item.get("labels", [])
                        if label.get("name")
                    ],
                    creator=(item.get("user") or {}).get("login"),
                    assignee=(item.get("assignee") or {}).get("login"),
                    comments=item.get("comments", 0),
                    created_at=self._parse_datetime(item.get("created_at")),
                    closed_at=self._parse_datetime(item.get("closed_at")),
                )
            )
        return issues

    def list_releases(self, full_name: str) -> list[ReleaseInfo]:
        payload = self._paginate(f"/repos/{full_name}/releases")
        latest_tag = payload[0].get("tag_name") if payload else None
        releases: list[ReleaseInfo] = []
        for item in payload:
            releases.append(
                ReleaseInfo(
                    tag=item.get("tag_name", ""),
                    name=item.get("name"),
                    body=item.get("body"),
                    published_at=self._parse_datetime(item.get("published_at")),
                    latest=item.get("tag_name") == latest_tag,
                )
            )
        return releases

    def list_structure(self, full_name: str, branch: str | None) -> list[StructureItem]:
        if not branch:
            return []
        branch_payload = self._request(f"/repos/{full_name}/branches/{branch}")
        tree_sha = branch_payload.get("commit", {}).get("commit", {}).get("tree", {}).get("sha")
        if not tree_sha:
            return []
        tree_payload = self._request(
            f"/repos/{full_name}/git/trees/{tree_sha}", {"recursive": "1"}
        )
        structure: list[StructureItem] = []
        for item in tree_payload.get("tree", []):
            path = item.get("path", "")
            if self._should_skip_remote_path(path):
                continue
            structure.append(
                StructureItem(
                    path=path,
                    kind=item.get("type", "blob"),
                    size_bytes=item.get("size"),
                )
            )
        return structure

    def extract_dependencies_from_structure(
        self,
        full_name: str,
        structure: list[StructureItem],
        default_branch: str | None = None,
    ) -> list[DependencyItem]:
        dependencies: list[DependencyItem] = []
        candidate_paths = [
            item.path
            for item in structure
            if Path(item.path).name.lower()
            in {"requirements.txt", "pyproject.toml", "package.json", "pom.xml"}
            and not self._should_skip_remote_path(item.path)
        ]
        for path in candidate_paths:
            content = self._get_file_text(full_name, path, default_branch)
            if not content:
                continue
            if path.endswith("requirements.txt"):
                for line in content.splitlines():
                    candidate = line.strip()
                    if not candidate or candidate.startswith("#"):
                        continue
                    name, version = self._split_requirement(candidate)
                    dependencies.append(
                        DependencyItem(
                            name=name, version=version, specifier=version, scope="runtime"
                        )
                    )
            elif path.endswith("package.json"):
                payload = json.loads(content)
                for scope in ("dependencies", "devDependencies"):
                    for name, version in payload.get(scope, {}).items():
                        dependencies.append(DependencyItem(name=name, version=version, scope=scope))
            elif path.endswith("pyproject.toml"):
                try:
                    import tomllib
                except Exception:
                    continue
                payload = tomllib.loads(content)
                for requirement in payload.get("project", {}).get("dependencies", []):
                    name, specifier = self._split_requirement(requirement)
                    dependencies.append(
                        DependencyItem(name=name, specifier=specifier, scope="runtime")
                    )
            elif path.endswith("pom.xml"):
                dependencies.append(DependencyItem(name="maven", scope="build"))
        return dependencies

    def detect_technologies(
        self,
        repo_payload: dict[str, Any],
        languages: dict[str, int],
        structure: list[StructureItem],
        dependencies: list[DependencyItem],
    ) -> list[TechnologyEvidence]:
        technologies: list[TechnologyEvidence] = []
        file_paths = [item.path.lower() for item in structure]
        dependency_names = {dependency.name.lower() for dependency in dependencies}

        if any(path.endswith("requirements.txt") for path in file_paths):
            technologies.append(
                TechnologyEvidence(name="Python", evidence=["requirements.txt"], confidence=0.9)
            )
        if any(path.endswith("package.json") for path in file_paths):
            technologies.append(
                TechnologyEvidence(name="Node.js", evidence=["package.json"], confidence=0.9)
            )
            technologies.append(
                TechnologyEvidence(name="JavaScript", evidence=["package.json"], confidence=0.8)
            )
        if any(path.endswith(".tsx") or path.endswith(".jsx") for path in file_paths):
            technologies.append(
                TechnologyEvidence(name="React", evidence=["tsx/jsx sources"], confidence=0.7)
            )
        if any(path.endswith("dockerfile") for path in file_paths):
            technologies.append(
                TechnologyEvidence(name="Docker", evidence=["Dockerfile"], confidence=0.95)
            )
        if any(path.startswith(".github/workflows/") for path in file_paths):
            technologies.append(
                TechnologyEvidence(
                    name="GitHub Actions", evidence=[".github/workflows"], confidence=0.95
                )
            )
        if any(path.endswith(".gitlab-ci.yml") for path in file_paths):
            technologies.append(
                TechnologyEvidence(name="GitLab CI", evidence=[".gitlab-ci.yml"], confidence=0.95)
            )
        frameworks = {"flask", "fastapi", "django"} & dependency_names
        if frameworks:
            framework = sorted(frameworks)[0]
            technologies.append(
                TechnologyEvidence(
                    name=framework.title(), evidence=["dependency analysis"], confidence=0.85
                )
            )
        return technologies

    def compute_code_statistics(
        self, structure: list[StructureItem], languages: dict[str, int]
    ) -> CodeStatistics:
        directories = {Path(item.path).parent.as_posix() for item in structure if item.kind == "tree"}
        source_files = [item for item in structure if self._is_source_file(item.path)]
        largest_directories = self._largest_directories(structure)
        return CodeStatistics(
            directories=len(directories),
            files=sum(1 for item in structure if item.kind == "blob"),
            source_files=len(source_files),
            loc_estimation=sum(languages.values()),
            largest_directories=largest_directories,
            language_distribution=languages,
        )

    def _largest_directories(self, structure: list[StructureItem]) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for item in structure:
            parent = Path(item.path).parent.as_posix()
            counts[parent] = counts.get(parent, 0) + 1
        return [
            {"directory": directory, "items": count}
            for directory, count in sorted(counts.items(), key=lambda pair: pair[1], reverse=True)[:5]
        ]

    @staticmethod
    def _is_source_file(path: str) -> bool:
        return Path(path).suffix.lower() in {
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".java",
            ".go",
            ".rs",
            ".cs",
            ".php",
            ".rb",
        }

    def _quality_indicators_from_remote(
        self, repo_payload: dict[str, Any], structure: list[StructureItem]
    ) -> QualityIndicators:
        file_paths = {item.path.lower() for item in structure}
        return QualityIndicators(
            readme_exists=any(path.startswith("readme") for path in file_paths),
            license_exists=any(path.startswith("license") for path in file_paths),
            ci_cd_configured=any(
                path.startswith(".github/workflows/") or path == ".gitlab-ci.yml"
                for path in file_paths
            ),
            tests_present=any(
                path.startswith("tests/") or path.endswith("_test.py") or path.endswith("test.py")
                for path in file_paths
            ),
            documentation_exists=any(path.startswith("docs/") for path in file_paths),
            docker_support=any(path == "dockerfile" or path == "docker-compose.yml" for path in file_paths),
            issue_templates=any(path.startswith(".github/ISSUE_TEMPLATE") for path in file_paths),
            pull_request_templates=any(
                path.startswith(".github/pull_request_template") for path in file_paths
            ),
            codeowners=any(path.endswith("codeowners") for path in file_paths),
            security_policy=any(
                path.startswith(".github/security-policy") or path.endswith("security.md")
                for path in file_paths
            ),
            dependabot=any(path.startswith(".github/dependabot") for path in file_paths),
        )

    @staticmethod
    def _is_recent(iso_date: str | None, window_days: int = 30) -> bool:
        if not iso_date:
            return False
        current = datetime.now(timezone.utc)
        branch_date = datetime.fromisoformat(iso_date)
        return (current - branch_date).days <= window_days

    def _get_file_text(self, full_name: str, path: str, ref: str | None) -> str | None:
        params = {"ref": ref} if ref else None
        payload = self._request(f"/repos/{full_name}/contents/{path}", params)
        if isinstance(payload, list):
            return None
        content = payload.get("content")
        encoding = payload.get("encoding")
        if not content or encoding != "base64":
            return None
        import base64

        return base64.b64decode(content).decode("utf-8", errors="ignore")

    @staticmethod
    def _should_skip_remote_path(path: str) -> bool:
        parts = {part.lower() for part in Path(path).parts}
        return (
            ".git" in parts
            or "__pycache__" in parts
            or ".pytest_cache" in parts
            or "node_modules" in parts
            or "dist" in parts
            or "build" in parts
        )

    @staticmethod
    def _split_requirement(requirement: str) -> tuple[str, str | None]:
        for separator in ("==", ">=", "<=", "~=", "!=", ">", "<"):
            if separator in requirement:
                name, version = requirement.split(separator, 1)
                return name.strip(), f"{separator}{version.strip()}"
        return requirement, None