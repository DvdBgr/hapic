from datetime import datetime
import flask
import marshmallow
import hapic
from hapic.processor.marshmallow import MarshmallowProcessor
from hapic.ext.flask import FlaskContext
import json

hapic = hapic.Hapic(processor_class=MarshmallowProcessor)
app = flask.Flask(__name__)


class UriPathSchema(marshmallow.Schema):  # schema describing the URI and allowed values
    name = marshmallow.fields.String(required=True)
    age = marshmallow.fields.Integer(required=False)


class HelloResponseSchema(marshmallow.Schema): # schema of the API response
    name = marshmallow.fields.String(required=True)
    now = marshmallow.fields.DateTime(required=False)
    greetings = marshmallow.fields.String(required=False)


@app.route('/hello/<name>')  # flask route. must always be before hapic decorators
@hapic.with_api_doc()  # the first hapic decorator. Register the method for auto-documentation
@hapic.input_path(UriPathSchema())  # validate the URI structure
@hapic.output_body(HelloResponseSchema())  # define output structure
def hello(name='<No name>', hapic_data=None):
    return {
        'name': name,
        'now': datetime.now(),
        'dummy': { 'some': 'dummy' }  # will be ignored
    }

class UriPathSchemaWithAge(marshmallow.Schema):  # schema describing the URI and allowed values
    name = marshmallow.fields.String(required=True)
    age = marshmallow.fields.Integer(required=False)


@app.route('/hello/<name>/age/<age>')
@hapic.with_api_doc()
@hapic.input_path(UriPathSchemaWithAge())
@hapic.output_body(HelloResponseSchema())
def hello2(name='<No name>', age=42, hapic_data=None):
    return {
        'name': name,
        'age': age,
        'greetings': 'Hello {name}, it looks like you are {age}'.format(
            name=name,
            age=age
        ),
        'now': datetime.now(),
        'dummy': { 'some': 'dummy' }  # will be ignored
    }


hapic.set_context(FlaskContext(app))
print(json.dumps(hapic.generate_doc(title='API Doc', description='doc desc.')))  # Generate the documentation
app.run('127.0.0.1', 8080, debug=True)
