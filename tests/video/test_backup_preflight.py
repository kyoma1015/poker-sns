"""Synthetic JIT/Storage backup preflight tests: no network and no real credentials."""
import importlib.util
from pathlib import Path
import unittest
from urllib.parse import quote

P = Path(__file__).resolve().parents[2]/"scripts"/"video_backup_preflight.py"
spec = importlib.util.spec_from_file_location("backup_preflight", P)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
REF = module.PROJECT

class BackupPreflightTests(unittest.TestCase):
    def setUp(self):
        self.settings = {
            "PROD_DB_URL": f"postgresql://postgres.{REF}:synthetic@aws-0-region.pooler.supabase.com:5432/postgres?sslmode=require",
            "PROD_SUPABASE_URL": f"https://{REF}.supabase.co",
            "PROD_STORAGE_READ_KEY": "sb_secret_" + "a"*32,
            "BACKUP_AGE_RECIPIENT": "age1" + "q"*58,
        }
    def check_rejected(self, key, value):
        self.settings[key] = value
        with self.assertRaises(ValueError):
            module.validate(self.settings)
    def test_pooler_valid(self):
        self.assertTrue(module.validate(self.settings))
    def test_direct_valid(self):
        self.settings["PROD_DB_URL"] = f"postgresql://postgres:synthetic@db.{REF}.supabase.co:5432/postgres?sslmode=verify-full"
        self.assertTrue(module.validate(self.settings))
    def test_wrong_project_and_host_rejected(self):
        self.check_rejected("PROD_DB_URL", "postgresql://postgres.other:password@aws-0-region.pooler.supabase.com:5432/postgres?sslmode=require")
        self.check_rejected("PROD_DB_URL", "postgresql://postgres:password@evil.example:5432/postgres?sslmode=require")
    def test_tls_missing_or_overridden_rejected(self):
        base = self.settings["PROD_DB_URL"]
        self.check_rejected("PROD_DB_URL", base.replace("sslmode=require", "sslmode=disable"))
        self.check_rejected("PROD_DB_URL", base + "&sslmode=disable")
    def test_wrong_port_and_redirect_rejected(self):
        base = self.settings["PROD_DB_URL"]
        self.check_rejected("PROD_DB_URL", base.replace(":5432/", ":6543/"))
        self.check_rejected("PROD_DB_URL", base + "&hostaddr=127.0.0.1")
    def test_jit_pooler_option_is_accepted(self):
        self.settings["PROD_DB_URL"] += "&options=-c%20jit%3Dtrue"
        self.assertTrue(module.validate(self.settings))

    def test_arbitrary_libpq_options_are_rejected(self):
        base=self.settings["PROD_DB_URL"]
        for suffix in ("&options=-c%20search_path%3Dpublic",
                       "&target_session_attrs=read-write",
                       "&sslmode=disable",
                       "&host=evil.example",
                       "&options=-c%20jit%3Dtrue%20-c%20role%3Dpostgres"):
            self.check_rejected("PROD_DB_URL",base+suffix)

    def test_jit_flag_on_direct_connection_is_rejected(self):
        self.settings["PROD_DB_URL"]=f"postgresql://postgres:synthetic@db.{REF}.supabase.co:5432/postgres?sslmode=require&options=-c%20jit%3Dtrue"
        with self.assertRaises(ValueError):
            module.validate(self.settings)

    def test_required_settings_fail_closed(self):
        for key in tuple(self.settings):
            settings = dict(self.settings)
            del settings[key]
            with self.assertRaises(ValueError):
                module.validate(settings)
    def test_storage_jit_token_rejected(self):
        self.check_rejected("PROD_STORAGE_READ_KEY", "temporary-access-pat")
        self.check_rejected("PROD_STORAGE_READ_KEY", "sb_publishable_demo")
    def test_legacy_storage_jwt_valid(self):
        self.settings["PROD_STORAGE_READ_KEY"] = "eyHeader.eyPayload.signature"
        self.assertTrue(module.validate(self.settings))
    def test_wrong_recipient_rejected(self):
        self.check_rejected("BACKUP_AGE_RECIPIENT", "age1invalid")
    def test_url_without_password_rejected(self):
        self.check_rejected("PROD_DB_URL", f"postgresql://postgres.{REF}@aws-0-region.pooler.supabase.com:5432/postgres?sslmode=require")

if __name__ == "__main__":
    unittest.main()
