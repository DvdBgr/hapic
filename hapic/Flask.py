# -*- coding: utf-8 -*-
import hapic
import flask
import os.path
import json
import marshmallow
import cgitb
import hashlib

from flask import request
from werkzeug import LimitedStream
from tempfile import TemporaryFile

from hapic.data import HapicData, File
from hapic.ext.flask import FlaskContext
from hapic.processor.marshmallow import MarshmallowProcessor
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder

# import werkzeug.FileStorage

# DOC: https://gist.github.com/mitsuhiko/5721547, https://www.python.org/dev/peps/pep-3333/#id41 https://rhodesmill.org/brandon/2013/chunked-wsgi/, http://mitsuhiko.pocoo.org/wzdoc/index.html, http://lucumr.pocoo.org/2007/5/21/getting-started-with-wsgi/,  https://www.xml.com/pub/a/2006/09/27/introducing-wsgi-pythons-secret-web-weapon.html

"""for get_input_stream() > LimitedStream() problems with non specified Content-length, maybe wsgiref avoid this:
"When read() returns an empty bytestring, iteration is ended and is not resumable."""

#  TODO: retrieve doc that mention other method to yield instead of iterating (open tab)
# TODO: use `with cgi.FieldStorage` instead of read with open(..)`

"""From https://werkzeug.palletsprojects.com/en/0.14.x/wsgi/#werkzeug.wsgi.LimitedStream:
calls to readline() and readlines() are not WSGI compliant because it passes a size argument to the readline methods.
Unfortunately the WSGI PEP is not safely implementable without a size argument to readline() because there is no EOF marker in the stream.
We strongly suggest using read() only or using the make_line_iter() which safely iterates line-based over a WSGI input stream.
https://docs.python.org/3/library/wsgiref.html
https://werkzeug.palletsprojects.com/en/0.15.x/wsgi/#werkzeug.wsgi.get_input_stream
https://werkzeug.palletsprojects.com/en/0.14.x/wsgi/?highlight=direct_passthrough#werkzeug.wsgi.LimitedStream
Solution : `make_chunk_iter(), range_wrapper()`?
"""

CLIENT_FOLDER = '~/Downloads/'
SERVE_FOLDER = '/private/tmp/'
# ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = flask.Flask(__name__)
app.config['UPLOAD_FOLDER'] = SERVE_FOLDER
hapic = hapic.Hapic(processor_class=MarshmallowProcessor)

chunk_size = 8192
cgitb.enable()


# f = io.StringIO("test")

class PostFileBodySchema(marshmallow.Schema):
    owner = marshmallow.fields.String(required=True)


class OutputBodySchema(marshmallow.Schema):
    file_id = marshmallow.fields.Integer(required=False)


class InputFileBodySchema(marshmallow.Schema):
    file = marshmallow.fields.Raw(required=True)


class OutputFileSchema(marshmallow.Schema):
    file = marshmallow.fields.Raw(required=True)


# use cgi.FieldStorage
"""def save_to_disk(file_path, file):
    with open(file_path, "bw") as f:
        for chunk in iter_file(file):
            f.write(chunk)
        # wrapper.close() inutile avec with"""


def validate_checksum_chunk(chunk):
    if hashlib.md5(chunk):
        pass



@app.route('/files', methods=['POST'])
@hapic.with_api_doc()  # the first hapic decorator. Register the method for auto-documentation
@hapic.input_files(InputFileBodySchema())
# @hapic.input_forms(PostFileBodySchema())  # validate the URI structure
@hapic.output_body(OutputBodySchema())  # define output structure
def post_file(hapic_data: HapicData):
    # final_path = os.path.join(SERVE_FOLDER, "42")
    # with open(final_path, "wb+") as file:
    #    save_to_disk(final_path, hapic_data.files["file"].stream)
    # .save()

    file_id = 45  # TODO: generate file_id based on HapicFile filename
    if 'file' not in hapic_data.files:  # check if the request contains a file
        return "No file provided"
    if request.headers['Content-Type'] == 'multipart/form':
        i = 0
        for file in hapic_data.files:  # use yield and `requests` in case of multipart form
            i += 1
            # default buffer_size  of 16KB, otherwise file.write(value.stream.read())
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(file_id + i)))
    else:
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(file_id)))
    # flask.environ ou flask infère environ ?
    stream = request.files['file']
    # read() take positional arguments, use read(seek(chunk_size, 1)) instead of iterating over with file_wrapper(), what about mmap (but os dependent ?
    # errors = environ['wsgi.errors'] = hapic.error
    content_length = int(flask.request.headers.get('Content-Length'))

    # test if content-lenght in ~~header~~ environ, otherwise use LimitedStream
    if content_length is None:
        return LimitedStream(File())
    if 'Content-Range' in request.headers:
        # extract starting byte from Content-Range header string
        range_str = request.headers['Content-Range']
        start_bytes = int(range_str.split(' ')[1].split('-')[0])
        # append chunk to the file on disk, or create new
        with open(filename, 'a') as f:
            f.seek(start_bytes)
            f.write(value.stream.read())
    # use wrapper.seek(chunk_size, 1) ?
    else:
        with open(file_path, "bw") as f:
            f.write(iter(stream.read(block_size=chunk_size), ''))  # fallback

        # file.save(os.path.join(SERVE_FOLDER, str(file_id)))
        # input_term
        # yield HapicFile()

    # Large file


    return (
        str(file_id)
        # "owner": owner  dic
    )


def iter_file(file, chunk_size=1024):
    while True:
        data = file.read(chunk_size)
        if not data:
            break
        yield data


@app.route('/files/<file_id>', methods=['GET'])
@hapic.with_api_doc()
@hapic.input_path(OutputBodySchema())  # define output structure
@hapic.output_file([])  # not sure what output_file is for
def retrieve_file(file_id, hapic_data=None):

    file_path = os.path.join(SERVE_FOLDER, str(file_id))

    if not os.path.exists(file_path):
        return "No existing file with this ID<<"

    stream = open(file_path, 'r+')

    #
    # with open (file_path, 'rb') as file:
    #    return Response(iter_file(file))
    # with open(file_path, 'rb') as file:
    #    return flask.send_file(file, mimetype="document/text")
    # return flask.send_file(file_path)
    #
    # if request.headers['Content-Type'] == 'text/plain':
    # return "Text Message: " + request.data

    # Forge HTTP 206 (range-content) response
    content_Range = chunk_size
    headers = Headers()
    headers.add(str(content_length), str(chunk_size))
    return File(stream=stream, mimetype=stream.mimetype),
        headers=headers)  # add mimetype in FileWrapper
    # yield HapicFile(fo=)?
    # mimetype="application/octets-stream")


# **Notes**
# https://werkzeug.palletsprojects.com/en/0.14.x/wrappers/?highlight=500kb#werkzeug.wrappers.BaseRequest._get_file_stream _get_file_stream() by default write file to disk if its exceed 500kb
# don't use with open()..f.read()
# HTTP range request? https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests
# In old werkzeug doc: If you want to pass out a file wrapper inside a response
#     object you have to set :attr:`BaseResponse.direct_passthrough=True`
# file = wsgi.file_wrapper.read/close()
#      for chunk in wrapper:
#            return HapicFile(...)
# get_stdin() = wsgi.input/error std_err
# werkzeug encapsulate environ in request object and start_response in Response
hapic.set_context(FlaskContext(app, default_error_builder=MarshmallowDefaultErrorBuilder()))
print(json.dumps(hapic.generate_doc(title='API Doc', description='doc desc.')))  # Generate the documentation
app.run('127.0.0.1', 8080, debug=True)
