"""
notify_failure.py
------------------
Sends a plain-text alert email when a scheduled GitHub Actions job fails.

Why this exists: three separate Claude-side scheduled tasks (content pack,
growth report, Reddit scout) ran silently 0 times over ~2 months because
they failed with no output and nothing surfaced the failure — the only
signal was "no email arrived," which is indistinguishable from "nothing to
report." GitHub Actions' scheduled workflows are far more reliable, but the
failure mode is the same shape: a workflow can start failing and the only
way to notice is checking the Actions tab, which nobody does daily on a
side project. This makes failure loud instead of silent.

Called as the LAST step of a job, with `if: failure()`, so it only runs
when something upstream in that job already failed. Never raises — a
failure inside a failure-alert step should not produce a second, confusing
failure annotation on top of the real one.

Required env var:
  GMAIL_APP_PASSWORD  — same Gmail App Password used by send_weekly_digest.py

Optional env vars:
  GMAIL_SENDER  — default: info@notadubaibroker.com
  ALERT_EMAIL   — where the alert is sent. Default: info@notadubaibroker.com
                  (Consider pointing this at an inbox you actually check
                  daily — a side-project brand inbox is easy to let go
                  stale, which defeats the point of an alert.)

  GITHUB_WORKFLOW, GITHUB_JOB, GITHUB_REPOSITORY, GITHUB_RUN_ID — provided
  automatically by GitHub Actions; used to build the alert body/link.

Usage (inside a workflow step):
  - name: Alert on failure
    if: failure()
    env:
      GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
      GMAIL_SENDER: ${{ secrets.GMAIL_SENDER }}
      ALERT_EMAIL: ${{ secrets.ALERT_EMAIL }}
    run: python scripts/notify_failure.py
"""

import os
import smtplib
from email.mime.text import MIMEText

SENDER         = os.environ.get("GMAIL_SENDER", "info@notadubaibroker.com")
ALERT_EMAIL    = os.environ.get("ALERT_EMAIL", "info@notadubaibroker.com")
GMAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

WORKFLOW = os.environ.get("GITHUB_WORKFLOW", "unknown workflow")
JOB      = os.environ.get("GITHUB_JOB", "unknown job")
REPO     = os.environ.get("GITHUB_REPOSITORY", "")
RUN_ID   = os.environ.get("GITHUB_RUN_ID", "")
RUN_URL  = f"https://github.com/{REPO}/actions/runs/{RUN_ID}" if REPO and RUN_ID else "(run URL unavailable)"


def main() -> None:
    if not GMAIL_PASSWORD:
        # Don't raise: this step already only runs after a real failure, and
        # a second exception here would just bury the original error under a
        # confusing one. The bare log line is still visible in the raw
        # Actions log for anyone who does go looking.
        print(
            "GMAIL_APP_PASSWORD not set — cannot send failure alert email. "
            f"({WORKFLOW} / {JOB} failed — see {RUN_URL})"
        )
        return

    subject = f"[ADInteract] ⚠ {WORKFLOW} failed"
    body = (
        f"A scheduled ADInteract workflow failed and produced no output.\n\n"
        f"Workflow: {WORKFLOW}\n"
        f"Job:      {JOB}\n"
        f"Run:      {RUN_URL}\n"
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER
    msg["To"] = ALERT_EMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER, GMAIL_PASSWORD)
            server.sendmail(SENDER, [ALERT_EMAIL], msg.as_string())
        print(f"Failure alert sent to {ALERT_EMAIL}.")
    except Exception as e:
        # Same reasoning as above — log, don't raise, inside a failure handler.
        print(f"Failed to send failure alert ({e}). ({WORKFLOW} / {JOB} failed — see {RUN_URL})")


if __name__ == "__main__":
    main()
