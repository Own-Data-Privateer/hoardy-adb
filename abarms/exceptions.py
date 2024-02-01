# This file is a part of kisstdlib project.
#
# This file can be distributed under the terms of the MIT-style license given
# below or Python Software Foundation License version 2 (PSF-2.0) as published
# by Python Software Foundation.
#
# Copyright (c) 2023 Jan Malakhovski <oxij@oxij.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Exceptions with printable descriptions.
"""

import typing as _t

class CatastrophicFailure(Exception):
    def __init__(self, what : str, *args : _t.Any) -> None:
        super().__init__()
        self.description = what % args

    def __str__(self) -> str:
        return self.description

    def elaborate(self, what : str, *args : _t.Any) -> None:
        self.description = what % args + ": " + self.description

class Failure(CatastrophicFailure):
    pass
