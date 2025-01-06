# encoding=utf-8
# -*- coding: UTF-8 -*-

# ------------------------------------------------------------------------
# Copyright (c) 2024-2025 Alexandre Bento Freire. All rights reserved.
# Licensed under the GPLv3 License.
# ------------------------------------------------------------------------

from docx import Document


class DocWorker:
    def __init__(self) -> None:
        self.files = {}

    def is_slow(self):
        return True

    def get_extensions(self):
        return ['.doc', '.docx']

    def eval_expr(self, macro, filename, groups):
        header = self.files[filename]
        if header:
            return macro.replace(f"%header%", header)
        raise

    def prepare(self, files):
        for filename in files:
            header = None
            try:
                doc = Document(filename)
                for paragraph in doc.paragraphs:
                    if paragraph.style.name.startswith("Heading"):
                        header = paragraph.text
                        break
            except:
                pass
            self.files[filename] = header


def get_worker():
    return DocWorker()
