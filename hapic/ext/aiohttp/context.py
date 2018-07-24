# coding: utf-8
import asyncio
import typing
from http import HTTPStatus
from json import JSONDecodeError

from aiohttp.web_request import Request
from aiohttp.web_response import Response
from multidict import MultiDict

from hapic.context import BaseContext
from hapic.context import RouteRepresentation
from hapic.decorator import DecoratedController
from hapic.exception import WorkflowException
from hapic.processor import ProcessValidationError
from hapic.processor import RequestParameters
from aiohttp import web


class AiohttpRequestParameters(object):
    def __init__(
        self,
        request: Request,
    ) -> None:
        self._request = request
        self._parsed_body = None

    @property
    async def body_parameters(self) -> dict:
        if self._parsed_body is None:
            content_type = self.header_parameters.get('Content-Type')
            is_json = content_type == 'application/json'

            if is_json:
                self._parsed_body = await self._request.json()
            else:
                self._parsed_body = await self._request.post()

        return self._parsed_body

    @property
    def path_parameters(self):
        return dict(self._request.match_info)

    @property
    def query_parameters(self):
        return MultiDict(self._request.query.items())

    @property
    def form_parameters(self):
        # TODO BS 2018-07-24: There is misunderstanding around body/form/json
        return self.body_parameters

    @property
    def header_parameters(self):
        return dict(self._request.headers.items())

    @property
    def files_parameters(self):
        # TODO BS 2018-07-24: To do
        raise NotImplementedError('todo')


class AiohttpContext(BaseContext):
    def __init__(
        self,
        app: web.Application,
    ) -> None:
        self._app = app

    @property
    def app(self) -> web.Application:
        return self._app

    def get_request_parameters(
        self,
        *args,
        **kwargs
    ) -> RequestParameters:
        try:
            request = args[0]
        except IndexError:
            raise WorkflowException(
                'Unable to get aiohttp request object',
            )
        request = typing.cast(Request, request)
        return AiohttpRequestParameters(request)

    def get_response(
        self,
        response: str,
        http_code: int,
        mimetype: str = 'application/json',
    ) -> typing.Any:
        return Response(
            body=response,
            status=http_code,
            content_type=mimetype,
        )

    def get_validation_error_response(
        self,
        error: ProcessValidationError,
        http_code: HTTPStatus = HTTPStatus.BAD_REQUEST,
    ) -> typing.Any:
        # TODO BS 2018-07-24: To do
        raise NotImplementedError('todo')

    def find_route(
        self,
        decorated_controller: DecoratedController,
    ) -> RouteRepresentation:
        pass

    def get_swagger_path(
        self,
        contextualised_rule: str,
    ) -> str:
        pass

    def by_pass_output_wrapping(
        self,
        response: typing.Any,
    ) -> bool:
        pass

    def add_view(
        self,
        route: str,
        http_method: str,
        view_func: typing.Callable[..., typing.Any],
    ) -> None:
        pass

    def serve_directory(
        self,
        route_prefix: str,
        directory_path: str,
    ) -> None:
        pass

    def is_debug(
        self,
    ) -> bool:
        pass

    def handle_exception(
        self,
        exception_class: typing.Type[Exception],
        http_code: int,
    ) -> None:
        pass

    def handle_exceptions(
        self,
        exception_classes: typing.List[typing.Type[Exception]],
        http_code: int,
    ) -> None:
        pass
