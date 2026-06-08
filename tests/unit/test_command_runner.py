from model_due_diligence.external.command_runner import run_command


def test_missing_command() -> None:
    result = run_command("missing", ["definitely-not-a-real-command-xyz"])
    assert result.available is False
