from __future__ import annotations

from pathlib import Path

from app.services.profile_manager import ProfileManager


def test_create_profile_creates_directory(tmp_path: Path) -> None:
    manager = ProfileManager(tmp_path)
    info = manager.create_profile("Test Profile")
    assert info.path.is_dir()
    assert info.name == "Test Profile"
    assert (info.path / "settings.json").exists()
    assert (info.path / "logs").is_dir()
    assert (info.path / "exports").is_dir()


def test_list_profiles_finds_created_profiles(tmp_path: Path) -> None:
    manager = ProfileManager(tmp_path)
    manager.create_profile("Alpha")
    manager.create_profile("Beta")
    profiles = manager.list_profiles()
    names = [p.name for p in profiles]
    assert "Alpha" in names
    assert "Beta" in names
    assert len(profiles) == 2


def test_set_last_used_profile_updates_registry(tmp_path: Path) -> None:
    manager = ProfileManager(tmp_path)
    info = manager.create_profile("MyProfile")
    manager.set_last_used_profile(info.path)
    assert manager.registry_path.exists()
    last_used = manager.get_last_used_profile_path()
    assert last_used is not None
    assert last_used.resolve() == info.path.resolve()


def test_get_last_used_profile_path_reads_from_registry(tmp_path: Path) -> None:
    manager = ProfileManager(tmp_path)
    # No registry yet
    assert manager.get_last_used_profile_path() is None
    # Create and set
    info = manager.create_profile("Active")
    manager.set_last_used_profile(info.path)
    result = manager.get_last_used_profile_path()
    assert result is not None
    assert result.name == "Active"


def test_delete_profile_removes_directory(tmp_path: Path) -> None:
    manager = ProfileManager(tmp_path)
    info = manager.create_profile("ToDelete")
    assert info.path.is_dir()
    # Not current, so can delete
    result = manager.delete_profile(info.path)
    assert result is True
    assert not info.path.exists()
    # Verify removed from list
    profiles = manager.list_profiles()
    assert len(profiles) == 0


def test_delete_profile_fails_for_current_profile(tmp_path: Path) -> None:
    manager = ProfileManager(tmp_path)
    info = manager.create_profile("Current")
    manager.set_last_used_profile(info.path)
    # Should not allow deleting current profile
    result = manager.delete_profile(info.path)
    assert result is False
    assert info.path.is_dir()


def test_profile_isolation(tmp_path: Path) -> None:
    """Two profiles have independent paths."""
    manager = ProfileManager(tmp_path)
    p1 = manager.create_profile("Profile1")
    p2 = manager.create_profile("Profile2")
    assert p1.path != p2.path
    assert p1.path.resolve() != p2.path.resolve()
    # Write to one, verify the other is unaffected
    (p1.path / "test_file.txt").write_text("data1")
    assert not (p2.path / "test_file.txt").exists()


def test_get_current_profile_name(tmp_path: Path) -> None:
    manager = ProfileManager(tmp_path)
    assert manager.get_current_profile_name() == ""
    info = manager.create_profile("Named")
    manager.set_last_used_profile(info.path)
    assert manager.get_current_profile_name() == "Named"


def test_create_profile_with_duplicate_name(tmp_path: Path) -> None:
    manager = ProfileManager(tmp_path)
    p1 = manager.create_profile("Same")
    p2 = manager.create_profile("Same")
    assert p1.path != p2.path
    assert p1.path.is_dir()
    assert p2.path.is_dir()


def test_list_profiles_only_finds_valid_dirs(tmp_path: Path) -> None:
    """Only directories with app.db or settings.json are recognized."""
    manager = ProfileManager(tmp_path)
    # Create a regular directory without app.db/settings.json
    (tmp_path / "random_dir").mkdir()
    # Create a valid profile
    manager.create_profile("Valid")
    profiles = manager.list_profiles()
    names = [p.name for p in profiles]
    assert "Valid" in names
    assert "random_dir" not in names
