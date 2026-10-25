"""Isolated CLI and installer tests; no Norminette installation is needed."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = 'norm42'
CLEAR = b'\x1b[H\x1b[2J\x1b[3J'


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='norm42-test-')
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.mock_bin = self.home / 'mock bin'
        self.mock_bin.mkdir()
        (self.mock_bin / 'bash').symlink_to(shutil.which('bash'))
        self.trace = self.home / 'trace'
        self.argv = self.home / 'argv'
        self.env = dict(os.environ)
        self.env.update(HOME=str(self.home), PATH=str(self.mock_bin),
                        TRACE=str(self.trace), ARGV=str(self.argv), TERM='xterm')
        self.write_mock('clear', 'printf "clear\\n" >> "$TRACE"\n'
                        'printf "\\033[H\\033[2J\\033[3J"\nexit "${CLEAR_STATUS:-0}"\n')
        self.write_mock('norminette', 'printf "run\\n" >> "$TRACE"\n'
                        'printf "%s\\000" "$@" > "$ARGV"\n'
                        'printf "original stdout\\n"\nprintf "original stderr\\n" >&2\n'
                        'exit "${RUN_STATUS:-0}"\n')

    def write_mock(self, name, body):
        path = self.mock_bin / name
        path.write_text('#!/bin/sh\n' + body)
        path.chmod(0o755)

    def cli(self, *args, **env):
        return subprocess.run([str(ROOT / 'bin' / PROGRAM), *args], cwd=self.home,
                              env=dict(self.env, **env), capture_output=True, timeout=15)

    def arguments(self):
        return self.argv.read_bytes().split(b'\0')[:-1]

    def installer(self, *args, uninstall=False):
        env = dict(os.environ, HOME=str(self.home))
        name = 'uninstall.sh' if uninstall else 'install.sh'
        return subprocess.run(['bash', str(ROOT / name), *args], cwd=self.home,
                              env=env, capture_output=True, timeout=15)

    def test_default_directory_and_order(self):
        result = self.cli()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.arguments(), [b'-R', b'CheckForbiddenSourceHeader', b'.'])
        self.assertEqual(self.trace.read_text(), 'clear\nrun\n')
        self.assertEqual(result.stdout, CLEAR + b'original stdout\n')
        self.assertEqual(result.stderr, b'original stderr\n')

    def test_argument_boundaries(self):
        for args in [('file.c',), ('dir/',), ('/absolute/path/',),
                     ('one.c', 'two.h'), ('directory with spaces/file.c',)]:
            with self.subTest(args=args):
                result = self.cli(*args)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(self.arguments(), [b'-R', b'CheckForbiddenSourceHeader',
                                                   *[os.fsencode(a) for a in args]])

    def test_status_and_clear_failure(self):
        for status in [0, 1, 42, 127]:
            with self.subTest(status=status):
                self.assertEqual(self.cli(RUN_STATUS=str(status), CLEAR_STATUS='9').returncode,
                                 status)

    def test_missing_checker(self):
        (self.mock_bin / 'norminette').unlink()
        result = self.cli()
        self.assertEqual(result.returncode, 127)
        self.assertEqual(result.stdout, CLEAR)
        self.assertIn(b'not found in PATH', result.stderr)

    def test_install_default_and_idempotence(self):
        target = self.home / '.local/bin' / PROGRAM
        self.assertEqual(self.installer().returncode, 0)
        self.assertEqual(target.read_bytes(), (ROOT / 'bin' / PROGRAM).read_bytes())
        self.assertTrue(os.access(target, os.X_OK))
        before = target.stat().st_mtime_ns
        result = self.installer()
        self.assertEqual(result.returncode, 0)
        self.assertIn(b'Already installed', result.stdout)
        self.assertEqual(before, target.stat().st_mtime_ns)
        self.assertFalse(list(target.parent.glob(PROGRAM + '.backup.*')))

    def test_custom_directory_with_spaces(self):
        target_dir = self.home / 'custom tools/bin'
        self.assertEqual(self.installer('--bin-dir', str(target_dir)).returncode, 0)
        self.assertTrue((target_dir / PROGRAM).is_file())
        self.assertFalse((self.home / '.local/bin' / PROGRAM).exists())
        result = self.installer('--bin-dir', str(target_dir), uninstall=True)
        self.assertEqual(result.returncode, 0)
        self.assertFalse((target_dir / PROGRAM).exists())

    def test_collision_and_force_backup(self):
        target = self.home / '.local/bin' / PROGRAM
        target.parent.mkdir(parents=True)
        target.write_text('existing command\n')
        self.assertNotEqual(self.installer().returncode, 0)
        self.assertEqual(target.read_text(), 'existing command\n')
        self.assertEqual(self.installer('--force').returncode, 0)
        backups = list(target.parent.glob(PROGRAM + '.backup.*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), 'existing command\n')

    def test_symlink_is_never_replaced_or_removed(self):
        target = self.home / '.local/bin' / PROGRAM
        target.parent.mkdir(parents=True)
        target.symlink_to(ROOT / 'bin' / PROGRAM)
        self.assertNotEqual(self.installer('--force').returncode, 0)
        self.assertNotEqual(self.installer(uninstall=True).returncode, 0)
        self.assertTrue(target.is_symlink())

    def test_directory_is_never_replaced(self):
        target = self.home / '.local/bin' / PROGRAM
        target.mkdir(parents=True)
        self.assertNotEqual(self.installer('--force').returncode, 0)
        self.assertTrue(target.is_dir())

    def test_safe_uninstall(self):
        self.assertEqual(self.installer(uninstall=True).returncode, 0)
        self.assertEqual(self.installer().returncode, 0)
        self.assertEqual(self.installer(uninstall=True).returncode, 0)
        target = self.home / '.local/bin' / PROGRAM
        self.assertFalse(target.exists())
        self.assertEqual(self.installer().returncode, 0)
        target.write_text('modified command\n')
        self.assertNotEqual(self.installer(uninstall=True).returncode, 0)
        self.assertEqual(target.read_text(), 'modified command\n')

    def test_installer_help_and_bad_options(self):
        for uninstall in [False, True]:
            self.assertEqual(self.installer('--help', uninstall=uninstall).returncode, 0)
            for args in [('--bin-dir',), ('--bin-dir', ''), ('--unknown',)]:
                self.assertEqual(self.installer(*args, uninstall=uninstall).returncode, 64)


if __name__ == '__main__':
    unittest.main()
