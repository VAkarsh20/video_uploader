import sys
import smtplib
from email.message import EmailMessage
from pathlib import Path
import yaml

try:
    from logger import Logger
except ImportError:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))
    from logger import Logger


def get_config(login_file: Path) -> dict:
    """Load and validate configuration from YAML."""
    if not login_file.exists():
        raise FileNotFoundError(f"Missing login file: {login_file}")

    with open(login_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        conf = data.get("gmail", {})

    # Define required keys and their display names
    required = {
        "host": "host",
        "port": "port",
        "user_name": "username",
        "credential": "password",
    }

    missing = [display for key, display in required.items() if not conf.get(key)]
    if missing:
        raise ValueError(f"Missing fields in {login_file}: {', '.join(missing)}")

    return conf


def email_description(path: Path, conf: dict) -> None:
    """Send video description using provided configuration dictionary."""
    Logger.phase("Email Description")

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    body = path.read_text(encoding="utf-8")

    msg = EmailMessage()
    msg["From"] = conf["user_name"]
    msg["To"] = conf["user_name"]
    msg["Subject"] = f"Video Description: {path.name}".strip(".md")

    # 1. Set the plain text content
    msg.set_content(body)

    # 2. Add an HTML version to prevent "From " escaping and preserve emojis/formatting
    # We replace newlines with <br> to maintain your spacing in HTML
    html_body = body.replace("\n", "<br>")
    msg.add_alternative(
        f"""
    <html>
      <body>
        <div style="font-family: sans-serif; line-height: 1.5;">
            {html_body}
        </div>
      </body>
    </html>
    """,
        subtype="html",
    )

    Logger.info(
        f"Connecting to SMTP {conf['host']}:{conf['port']} as {conf['user_name']}"
    )

    with smtplib.SMTP(conf["host"], int(conf["port"])) as smtp:
        smtp.starttls()
        smtp.login(conf["user_name"], conf["credential"])
        smtp.send_message(msg)

    Logger.success(f"Email sent to {conf['user_name']}")


def main(argv: list[str] | None = None) -> int:
    Logger(log_file_path="automation.log")
    login_path = Path("login_details.yml")
    argv = argv or sys.argv

    # 1. Determine the path (Argv or Input)
    if len(argv) >= 2:
        file_path = Path(argv[1])
    else:
        prompt = f"\n{Logger.BOLD}{Logger.INFO}[INPUT]{Logger.ENDC} Enter the path to the description file (or 'q' to quit): "
        print(prompt, end="")
        user_input = input().strip().strip("'").strip('"')

        if user_input.lower() in ["q", "quit", ""]:
            Logger.info("Exiting workflow.")
            return 0
        file_path = Path(user_input)

    # 2. Execute with unified error handling
    try:
        config = get_config(login_path)
        email_description(file_path, config)
        return 0
    except Exception as e:
        error_msg = f"Email Operation failed: {e}"
        Logger.error(error_msg)
        print(error_msg, file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)
