from __future__ import annotations

import importlib
import logging
import sys
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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


def _load_gitpython() -> Any | None:
    local_root = Path(__file__).resolve().parents[1]
    original_module = sys.modules.get("git")
    original_path = list(sys.path)
    try:
        sys.modules.pop("git", None)
        sys.path = [entry for entry in sys.path if Path(entry or ".").resolve() != local_root]
        return importlib.import_module("git")
    except Exception:
        LOGGER.debug("GitPython could not be loaded", exc_info=True)
        return None
    finally:
        sys.path = original_path
        if original_module is not None:
            sys.modules["git"] = original_module


_GITPYTHON = _load_gitpython()


@dataclass(slots=True)
class LocalGitRepository:
    path: Path
    stale_branch_days: int = 90
    active_window_days: int = 30
    repo: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if _GITPYTHON is None:
            raise RuntimeError("GitPython is required for local repository analysis")
        self.repo = _GITPYTHON.Repo(self.path)
        if self.repo.bare:
            raise ValueError(f"{self.path} is not a valid Git repository")

    def collect_snapshot(self) -> RepositorySnapshot:
        repository = self._repository_info()
        branches = self._branches()
        commits = self._commits()
        contributors = self._contributors(commits)
        structure = self._structure()
        technologies = self._technologies(structure)
        dependencies = self._dependencies(structure)
        quality = self._quality_indicators(structure)
        statistics = self._code_statistics(structure)
        releases = self._releases()
        return RepositorySnapshot(
            source="local",
            repository=repository,
            branches=branches,
            commits=commits,
            contributors=contributors,
            pull_requests=[],
            issues=[],
            releases=releases,
            structure=structure,
            dependencies=dependencies,
            technologies=technologies,
            quality_indicators=quality,
            code_statistics=statistics,
        )

    def _repository_info(self) -> RepositoryInfo:
        head_commit = self.repo.head.commit
        remotes = list(self.repo.remotes)
        origin_url = remotes[0].url if remotes else str(self.path)
        license_text = self._detect_license()
        languages = self._language_distribution()
        return RepositoryInfo(
            name=self.path.name,
            description=None,
            owner=origin_url,
            visibility="local",
            created_at=self._format_datetime(head_commit.committed_datetime),
            updated_at=self._format_datetime(head_commit.committed_datetime),
            default_branch=self.repo.active_branch.name if not self.repo.head.is_detached else None,
            size_kb=self._repo_size_kb(),
            license=license_text,
            url=origin_url,
            stars=0,
            forks=0,
            watchers=0,
            open_issues_count=0,
            topics=[],
            homepage=None,
            languages=languages,
            age_days=self._repository_age_days(),
            archived=False,
        )

    def _branches(self) -> list[BranchInfo]:
        branches: list[BranchInfo] = []
        default_branch = None
        try:
            default_branch = self.repo.active_branch.name
        except Exception:
            default_branch = None
        for branch in self.repo.branches:
            commit = branch.commit
            commit_date = self._format_datetime(commit.committed_datetime)
            branches.append(
                BranchInfo(
                    name=branch.name,
                    default_branch=branch.name == default_branch,
                    protected=self._is_protected_branch(branch.name),
                    last_commit=commit.hexsha,
                    last_update=commit_date,
                    active=self._is_recent(commit.committed_datetime, self.active_window_days),
                )
            )
        return branches

    def _commits(self) -> list[CommitInfo]:
        commits: list[CommitInfo] = []
        for commit in self.repo.iter_commits("--all"):
            stats = commit.stats.total
            files = list(commit.stats.files.keys())
            commits.append(
                CommitInfo(
                    hash=commit.hexsha,
                    author=commit.author.name if commit.author else "unknown",
                    email=commit.author.email if commit.author else None,
                    date=self._format_datetime(commit.committed_datetime),
                    message=commit.message.strip(),
                    files_modified=files,
                    insertions=stats.get("insertions", 0),
                    deletions=stats.get("deletions", 0),
                    merge_commit=len(commit.parents) > 1,
                    statistics={"total": stats.get("total", 0), "files": stats.get("files", 0), "insertions": stats.get("insertions", 0), "deletions": stats.get("deletions", 0)},
                )
            )
        return commits

    def _contributors(self, commits: list[CommitInfo]) -> list[ContributorInfo]:
        ranking: dict[tuple[str, str | None], list[str]] = {}
        for commit in commits:
            key = (commit.author, commit.email)
            ranking.setdefault(key, []).append(commit.date)
        ordered = sorted(ranking.items(), key=lambda item: len(item[1]), reverse=True)
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

    def _structure(self) -> list[StructureItem]:
        structure: list[StructureItem] = []
        for path in self.path.rglob("*"):
            if self._should_skip_path(path):
                continue
            kind = "tree" if path.is_dir() else "blob"
            structure.append(StructureItem(path=str(path.relative_to(self.path)).replace("\\", "/"), kind=kind, size_bytes=path.stat().st_size if path.is_file() else None))
        return structure

    def _releases(self) -> list[ReleaseInfo]:
        releases: list[ReleaseInfo] = []
        for tag in self.repo.tags:
            commit_date = getattr(tag.commit, "committed_datetime", None)
            releases.append(
                ReleaseInfo(
                    tag=tag.name,
                    name=tag.name,
                    body=None,
                    published_at=self._format_datetime(commit_date) if commit_date else None,
                    latest=False,
                )
            )
        if releases:
            releases[0].latest = True
        return releases

    def _technologies(self, structure: list[StructureItem]) -> list[TechnologyEvidence]:
        paths = [item.path.lower() for item in structure]
        dependencies = self._dependencies(structure)
        technologies: list[TechnologyEvidence] = []
        if any(path.endswith(".py") for path in paths):
            technologies.append(TechnologyEvidence(name="Python", evidence=[".py files"], confidence=1.0))
        if any(path.endswith("package.json") for path in paths):
            technologies.append(TechnologyEvidence(name="Node.js", evidence=["package.json"], confidence=1.0))
        if any(path.endswith(".tsx") or path.endswith(".jsx") for path in paths):
            technologies.append(TechnologyEvidence(name="React", evidence=["tsx/jsx files"], confidence=0.8))
        if any(path.endswith("dockerfile") for path in paths):
            technologies.append(TechnologyEvidence(name="Docker", evidence=["Dockerfile"], confidence=1.0))
        if any(path.startswith(".github/workflows/") for path in paths):
            technologies.append(TechnologyEvidence(name="GitHub Actions", evidence=[".github/workflows"], confidence=1.0))
        if any(path == ".gitlab-ci.yml" for path in paths):
            technologies.append(TechnologyEvidence(name="GitLab CI", evidence=[".gitlab-ci.yml"], confidence=1.0))
        if any(path.endswith("requirements.txt") for path in paths):
            technologies.append(TechnologyEvidence(name="Python packaging", evidence=["requirements.txt"], confidence=0.9))
        frameworks = {"flask", "fastapi", "django"} & {dependency.name.lower() for dependency in dependencies}
        if frameworks:
            framework = sorted(frameworks)[0]
            technologies.append(TechnologyEvidence(name=framework.title(), evidence=["dependency analysis"], confidence=0.85))
        return technologies

    def _dependencies(self, structure: list[StructureItem]) -> list[DependencyItem]:
        dependencies: list[DependencyItem] = []
        requirements = self.path / "requirements.txt"
        if requirements.exists():
            for line in requirements.read_text(encoding="utf-8").splitlines():
                candidate = line.strip()
                if not candidate or candidate.startswith("#"):
                    continue
                name, version = self._split_requirement(candidate)
                dependencies.append(DependencyItem(name=name, version=version, specifier=version, scope="runtime"))
        pyproject = self.path / "pyproject.toml"
        if pyproject.exists():
            dependencies.extend(self._dependencies_from_pyproject(pyproject))
        package_json = self.path / "package.json"
        if package_json.exists():
            dependencies.extend(self._dependencies_from_package_json(package_json))
        pom = self.path / "pom.xml"
        if pom.exists():
            dependencies.append(DependencyItem(name="maven", scope="build"))
        return dependencies

    def _quality_indicators(self, structure: list[StructureItem]) -> QualityIndicators:
        file_paths = {item.path.lower() for item in structure}
        return QualityIndicators(
            readme_exists=any(path.startswith("readme") for path in file_paths),
            license_exists=any(path.startswith("license") for path in file_paths),
            ci_cd_configured=any(path.startswith(".github/workflows/") or path == ".gitlab-ci.yml" for path in file_paths),
            tests_present=any(path.startswith("tests/") or path.endswith("_test.py") or path.endswith("test.py") for path in file_paths),
            documentation_exists=any(path.startswith("docs/") for path in file_paths),
            docker_support=any(path == "dockerfile" or path == "docker-compose.yml" for path in file_paths),
            issue_templates=any(path.startswith(".github/issue_template") for path in file_paths),
            pull_request_templates=any(path.startswith(".github/pull_request_template") for path in file_paths),
            codeowners=any(path.endswith("codeowners") for path in file_paths),
            security_policy=any(path.startswith(".github/security") for path in file_paths),
            dependabot=any(path.startswith(".github/dependabot") for path in file_paths),
        )

    def _code_statistics(self, structure: list[StructureItem]) -> CodeStatistics:
        directories = {Path(item.path).parent.as_posix() for item in structure if item.kind == "tree"}
        source_files = [item for item in structure if self._is_source_file(item.path)]
        language_distribution = self._language_distribution()
        largest_directories = self._largest_directories(structure)
        return CodeStatistics(
            directories=len(directories),
            files=sum(1 for item in structure if item.kind == "blob"),
            source_files=len(source_files),
            loc_estimation=self._loc_estimation(),
            largest_directories=largest_directories,
            language_distribution=language_distribution,
        )

    def _largest_directories(self, structure: list[StructureItem]) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for item in structure:
            directory = Path(item.path).parent.as_posix()
            counts[directory] = counts.get(directory, 0) + 1
        return [
            {"directory": directory, "items": count}
            for directory, count in sorted(counts.items(), key=lambda pair: pair[1], reverse=True)[:5]
        ]

    def _language_distribution(self) -> dict[str, int]:
        distribution: dict[str, int] = {}
        for path in self.path.rglob("*"):
            if self._should_skip_path(path) or not path.is_file():
                continue
            language = self._language_from_suffix(path.suffix.lower())
            if not language:
                continue
            distribution[language] = distribution.get(language, 0) + 1
        return distribution

    @staticmethod
    def _language_from_suffix(suffix: str) -> str | None:
        mapping = {
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
            ".json": "JSON",
            ".yml": "YAML",
            ".yaml": "YAML",
            ".toml": "TOML",
            ".xml": "XML",
        }
        return mapping.get(suffix)

    @staticmethod
    def _is_source_file(path: str) -> bool:
        return Path(path).suffix.lower() in {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".cs", ".php", ".rb"}

    def _loc_estimation(self) -> int:
        total = 0
        for path in self.path.rglob("*"):
            if self._should_skip_path(path) or not path.is_file():
                continue
            if path.suffix.lower() in {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".cs", ".php", ".rb", ".json", ".yml", ".yaml", ".toml", ".xml"}:
                try:
                    total += len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
                except Exception:
                    continue
        return total

    def _repository_age_days(self) -> int | None:
        try:
            commits = list(self.repo.iter_commits("--all", reverse=True, max_count=1))
            if not commits:
                return None
            first_commit = commits[0]
            return max((datetime.now(timezone.utc) - first_commit.committed_datetime).days, 0)
        except Exception:
            return None

    def _repo_size_kb(self) -> int | None:
        try:
            return sum(path.stat().st_size for path in self.path.rglob("*") if path.is_file() and not self._should_skip_path(path)) // 1024
        except Exception:
            return None

    def _detect_license(self) -> str | None:
        for candidate in self.path.glob("LICENSE*"):
            return candidate.name
        return None

    def _is_protected_branch(self, branch_name: str) -> bool | None:
        return None

    def _should_skip_path(self, path: Path) -> bool:
        parts = {part.lower() for part in path.parts}
        return ".git" in parts or "__pycache__" in parts or ".pytest_cache" in parts or "node_modules" in parts or "dist" in parts or "build" in parts

    @staticmethod
    def _format_datetime(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc).isoformat()
        if isinstance(value, str):
            return value
        return None

    @staticmethod
    def _is_recent(value: datetime, window_days: int = 30) -> bool:
        current = datetime.now(timezone.utc)
        candidate = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return (current - candidate.astimezone(timezone.utc)).days <= window_days

    @staticmethod
    def _split_requirement(requirement: str) -> tuple[str, str | None]:
        for separator in ("==", ">=", "<=", "~=", "!=", ">", "<"):
            if separator in requirement:
                name, version = requirement.split(separator, 1)
                return name.strip(), f"{separator}{version.strip()}"
        return requirement, None

    @staticmethod
    def _dependencies_from_pyproject(pyproject: Path) -> list[DependencyItem]:
        try:
            import tomllib
        except Exception:
            return []
        payload = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        dependencies: list[DependencyItem] = []
        project = payload.get("project", {})
        for requirement in project.get("dependencies", []):
            name, specifier = LocalGitRepository._split_requirement(requirement)
            dependencies.append(DependencyItem(name=name, specifier=specifier, scope="runtime"))
        return dependencies

    @staticmethod
    def _dependencies_from_package_json(package_json: Path) -> list[DependencyItem]:
        import json

        payload = json.loads(package_json.read_text(encoding="utf-8"))
        dependencies: list[DependencyItem] = []
        for scope in ("dependencies", "devDependencies"):
            for name, version in payload.get(scope, {}).items():
                dependencies.append(DependencyItem(name=name, version=version, scope=scope))
        return dependencies
