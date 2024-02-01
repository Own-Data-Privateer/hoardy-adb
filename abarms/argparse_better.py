# This file is a part of kisstdlib project.
#
# This file can be distributed under the terms of the MIT-style license given
# below or Python Software Foundation License version 2 (PSF-2.0) as published
# by Python Software Foundation.
#
# Copyright (c) 2022-2023 Jan Malakhovski <oxij@oxij.org>
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

import typing as _t
from argparse import *
from gettext import gettext as _

class BetterHelpFormatter(HelpFormatter):
    """Like argparse.HelpFormatter, but with better formatting.
       Also, it adds `add_code` function.
    """

    def _fill_text(self, text : str, width : int, indent : str) -> str:
        import textwrap
        res = []
        for line in text.splitlines():
            if line == "":
                res.append(line)
                continue

            for sub in textwrap.wrap(line, width - len(indent)):
                sub = indent + sub
                res.append(sub)
        return "\n".join(res)

    def _split_lines(self, text : str, width : int) -> _t.List[str]:
        import textwrap
        res = []
        for line in text.splitlines():
            res += textwrap.wrap(line, width)
        return res

    def add_code(self, text : str) -> None:
        self.add_text(text.strip())

class MarkdownBetterHelpFormatter(BetterHelpFormatter):
    """BetterHelpFormatter that outputs stuff formatted in Markdown"""

    def add_code(self, text : str) -> None:
        self.add_text("```\n" + text.strip() + "\n```")

    def _format_usage(self, usage : _t.Optional[str], actions : _t.Any, groups : _t.Any, prefix : _t.Optional[str]) -> str:
        return super()._format_usage(usage, actions, groups, "")

    def _format_action(self, action : _t.Any) -> str:
        # determine the required width and the entry label
        action_header = self._format_action_invocation(action)

        tup = self._current_indent, '', "`" + action_header + "`"
        action_header = '%*s- %s\n' % tup

        # collect the pieces of the action help
        parts = [action_header]

        # if there was help for the action, add it
        if action.help and action.help.strip():
            first = True
            for line in self._expand_help(action).splitlines():
                if first:
                    parts.append('%*s: %s\n' % (self._current_indent, '', line))
                else:
                    parts.append('%*s  %s\n' % (self._current_indent, '', line))
                first = False

        # or add a newline if the description doesn't end with one
        elif not action_header.endswith('\n'):
            parts.append('\n')

        # if there are any sub-actions, add their help as well
        for subaction in self._iter_indented_subactions(action):
            parts.append(self._format_action(subaction))

        # return a single string
        return self._join_parts(parts)

    class _Section(HelpFormatter._Section):
        def format_help(self) -> str:
            if self.parent is not None:
                self.formatter._indent()
            join = self.formatter._join_parts
            item_help = join([func(*args) for func, args in self.items])
            if self.parent is not None:
                self.formatter._dedent()

            # return nothing if the section was empty
            if not item_help:
                return ''

            # add the heading if the section was non-empty
            if self.heading is not SUPPRESS and self.heading is not None:
                heading = '%*s- %s:\n' % (self.formatter._current_indent, '', self.heading)
            else:
                heading = ''

            # join the section-initial newline, the heading and the help
            return join(['\n', heading, item_help, '\n'])

class BetterArgumentParser(ArgumentParser):
    """Like argparse.ArgumentParser but uses BetterHelpFormatter by default,
       adds `--help` only to the root node, and
       that `--help` prints the help for all the subcommands at once.
       Also, provides `add_version` option.
    """

    formatter_class : _t.Any

    def __init__(self,
                 prog : _t.Optional[str] = None,
                 version : _t.Optional[str] = None,
                 add_version : bool = False, # we set these two to False by default
                 add_help : bool = False,    # so that subparsers don't get them enabled by default
                 additional_sections : _t.List[_t.Callable[[BetterHelpFormatter], None]] = [],
                 formatter_class : _t.Any = BetterHelpFormatter,
                 *args : _t.Any, **kwargs : _t.Any) -> None:
        super().__init__(prog, *args, formatter_class = formatter_class, add_help = False, **kwargs) # type: ignore

        if version is None:
            version = "dev"
            if prog is not None:
                try:
                    import importlib.metadata as meta
                    try:
                        version = meta.version(prog)
                    except meta.PackageNotFoundError:
                        pass
                except ImportError:
                    pass

        self.version = version
        self.add_version = add_version
        self.add_help = add_help
        self.additional_sections = additional_sections

        default_prefix = '-' if '-' in self.prefix_chars else self.prefix_chars[0]
        if self.add_version:
            self.add_argument(default_prefix*2 + "version", action="version", version="%(prog)s " + version)

        if self.add_help:
            self.add_argument(
                default_prefix + "h", default_prefix*2 + "help", action='help',
                default=SUPPRESS, help=_('show this help message and exit'))

    def set_formatter_class(self, formatter_class : _t.Any) -> None:
        self.formatter_class = formatter_class
        if hasattr(self._subparsers, "_group_actions"):
            for grp in self._subparsers._group_actions: # type: ignore
                for choice, e in grp.choices.items(): # type: ignore
                    if e.formatter_class != formatter_class:
                        e.formatter_class = formatter_class

    def format_help(self, width : _t.Optional[int] = None) -> str:
        if width is None:
            import shutil
            width = shutil.get_terminal_size().columns - 2
        formatter = self.formatter_class(prog=self.prog, width=width)

        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)
        formatter.add_text(self.description)

        if hasattr(self, "_action_groups"):
            for action_group in self._action_groups:
                formatter.start_section(action_group.title)
                formatter.add_text(action_group.description)
                formatter.add_arguments(action_group._group_actions)
                formatter.end_section()

        res : str = "# " + formatter.format_help()

        if hasattr(self._subparsers, "_group_actions"):
            seen = set()
            for grp in self._subparsers._group_actions: # type: ignore
                for choice, e in grp.choices.items(): # type: ignore
                    if e in seen: continue
                    seen.add(e)
                    e.formatter_class = self.formatter_class
                    res += "\n#" + e.format_help(width=width)

        for gen in self.additional_sections:
            formatter = self.formatter_class(prog=self.prog, width=width)
            gen(formatter)
            res += "\n" + formatter.format_help()

        formatter.add_text(self.epilog)

        return res
