"""Tests for init command (AI tool configuration)."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import yaml

from lucidshark.cli.commands.init import (
    AIDER_CONF_START_MARKER,
    AIDER_LINT_ARGS,
    InitCommand,
    LUCIDSHARK_CURSOR_RULE_CONTENT,
    LUCIDSHARK_MCP_ARGS,
    LUCIDSHARK_WINDSURF_RULE_CONTENT,
    WINDSURF_GLOBAL_MCP_CONFIG,
    LUCIDSHARK_SKILL_CONTENT,
    LUCIDSHARK_CLAUDE_MD_SECTION,
    LUCIDSHARK_HOOKS_CONFIG,
)
from lucidshark.cli.exit_codes import EXIT_SUCCESS


class TestInitCommand:
    """Tests for InitCommand."""

    def test_name(self) -> None:
        """Test command name property."""
        cmd = InitCommand(version="1.0.0")
        assert cmd.name == "init"

    def test_default_configures_claude_code(self, tmp_path: Path, capsys) -> None:
        """Test that init command configures Claude Code by default."""
        cmd = InitCommand(version="1.0.0")
        args = Namespace(
            dry_run=True,
            force=False,
            remove=False,
        )

        claude_config = tmp_path / ".mcp.json"

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=claude_config
            ):
                exit_code = cmd.execute(args)

        assert exit_code == EXIT_SUCCESS
        captured = capsys.readouterr()
        assert "Claude Code" in captured.out

    def test_init_all_configures_claude_code(self, tmp_path: Path, capsys) -> None:
        """Test that --all configures Claude Code."""
        cmd = InitCommand(version="1.0.0")
        args = Namespace(
            claude_code=False,
            init_all=True,
            dry_run=True,
            force=False,
            remove=False,
        )

        claude_config = tmp_path / ".mcp.json"

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=claude_config
            ):
                exit_code = cmd.execute(args)

        assert exit_code == EXIT_SUCCESS
        captured = capsys.readouterr()
        assert "Claude Code" in captured.out


class TestSetupClaudeCode:
    """Tests for Claude Code setup."""

    def test_creates_new_config_file(self, tmp_path: Path, capsys) -> None:
        """Test creating a new Claude Code config file."""
        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"

        args = Namespace(
            claude_code=True,
            init_all=False,
            dry_run=False,
            force=False,
            remove=False,
        )

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                with patch.object(
                    cmd,
                    "_find_lucidshark_path",
                    return_value="/usr/local/bin/lucidshark",
                ):
                    exit_code = cmd.execute(args)

        assert exit_code == EXIT_SUCCESS
        assert config_path.exists()

        config = json.loads(config_path.read_text())
        assert "mcpServers" in config
        assert "lucidshark" in config["mcpServers"]
        # Check that the full path is used in the config
        assert (
            config["mcpServers"]["lucidshark"]["command"] == "/usr/local/bin/lucidshark"
        )
        assert config["mcpServers"]["lucidshark"]["args"] == LUCIDSHARK_MCP_ARGS

    def test_preserves_existing_mcp_servers(self, tmp_path: Path) -> None:
        """Test that existing MCP servers are preserved."""
        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"

        # Create existing config with another MCP server
        existing_config = {
            "mcpServers": {
                "other-tool": {
                    "command": "other-command",
                    "args": ["--some-flag"],
                }
            }
        }
        config_path.write_text(json.dumps(existing_config))

        args = Namespace(
            claude_code=True,
            init_all=False,
            dry_run=False,
            force=False,
            remove=False,
        )

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                with patch.object(
                    cmd,
                    "_find_lucidshark_path",
                    return_value="/usr/local/bin/lucidshark",
                ):
                    exit_code = cmd.execute(args)

        assert exit_code == EXIT_SUCCESS

        config = json.loads(config_path.read_text())
        assert "other-tool" in config["mcpServers"]
        assert "lucidshark" in config["mcpServers"]

    def test_skips_if_already_configured(self, tmp_path: Path, capsys) -> None:
        """Test that setup skips if LucidShark already configured."""
        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"

        # Create existing config with lucidshark
        existing_config = {
            "mcpServers": {
                "lucidshark": {
                    "command": "/some/path/lucidshark",
                    "args": LUCIDSHARK_MCP_ARGS,
                },
            }
        }
        config_path.write_text(json.dumps(existing_config))

        args = Namespace(
            claude_code=True,
            init_all=False,
            dry_run=False,
            force=False,
            remove=False,
        )

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                with patch.object(
                    cmd,
                    "_find_lucidshark_path",
                    return_value="/usr/local/bin/lucidshark",
                ):
                    exit_code = cmd.execute(args)

        assert exit_code == EXIT_SUCCESS
        captured = capsys.readouterr()
        assert "already configured" in captured.out

    def test_force_overwrites_existing(self, tmp_path: Path) -> None:
        """Test that --force overwrites existing config."""
        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"

        # Create existing config with different lucidshark config
        existing_config = {
            "mcpServers": {
                "lucidshark": {
                    "command": "old-command",
                    "args": ["--old-flag"],
                },
            }
        }
        config_path.write_text(json.dumps(existing_config))

        args = Namespace(
            claude_code=True,
            init_all=False,
            dry_run=False,
            force=True,
            remove=False,
        )

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                with patch.object(
                    cmd,
                    "_find_lucidshark_path",
                    return_value="/usr/local/bin/lucidshark",
                ):
                    exit_code = cmd.execute(args)

        assert exit_code == EXIT_SUCCESS

        config = json.loads(config_path.read_text())
        assert (
            config["mcpServers"]["lucidshark"]["command"] == "/usr/local/bin/lucidshark"
        )
        assert config["mcpServers"]["lucidshark"]["args"] == LUCIDSHARK_MCP_ARGS

    def test_dry_run_does_not_write(self, tmp_path: Path, capsys) -> None:
        """Test that --dry-run does not write config file."""
        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"

        args = Namespace(
            claude_code=True,
            init_all=False,
            dry_run=True,
            force=False,
            remove=False,
        )

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                with patch.object(
                    cmd,
                    "_find_lucidshark_path",
                    return_value="/usr/local/bin/lucidshark",
                ):
                    exit_code = cmd.execute(args)

        assert exit_code == EXIT_SUCCESS
        assert not config_path.exists()

        captured = capsys.readouterr()
        assert "Would write" in captured.out

    def test_remove_deletes_lucidshark(self, tmp_path: Path, capsys) -> None:
        """Test that --remove removes LucidShark from config."""
        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"

        # Create existing config with lucidshark and another tool
        existing_config = {
            "mcpServers": {
                "lucidshark": {
                    "command": "/some/path/lucidshark",
                    "args": LUCIDSHARK_MCP_ARGS,
                },
                "other-tool": {"command": "other"},
            }
        }
        config_path.write_text(json.dumps(existing_config))

        args = Namespace(
            claude_code=True,
            init_all=False,
            dry_run=False,
            force=False,
            remove=True,
        )

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                exit_code = cmd.execute(args)

        assert exit_code == EXIT_SUCCESS

        config = json.loads(config_path.read_text())
        assert "lucidshark" not in config["mcpServers"]
        assert "other-tool" in config["mcpServers"]

        captured = capsys.readouterr()
        assert "Removed lucidshark" in captured.out

    def test_remove_not_found(self, tmp_path: Path, capsys) -> None:
        """Test removing when LucidShark not in config."""
        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"

        # Create existing config without lucidshark
        existing_config = {
            "mcpServers": {
                "other-tool": {"command": "other"},
            }
        }
        config_path.write_text(json.dumps(existing_config))

        args = Namespace(
            claude_code=True,
            init_all=False,
            dry_run=False,
            force=False,
            remove=True,
        )

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                exit_code = cmd.execute(args)

        assert exit_code == EXIT_SUCCESS
        captured = capsys.readouterr()
        assert "not found" in captured.out


class TestConfigureClaudeSkill:
    """Tests for Claude skill configuration."""

    def test_creates_new_skill_file(self, tmp_path: Path, capsys) -> None:
        """Test creating a new Claude skill file."""
        cmd = InitCommand(version="1.0.0")
        skill_path = tmp_path / ".claude" / "skills" / "lucidshark" / "SKILL.md"

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_skill(
                dry_run=False, force=False, remove=False
            )

        assert success
        assert skill_path.exists()
        content = skill_path.read_text(encoding="utf-8")
        assert "LucidShark" in content

    def test_skips_if_already_configured(self, tmp_path: Path, capsys) -> None:
        """Test that setup skips if lucidshark skill already exists."""
        cmd = InitCommand(version="1.0.0")
        skill_path = tmp_path / ".claude" / "skills" / "lucidshark" / "SKILL.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text(LUCIDSHARK_SKILL_CONTENT, encoding="utf-8")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_skill(
                dry_run=False, force=False, remove=False
            )

        assert success
        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_force_overwrites_existing(self, tmp_path: Path) -> None:
        """Test that --force overwrites existing skill."""
        cmd = InitCommand(version="1.0.0")
        skill_path = tmp_path / ".claude" / "skills" / "lucidshark" / "SKILL.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text("Old skill content")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_skill(
                dry_run=False, force=True, remove=False
            )

        assert success
        content = skill_path.read_text(encoding="utf-8")
        assert "Old skill content" not in content
        assert "LucidShark" in content

    def test_dry_run_does_not_write(self, tmp_path: Path, capsys) -> None:
        """Test that --dry-run does not write skill file."""
        cmd = InitCommand(version="1.0.0")
        skill_path = tmp_path / ".claude" / "skills" / "lucidshark" / "SKILL.md"

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_skill(
                dry_run=True, force=False, remove=False
            )

        assert success
        assert not skill_path.exists()
        captured = capsys.readouterr()
        assert "Would create" in captured.out

    def test_remove_deletes_skill(self, tmp_path: Path, capsys) -> None:
        """Test that --remove removes lucidshark skill."""
        cmd = InitCommand(version="1.0.0")
        skill_path = tmp_path / ".claude" / "skills" / "lucidshark" / "SKILL.md"
        skill_path.parent.mkdir(parents=True)
        skill_path.write_text(LUCIDSHARK_SKILL_CONTENT, encoding="utf-8")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_skill(
                dry_run=False, force=False, remove=True
            )

        assert success
        assert not skill_path.exists()
        captured = capsys.readouterr()
        assert "Removed" in captured.out

    def test_remove_not_found(self, tmp_path: Path, capsys) -> None:
        """Test removing when skill does not exist."""
        cmd = InitCommand(version="1.0.0")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_skill(
                dry_run=False, force=False, remove=True
            )

        assert success
        captured = capsys.readouterr()
        assert "not found" in captured.out


class TestFindLucidsharkPath:
    """Tests for _find_lucidshark_path method."""

    def test_finds_in_path(self, tmp_path: Path) -> None:
        """Test finding lucidshark via shutil.which (in PATH)."""
        cmd = InitCommand(version="1.0.0")
        # Mock CWD to avoid local ./lucidshark interference
        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch("shutil.which", return_value="/usr/local/bin/lucidshark"):
                path = cmd._find_lucidshark_path()
        assert path == "/usr/local/bin/lucidshark"

    def test_finds_in_venv(self, tmp_path: Path) -> None:
        """Test finding lucidshark in venv bin directory."""
        cmd = InitCommand(version="1.0.0")
        # Create a fake lucidshark in the venv with platform-appropriate paths
        venv_bin = tmp_path / "venv" / "bin"
        venv_bin.mkdir(parents=True)
        lucidshark_exe = venv_bin / "lucidshark"
        lucidshark_exe.touch()

        # Mock CWD to avoid local ./lucidshark interference
        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch("shutil.which", return_value=None):
                with patch("sys.executable", str(venv_bin / "python")):
                    path = cmd._find_lucidshark_path()
        assert path == str(lucidshark_exe)

    def test_returns_none_when_not_found(self, tmp_path: Path) -> None:
        """Test returning None when lucidshark not found."""
        cmd = InitCommand(version="1.0.0")
        # Mock CWD to avoid local ./lucidshark interference
        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch("shutil.which", return_value=None):
                with patch("sys.executable", str(tmp_path / "nonexistent" / "python")):
                    path = cmd._find_lucidshark_path()
        assert path is None

    def test_fallback_uses_bare_command(self, tmp_path: Path, capsys) -> None:
        """Test that fallback uses 'lucidshark' when path not found."""
        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"

        args = Namespace(
            claude_code=True,
            init_all=False,
            dry_run=False,
            force=False,
            remove=False,
        )

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                with patch.object(cmd, "_find_lucidshark_path", return_value=None):
                    exit_code = cmd.execute(args)

        assert exit_code == EXIT_SUCCESS

        config = json.loads(config_path.read_text())
        # When not found, should fall back to bare "lucidshark" command
        assert config["mcpServers"]["lucidshark"]["command"] == "lucidshark"

        captured = capsys.readouterr()
        assert "Warning" in captured.out


class TestConfigPaths:
    """Tests for config path determination."""

    def test_claude_code_config_path(self) -> None:
        """Test Claude Code config path returns .mcp.json."""
        cmd = InitCommand(version="1.0.0")
        path = cmd._get_claude_code_config_path()
        assert path is not None
        assert ".mcp.json" in str(path)


class TestConfigureClaudeMd:
    """Tests for CLAUDE.md configuration."""

    def test_creates_new_claude_md(self, tmp_path: Path, capsys) -> None:
        """Test creating a new .claude/CLAUDE.md with LucidShark section."""
        cmd = InitCommand(version="1.0.0")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_md(dry_run=False, force=False, remove=False)

        assert success
        claude_md = tmp_path / ".claude" / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text(encoding="utf-8")
        assert "<!-- lucidshark:start" in content
        assert "<!-- lucidshark:end -->" in content
        assert "MUST" in content  # Directive-first language
        assert "mcp__lucidshark__scan" in content  # MCP tools primary
        assert "Domain Selection" in content

    def test_appends_to_existing_claude_md(self, tmp_path: Path) -> None:
        """Test appending to an existing .claude/CLAUDE.md without LucidShark section."""
        cmd = InitCommand(version="1.0.0")
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"
        claude_md.write_text("# My Project\n\nExisting instructions here.\n")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_md(dry_run=False, force=False, remove=False)

        assert success
        content = claude_md.read_text(encoding="utf-8")
        assert content.startswith("# My Project")
        assert "Existing instructions here." in content
        assert "<!-- lucidshark:start" in content

    def test_skips_if_section_already_exists(self, tmp_path: Path, capsys) -> None:
        """Test that setup skips if LucidShark section already exists."""
        cmd = InitCommand(version="1.0.0")
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"
        claude_md.write_text(
            "# Project\n" + LUCIDSHARK_CLAUDE_MD_SECTION, encoding="utf-8"
        )

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_md(dry_run=False, force=False, remove=False)

        assert success
        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_force_updates_existing_section(self, tmp_path: Path) -> None:
        """Test that --force replaces the existing LucidShark section."""
        cmd = InitCommand(version="1.0.0")
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"
        old_content = (
            "# Project\n\n"
            "<!-- lucidshark:start - managed by lucidshark init, do not edit manually -->\n"
            "Old lucidshark content\n"
            "<!-- lucidshark:end -->\n\n"
            "## Other stuff\n"
        )
        claude_md.write_text(old_content, encoding="utf-8")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_md(dry_run=False, force=True, remove=False)

        assert success
        content = claude_md.read_text(encoding="utf-8")
        assert "Old lucidshark content" not in content
        assert "MUST" in content  # New directive-first content
        assert "mcp__lucidshark__scan" in content
        assert "## Other stuff" in content

    def test_dry_run_does_not_write(self, tmp_path: Path, capsys) -> None:
        """Test that --dry-run does not create .claude/CLAUDE.md."""
        cmd = InitCommand(version="1.0.0")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_md(dry_run=True, force=False, remove=False)

        assert success
        assert not (tmp_path / ".claude" / "CLAUDE.md").exists()
        captured = capsys.readouterr()
        assert "Would create" in captured.out

    def test_remove_deletes_section(self, tmp_path: Path, capsys) -> None:
        """Test that --remove removes the LucidShark section from .claude/CLAUDE.md."""
        cmd = InitCommand(version="1.0.0")
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"
        claude_md.write_text(
            "# Project\n" + LUCIDSHARK_CLAUDE_MD_SECTION + "\n## Other\n",
            encoding="utf-8",
        )

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_md(dry_run=False, force=False, remove=True)

        assert success
        content = claude_md.read_text(encoding="utf-8")
        assert "lucidshark:start" not in content
        assert "lucidshark:end" not in content
        assert "# Project" in content
        assert "## Other" in content

    def test_remove_deletes_file_if_empty(self, tmp_path: Path, capsys) -> None:
        """Test that --remove deletes .claude/CLAUDE.md if only LucidShark content remains."""
        cmd = InitCommand(version="1.0.0")
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        claude_md = claude_dir / "CLAUDE.md"
        claude_md.write_text(LUCIDSHARK_CLAUDE_MD_SECTION, encoding="utf-8")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_md(dry_run=False, force=False, remove=True)

        assert success
        assert not claude_md.exists()
        captured = capsys.readouterr()
        assert "was empty" in captured.out

    def test_remove_not_found(self, tmp_path: Path, capsys) -> None:
        """Test removing when LucidShark section does not exist."""
        cmd = InitCommand(version="1.0.0")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_md(dry_run=False, force=False, remove=True)

        assert success
        captured = capsys.readouterr()
        assert "not found" in captured.out


class TestConfigureClaudeHooks:
    """Tests for Claude Code hooks configuration."""

    def test_creates_new_settings_json(self, tmp_path: Path, capsys) -> None:
        """Test creating .claude/settings.json with hooks."""
        cmd = InitCommand(version="1.0.0")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_hooks(
                dry_run=False, force=False, remove=False
            )

        assert success
        settings_path = tmp_path / ".claude" / "settings.json"
        assert settings_path.exists()
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        assert "hooks" in settings
        assert "PostToolUse" in settings["hooks"]
        # Verify it contains the LucidShark hook
        hook_group = settings["hooks"]["PostToolUse"][0]
        assert "Edit" in hook_group["matcher"]
        assert "LucidShark" in hook_group["hooks"][0]["command"]

    def test_preserves_existing_settings(self, tmp_path: Path) -> None:
        """Test merging hooks into existing settings."""
        cmd = InitCommand(version="1.0.0")
        settings_path = tmp_path / ".claude" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        existing = {
            "other_setting": "value",
            "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": []}]},
        }
        settings_path.write_text(json.dumps(existing), encoding="utf-8")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_hooks(
                dry_run=False, force=False, remove=False
            )

        assert success
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        assert settings["other_setting"] == "value"
        assert "PostToolUse" in settings["hooks"]
        # PreToolUse hooks must also be preserved
        assert "PreToolUse" in settings["hooks"]
        assert settings["hooks"]["PreToolUse"] == [{"matcher": "Bash", "hooks": []}]

    def test_skips_if_already_configured(self, tmp_path: Path, capsys) -> None:
        """Test that setup skips if hooks already configured."""
        cmd = InitCommand(version="1.0.0")
        settings_path = tmp_path / ".claude" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        # Include both hooks and enabledMcpjsonServers to trigger "already configured" check
        config_with_server = dict(LUCIDSHARK_HOOKS_CONFIG)
        config_with_server["enabledMcpjsonServers"] = ["lucidshark"]
        settings_path.write_text(json.dumps(config_with_server), encoding="utf-8")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_hooks(
                dry_run=False, force=False, remove=False
            )

        assert success
        captured = capsys.readouterr()
        assert "already configured" in captured.out

    def test_force_overwrites_existing(self, tmp_path: Path) -> None:
        """Test that --force replaces hooks."""
        cmd = InitCommand(version="1.0.0")
        settings_path = tmp_path / ".claude" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        # Write existing hooks with different content
        old_hooks = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "Edit|Write|NotebookEdit",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo '[LucidShark] old message'",
                            }
                        ],
                    }
                ]
            }
        }
        settings_path.write_text(json.dumps(old_hooks), encoding="utf-8")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_hooks(
                dry_run=False, force=True, remove=False
            )

        assert success
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        # Should have exactly one PostToolUse hook group (old replaced, not duplicated)
        assert len(settings["hooks"]["PostToolUse"]) == 1
        command = settings["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
        assert "scan before completing" in command

    def test_force_preserves_non_lucidshark_hooks(self, tmp_path: Path) -> None:
        """Test that --force only updates LucidShark hook, preserving others."""
        cmd = InitCommand(version="1.0.0")
        settings_path = tmp_path / ".claude" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        # Write settings with both LucidShark and non-LucidShark hooks
        mixed_hooks = {
            "other_setting": "keep_me",
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {"type": "command", "command": "echo 'custom pre-hook'"}
                        ],
                    }
                ],
                "PostToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {"type": "command", "command": "echo 'custom post-hook'"}
                        ],
                    },
                    {
                        "matcher": "Edit|Write|NotebookEdit",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "echo '[LucidShark] old message'",
                            }
                        ],
                    },
                ],
            },
        }
        settings_path.write_text(json.dumps(mixed_hooks), encoding="utf-8")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_hooks(
                dry_run=False, force=True, remove=False
            )

        assert success
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        # Non-hook settings preserved
        assert settings["other_setting"] == "keep_me"
        # PreToolUse hooks preserved
        assert len(settings["hooks"]["PreToolUse"]) == 1
        assert settings["hooks"]["PreToolUse"][0]["matcher"] == "Bash"
        # PostToolUse: custom hook preserved + LucidShark hook updated
        post_hooks = settings["hooks"]["PostToolUse"]
        assert len(post_hooks) == 2
        # Custom hook still there
        custom = [h for h in post_hooks if h["matcher"] == "Bash"]
        assert len(custom) == 1
        assert "custom post-hook" in custom[0]["hooks"][0]["command"]
        # LucidShark hook updated
        ls_hooks = [
            h for h in post_hooks if "LucidShark" in h["hooks"][0].get("command", "")
        ]
        assert len(ls_hooks) == 1
        assert "scan before completing" in ls_hooks[0]["hooks"][0]["command"]

    def test_dry_run_does_not_write(self, tmp_path: Path, capsys) -> None:
        """Test that --dry-run does not write settings file."""
        cmd = InitCommand(version="1.0.0")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_hooks(
                dry_run=True, force=False, remove=False
            )

        assert success
        assert not (tmp_path / ".claude" / "settings.json").exists()
        captured = capsys.readouterr()
        assert "Would create" in captured.out

    def test_remove_deletes_hooks(self, tmp_path: Path, capsys) -> None:
        """Test that --remove removes hooks key, preserves other settings."""
        cmd = InitCommand(version="1.0.0")
        settings_path = tmp_path / ".claude" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        settings = {"other_setting": "keep_me"}
        settings.update(LUCIDSHARK_HOOKS_CONFIG)
        settings_path.write_text(json.dumps(settings), encoding="utf-8")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_hooks(
                dry_run=False, force=False, remove=True
            )

        assert success
        assert settings_path.exists()
        remaining = json.loads(settings_path.read_text(encoding="utf-8"))
        assert "hooks" not in remaining
        assert remaining["other_setting"] == "keep_me"
        captured = capsys.readouterr()
        assert "Removed LucidShark hooks" in captured.out

    def test_remove_deletes_file_if_empty(self, tmp_path: Path, capsys) -> None:
        """Test that --remove removes file if only hooks remain."""
        cmd = InitCommand(version="1.0.0")
        settings_path = tmp_path / ".claude" / "settings.json"
        settings_path.parent.mkdir(parents=True)
        settings_path.write_text(json.dumps(LUCIDSHARK_HOOKS_CONFIG), encoding="utf-8")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_hooks(
                dry_run=False, force=False, remove=True
            )

        assert success
        assert not settings_path.exists()
        captured = capsys.readouterr()
        assert "was empty" in captured.out

    def test_remove_not_found(self, tmp_path: Path, capsys) -> None:
        """Test removing when hooks do not exist."""
        cmd = InitCommand(version="1.0.0")

        with patch.object(Path, "cwd", return_value=tmp_path):
            success = cmd._configure_claude_hooks(
                dry_run=False, force=False, remove=True
            )

        assert success
        captured = capsys.readouterr()
        assert "not found" in captured.out


class TestManagedSectionHelpers:
    """Tests for _remove_managed_section and _replace_managed_section."""

    def test_remove_managed_section(self) -> None:
        """Test removing a managed section from content."""
        content = (
            "before\n"
            "<!-- lucidshark:start - managed -->\n"
            "managed content\n"
            "<!-- lucidshark:end -->\n"
            "after"
        )
        result = InitCommand._remove_managed_section(
            content, "<!-- lucidshark:start", "<!-- lucidshark:end -->"
        )
        assert "managed content" not in result
        assert "before" in result
        assert "after" in result

    def test_replace_managed_section(self) -> None:
        """Test replacing a managed section in content."""
        content = (
            "before\n"
            "<!-- lucidshark:start - managed -->\n"
            "old content\n"
            "<!-- lucidshark:end -->\n"
            "after"
        )
        new_section = (
            "<!-- lucidshark:start - managed -->\nnew content\n<!-- lucidshark:end -->"
        )
        result = InitCommand._replace_managed_section(
            content, "<!-- lucidshark:start", "<!-- lucidshark:end -->", new_section
        )
        assert "old content" not in result
        assert "new content" in result
        assert "before" in result
        assert "after" in result


class TestJsonConfigOperations:
    """Tests for JSON config read/write operations."""

    def test_read_nonexistent_file(self, tmp_path: Path) -> None:
        """Test reading nonexistent config file."""
        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / "nonexistent.json"

        config, error = cmd._read_json_config(config_path)
        assert config == {}
        assert error is not None
        assert "does not exist" in error

    def test_read_empty_file(self, tmp_path: Path) -> None:
        """Test reading empty config file."""
        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / "empty.json"
        config_path.write_text("")

        config, error = cmd._read_json_config(config_path)
        assert config == {}
        assert error is None

    def test_read_invalid_json(self, tmp_path: Path) -> None:
        """Test reading invalid JSON file."""
        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / "invalid.json"
        config_path.write_text("{ not valid json }")

        config, error = cmd._read_json_config(config_path)
        assert config == {}
        assert error is not None
        assert "Invalid JSON" in error

    def test_write_config(self, tmp_path: Path) -> None:
        """Test writing config file."""
        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / "test.json"

        config = {"key": "value"}
        success = cmd._write_json_config(config_path, config)

        assert success
        assert config_path.exists()

        written = json.loads(config_path.read_text())
        assert written == config


class TestMcpArgsCompatibility:
    """Tests that verify LUCIDSHARK_MCP_ARGS work with the serve command.

    These tests explicitly validate that the args generated by init command
    can be successfully parsed by the serve command's argument parser.
    This prevents bugs where init generates invalid command-line arguments.
    """

    def test_mcp_args_are_valid_for_serve_parser(self) -> None:
        """Test that LUCIDSHARK_MCP_ARGS can be parsed by serve command."""
        from lucidshark.cli.arguments import build_parser

        parser = build_parser()

        # Parse the args that init writes to .mcp.json (excluding 'lucidshark' command)
        args = parser.parse_args(LUCIDSHARK_MCP_ARGS)

        # Verify the args were parsed correctly
        assert args.command == "serve"
        assert args.mcp is True
        assert args.path == "."

    def test_generated_mcp_config_args_are_valid(self, tmp_path: Path) -> None:
        """Test that args written to .mcp.json by init work with serve command."""
        from lucidshark.cli.arguments import build_parser

        # Create config file using init command
        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"

        args = Namespace(
            claude_code=True,
            init_all=False,
            dry_run=False,
            force=False,
            remove=False,
        )

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                with patch.object(
                    cmd,
                    "_find_lucidshark_path",
                    return_value="lucidshark",
                ):
                    exit_code = cmd.execute(args)

        assert exit_code == 0

        # Read the generated config
        config = json.loads(config_path.read_text())
        mcp_args = config["mcpServers"]["lucidshark"]["args"]

        # Verify these args can be parsed by the serve command
        parser = build_parser()
        parsed_args = parser.parse_args(mcp_args)

        assert parsed_args.command == "serve"
        assert parsed_args.mcp is True
        assert parsed_args.path == "."

    def test_mcp_args_use_positional_path_not_flag(self) -> None:
        """Test that LUCIDSHARK_MCP_ARGS uses positional path, not --path flag.

        This explicitly tests for the bug where --path was used as a flag,
        which is invalid because the serve command defines path as a positional argument.
        """
        # Verify --path flag is NOT in the args
        assert "--path" not in LUCIDSHARK_MCP_ARGS

        # Verify the positional path argument "." IS in the args
        assert "." in LUCIDSHARK_MCP_ARGS

        # Verify the args follow the pattern: ["serve", "--mcp", "."]
        assert LUCIDSHARK_MCP_ARGS == ["serve", "--mcp", "."]


class TestConfigGeneration:
    """Tests for lucidshark.yml generation in init command."""

    def _make_args(
        self,
        dry_run: bool = False,
        force: bool = False,
        remove: bool = False,
        no_config: bool = False,
    ) -> Namespace:
        return Namespace(
            dry_run=dry_run,
            force=force,
            remove=remove,
            no_config=no_config,
        )

    def test_init_generates_config_by_default(self, tmp_path: Path, capsys) -> None:
        """Init generates lucidshark.yml when no config exists."""
        # Create a Python marker file so detection finds something
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        (tmp_path / "main.py").write_text("print('hello')\n")

        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"
        args = self._make_args()

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                exit_code = cmd.execute(args)

        assert exit_code == EXIT_SUCCESS
        assert (tmp_path / "lucidshark.yml").exists()

        captured = capsys.readouterr()
        assert "Generating lucidshark.yml" in captured.out

    def test_init_skips_config_if_exists(self, tmp_path: Path, capsys) -> None:
        """Init skips config generation when lucidshark.yml exists."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        (tmp_path / "lucidshark.yml").write_text("version: 1\n")

        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"
        args = self._make_args()

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                cmd.execute(args)

        captured = capsys.readouterr()
        assert "already exists" in captured.out

        # File should still have original content
        assert (tmp_path / "lucidshark.yml").read_text() == "version: 1\n"

    def test_init_force_overwrites_config(self, tmp_path: Path, capsys) -> None:
        """Init with --force regenerates lucidshark.yml."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        (tmp_path / "main.py").write_text("print('hello')\n")
        (tmp_path / "lucidshark.yml").write_text("version: 1\n")

        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"
        args = self._make_args(force=True)

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                cmd.execute(args)

        # File should have been regenerated with full config
        content = (tmp_path / "lucidshark.yml").read_text()
        assert "pipeline" in content

    def test_init_no_config_flag_skips_generation(self, tmp_path: Path, capsys) -> None:
        """Init with --no-config skips config generation."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"
        args = self._make_args(no_config=True)

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                cmd.execute(args)

        assert not (tmp_path / "lucidshark.yml").exists()

    def test_init_dry_run_does_not_write_config(self, tmp_path: Path, capsys) -> None:
        """Init with --dry-run does not write lucidshark.yml."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        (tmp_path / "main.py").write_text("print('hello')\n")

        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"
        args = self._make_args(dry_run=True)

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                cmd.execute(args)

        assert not (tmp_path / "lucidshark.yml").exists()

    def test_init_no_languages_skips_config(self, tmp_path: Path, capsys) -> None:
        """Init skips config when no languages detected."""
        # Empty directory — no language markers
        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"
        args = self._make_args()

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                cmd.execute(args)

        assert not (tmp_path / "lucidshark.yml").exists()
        captured = capsys.readouterr()
        assert "No supported languages" in captured.out

    def test_init_remove_does_not_generate_config(self, tmp_path: Path, capsys) -> None:
        """Init with --remove does not generate config."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        cmd = InitCommand(version="1.0.0")
        config_path = tmp_path / ".mcp.json"
        args = self._make_args(remove=True)

        with patch.object(Path, "cwd", return_value=tmp_path):
            with patch.object(
                cmd, "_get_claude_code_config_path", return_value=config_path
            ):
                cmd.execute(args)

        assert not (tmp_path / "lucidshark.yml").exists()


def _tool_args(**overrides) -> Namespace:
    """Build init args with every tool flag off unless overridden."""
    values = dict(
        claude_code=False,
        cursor=False,
        windsurf=False,
        aider=False,
        all_tools=False,
        dry_run=False,
        force=False,
        remove=False,
        no_config=True,
    )
    values.update(overrides)
    return Namespace(**values)


def _run_init(tmp_path: Path, args: Namespace, lucidshark_path=None) -> int:
    """Run init in tmp_path with a fixed lucidshark executable path."""
    cmd = InitCommand(version="1.0.0")
    with patch.object(Path, "cwd", return_value=tmp_path):
        with patch.object(cmd, "_find_lucidshark_path", return_value=lucidshark_path):
            return cmd.execute(args)


class TestToolSelection:
    """Tests for choosing which AI tools init configures."""

    def test_no_flags_selects_claude_code_only(self) -> None:
        assert InitCommand._selected_tools(Namespace()) == ["claude_code"]

    def test_flags_combine_in_setup_order(self) -> None:
        args = _tool_args(aider=True, cursor=True)
        assert InitCommand._selected_tools(args) == ["cursor", "aider"]

    def test_all_tools_selects_everything(self) -> None:
        args = _tool_args(all_tools=True)
        assert InitCommand._selected_tools(args) == [
            "claude_code",
            "cursor",
            "windsurf",
            "aider",
        ]

    def test_tool_flag_skips_claude_code(self, tmp_path: Path) -> None:
        assert _run_init(tmp_path, _tool_args(cursor=True)) == EXIT_SUCCESS
        assert not (tmp_path / ".mcp.json").exists()
        assert not (tmp_path / ".claude").exists()
        assert (tmp_path / ".cursor" / "mcp.json").exists()

    def test_all_tools_creates_every_file(self, tmp_path: Path) -> None:
        assert _run_init(tmp_path, _tool_args(all_tools=True)) == EXIT_SUCCESS
        for rel in (
            ".mcp.json",
            ".claude/CLAUDE.md",
            ".cursor/mcp.json",
            ".cursor/rules/lucidshark.mdc",
            ".windsurf/rules/lucidshark.md",
            ".aider.conf.yml",
            "CONVENTIONS.md",
        ):
            assert (tmp_path / rel).exists(), rel

    def test_parser_accepts_tool_flags(self) -> None:
        from lucidshark.cli.arguments import build_parser

        args = build_parser().parse_args(
            ["init", "--cursor", "--windsurf", "--aider", "--claude-code"]
        )
        assert args.cursor and args.windsurf and args.aider and args.claude_code
        assert not args.all_tools
        assert build_parser().parse_args(["init", "--all-tools"]).all_tools

    def test_parser_defaults_to_no_tool_flags(self) -> None:
        from lucidshark.cli.arguments import build_parser

        args = build_parser().parse_args(["init"])
        assert InitCommand._selected_tools(args) == ["claude_code"]


class TestSetupCursor:
    """Tests for Cursor setup."""

    def test_creates_mcp_config_and_rule(self, tmp_path: Path) -> None:
        assert _run_init(tmp_path, _tool_args(cursor=True)) == EXIT_SUCCESS

        config = json.loads((tmp_path / ".cursor" / "mcp.json").read_text())
        assert config["mcpServers"]["lucidshark"] == {
            "command": "lucidshark",
            "args": LUCIDSHARK_MCP_ARGS,
        }
        rule = (tmp_path / ".cursor" / "rules" / "lucidshark.mdc").read_text()
        assert rule == LUCIDSHARK_CURSOR_RULE_CONTENT
        assert rule.startswith("---\ndescription: ")
        assert "alwaysApply: true\n---\n" in rule
        assert "mcp__lucidshark__" not in rule
        assert "lucidshark `scan` MCP tool" in rule

    def test_rerun_is_idempotent(self, tmp_path: Path, capsys) -> None:
        _run_init(tmp_path, _tool_args(cursor=True))
        mcp_before = (tmp_path / ".cursor" / "mcp.json").read_text()
        rule_path = tmp_path / ".cursor" / "rules" / "lucidshark.mdc"
        rule_path.write_text("user edited", encoding="utf-8")
        capsys.readouterr()

        assert _run_init(tmp_path, _tool_args(cursor=True)) == EXIT_SUCCESS

        assert (tmp_path / ".cursor" / "mcp.json").read_text() == mcp_before
        assert rule_path.read_text() == "user edited"
        assert "already" in capsys.readouterr().out

    def test_force_overwrites_rule(self, tmp_path: Path) -> None:
        _run_init(tmp_path, _tool_args(cursor=True))
        rule_path = tmp_path / ".cursor" / "rules" / "lucidshark.mdc"
        rule_path.write_text("stale", encoding="utf-8")

        _run_init(tmp_path, _tool_args(cursor=True, force=True))

        assert rule_path.read_text() == LUCIDSHARK_CURSOR_RULE_CONTENT

    def test_merges_into_existing_mcp_config(self, tmp_path: Path) -> None:
        config_path = tmp_path / ".cursor" / "mcp.json"
        config_path.parent.mkdir()
        config_path.write_text(
            json.dumps({"mcpServers": {"other": {"command": "other"}}, "x": 1})
        )

        _run_init(tmp_path, _tool_args(cursor=True))

        config = json.loads(config_path.read_text())
        assert config["x"] == 1
        assert config["mcpServers"]["other"] == {"command": "other"}
        assert "lucidshark" in config["mcpServers"]

    def test_remove_keeps_user_content(self, tmp_path: Path) -> None:
        config_path = tmp_path / ".cursor" / "mcp.json"
        config_path.parent.mkdir()
        config_path.write_text(
            json.dumps({"mcpServers": {"other": {"command": "other"}}})
        )
        user_rule = tmp_path / ".cursor" / "rules" / "mine.mdc"
        _run_init(tmp_path, _tool_args(cursor=True))
        user_rule.write_text("mine", encoding="utf-8")

        assert _run_init(tmp_path, _tool_args(cursor=True, remove=True)) == 0

        config = json.loads(config_path.read_text())
        assert config == {"mcpServers": {"other": {"command": "other"}}}
        assert not (tmp_path / ".cursor" / "rules" / "lucidshark.mdc").exists()
        assert user_rule.read_text() == "mine"

    def test_remove_cleans_empty_rules_dir(self, tmp_path: Path) -> None:
        _run_init(tmp_path, _tool_args(cursor=True))
        _run_init(tmp_path, _tool_args(cursor=True, remove=True))
        assert not (tmp_path / ".cursor" / "rules").exists()

    def test_dry_run_writes_nothing(self, tmp_path: Path, capsys) -> None:
        assert _run_init(tmp_path, _tool_args(cursor=True, dry_run=True)) == 0
        assert not (tmp_path / ".cursor").exists()
        out = capsys.readouterr().out
        assert "Would write" in out
        assert "Would create Cursor rule" in out

    def test_dry_run_remove_keeps_files(self, tmp_path: Path, capsys) -> None:
        _run_init(tmp_path, _tool_args(cursor=True))
        _run_init(tmp_path, _tool_args(cursor=True, remove=True, dry_run=True))
        assert (tmp_path / ".cursor" / "rules" / "lucidshark.mdc").exists()
        assert "Would remove" in capsys.readouterr().out


class TestSetupWindsurf:
    """Tests for Windsurf setup."""

    def test_creates_rule_and_prints_snippet(self, tmp_path: Path, capsys) -> None:
        assert _run_init(tmp_path, _tool_args(windsurf=True)) == EXIT_SUCCESS

        rule = (tmp_path / ".windsurf" / "rules" / "lucidshark.md").read_text()
        assert rule == LUCIDSHARK_WINDSURF_RULE_CONTENT
        assert rule.startswith("---\ntrigger: always_on\n---\n")
        out = capsys.readouterr().out
        assert WINDSURF_GLOBAL_MCP_CONFIG in out
        assert '"lucidshark"' in out
        assert str(tmp_path) in out

    def test_never_writes_global_config(self, tmp_path: Path) -> None:
        home = tmp_path / "home"
        home.mkdir()
        project = tmp_path / "project"
        project.mkdir()
        with patch.object(Path, "home", return_value=home):
            _run_init(project, _tool_args(windsurf=True))
        assert list(home.iterdir()) == []
        assert not (project / ".devin").exists()

    def test_snippet_uses_absolute_paths(self, tmp_path: Path) -> None:
        (tmp_path / "lucidshark").write_text("binary")
        cmd = InitCommand(version="1.0.0")
        with patch.object(Path, "cwd", return_value=tmp_path):
            config = cmd._build_windsurf_mcp_config()
        assert config["command"] == str(tmp_path / "lucidshark")
        assert config["args"] == ["serve", "--mcp", str(tmp_path)]

    def test_rerun_is_idempotent(self, tmp_path: Path, capsys) -> None:
        _run_init(tmp_path, _tool_args(windsurf=True))
        rule_path = tmp_path / ".windsurf" / "rules" / "lucidshark.md"
        rule_path.write_text("user edited", encoding="utf-8")
        capsys.readouterr()

        _run_init(tmp_path, _tool_args(windsurf=True))

        assert rule_path.read_text() == "user edited"
        assert "already exists" in capsys.readouterr().out

    def test_remove(self, tmp_path: Path, capsys) -> None:
        _run_init(tmp_path, _tool_args(windsurf=True))
        other = tmp_path / ".windsurf" / "rules" / "team.md"
        other.write_text("team rule", encoding="utf-8")

        _run_init(tmp_path, _tool_args(windsurf=True, remove=True))

        assert not (tmp_path / ".windsurf" / "rules" / "lucidshark.md").exists()
        assert other.read_text() == "team rule"
        assert "manually" in capsys.readouterr().out

    def test_dry_run_writes_nothing(self, tmp_path: Path, capsys) -> None:
        _run_init(tmp_path, _tool_args(windsurf=True, dry_run=True))
        assert not (tmp_path / ".windsurf").exists()
        assert "Would create Windsurf rule" in capsys.readouterr().out


class TestSetupAider:
    """Tests for Aider setup."""

    @staticmethod
    def _conf(tmp_path: Path) -> dict:
        return yaml.safe_load((tmp_path / ".aider.conf.yml").read_text())

    def test_creates_conf_and_conventions(self, tmp_path: Path) -> None:
        assert _run_init(tmp_path, _tool_args(aider=True)) == EXIT_SUCCESS

        conf = self._conf(tmp_path)
        assert conf == {
            "lint-cmd": f"lucidshark {AIDER_LINT_ARGS}",
            "auto-lint": True,
            "read": ["CONVENTIONS.md"],
        }
        # aider appends the file name, so --files must be the last argument
        assert conf["lint-cmd"].endswith("--files")
        conventions = (tmp_path / "CONVENTIONS.md").read_text()
        assert "<!-- lucidshark:start" in conventions
        assert "<!-- lucidshark:end -->" in conventions

    def test_lint_cmd_parses_with_appended_files(self, tmp_path: Path) -> None:
        from lucidshark.cli.arguments import build_parser

        _run_init(tmp_path, _tool_args(aider=True))
        argv = self._conf(tmp_path)["lint-cmd"].split()[1:] + ["src/app.py"]
        args = build_parser().parse_args(argv)
        assert args.files == ["src/app.py"]
        assert args.linting and args.type_checking
        assert args.fail_on == "low"

    def test_uses_local_binary(self, tmp_path: Path) -> None:
        _run_init(tmp_path, _tool_args(aider=True), lucidshark_path="./lucidshark")
        assert self._conf(tmp_path)["lint-cmd"].startswith("./lucidshark scan ")

    def test_preserves_user_keys_and_comments(self, tmp_path: Path) -> None:
        user = "# my settings\nmodel: sonnet  # preferred\ndark-mode: true\n"
        (tmp_path / ".aider.conf.yml").write_text(user)

        _run_init(tmp_path, _tool_args(aider=True))

        text = (tmp_path / ".aider.conf.yml").read_text()
        assert text.startswith(user)
        conf = self._conf(tmp_path)
        assert conf["model"] == "sonnet"
        assert conf["dark-mode"] is True
        assert conf["auto-lint"] is True

    def test_does_not_override_user_lint_cmd_or_read(
        self, tmp_path: Path, capsys
    ) -> None:
        user = "lint-cmd: flake8\nread: [NOTES.md]\n"
        (tmp_path / ".aider.conf.yml").write_text(user)

        _run_init(tmp_path, _tool_args(aider=True))

        text = (tmp_path / ".aider.conf.yml").read_text()
        assert text.count("lint-cmd") == 1
        assert text.count("read:") == 1
        conf = self._conf(tmp_path)
        assert conf["lint-cmd"] == "flake8"
        assert conf["read"] == ["NOTES.md"]
        assert conf["auto-lint"] is True
        out = capsys.readouterr().out
        assert "'lint-cmd' is already set" in out
        assert "add CONVENTIONS.md" in out

    def test_rerun_is_idempotent(self, tmp_path: Path, capsys) -> None:
        (tmp_path / "CONVENTIONS.md").write_text("# Team conventions\n")
        _run_init(tmp_path, _tool_args(aider=True))
        conf_before = (tmp_path / ".aider.conf.yml").read_text()
        conv_before = (tmp_path / "CONVENTIONS.md").read_text()
        capsys.readouterr()

        _run_init(tmp_path, _tool_args(aider=True))

        assert (tmp_path / ".aider.conf.yml").read_text() == conf_before
        assert (tmp_path / "CONVENTIONS.md").read_text() == conv_before
        assert conv_before.startswith("# Team conventions\n")
        assert "already exist" in capsys.readouterr().out

    def test_force_rewrites_block_once(self, tmp_path: Path) -> None:
        (tmp_path / ".aider.conf.yml").write_text("model: sonnet\n")
        _run_init(tmp_path, _tool_args(aider=True))
        first = (tmp_path / ".aider.conf.yml").read_text()

        _run_init(tmp_path, _tool_args(aider=True, force=True))

        text = (tmp_path / ".aider.conf.yml").read_text()
        assert text == first
        assert text.count(AIDER_CONF_START_MARKER) == 1

    def test_remove_keeps_user_content(self, tmp_path: Path) -> None:
        (tmp_path / ".aider.conf.yml").write_text("model: sonnet\n")
        (tmp_path / "CONVENTIONS.md").write_text("# Team conventions\n")
        _run_init(tmp_path, _tool_args(aider=True))

        _run_init(tmp_path, _tool_args(aider=True, remove=True))

        assert (tmp_path / ".aider.conf.yml").read_text().strip() == "model: sonnet"
        conventions = (tmp_path / "CONVENTIONS.md").read_text()
        assert conventions.strip() == "# Team conventions"

    def test_remove_deletes_files_left_empty(self, tmp_path: Path) -> None:
        _run_init(tmp_path, _tool_args(aider=True))
        _run_init(tmp_path, _tool_args(aider=True, remove=True))
        assert not (tmp_path / ".aider.conf.yml").exists()
        assert not (tmp_path / "CONVENTIONS.md").exists()

    def test_remove_when_not_configured(self, tmp_path: Path, capsys) -> None:
        assert _run_init(tmp_path, _tool_args(aider=True, remove=True)) == 0
        assert "not found" in capsys.readouterr().out

    def test_dry_run_writes_nothing(self, tmp_path: Path, capsys) -> None:
        _run_init(tmp_path, _tool_args(aider=True, dry_run=True))
        assert not (tmp_path / ".aider.conf.yml").exists()
        assert not (tmp_path / "CONVENTIONS.md").exists()
        out = capsys.readouterr().out
        assert "Would create LucidShark settings" in out
        assert "lint-cmd" in out

    def test_invalid_yaml_is_not_modified(self, tmp_path: Path) -> None:
        bad = "model: [unclosed\n"
        (tmp_path / ".aider.conf.yml").write_text(bad)

        exit_code = _run_init(tmp_path, _tool_args(aider=True))

        assert exit_code != EXIT_SUCCESS
        assert (tmp_path / ".aider.conf.yml").read_text() == bad

    def test_non_mapping_yaml_is_not_modified(self, tmp_path: Path) -> None:
        (tmp_path / ".aider.conf.yml").write_text("- a\n- b\n")
        assert _run_init(tmp_path, _tool_args(aider=True)) != EXIT_SUCCESS
        assert (tmp_path / ".aider.conf.yml").read_text() == "- a\n- b\n"
