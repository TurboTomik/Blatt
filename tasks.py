"""
Invoke tasks for Django project management.

Run with: uv run inv[oke] <task-name>

uv Integration:
- `invoke setup` - Uses `uv init` and `uv sync`
- `invoke deps.add <package>` - Add packages with uv
- `invoke deps.remove <package>` - Remove packages
- `invoke deps.sync` - Sync dependencies
- `invoke deps.lock` - Update lock file

pytest Integration:
- `invoke test.run` - Run tests with pytest
- `invoke test.coverage` - Coverage with pytest-cov

ruff Integration:
- `invoke lint.check` - Check code with ruff
- `invoke lint.format` - Format code with ruff
- `invoke lint --fix` - Auto-fix issues

Additional Features:
- `invoke clean` - Clean up temp files and caches.
- `invoke ci` - Full CI pipeline
- `invoke dev` - Quick development setup
"""

from pathlib import Path

from invoke import Collection, task
from invoke.exceptions import Exit


@task
def runserver(c, host="127.0.0.1", port=8000, settings=None):
    """
    Start Django development server using uv.

    Args:
        host: Server host (default: 127.0.0.1)
        port: Server port (default: 8000)
        settings: Django settings module
    """
    print(f"🌐 Starting Django server on {host}:{port}")

    cmd = f"uv run python manage.py runserver {host}:{port}"
    if settings:
        cmd = f"DJANGO_SETTINGS_MODULE={settings} {cmd}"

    c.run(cmd, pty=True)


@task
def shell(c, settings=None):
    """
    Start Django shell using uv.

    Args:
        settings: Django settings module
    """
    print("🐍 Starting Django shell...")

    cmd = "uv run python manage.py shell"
    if settings:
        cmd = f"DJANGO_SETTINGS_MODULE={settings} {cmd}"

    c.run(cmd, pty=True)


@task
def migrate(c, app=None, fake=False, settings=None):
    """
    Run Django migrations using uv.

    Args:
        app: Specific app to migrate
        fake: Mark migrations as run without actually running them
        settings: Django settings module
    """
    print("📦 Running Django migrations...")

    cmd = "uv run python manage.py migrate"
    if app:
        cmd += f" {app}"
    if fake:
        cmd += " --fake"

    if settings:
        cmd = f"DJANGO_SETTINGS_MODULE={settings} {cmd}"

    c.run(cmd)
    print("✅ Migrations completed!")


@task
def makemigrations(c, app=None, name=None, empty=False, settings=None):
    """
    Create Django migrations using uv.

    Args:
        app: Specific app to create migrations for
        name: Migration name
        empty: Create empty migration
        settings: Django settings module
    """
    print("📝 Creating Django migrations...")

    cmd = "uv run python manage.py makemigrations"
    if app:
        cmd += f" {app}"
    if name:
        cmd += f" --name {name}"
    if empty:
        cmd += " --empty"

    if settings:
        cmd = f"DJANGO_SETTINGS_MODULE={settings} {cmd}"

    c.run(cmd)
    print("✅ Migrations created!")


@task
def test(
    c,
    app=None,
    pattern=None,
    keepdb=False,
    verbose=False,
    settings=None,
):
    """
    Run tests using pytest.

    Args:
        app: Specific app to test
        pattern: Test pattern to match
        keepdb: Keep test database
        verbose: Verbose output
        settings: Django settings module
    """
    print("🧪 Running tests with pytest...")

    cmd = "uv run pytest"

    if verbose:
        cmd += " -v"
    if keepdb:
        cmd += " --reuse-db"
    if pattern:
        cmd += f" -k {pattern}"
    if app:
        cmd += f" {app}/"

    if settings:
        cmd = f"DJANGO_SETTINGS_MODULE={settings} {cmd}"

    result = c.run(cmd, warn=True)
    if result.exited != 0:
        print("❌ Tests failed!")
        raise Exit(code=1)

    print("✅ All tests passed!")


@task
def coverage(c, app=None, html=False, settings=None):
    """
    Run tests with coverage report using pytest-cov.

    Args:
        app: Specific app to test
        html: Generate HTML coverage report
        settings: Django settings module
    """
    print("📊 Running tests with coverage...")

    cmd = "uv run pytest --cov=."
    if app:
        cmd += f" {app}/"
    if html:
        cmd += " --cov-report=html"

    # Always show terminal report
    cmd += " --cov-report=term-missing"

    if settings:
        cmd = f"DJANGO_SETTINGS_MODULE={settings} {cmd}"

    c.run(cmd)

    if html:
        print("📄 HTML coverage report generated in htmlcov/")

    print("✅ Coverage analysis completed!")


@task
def lint(c, fix=False, check=False):
    """
    Run code linting and formatting with ruff.

    Args:
        fix: Automatically fix issues
        check: Only check, don't fix
    """
    print("🔍 Running code linting with ruff...")

    if fix:
        print("Running ruff (with fixes)...")
        c.run("uv run ruff check --fix .")
        c.run("uv run ruff format .")
        print("✅ Code formatted and linted with ruff!")
    elif check:
        print("Running ruff (check only)...")
        result1 = c.run("uv run ruff check .", warn=True)
        result2 = c.run("uv run ruff format --check .", warn=True)

        if result1.exited != 0 or result2.exited != 0:
            print("❌ Ruff found issues! Run 'invoke lint --fix' to fix them.")
            raise Exit(code=1)
        print("✅ No linting issues found!")
    else:
        # Default behavior: check and show issues
        c.run("uv run ruff check .")
        result = c.run("uv run ruff format --check .", warn=True)
        if result.exited != 0:
            print("💡 Run 'invoke lint --fix' to automatically fix formatting issues.")


@task
def format(c):
    """
    Format code with ruff.
    """
    print("🎨 Formatting code with ruff...")
    c.run("uv run ruff format .")
    print("✅ Code formatted!")


@task
def collectstatic(c, noinput=True, settings=None):
    """
    Collect static files using uv.

    Args:
        noinput: Don't prompt for user input
        settings: Django settings module
    """
    print("📁 Collecting static files...")

    cmd = "uv run python manage.py collectstatic"
    if noinput:
        cmd += " --noinput"

    if settings:
        cmd = f"DJANGO_SETTINGS_MODULE={settings} {cmd}"

    c.run(cmd)
    print("✅ Static files collected!")


@task
def createsuperuser(c, username=None, email=None, settings=None):
    """
    Create Django superuser using uv.

    Args:
        username: Superuser username
        email: Superuser email
        settings: Django settings module
    """
    print("👤 Creating Django superuser...")

    cmd = "uv run python manage.py createsuperuser"
    if username:
        cmd += f" --username {username}"
    if email:
        cmd += f" --email {email}"

    if settings:
        cmd = f"DJANGO_SETTINGS_MODULE={settings} {cmd}"

    c.run(cmd, pty=True)
    print("✅ Superuser created!")


@task
def loaddata(c, fixture, settings=None):
    """
    Load data from fixture using uv.

    Args:
        fixture: Fixture file to load
        settings: Django settings module
    """
    print(f"📥 Loading fixture: {fixture}")

    cmd = f"uv run python manage.py loaddata {fixture}"
    if settings:
        cmd = f"DJANGO_SETTINGS_MODULE={settings} {cmd}"

    c.run(cmd)
    print("✅ Fixture loaded!")


@task
def dumpdata(c, app=None, output=None, indent=2, settings=None):
    """
    Dump data to fixture using uv.

    Args:
        app: Specific app to dump data from
        output: Output file name
        indent: JSON indentation
        settings: Django settings module
    """
    print("📤 Dumping data...")

    cmd = "uv run python manage.py dumpdata"
    if app:
        cmd += f" {app}"
    if output:
        cmd += f" --output {output}"
    if indent:
        cmd += f" --indent {indent}"

    if settings:
        cmd = f"DJANGO_SETTINGS_MODULE={settings} {cmd}"

    c.run(cmd)
    print("✅ Data dumped!")


@task
def reset_db(c, settings=None):
    """
    Reset database (drop and recreate).

    WARNING: This will delete all data!

    Args:
        settings: Django settings module
    """
    print("⚠️  WARNING: This will delete all database data!")
    confirm = input("Are you sure you want to continue? (yes/no): ")

    if confirm.lower() != "yes":
        print("❌ Database reset cancelled.")
        return

    print("🗑️  Resetting database...")

    # Remove migration files (except __init__.py)
    for app_dir in Path().glob("*/migrations"):
        for migration_file in app_dir.glob("*.py"):
            if migration_file.name != "__init__.py":
                migration_file.unlink()
                print(f"Removed {migration_file}")

    # Create new migrations and migrate
    makemigrations(c, settings=settings)
    migrate(c, settings=settings)

    print("✅ Database reset completed!")


@task
def backup_db(c, output=None, settings=None):
    """
    Create database backup using uv.

    Args:
        output: Output file name
        settings: Django settings module
    """
    if not output:
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = f"backup_{timestamp}.json"

    print(f"💾 Creating database backup: {output}")
    dumpdata(c, output=output, settings=settings)
    print("✅ Database backup created!")


@task
def add(c, package, dev=False):
    """
    Add a package using uv.

    Args:
        package: Package name to add
        dev: Add as development dependency
    """
    print(f"📦 Adding package: {package}")

    cmd = f"uv add {package}"
    if dev:
        cmd += " --dev"

    c.run(cmd)
    print("✅ Package added!")


@task
def remove(c, package):
    """
    Remove a package using uv.

    Args:
        package: Package name to remove
    """
    print(f"🗑️  Removing package: {package}")
    c.run(f"uv remove {package}")
    print("✅ Package removed!")


@task
def sync(c):
    """Sync dependencies using uv."""
    print("🔄 Syncing dependencies...")
    c.run("uv sync")
    print("✅ Dependencies synced!")


@task
def lock(c):
    """Update lock file using uv."""
    print("🔒 Updating lock file...")
    c.run("uv lock")
    print("✅ Lock file updated!")


@task
def clean(c):
    """Clean up temporary files and caches."""
    print("🧹 Cleaning up temporary files...")

    # Remove Python cache files
    c.run("find . -type f -name '*.pyc' -delete", warn=True)
    c.run("find . -type d -name '__pycache__' -delete", warn=True)

    # Remove pytest cache
    c.run("rm -rf .pytest_cache/", warn=True)

    # Remove coverage files
    c.run("rm -rf htmlcov/", warn=True)
    c.run("rm -f .coverage", warn=True)

    # Remove ruff cache
    c.run("rm -rf .ruff_cache/", warn=True)

    print("✅ Cleanup completed!")


@task
def check(c, settings=None):
    """
    Run Django system checks using uv.

    Args:
        settings: Django settings module
    """
    print("🔍 Running Django system checks...")

    cmd = "uv run python manage.py check"
    if settings:
        cmd = f"DJANGO_SETTINGS_MODULE={settings} {cmd}"

    result = c.run(cmd, warn=True)
    if result.exited != 0:
        print("❌ System checks failed!")
        raise Exit(code=1)

    print("✅ System checks passed!")


@task
def ci(c):
    """Run full CI pipeline (lint, type check, test, security)."""
    print("🚀 Running full CI pipeline...")

    lint(c, check=True)

    coverage(c)

    check(c)

    print("✅ CI pipeline completed successfully!")


@task
def dev(c):
    """Start development environment (install deps, migrate, runserver)."""
    print("🚀 Starting development environment...")

    sync(c)

    migrate(c)

    runserver(c)


# Create task collections
db_tasks = Collection("db")
db_tasks.add_task(migrate)
db_tasks.add_task(makemigrations)
db_tasks.add_task(reset_db, "reset")
db_tasks.add_task(backup_db, "backup")
db_tasks.add_task(loaddata, "load")
db_tasks.add_task(dumpdata, "dump")

test_tasks = Collection("test")
test_tasks.add_task(test, "run")
test_tasks.add_task(coverage)

lint_tasks = Collection("lint")
lint_tasks.add_task(lint, "check")
lint_tasks.add_task(format)

deps_tasks = Collection("deps")
deps_tasks.add_task(add)
deps_tasks.add_task(remove)
deps_tasks.add_task(sync)
deps_tasks.add_task(lock)

# Main namespace
ns = Collection()
ns.add_task(dev)
ns.add_task(runserver)
ns.add_task(shell)
ns.add_task(createsuperuser)
ns.add_task(collectstatic)
ns.add_task(check)
ns.add_task(clean)
ns.add_task(ci)

# Add collections
ns.add_collection(db_tasks)
ns.add_collection(test_tasks)
ns.add_collection(lint_tasks)
ns.add_collection(deps_tasks)
