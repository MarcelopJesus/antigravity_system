"""Tests for settings and credential loading (Story 1.4)."""
import os
import pytest
from unittest.mock import patch
from config.settings import load_wp_credentials


class TestLoadWpCredentials:
    def test_env_prefix_mode(self):
        site = {
            "site_name": "Test Site",
            "credentials_env_prefix": "TEST"
        }
        with patch.dict(os.environ, {
            "TEST_WP_USERNAME": "admin",
            "TEST_WP_APP_PASSWORD": "secret123"
        }):
            user, pwd = load_wp_credentials(site)
        assert user == "admin"
        assert pwd == "secret123"

    def test_env_prefix_missing_raises(self):
        site = {
            "site_name": "Test Site",
            "credentials_env_prefix": "MISSING"
        }
        with patch.dict(os.environ, {}, clear=False):
            # Ensure the vars don't exist
            os.environ.pop("MISSING_WP_USERNAME", None)
            os.environ.pop("MISSING_WP_APP_PASSWORD", None)
            with pytest.raises(ValueError, match="credentials not found"):
                load_wp_credentials(site)

    def test_legacy_mode(self):
        site = {
            "site_name": "Legacy Site",
            "wordpress_username": "old_admin",
            "wordpress_app_password": "old_pass"
        }
        user, pwd = load_wp_credentials(site)
        assert user == "old_admin"
        assert pwd == "old_pass"

    def test_legacy_missing_raises(self):
        site = {"site_name": "Broken Site"}
        with pytest.raises(ValueError, match="credentials missing"):
            load_wp_credentials(site)

    def test_env_prefix_takes_priority(self):
        site = {
            "site_name": "Test",
            "credentials_env_prefix": "PRI",
            "wordpress_username": "should_not_use",
            "wordpress_app_password": "should_not_use"
        }
        with patch.dict(os.environ, {
            "PRI_WP_USERNAME": "env_user",
            "PRI_WP_APP_PASSWORD": "env_pass"
        }):
            user, pwd = load_wp_credentials(site)
        assert user == "env_user"
        assert pwd == "env_pass"
