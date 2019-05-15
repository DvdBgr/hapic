# -*- coding: utf-8 -*-
from datetime import datetime
import flask
import marshmallow
import hapic
import os.path
from hapic.data import HapicData
from hapic.ext.flask import FlaskContext
from hapic.processor.marshmallow import MarshmallowProcessor
from hapic.error.marshmallow import MarshmallowDefaultErrorBuilder
import json
from hapic.data import HapicFile

hapic = hapic.Hapic(processor_class=MarshmallowProcessor)
app = flask.Flask(__name__)

"""class File(object):
    def __init__(self, name, mediatype, size, last_modified, payload):
        self.name = name
        self.mediatype = mediatype
        self.size = size        
        self.last_modified = last_modified
        self.payload = payload
"""
"""
class HapicFile2(object):
    def __init__(
        self,
        file: typing.Any = None,
        file_path: typing.Optional[str] = None,
        mediatype: typing.Any = None,
        name: str = None,
        size: int = None,
        last_modified: datetime = None,
        as_attachment: bool = False,
    ):
        self.file = file
        self.file_path = file_path
        self.name = name
        self.mediatype = mediatype
        self.as_attachment = as_attachment
        self.size = size
        self.last_modified = last_modified

    def get_content_disposition_header_value(self) -> str:
        disposition = "inline"
        if self.as_attachment:
            disposition = "attachment"
        if self.name:
            # INFO - G.M - 2018-10-26 - deal correctly with unicode filename
            # see rfc6266 for more info.
            ascii_filename = self.name.encode("ascii", "replace").decode()
            # INFO - G.M - 2018-10-30 - Format correctly unicode.
            # encoding is needed for correct unicode character support,
            # Percent-encoding is best pratices, see also rfc5987.
            urlencoded_unicode_filename = urllib.parse.quote(self.name)

            disposition = "{}; filename=\"{}\"; filename*=UTF-8''{};".format(
                disposition, ascii_filename, urlencoded_unicode_filename
            )
        return disposition
"""


class PostFileBodySchema(marshmallow.Schema):
    owner = marshmallow.fields.String(required=True)
    """file_path = marshmallow.fields.String(required=False)
    mediatype = marshmallow.fields.String(required=False)  # https://github.com/algoo/hapic/blob/c60ac86a9741519bc557905435238797d54963d7/hapic/data.py#L17
    size = marshmallow.fields.Integer(required=False) # needs to convert to human readable format
    as_attachment = marshmallow.fields.Boolean(required=False)
    last_modified = marshmallow.fields.DateTime(required=False)"""


class OutputBodySchema(marshmallow.Schema):
    file_id = marshmallow.fields.Integer(required=True)


class InputFileBodySchema(marshmallow.Schema):  # schema of the API response
    file = marshmallow.fields.Raw(required=True)  # changer nom pour autre chose que payload

class OutputFileSchema(marshmallow.Schema):
    file = marshmallow.fields.Raw(required=True)

@app.route('/files/<file_id>', methods=['GET'])  # séparer 2 vues
@hapic.with_api_doc()
@hapic.input_path(OutputBodySchema())  # FileSchema
@hapic.output_file(OutputFileSchema)
def retrieve_test(file_id, hapic_data=None):  # hapic_data=None
    file_path = f"/private/tmp/{file_id}"
    if not os.path.exists(file_path):  # new file write file on disk
        abort(400)
    else:
        return HapicFile(
            file_path = file_path,
            mimetype = 'application/octets-stream',
            as_attachment = False
        )

@app.route('/files/<file_id>', methods=['PUT'])
@hapic.with_api_doc()
@hapic.input_path(OutputBodySchema())  # FileSchema
# @hapic.output_file(['image/jpeg'])
def retrieve_t(file_id, hapic_data: HapicData):
    file_path = f"/private/tmp/{file_id}"
    if not hapic_data.file or not os.path.exists(file_path):  # write new file on disk
        abort(400)
    else:
        return HapicFile(
            file_path = file_path,
            mimetype = mimetype,
            as_attachment = as_attachment
         )

@app.route('/files', methods=['POST'])  # flask route. must always be before hapic decorators
@hapic.with_api_doc()  # the first hapic decorator. Register the method for auto-documentation
@hapic.input_files(InputFileBodySchema())
@hapic.input_forms(PostFileBodySchema())  # validate the URI structure
@hapic.output_body(OutputBodySchema())  # define output structure
def create_file(hapic_data: HapicData):
    file_id = 42  # os.path.basename(local_path)
    file_path = f'/private/tmp/{file_id}'
    #  mimetype = image
    with open(file_path, 'wb+') as file:
        file.write(hapic_data.files["file"].read())
    return {
        "file_id": file_id
    }
    """HapicFile(
                file_path=file_path,
                mimetype='image/jpeg',
                as_attachment=False)"""


"""@app.route('/files', methods=['GET', 'PUT'])
@hapic.with_api_doc()
@hapic.output_file(['image/jpeg'])
def postFile(hapic_data=None): #HapicFile/Data
    return HapicFile(
             file_path='/Users/admin/Downloads/ara.jpeg',
             mimetype='image/jpeg',
             as_attachment=False,
)
"""
"""
    i = 0
    while os.path.exists(file_path):
        try:
            os.path.exists(file_path + "(" + str(i)) + ")")
            i += 1
        except Exception as exc:
            continue
        file = file_path + "(" + str(i)) + ")")

        with open(file_path, 'w+') as file: # check if path already exist
            file.write(hapic_data.files["file"].read())
    except:
        while



    return (HapicFile(
             file_path='/Users/admin/Downloads/ara.jpeg',
             mimetype='image/jpeg',
             as_attachment=False
    ),
    HapicFile(
            file_path='/Users/admin/Downloads/ara2.jpeg',
            mimetype='image/jpeg',
            as_attachment=False
    ))

"""
hapic.set_context(FlaskContext(app, default_error_builder=MarshmallowDefaultErrorBuilder()))
print(json.dumps(hapic.generate_doc(title='API Doc', description='doc desc.')))  # Generate the documentation
app.run('127.0.0.1', 8080, debug=True)
