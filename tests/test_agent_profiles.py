"""Cross-platform native agent declarations and release boundaries."""
import json
import sys
import unittest
from pathlib import Path

if sys.version_info < (3, 11):
    raise unittest.SkipTest(
        "需要 Python 3.11+（tomllib）才能校验 Codex 的 TOML 角色文件；请用 python3.12 -m unittest"
    )

import tomllib  # noqa: E402  # requires Python 3.11+

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import sync_agents

class NativeAgentsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry=json.loads((ROOT/"agents/registry.json").read_text(encoding="utf-8"))
    def test_all_roles_have_four_native_profiles(self):
        self.assertEqual(len(self.registry["roles"]),10)
        self.assertFalse(sync_agents.validate_registry(self.registry))
        for platform in sync_agents.TARGETS:
            for path,text in sync_agents.expected_paths(self.registry,platform).items():
                self.assertTrue(path.is_file(),path)
                self.assertEqual(path.read_text(encoding="utf-8"),text,path)
    def test_codex_toml_loads_and_never_overrides_parent_policy(self):
        for file in (ROOT/".codex/agents").glob("*.toml"):
            d=tomllib.loads(file.read_text(encoding="utf-8"))
            self.assertTrue(d["developer_instructions"])
            self.assertNotIn("approval_policy",d)
            self.assertNotIn("sandbox_mode",d)
    def test_open_code_v2_and_read_only_roles(self):
        for role in self.registry["roles"]:
            text=(ROOT/".opencode/agents"/(role["id"]+".md")).read_text(encoding="utf-8")
            self.assertIn("permissions:",text)
            self.assertNotIn("\npermission:",text)
            if role["access"]=="reviewer":
                self.assertIn('action: edit',text)
                self.assertIn('effect: deny',text)
                c=(ROOT/".claude/agents"/(role["id"]+".md")).read_text(encoding="utf-8")
                self.assertIn("tools: Read, Grep, Glob",c)
    def test_pi_extension_is_opt_in(self):
        docs=(ROOT/".pi/README.md").read_text(encoding="utf-8")
        self.assertIn("agentScope",docs)
        self.assertIn("subagent",docs.lower())
    def test_handoff_sample_explicitly_pending(self):
        data=json.loads((ROOT/"agents/examples/pending-verification.json").read_text(encoding="utf-8"))
        self.assertEqual(data["status"],"pending")
        self.assertEqual(data["evidence"],[])
        self.assertIn("blockers",data)

if __name__=="__main__":
    unittest.main()
