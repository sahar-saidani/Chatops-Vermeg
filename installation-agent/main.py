import argparse
import os
import platform
import sys
import json as jsonlib
from pathlib import Path

from dotenv import load_dotenv

# Ensure app path is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# python-dotenv's load_dotenv() locates .env relative to the *calling
# file's* directory (via stack inspection), not the process cwd. Load it
# here, from main.py's own location, so MachineIdentity.from_env() (which
# also calls load_dotenv(), but from within chatops_common/ - a different
# directory) still finds this agent's installation-agent/.env. Mirrors
# what cli.py already does.
load_dotenv()

from app.config.settings import settings
from app.config.machine_identity import MachineIdentity
from app.core.logging_config import setup_logging
from app.core.pipeline import run_analysis_pipeline
from app.services.reporting.canonical_result_builder import build_canonical_result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Installation Discovery Agent"
    )

    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan the real config/installation directory once, analyze it and exit",
    )

    parser.add_argument(
        "--config-dir",
        dest="config_dir",
        default=None,
        help="Directory to scan. Defaults to this agent's own config/ folder.",
    )

    parser.add_argument(
        "--os",
        dest="operating_system",
        choices=("LINUX", "WINDOWS"),
        type=str.upper,
        default=None,
        help="Target operating system (defaults to OPERATING_SYSTEM env var, then platform detection)",
    )

    return parser.parse_args()


def detect_operating_system(override: str | None) -> str:
    if override:
        return override

    env_os = os.getenv("OPERATING_SYSTEM")
    if env_os:
        normalized = env_os.strip().upper()
        if normalized in {"LINUX", "WINDOWS"}:
            return normalized

    detected = platform.system().strip().upper()
    if detected == "LINUX":
        return "LINUX"
    if detected == "WINDOWS":
        return "WINDOWS"

    raise RuntimeError(f"Unsupported operating system: {detected}")


def run_scan(config_dir_arg: str | None, os_override: str | None, logger) -> int:
    identity = MachineIdentity.from_env()
    rabbitmq_url = os.getenv("RABBITMQ_URL")

    try:
        operating_system = detect_operating_system(os_override)
    except Exception as exc:
        logger.exception("Unable to determine operating system")
        print(f"Scan failed: {exc}")
        return 2

    config_dir = (
        Path(config_dir_arg)
        if config_dir_arg
        else settings.get_absolute_path(settings.config_dir)
    )

    logger.info(
        "%s",
        identity.startup_banner("installation-agent", rabbitmq_url),
    )

    logger.info(
        "Installation scan starting | tenant=%s machine=%s os=%s config_dir=%s",
        identity.tenant_name,
        identity.machine_reference,
        operating_system,
        config_dir,
    )

    scan_status = "COMPLETED"
    report = None

    if not config_dir.exists():
        logger.error("Config directory does not exist: %s", config_dir)
        scan_status = "MISSING_CONFIG_DIR"
    else:
        try:
            report = run_analysis_pipeline(target_dir=config_dir)
        except Exception:
            logger.exception("Installation scan pipeline failed")
            scan_status = "FAILED"

    result = build_canonical_result(
        report,
        tenant=identity.tenant_name,
        environment=identity.environment_name,
        environment_type=identity.environment_type,
        machine_reference=identity.machine_reference,
        operating_system=operating_system,
        config_path=str(config_dir),
        scan_status=scan_status,
    )

    # --------------------------------------------------------------
    # CLI summary (never prints secret values - result is pre-redacted)
    # --------------------------------------------------------------
    print("Installation Agent")
    print(f"Tenant: {identity.tenant_name}")
    print(f"Machine: {identity.machine_reference}")
    print(f"OS: {operating_system}")
    print()
    print("Config directory:")
    print(str(config_dir))
    print()
    print(f"Files scanned: {result['files_scanned']}")
    print(f"Installation scripts: {result['files_by_type']['scripts']}")
    print(f"Environment files: {result['files_by_type']['environment']}")
    print(f"Generated files: {result['files_by_type']['generated']}")
    print(f"Secrets detected: {len(result['secrets_detected'])}")
    print(f"Issues: {len(result['issues'])}")
    print()
    print(f"Risk score: {result['risk_score']}/100")
    print(f"Risk level: {result['risk_level']}")

    logger.info(
        "Installation scan completed | status=%s files_scanned=%d "
        "secrets_detected=%d risk_score=%d risk_level=%s",
        scan_status,
        result["files_scanned"],
        len(result["secrets_detected"]),
        result["risk_score"],
        result["risk_level"],
    )

    # --------------------------------------------------------------
    # Publish to RabbitMQ (same contract as the other agents)
    # --------------------------------------------------------------
    if rabbitmq_url:
        from app.services.publisher.rabbitmq_publisher import RabbitMqPublisher

        publisher = RabbitMqPublisher(url=rabbitmq_url)
        publisher.publish(agent_key="installation", data=result, identity=identity)
        logger.info("Installation scan result successfully published to RabbitMQ.")
    else:
        logger.warning("RABBITMQ_URL not configured - skipping publish step.")

    # Printed last, on its own, so the orchestrator can find/parse it as the
    # summary line of stdout (matches the log-agent / infrastructure-agent
    # convention of emitting one JSON line at the end of a bounded run).
    print(jsonlib.dumps(result, ensure_ascii=False, default=str))

    if scan_status != "COMPLETED":
        return 2

    return 0


def main() -> int:
    logger = setup_logging(settings.log_level, settings.log_file)
    args = parse_args()

    if not args.scan:
        import uvicorn

        print("Launching Installation Discovery Agent FastAPI Web Server...")
        print("Documentation will be available at: http://127.0.0.1:8000/docs")
        uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
        return 0

    return run_scan(args.config_dir, args.operating_system, logger)


if __name__ == "__main__":
    raise SystemExit(main())
