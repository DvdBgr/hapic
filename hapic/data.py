# -*- coding: utf-8 -*-
from datetime import datetime
import typing
import urllib.parse


class HapicData(object):
    def __init__(self):
        self.body = {}
        self.path = {}
        self.query = {}
        self.headers = {}
        self.forms = {}
        self.files = {}


class File(object):

    buffer_size = 1024

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
        self.stream = stream  # input stream for the uploaded file
        self.filename = filename  # name on client side
        self.file_path = file_path
        self.name = name  # name of form field
        self.content_length = content_length
        self.content_type = content_type
        self.mimetype = mimetype

    def read(self):
        data = self.stream.read(content_length)
        if data:
            return data
        else: raise IndexError

    def close(self):            # file-like object expose close() and read()
        if hasattr(self.file, 'close'):
            self.file.close()

    def __iter__(self):
        return self

    def next(self):
        data = self.file.read(self.buffer_size)
        if data:
            return data
        raise StopIteration()


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
