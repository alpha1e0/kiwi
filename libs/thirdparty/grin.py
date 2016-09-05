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
TEXTCHARS = ''.join(map(chr, [7,8,9,10,12,13,27] + range(0x20, 0x100)))
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


class FileRecognizer(object):
    """ Configurable way to determine what kind of file something is.

    Attributes
    ----------
    skip_hidden_dirs : bool
        Whether to skip recursing into hidden directories, i.e. those starting
        with a "." character.
    skip_hidden_files : bool
        Whether to skip hidden files.
    skip_backup_files : bool
        Whether to skip backup files.
    skip_dirs : container of str
        A list of directory names to skip. For example, one might want to skip
        directories named "CVS".
    skip_exts : container of str
        A list of file extensions to skip. For example, some file names like
        ".so" are known to be binary and one may want to always skip them.
    skip_symlink_dirs : bool
        Whether to skip symlinked directories.
    skip_symlink_files : bool
        Whether to skip symlinked files.
    binary_bytes : int
        The number of bytes to check at the beginning and end of a file for
        binary characters.
    """

    def __init__(self, skip_hidden_dirs=False, skip_hidden_files=False,
                 skip_backup_files=False, skip_dirs=set(), skip_exts=set(),
                 skip_symlink_dirs=True, skip_symlink_files=True,
                 binary_bytes=4096):
        self.skip_hidden_dirs = skip_hidden_dirs
        self.skip_hidden_files = skip_hidden_files
        self.skip_backup_files = skip_backup_files
        self.skip_dirs = skip_dirs

        # For speed, split extensions into the simple ones, that are
        # compatible with os.path.splitext and hence can all be
        # checked for in a single set-lookup, and the weirdos that
        # can't and therefore must be checked for one at a time.
        self.skip_exts_simple = set()
        self.skip_exts_endswith = list()
        for ext in skip_exts:
            if os.path.splitext('foo.bar'+ext)[1] == ext:
                self.skip_exts_simple.add(ext)
            else:
                self.skip_exts_endswith.append(ext)
        
        self.skip_symlink_dirs = skip_symlink_dirs
        self.skip_symlink_files = skip_symlink_files
        self.binary_bytes = binary_bytes

    def is_binary(self, filename):
        """ Determine if a given file is binary or not.

        Parameters
        ----------
        filename : str

        Returns
        -------
        is_binary : bool
        """
        f = open(filename, 'rb')
        is_binary = self._is_binary_file(f)
        f.close()
        return is_binary

    def _is_binary_file(self, f):
        """ Determine if a given filelike object has binary data or not.

        Parameters
        ----------
        f : filelike object

        Returns
        -------
        is_binary : bool
        """
        try:
            bytes = f.read(self.binary_bytes)
        except Exception, e:
            # When trying to read from something that looks like a gzipped file,
            # it may be corrupt. If we do get an error, assume that the file is binary.
            return True
        return is_binary_string(bytes)

    def is_gzipped_text(self, filename):
        """ Determine if a given file is a gzip-compressed text file or not.

        If the uncompressed file is binary and not text, then this will return
        False.

        Parameters
        ----------
        filename : str

        Returns
        -------
        is_gzipped_text : bool
        """
        is_gzipped_text = False
        f = open(filename, 'rb')
        marker = f.read(2)
        f.close()
        if marker == GZIP_MAGIC:
            fp = gzip.open(filename)
            try:
                try:
                    is_gzipped_text = not self._is_binary_file(fp)
                except IOError:
                    # We saw the GZIP_MAGIC marker, but it is not actually a gzip
                    # file.
                    is_gzipped_text = False
            finally:
                fp.close()
        return is_gzipped_text

    def recognize(self, filename):
        """ Determine what kind of thing a filename represents.

        It will also determine what a directory walker should do with the
        file:

            'text' :
                It should should be grepped for the pattern and the matching
                lines displayed. 
            'binary' : 
                The file is binary and should be either ignored or grepped
                without displaying the matching lines depending on the
                configuration.
            'gzip' :
                The file is gzip-compressed and should be grepped while
                uncompressing.
            'directory' :
                The filename refers to a readable and executable directory that
                should be recursed into if we are configured to do so.
            'link' :
                The filename refers to a symlink that should be skipped.
            'unreadable' :
                The filename cannot be read (and also, in the case of
                directories, is not executable either).
            'skip' :
                The filename, whether a directory or a file, should be skipped
                for any other reason.

        Parameters
        ----------
        filename : str

        Returns
        -------
        kind : str
        """
        try:
            st_mode = os.stat(filename).st_mode
            if stat.S_ISREG(st_mode):
                return self.recognize_file(filename)
            elif stat.S_ISDIR(st_mode):
                return self.recognize_directory(filename)
            else:
                # We're only interested in regular files and directories.
                # A named pipe in particular would be problematic, because
                # it would cause open() to hang indefinitely.
                return 'skip'
        except OSError:
            return 'unreadable'
        
    def recognize_directory(self, filename):
        """ Determine what to do with a directory.
        """
        basename = os.path.split(filename)[-1]
        if (self.skip_hidden_dirs and basename.startswith('.') and 
            basename not in ('.', '..')):
            return 'skip'
        if self.skip_symlink_dirs and os.path.islink(filename):
            return 'link'
        if basename in self.skip_dirs:
            return 'skip'
        return 'directory'

    def recognize_file(self, filename):
        """ Determine what to do with a file.
        """
        basename = os.path.split(filename)[-1]
        if self.skip_hidden_files and basename.startswith('.'):
            return 'skip'
        if self.skip_backup_files and basename.endswith('~'):
            return 'skip'
        if self.skip_symlink_files and os.path.islink(filename):
            return 'link'
        
        filename_nc = os.path.normcase(filename)
        ext = os.path.splitext(filename_nc)[1]
        if ext in self.skip_exts_simple or ext.startswith('.~'):
            return 'skip'
        for ext in self.skip_exts_endswith:
            if filename_nc.endswith(ext):
                return 'skip'
        try:
            if self.is_binary(filename):
                if self.is_gzipped_text(filename):
                    return 'gzip'
                else:
                    return 'binary'
            else:
                return 'text'
        except (OSError, IOError):
            return 'unreadable'

    def walk(self, startpath):
        """ Walk the tree from a given start path yielding all of the files (not
        directories) and their kinds underneath it depth first.

        Paths which are recognized as 'skip', 'link', or 'unreadable' will
        simply be passed over without comment.

        Parameters
        ----------
        startpath : str

        Yields
        ------
        filename : str
        kind : str
        """
        kind = self.recognize(startpath)
        if kind in ('binary', 'text', 'gzip'):
            yield startpath, kind
            # Not a directory, so there is no need to recurse.
            return
        elif kind == 'directory':
            try:
                basenames = os.listdir(startpath)
            except OSError:
                return
            for basename in sorted(basenames):
                path = os.path.join(startpath, basename)
                for fn, k in self.walk(path):
                    yield fn, k


def get_grin_arg_parser(parser=None):
    """ Create the command-line parser.
    """
    if parser is None:
        parser = argparse.ArgumentParser(
            description="Search text files for a given regex pattern.",
            epilog="Bug reports to <enthought-dev@mail.enthought.com>.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

    parser.add_argument('-v', '--version', action='version', version='grin %s' % __version__,
        help="show program's version number and exit")
    parser.add_argument('-i', '--ignore-case', action='append_const',
        dest='re_flags', const=re.I, default=[], help="ignore case in the regex")
    parser.add_argument('-A', '--after-context', default=0, type=int,
        help="the number of lines of context to show after the match [default=%(default)r]")
    parser.add_argument('-B', '--before-context', default=0, type=int,
        help="the number of lines of context to show before the match [default=%(default)r]")
    parser.add_argument('-C', '--context', type=int,
        help="the number of lines of context to show on either side of the match")
    parser.add_argument('-I', '--include', default='*',
        help="only search in files matching this glob [default=%(default)r]")
    parser.add_argument('-n', '--line-number', action='store_true',
        dest='show_line_numbers', default=True,
        help="show the line numbers [default]")
    parser.add_argument('-N', '--no-line-number', action='store_false',
        dest='show_line_numbers', help="do not show the line numbers")
    parser.add_argument('-H', '--with-filename', action='store_true',
        dest='show_filename', default=True, 
        help="show the filenames of files that match [default]")
    parser.add_argument('--without-filename', action='store_false',
        dest='show_filename', 
        help="do not show the filenames of files that match")
    parser.add_argument('--emacs', action='store_true',
        dest='show_emacs',
        help="print the filename with every match for easier parsing by e.g. Emacs")
    parser.add_argument('-l', '--files-with-matches', action='store_false',
        dest='show_match',
        help="show only the filenames and not the texts of the matches")
    parser.add_argument('-L', '--files-without-matches', action='store_true',
        dest='show_match', default=False,
        help="show the matches with the filenames")
    parser.add_argument('--no-color', action='store_true', default=sys.platform == 'win32',
        help="do not use colorized output [default if piping the output]")
    parser.add_argument('--use-color', action='store_false', dest='no_color',
        help="use colorized output [default if outputting to a terminal]")
    parser.add_argument('--force-color', action='store_true',
        help="always use colorized output even when piping to something that "
            "may not be able to handle it")
    parser.add_argument('-s', '--no-skip-hidden-files',
        dest='skip_hidden_files', action='store_false',
        help="do not skip .hidden files")
    parser.add_argument('--skip-hidden-files',
        dest='skip_hidden_files', action='store_true', default=True,
        help="do skip .hidden files [default]")
    parser.add_argument('-b', '--no-skip-backup-files',
        dest='skip_backup_files', action='store_false',
        help="do not skip backup~ files [deprecated; edit --skip-exts]")
    parser.add_argument('--skip-backup-files',
        dest='skip_backup_files', action='store_true', default=True,
        help="do skip backup~ files [default] [deprecated; edit --skip-exts]")
    parser.add_argument('-S', '--no-skip-hidden-dirs', dest='skip_hidden_dirs',
        action='store_false',
        help="do not skip .hidden directories")
    parser.add_argument('--skip-hidden-dirs', dest='skip_hidden_dirs',
        default=True, action='store_true',
        help="do skip .hidden directories [default]")
    parser.add_argument('-d', '--skip-dirs',
        default='CVS,RCS,.svn,.hg,.bzr,build,dist',
        help="comma-separated list of directory names to skip [default=%(default)r]")
    parser.add_argument('-D', '--no-skip-dirs', dest='skip_dirs',
        action='store_const', const='',
        help="do not skip any directories")
    parser.add_argument('-e', '--skip-exts',
        default='.pyc,.pyo,.so,.o,.a,.tgz,.tar.gz,.rar,.zip,~,#,.bak,.png,.jpg,.gif,.bmp,.tif,.tiff,.pyd,.dll,.exe,.obj,.lib',
        help="comma-separated list of file extensions to skip [default=%(default)r]")
    parser.add_argument('-E', '--no-skip-exts', dest='skip_exts',
        action='store_const', const='',
        help="do not skip any file extensions")
    parser.add_argument('--no-follow', action='store_false', dest='follow_symlinks',
        default=False,
        help="do not follow symlinks to directories and files [default]")
    parser.add_argument('--follow', action='store_true', dest='follow_symlinks',
        help="follow symlinks to directories and files")
    parser.add_argument('-f', '--files-from-file', metavar="FILE",
        help="read files to search from a file, one per line; - for stdin")
    parser.add_argument('-0', '--null-separated', action='store_true',
        help="filenames specified in --files-from-file are separated by NULs")
    parser.add_argument('--sys-path', action='store_true',
        help="search the directories on sys.path")

    parser.add_argument('regex', help="the regular expression to search for")
    parser.add_argument('files', nargs='*', help="the files to search")

    return parser

def get_grind_arg_parser(parser=None):
    """ Create the command-line parser for the find-like companion program.
    """
    if parser is None:
        parser = argparse.ArgumentParser(
            description="Find text and binary files using similar rules as grin.",
            epilog="Bug reports to <enthought-dev@mail.enthought.com>.",
        )

    parser.add_argument('-v', '--version', action='version', version='grin %s' % __version__,
        help="show program's version number and exit")
    parser.add_argument('-s', '--no-skip-hidden-files',
        dest='skip_hidden_files', action='store_false',
        help="do not skip .hidden files")
    parser.add_argument('--skip-hidden-files',
        dest='skip_hidden_files', action='store_true', default=True,
        help="do skip .hidden files")
    parser.add_argument('-b', '--no-skip-backup-files',
        dest='skip_backup_files', action='store_false',
        help="do not skip backup~ files [deprecated; edit --skip-exts]")
    parser.add_argument('--skip-backup-files',
        dest='skip_backup_files', action='store_true', default=True,
        help="do skip backup~ files [default] [deprecated; edit --skip-exts]")
    parser.add_argument('-S', '--no-skip-hidden-dirs', dest='skip_hidden_dirs',
        action='store_false',
        help="do not skip .hidden directories")
    parser.add_argument('--skip-hidden-dirs', dest='skip_hidden_dirs',
        default=True, action='store_true',
        help="do skip .hidden directories")
    parser.add_argument('-d', '--skip-dirs',
        default='CVS,RCS,.svn,.hg,.bzr,build,dist',
        help="comma-separated list of directory names to skip [default=%(default)r]")
    parser.add_argument('-D', '--no-skip-dirs', dest='skip_dirs',
        action='store_const', const='',
        help="do not skip any directories")
    parser.add_argument('-e', '--skip-exts',
        default='.pyc,.pyo,.so,.o,.a,.tgz,.tar.gz,.rar,.zip,~,#,.bak,.png,.jpg,.gif,.bmp,.tif,.tiff,.pyd,.dll,.exe,.obj,.lib',
        help="comma-separated list of file extensions to skip [default=%(default)r]")
    parser.add_argument('-E', '--no-skip-exts', dest='skip_exts',
        action='store_const', const='',
        help="do not skip any file extensions")
    parser.add_argument('--no-follow', action='store_false', dest='follow_symlinks',
        default=False,
        help="do not follow symlinks to directories and files [default]")
    parser.add_argument('--follow', action='store_true', dest='follow_symlinks',
        help="follow symlinks to directories and files")
    parser.add_argument('-0', '--null-separated', action='store_true',
        help="print the filenames separated by NULs")
    parser.add_argument('--dirs', nargs='+', default=["."],
        help="the directories to start from")
    parser.add_argument('--sys-path', action='store_true',
        help="search the directories on sys.path")

    parser.add_argument('glob', default='*', nargs='?',
        help="the glob pattern to match; you may need to quote this to prevent "
            "the shell from trying to expand it [default=%(default)r]")

    return parser

def get_recognizer(args):
    """ Get the file recognizer object from the configured options.
    """
    fr = FileRecognizer(
        skip_hidden_files=args.skip_hidden_files,
        skip_backup_files=args.skip_backup_files,
        skip_hidden_dirs=args.skip_hidden_dirs,
        skip_dirs=set(args.skip_dirs.split(',')),
        skip_exts=set(args.skip_exts.split(',')),
        skip_symlink_files=not args.follow_symlinks,
        skip_symlink_dirs=not args.follow_symlinks,
    )
    return fr

def get_filenames(args):
    """ Generate the filenames to grep.

    Parameters
    ----------
    args : Namespace
        The commandline arguments object.

    Yields
    ------
    filename : str
    kind : either 'text' or 'gzip'
        What kind of file it is.

    Raises
    ------
    IOError if a requested file cannot be found.
    """
    files = []
    # If the user has given us a file with filenames, consume them first.
    if args.files_from_file is not None:
        if args.files_from_file == '-':
            files_file = sys.stdin
            should_close = False
        elif os.path.exists(args.files_from_file):
            files_file = open(args.files_from_file)
            should_close = True
        else:
            raise IOError(2, 'No such file: %r' % args.files_from_file)

        try:
            # Remove ''
            # XXX: how can I detect bad filenames? One user accidentally ran
            # grin -f against a binary file and got an unhelpful error message
            # later.
            if args.null_separated:
                files.extend([x.strip() for x in files_file.read().split('\0')])
            else:
                files.extend([x.strip() for x in files_file])
        finally:
            if should_close:
                files_file.close()

    # Now add the filenames provided on the command line itself.
    files.extend(args.files)
    if args.sys_path:
        files.extend(sys.path)
    # Make sure we don't have any empty strings lying around.
    # Also skip certain special null files which may be added by programs like
    # Emacs.
    if sys.platform == 'win32':
        upper_bad = set(['NUL:', 'NUL'])
        raw_bad = set([''])
    else:
        upper_bad = set()
        raw_bad = set(['', '/dev/null'])
    files = [fn for fn in files if fn not in raw_bad and fn.upper() not in upper_bad]
    if len(files) == 0:
        # Add the current directory at least.
        files = ['.']

    # Go over our list of filenames and see if we can recognize each as
    # something we want to grep.
    fr = get_recognizer(args)
    for fn in files:
        # Special case text stdin.
        if fn == '-':
            yield fn, 'text'
            continue
        kind = fr.recognize(fn)
        if kind in ('text', 'gzip') and fnmatch.fnmatch(os.path.basename(fn), args.include):
            yield fn, kind
        elif kind == 'directory':
            for filename, k in fr.walk(fn):
                if k in ('text', 'gzip') and fnmatch.fnmatch(os.path.basename(filename), args.include):
                    yield filename, k
        # XXX: warn about other files?
        # XXX: handle binary?

def get_regex(args):
    """ Get the compiled regex object to search with.
    """
    # Combine all of the flags.
    flags = 0
    for flag in args.re_flags:
        flags |= flag
    return re.compile(args.regex, flags)


def grin_main(argv=None):
    try:
#        import pdb
#        pdb.set_trace()
        if argv is None:
            # Look at the GRIN_ARGS environment variable for more arguments.
            env_args = shlex.split(os.getenv('GRIN_ARGS', ''))
            argv = [sys.argv[0]] + env_args + sys.argv[1:]
        parser = get_grin_arg_parser()
        args = parser.parse_args(argv[1:])
        if args.context is not None:
            args.before_context = args.context
            args.after_context = args.context
        args.use_color = args.force_color or (not args.no_color and
            sys.stdout.isatty() and
            (os.environ.get('TERM') != 'dumb'))

        regex = get_regex(args)
        g = GrepText(regex, args)
        openers = dict(text=open, gzip=gzip.open)
        for filename, kind in get_filenames(args):
            report = g.grep_a_file(filename, opener=openers[kind])
            sys.stdout.write(report)
    except KeyboardInterrupt:
        raise SystemExit(0)
    except IOError as e:
        if 'Broken pipe' in str(e):
            # The user is probably piping to a pager like less(1) and has exited
            # it. Just exit.
            raise SystemExit(0)
        raise

def print_line(filename):
    print filename

def print_null(filename):
    # Note that the final filename will have a trailing NUL, just like 
    # "find -print0" does.
    sys.stdout.write(filename)
    sys.stdout.write('\0')

def grind_main(argv=None):
    try:
        if argv is None:
            # Look at the GRIND_ARGS environment variable for more arguments.
            env_args = shlex.split(os.getenv('GRIND_ARGS', ''))
            argv = [sys.argv[0]] + env_args + sys.argv[1:]
        parser = get_grind_arg_parser()
        args = parser.parse_args(argv[1:])

        # Define the output function.
        if args.null_separated:
            output = print_null
        else:
            output = print_line

        if args.sys_path:
            args.dirs.extend(sys.path)

        fr = get_recognizer(args)
        for dir in args.dirs:
            for filename, k in fr.walk(dir):
                if fnmatch.fnmatch(os.path.basename(filename), args.glob):
                    output(filename)
    except KeyboardInterrupt:
        raise SystemExit(0)
    except IOError as e:
        if 'Broken pipe' in str(e):
            # The user is probably piping to a pager like less(1) and has exited
            # it. Just exit.
            raise SystemExit(0)
        raise

if __name__ == '__main__':
    grin_main()
