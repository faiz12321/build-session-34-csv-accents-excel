import os
from unittest import mock
"""Fixture tests, all writes confined to uniquely created temporary folders."""
import contextlib
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import excelbom

HERE = Path(__file__).resolve().parent


class Checks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.path = self.folder / 'a.csv'

    def tearDown(self):
        self.temp.cleanup()

    def call(self, data, fix=False):
        self.path.write_bytes(data)
        out, err = io.StringIO(), io.StringIO()
        args = ['excelbom.py', str(self.path)] + (['--fix'] if fix else [])
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = excelbom.main(args)
        return rc, out.getvalue(), err.getvalue()

    def test_plain_utf8(self):
        rc, out, _ = self.call('Item\nCafé\n'.encode())
        self.assertEqual(rc, 0)
        self.assertIn('WITHOUT', out)
        self.assertIn('simulation', out)
        self.assertEqual(sorted(p.name for p in self.folder.iterdir()), ['a.csv'])

    def test_bom_valid(self):
        self.assertIn('WITH a byte-order mark', self.call(excelbom.BOM+b'A\n')[1])

    def test_invalid_utf8_without_bom(self):
        self.assertEqual(self.call(b'A\n\xff', True)[0], 1)
        self.assertFalse((self.folder/'a.bom.csv').exists())

    def test_invalid_utf8_with_bom(self):
        rc, out, _ = self.call(excelbom.BOM+b'A\n\xff', True)
        self.assertEqual(rc, 1)
        self.assertIn('not valid UTF-8', out)
        self.assertFalse((self.folder/'a.bom.csv').exists())

    def test_new_copy_exact_bytes(self):
        original='A\nCafé\r\n'.encode()
        self.assertEqual(self.call(original, True)[0], 0)
        self.assertEqual((self.folder/'a.bom.csv').read_bytes(), excelbom.BOM+original)
        self.assertEqual(self.path.read_bytes(), original)

    def test_existing_copy_refused(self):
        target=self.folder/'a.bom.csv';target.write_bytes(b'KEEP')
        rc, _, err=self.call(b'A\n', True)
        self.assertEqual(rc, 1)
        self.assertEqual(target.read_bytes(), b'KEEP')
        self.assertIn('already exists', err)

    def test_output_directory_refused(self):
        (self.folder/'a.bom.csv').mkdir()
        self.assertNotEqual(self.call(b'A\n', True)[0], 0)
        self.assertTrue((self.folder/'a.bom.csv').is_dir())

    def test_marked_no_duplicate(self):
        self.assertEqual(self.call(excelbom.BOM+b'A\n', True)[0], 0)
        self.assertFalse((self.folder/'a.bom.csv').exists())

    def test_empty_utf8(self):
        self.assertEqual(self.call(b'', True)[0], 0)
        self.assertEqual((self.folder/'a.bom.csv').read_bytes(), excelbom.BOM)

    def test_read_only_keeps_bytes_metadata_and_directory(self):
        original='A\nThé\n'.encode();self.path.write_bytes(original)
        before=(self.path.read_bytes(),self.path.stat().st_mtime_ns,sorted(self.folder.iterdir()))
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(excelbom.main(['excelbom.py',str(self.path)]),0)
        self.assertEqual(before,(self.path.read_bytes(),self.path.stat().st_mtime_ns,sorted(self.folder.iterdir())))

    def test_fix_keeps_source_mtime(self):
        self.path.write_bytes(b'A\n');stamp=self.path.stat().st_mtime_ns
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(excelbom.main(['excelbom.py',str(self.path),'--fix']),0)
        self.assertEqual(self.path.stat().st_mtime_ns,stamp)

    def test_non_csv_still_not_certified(self):
        rc,out,_=self.call(b'not,a,consistent\nCSV\n')
        self.assertEqual(rc,0)
        self.assertIn('does not verify CSV structure',out)

    def test_wrong_flag(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(excelbom.main(['excelbom.py',str(self.path),'--overwrite']),2)

    def test_missing_file(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(excelbom.main(['excelbom.py',str(self.path)]),2)

    def test_setup_refuses_existing_sample(self):
        script=self.folder/'make_sample.py';shutil.copyfile(HERE/'make_sample.py',script)
        first=subprocess.run([sys.executable,str(script)],capture_output=True)
        self.assertEqual(first.returncode,0)
        target=self.folder/'sample'/'guests.csv';before=target.read_bytes()
        sentinel=self.folder/'sample'/'keep.txt';sentinel.write_bytes(b'KEEP')
        again=subprocess.run([sys.executable,str(script)],capture_output=True)
        self.assertNotEqual(again.returncode,0)
        self.assertEqual(target.read_bytes(),before)
        self.assertEqual(sentinel.read_bytes(),b'KEEP')


class PathSafety(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.root=self.base/'tree';self.root.mkdir()
        self.file=self.root/'zero';self.file.write_bytes(b'')
    def link(self,path,target,directory=False):
        try:path.symlink_to(target,target_is_directory=directory)
        except OSError:self.skipTest('Symlinks unavailable')
    def code(self,path):
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            return excelbom.main(['p',str(path)])
    def test_root_alias_refuses(self):
        p=self.base/'alias';self.link(p,self.root,True);self.assertEqual(self.code(p),2)
    def test_ancestor_alias_refuses(self):
        p=self.base/'alias';self.link(p,self.base,True);self.assertEqual(self.code(p/'tree'),2)
    def test_file_alias_refuses(self):
        p=self.base/'linked';self.link(p,self.file);self.assertEqual(self.code(p),2)
    def test_file_hardlink_refuses(self):
        p=self.base/'hard';os.link(self.file,p);self.assertEqual(self.code(p),2)
    def test_file_pipe_refuses(self):
        if not hasattr(os,'mkfifo'):self.skipTest('Unix pipe unavailable')
        p=self.base/'pipe';os.mkfifo(p);self.assertEqual(self.code(p),2)
    def test_file_self_loop_refuses(self):
        p=self.base/'loop';self.link(p,p);self.assertEqual(self.code(p),2)
    def test_file_dangling_refuses(self):
        p=self.base/'alias';self.link(p,self.base/'missing');self.assertEqual(self.code(p),2)
    def test_file_traversal_refuses(self):self.assertEqual(self.code(self.root/'..'/'tree'/'zero'),2)
    def test_file_ancestor_refuses(self):
        p=self.base/'alias';self.link(p,self.root,True);self.assertEqual(self.code(p/'zero'),2)
    def test_metadata_error_refuses(self):
        with mock.patch.object(Path,'lstat',side_effect=OSError('forced')):self.assertEqual(self.code(self.file),2)
    def test_reparse_attribute_refuses(self):
        real=Path.lstat
        def fake(p,*a,**kw):
            value=real(p,*a,**kw)
            if p==self.file:return type('Reparse',(),{'st_mode':value.st_mode,'st_file_attributes':0x400})()
            return value
        with mock.patch.object(Path,'lstat',fake):self.assertEqual(self.code(self.file),2)


    def test_read_error_stops(self):
        with mock.patch.object(Path,'open',side_effect=OSError('forced')):
            self.assertEqual(self.code(self.file),2)
    def test_setup_alias_parent_refuses(self):
        import make_sample
        p=self.base/'alias';self.link(p,self.root,True)
        with mock.patch.object(make_sample,'__file__',str(p/'make_sample.py')):
            with self.assertRaises(OSError):make_sample.main()
        self.assertFalse((self.root/'sample').exists())
    def test_setup_traversal_refuses(self):
        import make_sample
        with mock.patch.object(make_sample,'__file__',str(self.root/'..'/'make_sample.py')):
            with self.assertRaises(OSError):make_sample.main()

    def test_output_linked_parent_refuses(self):
        p=self.base/'alias';self.link(p,self.root,True)
        with self.assertRaises(OSError):excelbom.safe_output(p/'new')
        self.assertFalse((self.root/'new').exists())
    def test_output_traversal_refuses(self):
        with self.assertRaises(OSError):excelbom.safe_output(self.root/'..'/'new')
    def test_output_metadata_error_refuses(self):
        with mock.patch.object(Path,'lstat',side_effect=OSError('forced')):
            with self.assertRaises(OSError):excelbom.safe_output(self.root/'new')


if __name__ == '__main__':
    unittest.main()
