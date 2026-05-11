"""Symlink rejection / containment defense for install_hooks (LLD-008 r7 T8)."""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.install_hooks import SecurityError, install_one_hook


def test_symlink_destination_rejected(tmp_repo: Path, tmp_path: Path) -> None:
    """`.git/hooks/<hook>` exists as symlink → SecurityError; no write."""
    hooks_dir = tmp_repo / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / "pre-commit"

    external_target = tmp_path / "external-script.sh"
    external_target.write_text("#!/bin/bash\necho 'external'\n")
    hook_path.symlink_to(external_target)

    assert hook_path.is_symlink()
    with pytest.raises(SecurityError, match="symlinked hook destination"):
        install_one_hook(tmp_repo, "pre-commit")

    # Symlink unchanged; external target untouched
    assert hook_path.is_symlink()
    assert "external" in external_target.read_text()
