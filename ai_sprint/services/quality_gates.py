"""Quality gate execution service.

This module implements quality gates that enforce code standards:
- Static analysis (linting, type checking, complexity)
- Test quality (coverage, mutation testing)
- Security scanning (SAST, dependencies, secrets)
"""

import json
import logging
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from ai_sprint.config.settings import Settings

logger = logging.getLogger(__name__)


class GateType(Enum):
    """Quality gate types."""

    LINTING = "linting"
    TYPE_CHECKING = "type_checking"
    COMPLEXITY = "complexity"
    COVERAGE = "coverage"
    MUTATION = "mutation"
    SAST = "sast"
    DEPENDENCY_SCAN = "dependency_scan"
    SECRET_DETECTION = "secret_detection"


class GateStatus(Enum):
    """Quality gate execution status."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class GateResult:
    """Result of a quality gate execution."""

    gate_type: GateType
    status: GateStatus
    message: str
    details: dict
    score: Optional[float] = None


# =============================================================================
# T069: Quality gate runner framework
# =============================================================================


class QualityGateRunner:
    """
    Quality gate execution framework.

    Provides common infrastructure for running quality gates:
    - Tool execution with subprocess
    - Result parsing and validation
    - Threshold checking
    - Error handling
    """

    def __init__(self, settings: Settings, working_dir: Path):
        """
        Initialize quality gate runner.

        Args:
            settings: Application settings
            working_dir: Directory to run gates in
        """
        self.settings = settings
        self.working_dir = working_dir
        self.results: list[GateResult] = []

    def run_gate(
        self,
        gate_type: GateType,
        required: bool = True,
    ) -> GateResult:
        """
        Run a specific quality gate.

        Args:
            gate_type: Type of gate to run
            required: Whether this gate is required (vs optional)

        Returns:
            GateResult with status and details
        """
        logger.info(f"Running {gate_type.value} gate")

        try:
            if gate_type == GateType.LINTING:
                result = self._run_linting_gate()
            elif gate_type == GateType.TYPE_CHECKING:
                result = self._run_type_checking_gate()
            elif gate_type == GateType.COMPLEXITY:
                result = self._run_complexity_gate()
            elif gate_type == GateType.COVERAGE:
                result = self._run_coverage_gate()
            elif gate_type == GateType.MUTATION:
                result = self._run_mutation_gate()
            elif gate_type == GateType.SAST:
                result = self._run_sast_gate()
            elif gate_type == GateType.DEPENDENCY_SCAN:
                result = self._run_dependency_scan_gate()
            elif gate_type == GateType.SECRET_DETECTION:
                result = self._run_secret_detection_gate()
            else:
                result = GateResult(
                    gate_type=gate_type,
                    status=GateStatus.ERROR,
                    message=f"Unknown gate type: {gate_type}",
                    details={},
                )
        except Exception as e:
            logger.error(f"Error running {gate_type.value} gate: {e}")
            result = GateResult(
                gate_type=gate_type,
                status=GateStatus.ERROR if required else GateStatus.SKIP,
                message=f"Gate execution failed: {e}",
                details={"error": str(e)},
            )

        self.results.append(result)
        return result

    def run_all_gates(
        self,
        stage: str = "review",
    ) -> list[GateResult]:
        """
        Run all quality gates for a specific stage.

        Args:
            stage: Stage name (review, tests, merge)

        Returns:
            List of GateResult objects
        """
        self.results = []

        if stage == "review":
            # CAB stage: linting, type checking, complexity
            self.run_gate(GateType.LINTING, required=True)
            self.run_gate(GateType.TYPE_CHECKING, required=True)
            self.run_gate(GateType.COMPLEXITY, required=True)
        elif stage == "tests":
            # Tester stage: coverage, mutation testing
            self.run_gate(GateType.COVERAGE, required=True)
            self.run_gate(GateType.MUTATION, required=False)  # Optional
        elif stage == "merge":
            # Refinery stage: security gates
            self.run_gate(GateType.SAST, required=True)
            self.run_gate(GateType.DEPENDENCY_SCAN, required=True)
            self.run_gate(GateType.SECRET_DETECTION, required=True)

        return self.results

    def all_gates_passed(self) -> bool:
        """
        Check if all required gates passed.

        Returns:
            True if all required gates passed
        """
        for result in self.results:
            if result.status == GateStatus.FAIL:
                return False
            if result.status == GateStatus.ERROR:
                return False
        return True

    def get_failure_message(self) -> str:
        """
        Generate detailed failure message from failed gates.

        Implementation of T081: Specific rejection messages per gate.

        Returns:
            Human-readable failure message
        """
        failed_gates = [r for r in self.results if r.status == GateStatus.FAIL]
        error_gates = [r for r in self.results if r.status == GateStatus.ERROR]

        if not failed_gates and not error_gates:
            return "All quality gates passed"

        lines = ["Quality gate failures:"]
        lines.append("")

        for result in failed_gates:
            lines.append(f"❌ {result.gate_type.value.upper()}: {result.message}")
            if result.details:
                for key, value in result.details.items():
                    lines.append(f"   - {key}: {value}")
            lines.append("")

        for result in error_gates:
            lines.append(f"⚠️ {result.gate_type.value.upper()}: {result.message}")
            lines.append("")

        return "\n".join(lines)

    # =========================================================================
    # T070: Linting gate (ruff integration)
    # =========================================================================

    def _run_linting_gate(self) -> GateResult:
        """
        Run ruff linting gate.

        Returns:
            GateResult with linting results
        """
        try:
            result = subprocess.run(
                ["ruff", "check", "--output-format=json", "."],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                return GateResult(
                    gate_type=GateType.LINTING,
                    status=GateStatus.PASS,
                    message="No linting errors found",
                    details={"violations": 0},
                )

            # Parse ruff JSON output
            try:
                violations = json.loads(result.stdout)
                error_count = len(violations)

                return GateResult(
                    gate_type=GateType.LINTING,
                    status=GateStatus.FAIL,
                    message=f"Found {error_count} linting violations",
                    details={
                        "violations": error_count,
                        "errors": violations[:10],  # First 10 errors
                    },
                )
            except json.JSONDecodeError:
                return GateResult(
                    gate_type=GateType.LINTING,
                    status=GateStatus.ERROR,
                    message="Failed to parse ruff output",
                    details={"stdout": result.stdout[:500]},
                )

        except subprocess.TimeoutExpired:
            return GateResult(
                gate_type=GateType.LINTING,
                status=GateStatus.ERROR,
                message="Linting timed out after 120 seconds",
                details={},
            )
        except FileNotFoundError:
            return GateResult(
                gate_type=GateType.LINTING,
                status=GateStatus.SKIP,
                message="ruff not installed - skipping linting gate",
                details={},
            )

    # =========================================================================
    # T071: Type checking gate (mypy integration)
    # =========================================================================

    def _run_type_checking_gate(self) -> GateResult:
        """
        Run mypy type checking gate.

        Returns:
            GateResult with type checking results
        """
        try:
            result = subprocess.run(
                ["mypy", "--json-report", "/tmp/mypy-report", "."],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=180,
            )

            if result.returncode == 0:
                return GateResult(
                    gate_type=GateType.TYPE_CHECKING,
                    status=GateStatus.PASS,
                    message="No type errors found",
                    details={"errors": 0},
                )

            # Parse stderr for error count
            error_count = result.stderr.count("error:")

            return GateResult(
                gate_type=GateType.TYPE_CHECKING,
                status=GateStatus.FAIL,
                message=f"Found {error_count} type errors",
                details={
                    "errors": error_count,
                    "output": result.stdout[:1000],
                },
            )

        except subprocess.TimeoutExpired:
            return GateResult(
                gate_type=GateType.TYPE_CHECKING,
                status=GateStatus.ERROR,
                message="Type checking timed out after 180 seconds",
                details={},
            )
        except FileNotFoundError:
            return GateResult(
                gate_type=GateType.TYPE_CHECKING,
                status=GateStatus.SKIP,
                message="mypy not installed - skipping type checking gate",
                details={},
            )

    # =========================================================================
    # T072: Complexity gate (radon integration, max 15 cyclomatic)
    # =========================================================================

    def _run_complexity_gate(self) -> GateResult:
        """
        Run radon complexity analysis gate.

        Returns:
            GateResult with complexity results
        """
        try:
            result = subprocess.run(
                ["radon", "cc", "-j", "-n", "D", "."],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                return GateResult(
                    gate_type=GateType.COMPLEXITY,
                    status=GateStatus.ERROR,
                    message="radon execution failed",
                    details={"stderr": result.stderr[:500]},
                )

            # Parse JSON output
            try:
                complexity_data = json.loads(result.stdout)
                max_complexity = self.settings.quality.complexity_max

                violations = []
                max_found = 0

                for file_path, functions in complexity_data.items():
                    for func in functions:
                        complexity = func.get("complexity", 0)
                        if complexity > max_complexity:
                            violations.append(
                                {
                                    "file": file_path,
                                    "function": func.get("name"),
                                    "complexity": complexity,
                                }
                            )
                        max_found = max(max_found, complexity)

                if violations:
                    return GateResult(
                        gate_type=GateType.COMPLEXITY,
                        status=GateStatus.FAIL,
                        message=f"Found {len(violations)} functions exceeding complexity threshold {max_complexity}",
                        details={
                            "threshold": max_complexity,
                            "max_found": max_found,
                            "violations": violations[:10],
                        },
                    )

                return GateResult(
                    gate_type=GateType.COMPLEXITY,
                    status=GateStatus.PASS,
                    message=f"All functions below complexity threshold {max_complexity}",
                    details={
                        "threshold": max_complexity,
                        "max_found": max_found,
                    },
                )

            except json.JSONDecodeError:
                return GateResult(
                    gate_type=GateType.COMPLEXITY,
                    status=GateStatus.ERROR,
                    message="Failed to parse radon output",
                    details={"stdout": result.stdout[:500]},
                )

        except subprocess.TimeoutExpired:
            return GateResult(
                gate_type=GateType.COMPLEXITY,
                status=GateStatus.ERROR,
                message="Complexity analysis timed out after 60 seconds",
                details={},
            )
        except FileNotFoundError:
            return GateResult(
                gate_type=GateType.COMPLEXITY,
                status=GateStatus.SKIP,
                message="radon not installed - skipping complexity gate",
                details={},
            )

    # =========================================================================
    # T073: Coverage gate (pytest-cov, min 80%)
    # =========================================================================

    def _run_coverage_gate(self) -> GateResult:
        """
        Run pytest coverage gate.

        Returns:
            GateResult with coverage results
        """
        try:
            result = subprocess.run(
                [
                    "pytest",
                    "--cov=.",
                    "--cov-report=json:/tmp/coverage.json",
                    "--cov-report=term",
                ],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Read coverage JSON
            coverage_file = Path("/tmp/coverage.json")
            if not coverage_file.exists():
                return GateResult(
                    gate_type=GateType.COVERAGE,
                    status=GateStatus.ERROR,
                    message="Coverage report not generated",
                    details={},
                )

            with coverage_file.open() as f:
                coverage_data = json.load(f)

            total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
            threshold = self.settings.quality.coverage_threshold

            if total_coverage >= threshold:
                return GateResult(
                    gate_type=GateType.COVERAGE,
                    status=GateStatus.PASS,
                    message=f"Coverage {total_coverage:.1f}% meets threshold {threshold}%",
                    details={
                        "coverage": total_coverage,
                        "threshold": threshold,
                    },
                    score=total_coverage,
                )

            return GateResult(
                gate_type=GateType.COVERAGE,
                status=GateStatus.FAIL,
                message=f"Coverage {total_coverage:.1f}% below threshold {threshold}%",
                details={
                    "coverage": total_coverage,
                    "threshold": threshold,
                    "shortfall": threshold - total_coverage,
                },
                score=total_coverage,
            )

        except subprocess.TimeoutExpired:
            return GateResult(
                gate_type=GateType.COVERAGE,
                status=GateStatus.ERROR,
                message="Coverage tests timed out after 300 seconds",
                details={},
            )
        except FileNotFoundError:
            return GateResult(
                gate_type=GateType.COVERAGE,
                status=GateStatus.SKIP,
                message="pytest not installed - skipping coverage gate",
                details={},
            )

    # =========================================================================
    # T074: Mutation testing gate (mutmut, min 80%)
    # =========================================================================

    def _run_mutation_gate(self) -> GateResult:
        """
        Run mutmut mutation testing gate.

        Returns:
            GateResult with mutation testing results
        """
        try:
            # Run mutmut
            result = subprocess.run(
                ["mutmut", "run", "--paths-to-mutate=."],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes for mutation testing
            )

            # Get results
            result_cmd = subprocess.run(
                ["mutmut", "results"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Parse results from stdout
            output = result_cmd.stdout

            # Extract mutation score (simplified parsing)
            # Format: "Killed: X, Survived: Y, Timeout: Z"
            killed = 0
            survived = 0

            for line in output.split("\n"):
                if "Killed" in line:
                    try:
                        killed = int(line.split(":")[1].strip().split()[0])
                    except (IndexError, ValueError):
                        pass
                if "Survived" in line:
                    try:
                        survived = int(line.split(":")[1].strip().split()[0])
                    except (IndexError, ValueError):
                        pass

            total = killed + survived
            mutation_score = (killed / total * 100) if total > 0 else 0
            threshold = self.settings.quality.mutation_threshold

            if mutation_score >= threshold:
                return GateResult(
                    gate_type=GateType.MUTATION,
                    status=GateStatus.PASS,
                    message=f"Mutation score {mutation_score:.1f}% meets threshold {threshold}%",
                    details={
                        "score": mutation_score,
                        "threshold": threshold,
                        "killed": killed,
                        "survived": survived,
                    },
                    score=mutation_score,
                )

            return GateResult(
                gate_type=GateType.MUTATION,
                status=GateStatus.FAIL,
                message=f"Mutation score {mutation_score:.1f}% below threshold {threshold}%",
                details={
                    "score": mutation_score,
                    "threshold": threshold,
                    "killed": killed,
                    "survived": survived,
                },
                score=mutation_score,
            )

        except subprocess.TimeoutExpired:
            return GateResult(
                gate_type=GateType.MUTATION,
                status=GateStatus.ERROR,
                message="Mutation testing timed out after 600 seconds",
                details={},
            )
        except FileNotFoundError:
            return GateResult(
                gate_type=GateType.MUTATION,
                status=GateStatus.SKIP,
                message="mutmut not installed - skipping mutation gate",
                details={},
            )

    # =========================================================================
    # T075: SAST gate (semgrep integration)
    # =========================================================================

    def _run_sast_gate(self) -> GateResult:
        """
        Run semgrep SAST scanning gate.

        Returns:
            GateResult with SAST results
        """
        try:
            result = subprocess.run(
                [
                    "semgrep",
                    "scan",
                    "--config=auto",
                    "--json",
                    ".",
                ],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Parse JSON output
            try:
                findings = json.loads(result.stdout)
                results = findings.get("results", [])

                # Count by severity
                critical = sum(1 for r in results if r.get("extra", {}).get("severity") == "ERROR")
                high = sum(1 for r in results if r.get("extra", {}).get("severity") == "WARNING")

                if critical > 0 or high > 0:
                    return GateResult(
                        gate_type=GateType.SAST,
                        status=GateStatus.FAIL,
                        message=f"Found {critical} critical and {high} high severity findings",
                        details={
                            "critical": critical,
                            "high": high,
                            "total": len(results),
                            "findings": results[:5],  # First 5 findings
                        },
                    )

                return GateResult(
                    gate_type=GateType.SAST,
                    status=GateStatus.PASS,
                    message="No critical or high severity findings",
                    details={
                        "critical": 0,
                        "high": 0,
                        "total": len(results),
                    },
                )

            except json.JSONDecodeError:
                return GateResult(
                    gate_type=GateType.SAST,
                    status=GateStatus.ERROR,
                    message="Failed to parse semgrep output",
                    details={"stdout": result.stdout[:500]},
                )

        except subprocess.TimeoutExpired:
            return GateResult(
                gate_type=GateType.SAST,
                status=GateStatus.ERROR,
                message="SAST scan timed out after 300 seconds",
                details={},
            )
        except FileNotFoundError:
            return GateResult(
                gate_type=GateType.SAST,
                status=GateStatus.SKIP,
                message="semgrep not installed - skipping SAST gate",
                details={},
            )

    # =========================================================================
    # T076: Dependency scan gate (trivy integration)
    # =========================================================================

    def _run_dependency_scan_gate(self) -> GateResult:
        """
        Run trivy dependency vulnerability scanning gate.

        Returns:
            GateResult with dependency scan results
        """
        try:
            result = subprocess.run(
                [
                    "trivy",
                    "fs",
                    "--format=json",
                    "--severity=CRITICAL,HIGH,MEDIUM",
                    ".",
                ],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Parse JSON output
            try:
                scan_data = json.loads(result.stdout)
                results = scan_data.get("Results", [])

                critical = 0
                high = 0
                medium = 0

                for result_item in results:
                    vulnerabilities = result_item.get("Vulnerabilities", [])
                    for vuln in vulnerabilities:
                        severity = vuln.get("Severity", "").upper()
                        if severity == "CRITICAL":
                            critical += 1
                        elif severity == "HIGH":
                            high += 1
                        elif severity == "MEDIUM":
                            medium += 1

                # Check thresholds
                max_critical = self.settings.security.critical_cve_max
                max_high = self.settings.security.high_cve_max
                max_medium = self.settings.security.medium_cve_max

                if critical > max_critical or high > max_high or medium > max_medium:
                    return GateResult(
                        gate_type=GateType.DEPENDENCY_SCAN,
                        status=GateStatus.FAIL,
                        message=f"Found {critical} critical, {high} high, {medium} medium CVEs",
                        details={
                            "critical": critical,
                            "high": high,
                            "medium": medium,
                            "thresholds": {
                                "critical_max": max_critical,
                                "high_max": max_high,
                                "medium_max": max_medium,
                            },
                        },
                    )

                return GateResult(
                    gate_type=GateType.DEPENDENCY_SCAN,
                    status=GateStatus.PASS,
                    message="Dependency vulnerabilities within acceptable thresholds",
                    details={
                        "critical": critical,
                        "high": high,
                        "medium": medium,
                    },
                )

            except json.JSONDecodeError:
                return GateResult(
                    gate_type=GateType.DEPENDENCY_SCAN,
                    status=GateStatus.ERROR,
                    message="Failed to parse trivy output",
                    details={"stdout": result.stdout[:500]},
                )

        except subprocess.TimeoutExpired:
            return GateResult(
                gate_type=GateType.DEPENDENCY_SCAN,
                status=GateStatus.ERROR,
                message="Dependency scan timed out after 300 seconds",
                details={},
            )
        except FileNotFoundError:
            return GateResult(
                gate_type=GateType.DEPENDENCY_SCAN,
                status=GateStatus.SKIP,
                message="trivy not installed - skipping dependency scan gate",
                details={},
            )

    # =========================================================================
    # T077: Secret detection gate (trufflehog integration)
    # =========================================================================

    def _run_secret_detection_gate(self) -> GateResult:
        """
        Run trufflehog secret detection gate.

        Returns:
            GateResult with secret detection results
        """
        try:
            result = subprocess.run(
                [
                    "trufflehog",
                    "filesystem",
                    "--json",
                    ".",
                ],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=180,
            )

            # Parse JSON output (one JSON object per line)
            secrets_found = []
            for line in result.stdout.split("\n"):
                if line.strip():
                    try:
                        secret = json.loads(line)
                        secrets_found.append(secret)
                    except json.JSONDecodeError:
                        continue

            if secrets_found:
                return GateResult(
                    gate_type=GateType.SECRET_DETECTION,
                    status=GateStatus.FAIL,
                    message=f"Found {len(secrets_found)} potential secrets",
                    details={
                        "count": len(secrets_found),
                        "secrets": [
                            {
                                "file": s.get("SourceMetadata", {}).get("Data", {}).get("Filesystem", {}).get("file"),
                                "detector": s.get("DetectorName"),
                            }
                            for s in secrets_found[:5]
                        ],
                    },
                )

            return GateResult(
                gate_type=GateType.SECRET_DETECTION,
                status=GateStatus.PASS,
                message="No secrets detected",
                details={"count": 0},
            )

        except subprocess.TimeoutExpired:
            return GateResult(
                gate_type=GateType.SECRET_DETECTION,
                status=GateStatus.ERROR,
                message="Secret detection timed out after 180 seconds",
                details={},
            )
        except FileNotFoundError:
            return GateResult(
                gate_type=GateType.SECRET_DETECTION,
                status=GateStatus.SKIP,
                message="trufflehog not installed - skipping secret detection gate",
                details={},
            )
