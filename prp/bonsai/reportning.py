"""For reporting workflow events."""

from click import secho


class Reporter:
    """Hook for reporting workflow events to the CLI or logging system."""

    def on_step_start(self, sample_id: str | None, step: str):
        """Called when a step starts."""

    def on_step_success(self, sample_id: str | None, step: str):
        """Called when a step completes successfully."""

    def on_step_skip(self, sample_id: str | None, step: str):
        """Called when a step is skipped (e.g., already done in a resumed workflow)."""

    def on_step_fail(self, sample_id: str | None, step: str, error: Exception):
        """Called when a step fails with an error."""

    def on_resume(self, sample_id: str, completed_steps: list[str]):
        """Called when resuming a workflow, with a list of already completed steps."""


class SimpleReporter(Reporter):
    """Basic console reporter using click.secho for colored output."""

    def on_step_start(self, sample_id, step):
        secho(f"➡️  [{sample_id}] Starting: {step}...")

    def on_step_success(self, sample_id, step):
        secho(f"   ✓ [{sample_id}] Completed: {step}", fg="green")

    def on_step_skip(self, sample_id, step):
        secho(f"   • [{sample_id}] Skipped: {step}", fg="bright_black")

    def on_step_fail(self, sample_id, step, error):
        secho(f"   ✗ [{sample_id}] FAILED in '{step}': {error}", fg="red")

    def on_resume(self, sample_id, completed_steps):
        secho(
            f"🔁 Resuming [{sample_id}] — completed steps: {', '.join(completed_steps)}",
            fg="yellow",
        )
