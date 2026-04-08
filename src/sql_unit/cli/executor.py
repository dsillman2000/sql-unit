"""Test execution and result formatting for CLI."""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Optional

from sql_unit.cli.discovery import TestInfo
from sql_unit.database import DatabaseManager, ConnectionConfig
from sql_unit.parser import SqlBlockCommentParser
from sql_unit.runner import TestRunner


class TestStatus(str, Enum):
    """Status of a test execution."""

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    SKIP = "skip"


@dataclass
class TestExecutionResult:
    """Result of executing a single test."""

    name: str
    file_path: str
    status: TestStatus
    duration_ms: float
    error_message: Optional[str] = None
    details: dict = field(default_factory=dict)


@dataclass
class ExecutionSummary:
    """Summary of test execution."""

    passed: int = 0
    failed: int = 0
    errors: int = 0
    skipped: int = 0
    total_time_ms: float = 0.0


def execute_tests(
    tests: list[TestInfo],
    connection_config: Optional[ConnectionConfig] = None,
    threads: int = 1,
    verbose: bool = False,
) -> tuple[list[TestExecutionResult], ExecutionSummary]:
    """Execute SQL unit tests.

    Args:
        tests: List of tests to execute
        connection_config: Database connection configuration
        threads: Number of parallel threads (-1 for CPU count, 1 for sequential)
        verbose: Include detailed output

    Returns:
        Tuple of (results list, summary)
    """
    if not tests:
        return [], ExecutionSummary()

    # Convert threads flag
    if threads == -1:
        import multiprocessing

        threads = multiprocessing.cpu_count()
    elif threads < 1:
        threads = 1

    results = []
    summary = ExecutionSummary()
    lock = Lock()

    start_time = time.time()

    if threads == 1:
        # Sequential execution
        for test in tests:
            result = _execute_single_test(test, connection_config, verbose)
            results.append(result)
            _update_summary(summary, result, lock)
    else:
        # Parallel execution
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {
                executor.submit(_execute_single_test, test, connection_config, verbose): test
                for test in tests
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    _update_summary(summary, result, lock)
                except Exception as e:
                    test = futures[future]
                    results.append(
                        TestExecutionResult(
                            name=test.name,
                            file_path=test.file_path,
                            status=TestStatus.ERROR,
                            duration_ms=0.0,
                            error_message=str(e),
                        )
                    )
                    _update_summary(summary, results[-1], lock)

    summary.total_time_ms = (time.time() - start_time) * 1000
    return results, summary


def _execute_single_test(
    test: TestInfo,
    connection_config: Optional[ConnectionConfig],
    verbose: bool,
) -> TestExecutionResult:
    """Execute a single test.

    Args:
        test: Test to execute
        connection_config: Database connection configuration
        verbose: Include detailed output

    Returns:
        Test execution result
    """
    if not connection_config:
        return TestExecutionResult(
            name=test.name,
            file_path=test.file_path,
            status=TestStatus.ERROR,
            duration_ms=0.0,
            error_message="No database connection configured",
        )

    start_time = time.time()

    try:
        # Parse test file
        test_file = SqlBlockCommentParser.parse(test.file_path)

        # Find the test definition
        test_def = None
        for td in test_file.test_definitions:
            if td.name == test.name:
                test_def = td
                break

        if not test_def:
            return TestExecutionResult(
                name=test.name,
                file_path=test.file_path,
                status=TestStatus.ERROR,
                duration_ms=(time.time() - start_time) * 1000,
                error_message="Test definition not found",
            )

        # Execute test
        db_manager = DatabaseManager(connection_config)
        runner = TestRunner(db_manager)

        result = runner.run_test(test_def)

        duration_ms = (time.time() - start_time) * 1000

        # Determine status
        if result.skipped:
            status = TestStatus.SKIP
        elif result.passed:
            status = TestStatus.PASS
        else:
            status = TestStatus.FAIL

        details = {}
        if verbose:
            details = {
                "assertions": len(result.error_report.assertions) if result.error_report else 0,
            }

        return TestExecutionResult(
            name=test.name,
            file_path=test.file_path,
            status=status,
            duration_ms=duration_ms,
            error_message=None
            if status == TestStatus.PASS
            else result.error_report.message
            if result.error_report
            else None,
            details=details,
        )

    except Exception as e:
        return TestExecutionResult(
            name=test.name,
            file_path=test.file_path,
            status=TestStatus.ERROR,
            duration_ms=(time.time() - start_time) * 1000,
            error_message=str(e),
        )


def _update_summary(summary: ExecutionSummary, result: TestExecutionResult, lock: Lock) -> None:
    """Update summary with test result."""
    with lock:
        if result.status == TestStatus.PASS:
            summary.passed += 1
        elif result.status == TestStatus.FAIL:
            summary.failed += 1
        elif result.status == TestStatus.ERROR:
            summary.errors += 1
        elif result.status == TestStatus.SKIP:
            summary.skipped += 1
