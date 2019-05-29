# -*- coding: utf-8 -*-
import typing
import urllib.parse

from datetime import datetime
from shutil import copyfileobj


class HapicData(object):
    def __init__(self):
        self.body = {}
        self.path = {}
        self.query = {}
        self.headers = {}
        self.forms = {}
        self.files = {}


class HapicFile(object):
    def __init__(
        self,
        file_path: typing.Optional[str] = None,
        file_object: typing.Any = None,
        mimetype: typing.Any = None,
        filename: str = None,
        content_length: int = None,
        last_modified: datetime = None,
        as_attachment: bool = False,
    ):
        self.file_path = file_path
        self.file_object = file_object
        self.filename = filename
        self.mimetype = mimetype
        self.as_attachment = as_attachment
        self.content_length = content_length
        self.last_modified = last_modified

    def get_content_disposition_header_value(self) -> str:
        disposition = "inline"
        if self.as_attachment:
            disposition = "attachment"
        if self.filename:
            # INFO - G.M - 2018-10-26 - deal correctly with unicode filename
            # see rfc6266 for more info.
            ascii_filename = self.filename.encode("ascii", "replace").decode()
            # INFO - G.M - 2018-10-30 - Format correctly unicode.
            # encoding is needed for correct unicode character support,
            # Percent-encoding is best pratices, see also rfc5987.
            urlencoded_unicode_filename = urllib.parse.quote(self.filename)

            disposition = "{}; filename=\"{}\"; filename*=UTF-8''{};".format(
                disposition, ascii_filename, urlencoded_unicode_filename
            )
        return disposition


class File(HapicFile):

    buffer_size = 16 * 1024  # bytes held in memory during copy (default: 16KB) / iterate size
    chunk_size = 4 * 1024  # write chunk size

    def __init__(
        self,
        stream = None,
        file_path = None,
        filename = None,
        name = None,
        content_length = None,
        content_type = None,
        mimetype = None,
    ):
        HapicFile.__init__(self)
        self.stream = stream  # input stream for the uploaded file  # self.stream = self.file_path
        self.filename = filename  # name on client side
        self.file_path = file_path
        self.name = name  # name of form field
        self.content_length = content_length
        self.content_type = content_type
        self.mimetype = mimetype
#        self._hash = hashlib.sha1()
        # self.environ = environ  # wsgi env

    def read(self, chunk_size=None):
        chunk_size = chunk_size or self.chunk_size
        return self.stream.read(chunk_size)
#        self._hash.update(data)


    def close(self):            # file-like object expose close() and read()
        if hasattr(self.file, 'close'):
            self.file.close()

    def __iter__(self):
        return self

    def next(self):
        data = self.stream.read(self.buffer_size)
        if data:
            return data
        raise StopIteration()

    """:func:`copyfileobj`: https://github.com/python/cpython/blob/3.6/Lib/shutil.py#L76 https://docs.python.org/3/library/shutil.html#shutil.copyfileobj:
    "[...] a negative length value means to copy the data without looping over the source data in chunks; by default the data
    is read in chunks to avoid uncontrolled memory consumption. If the current file position of the fsrc object
    is not 0, only the contents from the current file position to the end of the file will be copied."
    Similiar to save_by_chunk"""


def save_(stream, file_path):   # rely on state
    copyfileobj(fsrc=stream, fdst=file_path, length=buffer_size)

def save_by_chunk(stream, file_path):
    with open(file_path, "bw") as f:
        while True:
            chunk = stream.read(chunk_size)
            if len(chunk) == 0:  # not chunk doesn't check for EOF
                return
            f.write(chunk)



