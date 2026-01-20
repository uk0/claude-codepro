"""Tests for ccp.auth module."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from ccp.auth import (
    GumroadLicenseVerifier,
    LicenseManager,
    LicenseResult,
    LicenseState,
    TamperedStateError,
    TrialAlreadyUsedError,
    create_eval_state,
    get_machine_fingerprint,
    has_used_trial,
    mark_trial_used,
)


class TestLicenseState:
    """Tests for LicenseState dataclass."""

    def test_license_state_to_dict(self):
        """LicenseState can be serialized to dict."""
        now = datetime.now(timezone.utc)
        state = LicenseState(
            license_key="TEST-KEY",
            tier="standard",
            email="test@example.com",
            created_at=now,
        )
        d = state.to_dict()
        assert d["license_key"] == "TEST-KEY"
        assert d["tier"] == "standard"
        assert d["email"] == "test@example.com"

    def test_license_state_from_dict(self):
        """LicenseState can be deserialized from dict."""
        now = datetime.now(timezone.utc)
        d = {
            "license_key": "TEST-KEY",
            "tier": "trial",
            "email": "test@example.com",
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(days=7)).isoformat(),
        }
        state = LicenseState.from_dict(d)
        assert state.license_key == "TEST-KEY"
        assert state.tier == "trial"
        assert state.email == "test@example.com"

    def test_is_trial_expired_false_for_standard(self):
        """Standard tier never expires."""
        state = LicenseState(license_key="KEY", tier="standard")
        assert state.is_trial_expired() is False

    def test_is_trial_expired_false_for_enterprise(self):
        """Enterprise tier never expires."""
        state = LicenseState(license_key="KEY", tier="enterprise")
        assert state.is_trial_expired() is False

    def test_is_trial_expired_false_when_trial_active(self):
        """Trial not expired when within 7 days."""
        now = datetime.now(timezone.utc)
        state = LicenseState(
            license_key="TRIAL",
            tier="trial",
            expires_at=now + timedelta(days=3),
        )
        assert state.is_trial_expired() is False

    def test_is_trial_expired_true_when_trial_past(self):
        """Trial expired when past expiration date."""
        now = datetime.now(timezone.utc)
        state = LicenseState(
            license_key="TRIAL",
            tier="trial",
            expires_at=now - timedelta(days=1),
        )
        assert state.is_trial_expired() is True

    def test_days_remaining_for_trial(self):
        """days_remaining returns days left for trial."""
        now = datetime.now(timezone.utc)
        state = LicenseState(
            license_key="TRIAL",
            tier="trial",
            expires_at=now + timedelta(days=5),
        )
        days = state.days_remaining()
        assert 4 <= days <= 5

    def test_days_remaining_zero_when_expired(self):
        """days_remaining returns 0 when expired."""
        now = datetime.now(timezone.utc)
        state = LicenseState(
            license_key="TRIAL",
            tier="trial",
            expires_at=now - timedelta(days=1),
        )
        assert state.days_remaining() == 0

    def test_days_remaining_none_for_standard(self):
        """days_remaining returns None for standard tier."""
        state = LicenseState(license_key="KEY", tier="standard")
        assert state.days_remaining() is None

    def test_days_remaining_none_for_enterprise(self):
        """days_remaining returns None for enterprise tier."""
        state = LicenseState(license_key="KEY", tier="enterprise")
        assert state.days_remaining() is None


class TestGumroadLicenseVerifier:
    """Tests for GumroadLicenseVerifier."""

    @patch("ccp.auth.httpx.post")
    def test_verify_license_success(self, mock_post):
        """Successful verification returns LicenseResult with success=True."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "purchase": {"quantity": 2, "email": "test@example.com"},
            "uses": 1,
        }

        verifier = GumroadLicenseVerifier()
        result = verifier.verify_license("TEST-KEY")

        assert result.success is True
        assert result.seats_total == 2
        assert result.email == "test@example.com"

    @patch("ccp.auth.httpx.post")
    def test_verify_license_invalid_key(self, mock_post):
        """Invalid key returns LicenseResult with success=False."""
        mock_post.return_value.status_code = 404

        verifier = GumroadLicenseVerifier()
        result = verifier.verify_license("INVALID")

        assert result.success is False
        assert "Invalid" in result.error

    @patch("ccp.auth.httpx.post")
    def test_verify_license_refunded(self, mock_post):
        """Refunded license returns error."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "success": True,
            "purchase": {"refunded": True},
        }

        verifier = GumroadLicenseVerifier()
        result = verifier.verify_license("TEST-KEY")

        assert result.success is False
        assert "refunded" in result.error.lower()

    @patch("ccp.auth.httpx.post")
    def test_verify_license_network_error(self, mock_post):
        """Network error returns LicenseResult with error."""
        mock_post.side_effect = Exception("Connection failed")

        verifier = GumroadLicenseVerifier()
        result = verifier.verify_license("TEST-KEY")

        assert result.success is False
        assert "Network error" in result.error


class TestLicenseManager:
    """Tests for LicenseManager."""

    def test_activate_success_standard(self, tmp_path):
        """Successful activation saves state with standard tier."""
        mock_verifier = MagicMock()
        mock_verifier.verify_license.return_value = LicenseResult(
            success=True,
            seats_total=1,
            seats_used=1,
            email="test@example.com",
            raw_response={"purchase": {"variants": "Standard License"}},
        )

        manager = LicenseManager(config_dir=tmp_path, verifier=mock_verifier)
        result = manager.activate("TEST-KEY")

        assert result.success is True
        assert result.tier == "standard"

        state = manager.get_state()
        assert state is not None
        assert state.tier == "standard"
        assert state.email == "test@example.com"

    def test_activate_success_enterprise(self, tmp_path):
        """Successful activation saves state with enterprise tier."""
        mock_verifier = MagicMock()
        mock_verifier.verify_license.return_value = LicenseResult(
            success=True,
            seats_total=5,
            seats_used=1,
            email="enterprise@example.com",
            raw_response={"purchase": {"variants": "Enterprise License"}},
        )

        manager = LicenseManager(config_dir=tmp_path, verifier=mock_verifier)
        result = manager.activate("ENTERPRISE-KEY")

        assert result.success is True
        assert result.tier == "enterprise"

        state = manager.get_state()
        assert state is not None
        assert state.tier == "enterprise"
        assert state.email == "enterprise@example.com"

    def test_activate_failure(self, tmp_path):
        """Failed activation returns error."""
        mock_verifier = MagicMock()
        mock_verifier.verify_license.return_value = LicenseResult(success=False, error="Invalid key")

        manager = LicenseManager(config_dir=tmp_path, verifier=mock_verifier)
        result = manager.activate("INVALID")

        assert result.success is False
        assert "Invalid" in result.error

    def test_get_state_returns_none_when_no_license(self, tmp_path):
        """get_state returns None when no license file."""
        manager = LicenseManager(config_dir=tmp_path)
        assert manager.get_state() is None

    def test_deactivate_removes_state(self, tmp_path):
        """deactivate removes the license file."""
        manager = LicenseManager(config_dir=tmp_path)
        create_eval_state(config_dir=tmp_path)

        assert manager.get_state() is not None
        assert manager.deactivate() is True
        assert manager.get_state() is None

    def test_deactivate_returns_false_when_no_license(self, tmp_path):
        """deactivate returns False when no license."""
        manager = LicenseManager(config_dir=tmp_path)
        assert manager.deactivate() is False

    def test_get_license_info_trial(self, tmp_path):
        """get_license_info returns expiration info for trial."""
        create_eval_state(config_dir=tmp_path)
        manager = LicenseManager(config_dir=tmp_path)

        info = manager.get_license_info()
        assert info is not None
        assert info["tier"] == "trial"
        assert info["days_remaining"] is not None
        assert info["created_at"] is not None
        assert info["expires_at"] is not None
        assert info["is_expired"] is False

    def test_get_license_info_standard(self, tmp_path):
        """get_license_info returns info for standard tier."""
        manager = LicenseManager(config_dir=tmp_path)
        state = LicenseState(
            license_key="STANDARD-KEY",
            tier="standard",
            email="test@example.com",
            created_at=datetime.now(timezone.utc),
        )
        manager._save_state(state)

        info = manager.get_license_info()
        assert info is not None
        assert info["tier"] == "standard"
        assert info["email"] == "test@example.com"
        assert info["days_remaining"] is None
        assert info["created_at"] is not None
        assert info["expires_at"] is None
        assert info["is_expired"] is False

    def test_tamper_detection(self, tmp_path):
        """Tampered state file raises error."""
        manager = LicenseManager(config_dir=tmp_path)
        create_eval_state(config_dir=tmp_path)

        license_file = tmp_path / ".license"
        content = license_file.read_text()
        license_file.write_text(content.replace("trial", "standard"))

        with pytest.raises(TamperedStateError):
            manager._load_state()


class TestCreateEvalState:
    """Tests for create_eval_state (trial)."""

    def test_creates_trial_tier(self, tmp_path):
        """Creates a trial tier state with 7-day expiration."""
        state = create_eval_state(config_dir=tmp_path)

        assert state.tier == "trial"
        assert state.license_key == "TRIAL"
        assert state.expires_at is not None

    def test_trial_expires_in_7_days(self, tmp_path):
        """Trial expires approximately 7 days from creation."""
        state = create_eval_state(config_dir=tmp_path)

        days = state.days_remaining()
        assert days is not None
        assert 6 <= days <= 7

    def test_state_is_persisted(self, tmp_path):
        """State is saved to disk."""
        create_eval_state(config_dir=tmp_path)

        manager = LicenseManager(config_dir=tmp_path)
        state = manager.get_state()

        assert state is not None
        assert state.tier == "trial"

    def test_trial_reactivation_within_window_succeeds(self, tmp_path):
        """Reactivating trial within 7-day window succeeds with original expiry."""
        # Create initial trial
        state1 = create_eval_state(config_dir=tmp_path)
        original_expires = state1.expires_at

        # Delete license file (simulating deactivation)
        license_file = tmp_path / ".license"
        license_file.unlink()

        # Reactivate - should work and keep original expiry
        state2 = create_eval_state(config_dir=tmp_path)
        assert state2.tier == "trial"
        assert state2.expires_at == original_expires

    def test_trial_expired_window_raises_error(self, tmp_path):
        """Creating trial after 7-day window expired raises TrialAlreadyUsedError."""
        from datetime import timedelta

        # Create trial_used file with expired dates
        expired_created = datetime.now(timezone.utc) - timedelta(days=10)
        expired_expires = expired_created + timedelta(days=7)
        mark_trial_used(config_dir=tmp_path, created_at=expired_created, expires_at=expired_expires)

        with pytest.raises(TrialAlreadyUsedError):
            create_eval_state(config_dir=tmp_path)


class TestLicenseValidation:
    """Tests for license validation and re-validation."""

    def test_validate_trial_not_expired(self, tmp_path):
        """Valid trial license passes validation."""
        create_eval_state(config_dir=tmp_path)
        manager = LicenseManager(config_dir=tmp_path)

        is_valid, error = manager.validate()

        assert is_valid is True
        assert error == ""

    def test_validate_trial_expired(self, tmp_path):
        """Expired trial license fails validation."""
        manager = LicenseManager(config_dir=tmp_path)
        # Manually create expired trial state
        state = LicenseState(
            license_key="TRIAL",
            tier="trial",
            created_at=datetime.now(timezone.utc) - timedelta(days=10),
            expires_at=datetime.now(timezone.utc) - timedelta(days=3),
        )
        manager._save_state(state)

        is_valid, error = manager.validate()

        assert is_valid is False
        assert "expired" in error.lower()

    def test_validate_no_license(self, tmp_path):
        """No license file fails validation."""
        manager = LicenseManager(config_dir=tmp_path)

        is_valid, error = manager.validate()

        assert is_valid is False
        assert "No license" in error

    def test_needs_revalidation_standard_old(self):
        """Standard license needs revalidation after 24 hours."""
        state = LicenseState(
            license_key="STANDARD-KEY",
            tier="standard",
            last_validated_at=datetime.now(timezone.utc) - timedelta(hours=25),
        )

        assert state.needs_revalidation() is True

    def test_needs_revalidation_standard_recent(self):
        """Standard license doesn't need revalidation within 24 hours."""
        state = LicenseState(
            license_key="STANDARD-KEY",
            tier="standard",
            last_validated_at=datetime.now(timezone.utc) - timedelta(hours=12),
        )

        assert state.needs_revalidation() is False

    def test_needs_revalidation_enterprise(self):
        """Enterprise license needs revalidation after 24 hours."""
        state = LicenseState(
            license_key="ENTERPRISE-KEY",
            tier="enterprise",
            last_validated_at=datetime.now(timezone.utc) - timedelta(hours=25),
        )

        assert state.needs_revalidation() is True

    def test_validate_standard_revalidates_with_gumroad(self, tmp_path):
        """Standard license re-validates with Gumroad API when needed."""
        mock_verifier = MagicMock()
        mock_verifier.verify_license.return_value = LicenseResult(success=True)

        manager = LicenseManager(config_dir=tmp_path, verifier=mock_verifier)

        # Create standard state that needs revalidation
        state = LicenseState(
            license_key="STANDARD-KEY",
            tier="standard",
            last_validated_at=datetime.now(timezone.utc) - timedelta(hours=25),
        )
        manager._save_state(state)

        is_valid, _ = manager.validate()

        assert is_valid is True
        mock_verifier.verify_license.assert_called_once_with("STANDARD-KEY", increment_uses=False)

    def test_validate_standard_subscription_cancelled(self, tmp_path):
        """Standard license fails when subscription is cancelled."""
        mock_verifier = MagicMock()
        mock_verifier.verify_license.return_value = LicenseResult(
            success=False, error="Subscription has been cancelled"
        )

        manager = LicenseManager(config_dir=tmp_path, verifier=mock_verifier)

        # Create standard state that needs revalidation
        state = LicenseState(
            license_key="STANDARD-KEY",
            tier="standard",
            last_validated_at=datetime.now(timezone.utc) - timedelta(hours=25),
        )
        manager._save_state(state)

        is_valid, error = manager.validate()

        assert is_valid is False
        assert "cancelled" in error.lower()
        # License file should be removed
        assert manager.get_state() is None


class TestHardwareFingerprint:
    """Tests for hardware fingerprint functions."""

    def test_get_machine_fingerprint_returns_consistent_value(self):
        """Machine fingerprint returns same value on repeated calls."""
        fp1 = get_machine_fingerprint()
        fp2 = get_machine_fingerprint()

        assert fp1 == fp2
        assert isinstance(fp1, str)
        assert len(fp1) > 0

    def test_get_machine_fingerprint_returns_sha256_hex(self):
        """Machine fingerprint is a valid SHA256 hex string."""
        fp = get_machine_fingerprint()

        # SHA256 produces 64 hex characters
        assert len(fp) == 64
        assert all(c in "0123456789abcdef" for c in fp)

    def test_get_machine_fingerprint_fallback_path(self):
        """Machine fingerprint uses hostname/username fallback when machine-id unavailable."""
        with patch("ccp.auth.Path") as mock_path_class:
            # Mock Path to simulate no machine-id files
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_path_class.return_value = mock_path

            with patch("ccp.auth.platform.system", return_value="Linux"):
                with patch("ccp.auth.socket.gethostname", return_value="test-host"):
                    with patch("ccp.auth.getpass.getuser", return_value="test-user"):
                        fp = get_machine_fingerprint()

                        # Should still return valid fingerprint
                        assert len(fp) == 64
                        assert all(c in "0123456789abcdef" for c in fp)

    def test_has_used_trial_returns_false_initially(self, tmp_path):
        """has_used_trial returns False when no trial has been used."""
        result = has_used_trial(config_dir=tmp_path)

        assert result is False

    def test_mark_trial_used_creates_file(self, tmp_path):
        """mark_trial_used creates the .trial_used file."""
        mark_trial_used(config_dir=tmp_path)

        trial_used_file = tmp_path / ".trial_used"
        assert trial_used_file.exists()

    def test_has_used_trial_returns_true_after_marking(self, tmp_path):
        """has_used_trial returns True after mark_trial_used is called."""
        assert has_used_trial(config_dir=tmp_path) is False

        mark_trial_used(config_dir=tmp_path)

        assert has_used_trial(config_dir=tmp_path) is True

    def test_deactivate_does_not_remove_trial_used(self, tmp_path):
        """Deactivating license does not remove trial_used marker."""
        # Create trial and mark as used
        create_eval_state(config_dir=tmp_path)

        manager = LicenseManager(config_dir=tmp_path)
        assert manager.get_state() is not None
        assert has_used_trial(config_dir=tmp_path) is True

        # Deactivate
        manager.deactivate()

        # License gone but trial marker remains
        assert manager.get_state() is None
        assert has_used_trial(config_dir=tmp_path) is True
