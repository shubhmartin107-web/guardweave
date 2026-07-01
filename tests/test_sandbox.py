import pytest

from guardweave.sandbox.executor import SandboxExecutor
from guardweave.sandbox.resource_limit import ResourceLimits


@pytest.mark.slow
@pytest.mark.asyncio
async def test_sandbox_echo():
    executor = SandboxExecutor()
    result = await executor.execute(["echo", "hello"])
    assert result.success
    assert result.stdout.strip() == "hello"
    assert result.exit_code == 0


@pytest.mark.slow
@pytest.mark.asyncio
async def test_sandbox_blocked_command():
    executor = SandboxExecutor()
    result = await executor.execute(["sudo", "ls"])
    assert not result.success
    assert result.resource_violation
    assert "blocked" in result.violation_reason.lower()


@pytest.mark.slow
@pytest.mark.asyncio
async def test_sandbox_timeout():
    executor = SandboxExecutor()
    limits = ResourceLimits(max_cpu_time_seconds=1)
    result = await executor.execute(["sleep", "10"], limits=limits)
    assert result.timed_out


@pytest.mark.slow
@pytest.mark.asyncio
async def test_sandbox_no_network():
    executor = SandboxExecutor()
    limits = ResourceLimits(network_access=False)
    result = await executor.execute(["curl", "http://example.com"], limits=limits)
    assert not result.success
    assert result.resource_violation


@pytest.mark.slow
@pytest.mark.asyncio
async def test_sandbox_env_cleanup():
    executor = SandboxExecutor()
    limits = ResourceLimits(env_whitelist=["PATH"])
    result = await executor.execute(["env"], limits=limits)
    assert result.success
    assert "PATH=" in result.stdout
    assert "SECRET" not in result.stdout


@pytest.mark.slow
@pytest.mark.asyncio
async def test_sandbox_exit_code():
    executor = SandboxExecutor()
    result = await executor.execute(["sh", "-c", "exit 42"])
    assert not result.success
    assert result.exit_code == 42


@pytest.mark.slow
@pytest.mark.asyncio
async def test_sandbox_command_not_found():
    executor = SandboxExecutor()
    result = await executor.execute(["nonexistent_command_xyz"])
    assert not result.success
    assert "not found" in result.stderr.lower() or "not found" in result.violation_reason


@pytest.mark.slow
@pytest.mark.asyncio
async def test_sandbox_cwd():
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        executor = SandboxExecutor(work_dir=tmpdir)
        result = await executor.execute(["pwd"])
        assert result.success
        assert tmpdir in result.stdout.strip()
