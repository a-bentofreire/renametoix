# --------------------------------------------------------------------
# Copyright (c) 2024 Alexandre Bento Freire. All rights reserved.
# Licensed under the MIT license
# --------------------------------------------------------------------

import os
import re
import shutil
import pytest

package_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../usr/lib/renametoix')


class TestInitStream:

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self, tmpdir):
        self.files = [
            'IMG_501.jpg', 'IMG_503.jpg',
            'Doc_a.txt', 'doc_b.txt', 'd.txt',
            'e.pdf',
        ]
        self.work_path = tmpdir.join("renametoix-tests")
        shutil.rmtree(self.work_path, ignore_errors=True)
        os.makedirs(self.work_path, exist_ok=True)
        for filename in self.files:
            with open(os.path.join(self.work_path, filename), "w") as f:
                f.write("x" * 5)
        yield
        shutil.rmtree(self.work_path, ignore_errors=True)

    def call(self, find, replace, reg_ex=False, pattern='*', params='', changes=None):
        cmd_line = f"python3 {package_path}/crenametoix.py -find '{find}' -replace '{replace}' "\
            f"{'-reg-ex' if reg_ex else ''} {params} {self.work_path}/{pattern}"
        print(cmd_line)
        os.system(cmd_line)
        actual_list = sorted(os.listdir(self.work_path))
        expected_list = []
        for filename in self.files:
            name, ext = os.path.splitext(filename)
            name = changes(name, ext)
            expected_list.append(name + ext)
        expected_list = sorted(expected_list)
        if actual_list != expected_list:
            print(f"Actual:   {str(actual_list)}\nExpected: {str(expected_list)}")
        assert actual_list == expected_list
        self.files = expected_list

    def test_rename(self):
        self.call('oc', 'C', changes=lambda name, _: name.replace('oc', 'C'))
        self.call('', 'prefix-%B', pattern='*.txt',
                  changes=lambda name, ext: f'prefix-{name}' if ext.endswith('.txt') else name)
        self.call('.5', '-6', reg_ex=True,
                  changes=lambda name, _: re.sub(r'.5', r'-6', name))


if __name__ == '__main__':
    pytest.main()
