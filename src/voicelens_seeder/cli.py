#!/usr/bin/env python3
"""
VoiceLens Seeder CLI - Generate synthetic VCP 0.3 compliant conversation data

A powerful CLI toolkit for creating realistic conversation datasets,
computing perception gaps, and generating GTM narratives.
"""

import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.traceback import install

# Install rich traceback for better error formatting
install(show_locals=True)

# Global console for consistent output
console = Console()

# Main app with command groups
app = typer.Typer(
    name="voicelens",
    help="Generate synthetic VCP 0.3 compliant conversation data for GTM narratives",
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)

# Command groups
db_app = typer.Typer(name="db", help="Database operations and migrations")
config_app = typer.Typer(name="config", help="Configuration and profile management")
generate_app = typer.Typer(name="generate", help="Generate synthetic conversation data")
normalize_app = typer.Typer(name="normalize", help="Process and normalize VCP payloads")
classify_app = typer.Typer(name="classify", help="Run agent role classification")
gaps_app = typer.Typer(name="gaps", help="Compute perception gaps")
validate_app = typer.Typer(name="validate", help="Data quality validation")
analyze_app = typer.Typer(name="analyze", help="Generate insights and summaries")
export_app = typer.Typer(name="export", help="Export data to various formats")
send_app = typer.Typer(name="send", help="Send data to remote endpoints")
demo_app = typer.Typer(name="demo", help="Guided workflows and demos")

# Add command groups to main app
app.add_typer(db_app)
app.add_typer(config_app)
app.add_typer(generate_app)
app.add_typer(normalize_app)
app.add_typer(classify_app)
app.add_typer(gaps_app)
app.add_typer(validate_app)
app.add_typer(analyze_app)
app.add_typer(export_app)
app.add_typer(send_app)
app.add_typer(demo_app)

# Global options that can be used with any command
CommonOptions = Annotated[
    Optional[Path],
    typer.Option(
        "--db",
        help="Path to SQLite database file",
        envvar="VOICELENS_DB",
    ),
]

ProfileOption = Annotated[
    Optional[str],
    typer.Option(
        "--profile",
        help="Configuration profile name",
        envvar="VOICELENS_PROFILE",
    ),
]

LogLevelOption = Annotated[
    str,
    typer.Option(
        "--log-level",
        help="Logging level",
        envvar="VOICELENS_LOG_LEVEL",
    ),
]

DryRunOption = Annotated[
    bool,
    typer.Option(
        "--dry-run",
        help="Show what would be done without executing",
        envvar="VOICELENS_DRY_RUN",
    ),
]

YesOption = Annotated[
    bool,
    typer.Option(
        "--yes", "-y",
        help="Skip confirmation prompts",
        envvar="VOICELENS_YES",
    ),
]


# Database commands
@db_app.command("init")
def init_db(
    db: CommonOptions = None,
    yes: YesOption = False,
) -> None:
    """Initialize SQLite database with schema."""
    console.print("🗄️  Initializing VoiceLens database schema...")
    # TODO: Implement database initialization
    console.print("✅ Database initialized successfully")


@db_app.command("migrate")
def migrate_db(
    db: CommonOptions = None,
    target_version: Optional[str] = typer.Option(None, help="Target schema version"),
) -> None:
    """Run database migrations."""
    console.print("🔄 Running database migrations...")
    # TODO: Implement migration logic
    console.print("✅ Migrations completed")


# Configuration commands
@config_app.command("init")
def init_config(
    profile: ProfileOption = None,
) -> None:
    """Initialize configuration with interactive setup."""
    console.print("⚙️  Setting up VoiceLens configuration...")
    # TODO: Implement config initialization
    console.print("✅ Configuration initialized")


@config_app.command("list")
def list_configs() -> None:
    """List all available configuration profiles."""
    console.print("📋 Available profiles:")
    # TODO: Implement profile listing
    console.print("  • happy_path_hvac - HVAC service booking scenarios")
    console.print("  • mixed_scenarios - Diverse conversation types")
    console.print("  • enterprise_support - B2B support scenarios")


@config_app.command("show")
def show_config(
    profile: ProfileOption = None,
) -> None:
    """Show current configuration."""
    console.print(f"🔍 Configuration for profile: {profile or 'default'}")
    # TODO: Implement config display


# Generation commands
@generate_app.command("conversations")
def generate_conversations(
    count: int = typer.Option(100, help="Number of conversations to generate"),
    profile: ProfileOption = None,
    start_days_ago: int = typer.Option(30, help="Generate data starting N days ago"),
    vcp_mode: str = typer.Option("gtm", help="VCP mode: gtm or full"),
    out: Optional[Path] = typer.Option(None, help="Output directory for generated files"),
    dry_run: DryRunOption = False,
) -> None:
    """Generate synthetic conversation data."""
    console.print(f"🎭 Generating {count} synthetic conversations...")
    console.print(f"   Profile: {profile or 'default'}")
    console.print(f"   VCP Mode: {vcp_mode}")
    console.print(f"   Time Range: {start_days_ago} days ago to now")
    
    if dry_run:
        console.print("🔍 [yellow]DRY RUN - no files will be created[/yellow]")
        return
        
    # TODO: Implement conversation generation
    console.print("✅ Conversations generated successfully")


# Demo commands
@demo_app.command("happy-path")
def demo_happy_path(
    profile: ProfileOption = "happy_path_hvac",
    count: int = typer.Option(500, help="Number of conversations"),
    send_endpoint: Optional[str] = typer.Option(None, help="Endpoint to send data to"),
) -> None:
    """Run complete happy path demo workflow."""
    console.print("🚀 [bold green]VoiceLens Happy Path Demo[/bold green]")
    console.print(f"   Generating {count} conversations with profile: {profile}")
    
    # TODO: Implement complete demo workflow
    # 1. Generate synthetic data
    # 2. Normalize and classify
    # 3. Compute perception gaps
    # 4. Validate data quality
    # 5. Generate analytics
    # 6. Export results
    # 7. Optionally send to endpoint
    
    console.print("✅ Happy path demo completed!")
    console.print("📊 Check exports/ directory for generated data")


# Main CLI entry point
@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", help="Show version and exit"
    ),
) -> None:
    """VoiceLens Seeder - Synthetic Data Generation for Voice AI Systems."""
    if version:
        from . import __version__
        console.print(f"VoiceLens Seeder v{__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()