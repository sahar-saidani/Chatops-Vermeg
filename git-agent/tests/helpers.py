from __future__ import annotations

from datetime import datetime, timezone

from models.schemas import (
    BranchInfo,
    CodeStatistics,
    CommitInfo,
    ContributorInfo,
    DependencyItem,
    HealthScore,
    IssueInfo,
    PullRequestInfo,
    QualityIndicators,
    ReleaseInfo,
    RepositoryInfo,
    RepositoryMetrics,
    RepositoryReport,
    RepositorySnapshot,
    StructureItem,
    TechnologyEvidence,
)


def build_sample_snapshot(source: str = "github") -> RepositorySnapshot:
    repository = RepositoryInfo(
        name="ToDoList",
        description="Simple todo application",
        owner="sahar-saidani",
        visibility="public",
        created_at="2024-01-01T00:00:00+00:00",
        updated_at="2024-02-10T00:00:00+00:00",
        default_branch="main",
        size_kb=128,
        license="MIT",
        url="https://github.com/sahar-saidani/ToDoList",
        stars=10,
        forks=2,
        watchers=3,
        open_issues_count=1,
        topics=["python", "todo"],
        homepage="https://example.com",
        languages={"Python": 1200},
        age_days=40,
        archived=False,
    )
    branches = [
        BranchInfo(
            name="main",
            default_branch=True,
            protected=True,
            last_commit="abc123",
            last_update="2024-02-10T00:00:00+00:00",
            active=True,
        ),
        BranchInfo(
            name="feature/old",
            default_branch=False,
            protected=False,
            last_commit="def456",
            last_update="2023-12-01T00:00:00+00:00",
            active=False,
        ),
    ]
    commits = [
        CommitInfo(
            hash="abc123",
            author="Alice",
            email="alice@example.com",
            date="2024-02-10T00:00:00+00:00",
            message="Add feature",
            files_modified=["app.py"],
            insertions=10,
            deletions=2,
            merge_commit=False,
            statistics={"total": 12, "additions": 10, "deletions": 2},
        ),
        CommitInfo(
            hash="def456",
            author="Bob",
            email="bob@example.com",
            date="2024-02-09T00:00:00+00:00",
            message="Merge branch",
            files_modified=["README.md"],
            insertions=5,
            deletions=1,
            merge_commit=True,
            statistics={"total": 6, "additions": 5, "deletions": 1},
        ),
    ]
    contributors = [
        ContributorInfo(name="Alice", email="alice@example.com", commits=1, last_contribution="2024-02-10T00:00:00+00:00", ranking=1),
        ContributorInfo(name="Bob", email="bob@example.com", commits=1, last_contribution="2024-02-09T00:00:00+00:00", ranking=2),
    ]
    pull_requests = [
        PullRequestInfo(
            title="Improve UI",
            description="Polish layout",
            author="Alice",
            state="closed",
            open=False,
            closed=True,
            merged=True,
            created_at="2024-02-01T00:00:00+00:00",
            merged_at="2024-02-03T12:00:00+00:00",
            closed_at="2024-02-03T12:00:00+00:00",
            reviewers=["Bob"],
            comments=2,
            labels=["enhancement"],
            merge_duration_hours=60.0,
        ),
        PullRequestInfo(
            title="Work in progress",
            description=None,
            author="Bob",
            state="open",
            open=True,
            closed=False,
            merged=False,
            created_at="2024-02-05T00:00:00+00:00",
            merged_at=None,
            closed_at=None,
            reviewers=[],
            comments=0,
            labels=[],
            merge_duration_hours=None,
        ),
    ]
    issues = [
        IssueInfo(
            title="Bug in validation",
            state="closed",
            labels=["bug"],
            creator="Alice",
            assignee="Bob",
            comments=4,
            created_at="2024-01-20T00:00:00+00:00",
            closed_at="2024-01-22T12:00:00+00:00",
        ),
        IssueInfo(
            title="Add export feature",
            state="open",
            labels=["enhancement"],
            creator="Bob",
            assignee=None,
            comments=1,
            created_at="2024-01-25T00:00:00+00:00",
            closed_at=None,
        ),
    ]
    releases = [
        ReleaseInfo(tag="v1.0.0", name="First release", body="Initial release", published_at="2024-02-01T00:00:00+00:00", latest=True)
    ]
    structure = [
        StructureItem(path="README.md", kind="blob", size_bytes=1200),
        StructureItem(path="LICENSE", kind="blob", size_bytes=1000),
        StructureItem(path="requirements.txt", kind="blob", size_bytes=200),
        StructureItem(path="app.py", kind="blob", size_bytes=800),
        StructureItem(path="tests", kind="tree", size_bytes=None),
        StructureItem(path="tests/test_app.py", kind="blob", size_bytes=400),
        StructureItem(path=".github", kind="tree", size_bytes=None),
        StructureItem(path=".github/workflows/ci.yml", kind="blob", size_bytes=300),
        StructureItem(path="Dockerfile", kind="blob", size_bytes=100),
        StructureItem(path=".gitlab-ci.yml", kind="blob", size_bytes=150),
        StructureItem(path="package.json", kind="blob", size_bytes=220),
    ]
    dependencies = [
        DependencyItem(name="Flask", version="==3.0.0", specifier="==3.0.0", scope="runtime"),
        DependencyItem(name="pytest", version="==8.0.0", specifier="==8.0.0", scope="devDependencies"),
    ]
    technologies = [
        TechnologyEvidence(name="Python", evidence=["requirements.txt"], confidence=0.9),
        TechnologyEvidence(name="Flask", evidence=["dependency analysis"], confidence=0.85),
    ]
    quality = QualityIndicators(
        readme_exists=True,
        license_exists=True,
        ci_cd_configured=True,
        tests_present=True,
        documentation_exists=False,
        docker_support=True,
        issue_templates=False,
        pull_request_templates=False,
        codeowners=False,
        security_policy=False,
        dependabot=False,
    )
    statistics = CodeStatistics(
        directories=3,
        files=7,
        source_files=2,
        loc_estimation=200,
        largest_directories=[{"directory": ".", "items": 5}],
        language_distribution={"Python": 200},
    )
    return RepositorySnapshot(
        source=source,
        repository=repository,
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


def build_sample_report(source: str = "github") -> RepositoryReport:
    snapshot = build_sample_snapshot(source=source)
    metrics = RepositoryMetrics(
        commits_per_day=1.0,
        commits_per_week=7.0,
        top_contributors=snapshot.contributors,
        last_activity="2024-02-10T00:00:00+00:00",
        merged_pr_count=1,
        open_pr_count=1,
        average_merge_duration_hours=60.0,
        number_of_bugs=1,
        number_of_enhancements=1,
        average_resolution_time_hours=60.0,
        stale_branches=1,
    )
    health_score = HealthScore(score=76, breakdown={"documentation": 20, "activity": 10, "maintenance": 15, "testing": 15, "ci_cd": 15, "security": 0, "organization": 1})
    return RepositoryReport(snapshot=snapshot, metrics=metrics, health_score=health_score, generated_at="2024-02-11T00:00:00+00:00")
