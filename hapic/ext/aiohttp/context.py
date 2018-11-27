# coding: utf-8
from http import HTTPStatus
import json
import re
import typing

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from multidict import MultiDict

from hapic.context import BaseContext
from hapic.context import HandledException
from hapic.context import RouteRepresentation
from hapic.decorator import DECORATION_ATTRIBUTE_NAME
from hapic.decorator import DecoratedController
from hapic.error import DefaultErrorBuilder
from hapic.error import ErrorBuilderInterface
from hapic.exception import NoRoutesException
from hapic.exception import OutputValidationException
from hapic.exception import RouteNotFound
from hapic.exception import WorkflowException
from hapic.processor.main import ProcessValidationError
from hapic.processor.main import RequestParameters

# Aiohttp regular expression to locate url parameters
AIOHTTP_RE_PATH_URL = re.compile(r'{([^:<>]+)(?::[^<>]+)?}')


class AiohttpRequestParameters(RequestParameters):
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
        default_error_builder: ErrorBuilderInterface=None,
        debug: bool = False,
    ) -> None:
        self._app = app
        self._debug = debug
        self.default_error_builder = \
            default_error_builder or DefaultErrorBuilder()  # FDV

        # Managed exceptions
        @web.middleware
        async def error_middleware(
            request: Request,
            handler: typing.Callable[..., typing.Any],
        ) -> typing.Any:
            """
            Wrapper installed by aiohttp who wrap real controller. This wrapper
            will catch any exception then test if it is an hapic managed
            exception. If yes, return an hapic response else raise again.
            :param request: aiohttp request object
            :param handler: wrapped controller
            :return: handler return. Probably aiohttp.web_response.Response but
            this cannot be sure because handler can be any wrapped function
            like other middleware wrapper.
            """
            try:
                response = await handler(request)
                return response
            except Exception as exc:
                # Parse each managed exceptions to manage it if must be
                for handled_exception in self._handled_exceptions:
                    if isinstance(exc, handled_exception.exception_class):
                        error_builder = self.get_default_error_builder()
                        error_body = error_builder.build_from_exception(
                            exc,
                            include_traceback=self.is_debug(),
                        )
                        dumped = error_builder.dump(error_body).data
                        return self.get_response(
                            json.dumps(dumped),
                            handled_exception.http_code,
                        )
                raise exc

        self._handled_exceptions = []  # type: typing.List[HandledException]
        self._error_middleware = error_middleware
        self._error_middleware_installed = False

    @property
    def app(self) -> web.Application:
        return self._app

    def get_request_parameters(
        self,
        *args,
        **kwargs
    ) -> RequestParameters:
        for arg in args:
            if isinstance(arg, Request):
                return AiohttpRequestParameters(arg)

        raise WorkflowException(
            'Unable to get aiohttp request object',
        )

    def get_response(
        self,
        response: str,
        http_code: int,
        mimetype: str = 'application/json',
    ) -> typing.Any:
        # A 204 no content response should not have content type header
        if http_code == HTTPStatus.NO_CONTENT:
            mimetype = None
            response = ''

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
        error_builder = self.get_default_error_builder()
        error_content = error_builder.build_from_validation_error(
            error,
        )

        # Check error
        dumped = error_builder.dump(error_content).data
        unmarshall = error_builder.load(dumped)
        if unmarshall.errors:
            raise OutputValidationException(
                'Validation error during dump of error response: {}'.format(
                    str(unmarshall.errors)
                )
            )

        return web.Response(
            text=json.dumps(dumped),
            headers=[
                ('Content-Type', 'application/json'),
            ],
            status=int(http_code),
        )

    def find_route(
        self,
        decorated_controller: DecoratedController,
    ) -> RouteRepresentation:
        if not len(self.app.router.routes()):
            raise NoRoutesException('There is no routes in your aiohttp app')

        reference = decorated_controller.reference

        for route in self.app.router.routes():
            route_token = getattr(
                route.handler,
                DECORATION_ATTRIBUTE_NAME,
                None,
            )

            match_with_wrapper = route.handler == reference.wrapper
            match_with_wrapped = route.handler == reference.wrapped
            match_with_token = route_token == reference.token

            # TODO BS 2018-07-27: token is set in HEAD view to, must solve this
            # case
            if not match_with_wrapper \
                    and not match_with_wrapped \
                    and match_with_token \
                    and route.method.lower() == 'head':
                continue

            if match_with_wrapper or match_with_wrapped or match_with_token:
                return RouteRepresentation(
                    rule=self.get_swagger_path(route.resource.canonical),
                    method=route.method.lower(),
                    original_route_object=route,
                )
        # TODO BS 20171010: Raise exception or print error ? see #10
        raise RouteNotFound(
            'Decorated route "{}" was not found in aiohttp routes'.format(
                decorated_controller.name,
            )
        )

    def get_swagger_path(
        self,
        contextualised_rule: str,
    ) -> str:
        return AIOHTTP_RE_PATH_URL.sub(r'{\1}', contextualised_rule)

    def by_pass_output_wrapping(
        self,
        response: typing.Any,
    ) -> bool:
        return isinstance(response, web.Response)

    def add_view(
        self,
        route: str,
        http_method: str,
        view_func: typing.Callable[..., typing.Any],
    ) -> None:
        # TODO BS 2018-07-15: to do
        raise NotImplementedError('todo')

    def serve_directory(
        self,
        route_prefix: str,
        directory_path: str,
    ) -> None:
        # TODO BS 2018-07-15: to do
        raise NotImplementedError('todo')

    def is_debug(
        self,
    ) -> bool:
        return self._debug

    def handle_exception(
        self,
        exception_class: typing.Type[Exception],
        http_code: int,
    ) -> None:
        """
        Manage an exception class (and it's children) by associating an http
        status code
        :param exception_class: exception class to manage
        :param http_code: HTTP status code associated
        """
        handled_exception = HandledException(exception_class, http_code)
        self._handled_exceptions.append(handled_exception)

        # If it is the first call to handle exception, we must enable the
        # middleware
        if not self._error_middleware_installed:
            self.app.middlewares.append(self._error_middleware)

    def handle_exceptions(
        self,
        exception_classes: typing.List[typing.Type[Exception]],
        http_code: int,
    ) -> None:
        """
        Manage exception classes (and theirs children) by associating an http
        status code
        :param exception_classes: exception class list to manage
        :param http_code: HTTP status code associated
        """
        for exception_class in exception_classes:
            self.handle_exception(exception_class, http_code)

    async def get_stream_response_object(
        self,
        func_args,
        func_kwargs,
        http_code: HTTPStatus = HTTPStatus.OK,
        headers: dict = None,
    ) -> web.StreamResponse:
        headers = headers or {
            'Content-Type': 'text/plain; charset=utf-8',
        }

        response = web.StreamResponse(
            status=http_code,
            headers=headers,
        )

        try:
            request = func_args[0]
        except IndexError:
            raise WorkflowException(
                'Unable to get aiohttp request object',
            )
        request = typing.cast(Request, request)

        await response.prepare(request)

        return response

    async def feed_stream_response(
        self,
        stream_response: web.StreamResponse,
        serialized_item: dict,
    ) -> None:
        await stream_response.write(
            # FIXME BS 2018-07-25: need \n :/
            json.dumps(serialized_item).encode('utf-8') + b'\n',
        )
