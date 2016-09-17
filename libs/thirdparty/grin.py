#!/usr/bin/env python
""" grin searches text files.
"""

import bisect
import fnmatch
import gzip
import itertools
import os
import re
import shlex
import stat
import sys

import argparse


#### Constants ####
__version__ = '1.2.1'

# Maintain the numerical order of these constants. We use them for sorting.
PRE = -1
MATCH = 0
POST = 1

# Use file(1)'s choices for what's text and what's not.
TEXTCHARS = ''.join(map(chr, [7,8,9,10,12,13,27] + list(range(0x20, 0x100))))
ALLBYTES = ''.join(map(chr, range(256)))

COLOR_TABLE = ['black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan',
               'white', 'default']
COLOR_STYLE = {
        'filename': dict(fg="green", bold=True),
        'searchterm': dict(fg="black", bg="yellow"),
        }

# gzip magic header bytes.
GZIP_MAGIC = '\037\213'

# Target amount of data to read into memory at a time.
READ_BLOCKSIZE = 16 * 1024 * 1024


def is_binary_string(bytes):
    """ Determine if a string is classified as binary rather than text.

    Parameters
    ----------
    bytes : str

    Returns
    -------
    is_binary : bool
    """
    nontext = bytes.translate(ALLBYTES, TEXTCHARS)
    return bool(nontext)
    
def get_line_offsets(block):
    """ Compute the list of offsets in DataBlock 'block' which correspond to
    the beginnings of new lines.

    Returns: (offset list, count of lines in "current block")
    """
    # Note: this implementation based on string.find() benchmarks about twice as
    # fast as a list comprehension using re.finditer().
    line_offsets = [0]
    line_count = 0    # Count of lines inside range [block.start, block.end) *only*
    s = block.data
    while True:
        next_newline = s.find('\n', line_offsets[-1])
        if next_newline < 0:
            # Tack on a final "line start" corresponding to EOF, if not done already.
            # This makes it possible to determine the length of each line by computing
            # a difference between successive elements.
            if line_offsets[-1] < len(s):
                line_offsets.append(len(s))
            return (line_offsets, line_count)
        else:
            line_offsets.append(next_newline + 1)
            # Keep track of the count of lines within the "current block"
            if next_newline >= block.start and next_newline < block.end:
                line_count += 1
            
def colorize(s, fg=None, bg=None, bold=False, underline=False, reverse=False):
    """ Wraps a string with ANSI color escape sequences corresponding to the
    style parameters given.
    
    All of the color and style parameters are optional.
    
    Parameters
    ----------
    s : str
    fg : str
        Foreground color of the text.  One of (black, red, green, yellow, blue, 
        magenta, cyan, white, default)
    bg : str
        Background color of the text.  Color choices are the same as for fg.
    bold : bool
        Whether or not to display the text in bold.
    underline : bool
        Whether or not to underline the text.
    reverse : bool
        Whether or not to show the text in reverse video.

    Returns
    -------
    A string with embedded color escape sequences.
    """
    
    style_fragments = []
    if fg in COLOR_TABLE:
        # Foreground colors go from 30-39
        style_fragments.append(COLOR_TABLE.index(fg) + 30)
    if bg in COLOR_TABLE:
        # Background colors go from 40-49
        style_fragments.append(COLOR_TABLE.index(bg) + 40)
    if bold:
        style_fragments.append(1)
    if underline:
        style_fragments.append(4)
    if reverse:
        style_fragments.append(7)
    style_start = '\x1b[' + ';'.join(map(str,style_fragments)) + 'm'
    style_end = '\x1b[0m'
    return style_start + s + style_end


class Options(dict):
    """ Simple options.
    """

    def __init__(self, *args, **kwds):
        dict.__init__(self, *args, **kwds)
        self.__dict__ = self


def default_options():
    """ Populate the default options.
    """
    opt = Options(
        before_context = 0,
        after_context = 0,
        show_line_numbers = True,
        show_match = True,
        show_filename = True,
        show_emacs = False,
        skip_hidden_dirs=False,
        skip_hidden_files=False,
        skip_backup_files=True,
        skip_dirs=set(),
        skip_exts=set(),
        skip_symlink_dirs=True,
        skip_symlink_files=True,
        binary_bytes=4096,
        use_color=True,
    )
    return opt


class DataBlock(object):
    """ This class holds a block of data read from a file, along with
    some preceding and trailing context.

    Attributes
    ----------
    data  : byte string
    start : int
        Offset into 'data' where the "current block" begins; everything
        prior to this is 'before' context bytes
    end : int
        Offset into 'data' where the "current block" ends; everything
        after this is 'after' context bytes
    before_count : int
        Number of lines contained in data[:start]
    is_last : bool
        True if this is the final block in the file
    """
    def __init__(self, data='', start=0, end=0, before_count=0, is_last=False):
        self.data = data
        self.start = start
        self.end = end
        self.before_count = before_count
        self.is_last = is_last

EMPTY_DATABLOCK = DataBlock()


class GrepText(object):
    """ Grep a single file for a regex by iterating over the lines in a file.

    Attributes
    ----------
    regex : compiled regex
    options : Options or similar
    """

    def __init__(self, regex, options=None):
        # The compiled regex.
        self.regex = regex
        # An equivalent regex with multiline enabled.
        self.regex_m = re.compile(regex.pattern, regex.flags | re.MULTILINE)

        # The options object from parsing the configuration and command line.
        if options is None:
            options = default_options()
        self.options = options

    def read_block_with_context(self, prev, fp, fp_size):
        """ Read a block of data from the file, along with some surrounding
        context.
        
        Parameters
        ----------
        prev : DataBlock, or None
            The result of the previous application of read_block_with_context(),
            or None if this is the first block.

        fp : filelike object
            The source of block data.
        
        fp_size : int or None
            Size of the file in bytes, or None if the size could not be
            determined.
        
        Returns
        -------
        A DataBlock representing the "current" block along with context.
        """
        if fp_size is None:
            target_io_size = READ_BLOCKSIZE
            block_main = fp.read(target_io_size)
            is_last_block = len(block_main) < target_io_size
        else:
            remaining = max(fp_size - fp.tell(), 0)
            target_io_size = min(READ_BLOCKSIZE, remaining)
            block_main = fp.read(target_io_size)
            is_last_block = target_io_size == remaining

        if prev is None:
            if is_last_block:
                # FAST PATH: the entire file fits into a single block, so we
                # can avoid the overhead of locating lines of 'before' and
                # 'after' context.
                result = DataBlock(
                    data = block_main,
                    start = 0,
                    end = len(block_main),
                    before_count = 0,
                    is_last = True,
                )
                return result
            else:
                prev = EMPTY_DATABLOCK

        # SLOW PATH: handle the general case of a large file which is split
        # across multiple blocks.

        # Look back into 'preceding' for some lines of 'before' context.
        if prev.end == 0:
            before_start = 0
            before_count = 0
        else:
            before_start = prev.end - 1
            before_count = 0
            for i in range(self.options.before_context):
                ofs = prev.data.rfind('\n', 0, before_start)
                before_start = ofs
                before_count += 1
                if ofs < 0:
                    break
            before_start += 1
        before_lines = prev.data[before_start:prev.end]
        # Using readline() to force this block out to a newline boundary...
        curr_block = (prev.data[prev.end:] + block_main +
            ('' if is_last_block else fp.readline()))
        # Read in some lines of 'after' context.
        if is_last_block:
            after_lines = ''
        else:
            after_lines_list = [fp.readline() for i in range(self.options.after_context)]
            after_lines = ''.join(after_lines_list)

        result = DataBlock(
            data = before_lines + curr_block + after_lines,
            start = len(before_lines),
            end = len(before_lines) + len(curr_block),
            before_count = before_count,
            is_last = is_last_block,
        )
        return result

    def do_grep(self, fp):
        """ Do a full grep.

        Parameters
        ----------
        fp : filelike object
            An open filelike object.

        Returns
        -------
        A list of 4-tuples (lineno, type (POST/PRE/MATCH), line, spans).  For
        each tuple of type MATCH, **spans** is a list of (start,end) positions
        of substrings that matched the pattern.
        """
        context = []
        line_count = 0
        if isinstance(fp, gzip.GzipFile):
            fp_size = None  # gzipped data is usually longer than the file
        else:
            try:
                status = os.fstat(fp.fileno())
                if stat.S_ISREG(status.st_mode):
                    fp_size = status.st_size
                else:
                    fp_size = None
            except AttributeError:  # doesn't support fileno()
                fp_size = None

        block = self.read_block_with_context(None, fp, fp_size)
        while block.end > block.start:
            (block_line_count, block_context) = self.do_grep_block(block,
                    line_count - block.before_count)
            context += block_context
            if block.is_last:
                break

            next_block = self.read_block_with_context(block, fp, fp_size)
            if next_block.end > next_block.start:
                if block_line_count is None:
                    # If the file contains N blocks, then in the best case we
                    # will need to compute line offsets for the first N-1 blocks.
                    # Most files will fit within a single block, so if there are
                    # no regex matches then we can typically avoid computing *any*
                    # line offsets.
                    (_, block_line_count) = get_line_offsets(block)
                line_count += block_line_count
            block = next_block

        unique_context = self.uniquify_context(context)
        return unique_context

    def do_grep_block(self, block, line_num_offset):
        """ Grep a single block of file content.

        Parameters
        ----------
        block : DataBlock
            A chunk of file data.

        line_num_offset: int
            The number of lines preceding block.data.

        Returns
        -------
        Tuple of the form
            (line_count, list of (lineno, type (POST/PRE/MATCH), line, spans).
        'line_count' is either the number of lines in the block, or None if
        the line_count was not computed.  For each 4-tuple of type MATCH,
        **spans** is a list of (start,end) positions of substrings that matched
        the pattern.
        """
        before = self.options.before_context
        after = self.options.after_context
        block_context = []
        line_offsets = None
        line_count = None
        
        def build_match_context(match):
            match_line_num = bisect.bisect(line_offsets, match.start() + block.start) - 1
            before_count = min(before, match_line_num)
            after_count = min(after, (len(line_offsets) - 1) - match_line_num - 1)
            match_line = block.data[line_offsets[match_line_num]:line_offsets[match_line_num + 1]]
            spans = [m.span() for m in self.regex.finditer(match_line)]

            before_ctx = [(i + line_num_offset, PRE,
                block.data[line_offsets[i]:line_offsets[i+1]], None)
                    for i in range(match_line_num - before_count, match_line_num)]
            after_ctx = [(i + line_num_offset, POST,
                block.data[line_offsets[i]:line_offsets[i+1]], None)
                    for i in range(match_line_num + 1, match_line_num + after_count + 1)]
            match_ctx = [(match_line_num + line_num_offset, MATCH, match_line, spans)]
            return before_ctx + match_ctx + after_ctx

        # Using re.MULTILINE here, so ^ and $ will work as expected.
        for match in self.regex_m.finditer(block.data[block.start:block.end]):
            # Computing line offsets is expensive, so we do it lazily.  We don't
            # take the extra CPU hit unless there's a regex match in the file.
            if line_offsets is None:
                (line_offsets, line_count) = get_line_offsets(block)
            block_context += build_match_context(match)

        return (line_count, block_context)

    def uniquify_context(self, context):
        """ Remove duplicate lines from the list of context lines.
        """
        context.sort()
        unique_context = []
        for group in itertools.groupby(context, lambda ikl: ikl[0]):
            for i, kind, line, matches in group[1]:
                if kind == MATCH:
                    # Always use a match.
                    unique_context.append((i, kind, line, matches))
                    break
            else:
                # No match, only PRE and/or POST lines. Use the last one, which
                # should be a POST since we've sorted it that way.
                unique_context.append((i, kind, line, matches))

        return unique_context

    def report(self, context_lines, filename=None):
        """ Return a string showing the results.

        Parameters
        ----------
        context_lines : list of tuples of (int, PRE/MATCH/POST, str, spans)
            The lines of matches and context.
        filename : str, optional
            The name of the file being grepped, if one exists. If not provided,
            the filename may not be printed out.

        Returns
        -------
        text : str
            This will end in a newline character if there is any text. Otherwise, it
            might be an empty string without a newline.
        """
        if len(context_lines) == 0:
            return ''
        lines = []
        if not self.options.show_match:
            # Just show the filename if we match.
            line = '%s\n' % filename
            lines.append(line)
        else:
            if self.options.show_filename and filename is not None and not self.options.show_emacs:
                line = '%s:\n' % filename
                if self.options.use_color:
                    line = colorize(line, **COLOR_STYLE.get('filename', {}))
                lines.append(line)
            if self.options.show_emacs:
                template = '%(filename)s:%(lineno)s: %(line)s'
            elif self.options.show_line_numbers:
                template = '%(lineno)5s %(sep)s %(line)s'
            else:
                template = '%(line)s'
            for i, kind, line, spans in context_lines:
                if self.options.use_color and kind == MATCH and 'searchterm' in COLOR_STYLE:
                    style = COLOR_STYLE['searchterm']
                    orig_line = line[:]
                    total_offset = 0
                    for start, end in spans:
                        old_substring = orig_line[start:end]
                        start += total_offset
                        end += total_offset
                        color_substring = colorize(old_substring, **style)
                        line = line[:start] + color_substring + line[end:]
                        total_offset += len(color_substring) - len(old_substring)
                        
                ns = dict(
                    lineno = i+1,
                    sep = {PRE: '-', POST: '+', MATCH: ':'}[kind],
                    line = line,
                    filename = filename,
                )
                line = template % ns
                lines.append(line)
                if not line.endswith('\n'):
                    lines.append('\n')

        text = ''.join(lines)
        return text


    def grep_a_file(self, filename, opener=open):
        """ Grep a single file that actually exists on the file system.

        Parameters
        ----------
        filename : str
            The file to open.
        opener : callable
            A function to call which creates a file-like object. It should
            accept a filename and a mode argument like the builtin open()
            function which is the default.

        Returns
        -------
        report : str
            The grep results as text.
        """
        # Special-case stdin as "-".
        if filename == '-':
            f = sys.stdin
            filename = '<STDIN>'
        else:
            # 'r' does the right thing for both open ('rt') and gzip.open ('rb')
            f = opener(filename, 'r')
        try:
            unique_context = self.do_grep(f)
        finally:
            if filename != '-':
                f.close()
        report = self.report(unique_context, filename)
        return report

