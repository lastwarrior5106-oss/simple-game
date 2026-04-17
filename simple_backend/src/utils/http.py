from __future__ import annotations

import json
from contextvars import ContextVar
from typing import Any, AsyncContextManager, Callable, Dict, Type, Union

from aiohttp import ClientResponse, ClientSession, FormData, hdrs
from loguru import logger
from pydantic import BaseModel

from .common import json_serializer
from .error import Error

request_id_trace_context = ContextVar("request_id_trace_context")


class HttpClient:
    session: ClientSession = None
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    @staticmethod
    async def start(
        *args,
        headers=None,
        json_serialize=json_serializer,
        raise_for_status=True,
        **kwargs,
    ):
        if headers is None:
            headers = HttpClient.headers

        HttpClient.session = ClientSession(
            headers=headers,
            json_serialize=json_serialize,
            raise_for_status=raise_for_status,
            **kwargs,
        )

    @staticmethod
    async def stop():
        if HttpClient.session is not None:
            await HttpClient.session.close()
            HttpClient.session = None

    @staticmethod
    async def restart(*args, **kwargs):
        await HttpClient.stop()
        await HttpClient.start(*args, **kwargs)

    def __call__(self) -> ClientSession:
        assert HttpClient.session is not None, "Session not found. Please start or restart session."
        return HttpClient.session


client = HttpClient()


class Request:
    validation_function = None
    validation_model = None
    error_class = None

    def __init__(
        self,
        method: hdrs.METH_ALL,
        url: str,
        *,
        validation_function: Callable = None,
        validation_model: Union[BaseModel, Type] = None,
        validate_key: str = None,
        error_class: Type[Error] = Error,
        is_multipart: bool = False,
        **kwargs,
    ):
        self.request = self._create_request(method, url, is_multipart, **kwargs)
        self.validation_function = validation_function
        self.validation_model = validation_model
        self.validate_key = validate_key
        self.is_multipart = is_multipart
        self.error_class: Type[Error] = error_class
        self._response: Union[Dict, None] = None
        self._validated_data = None
        self._exception: Union[Error, None] = None

    def _create_request(
        self,
        method: hdrs.METH_ALL,
        url: str,
        is_multipart: bool = False,
        raise_for_status: bool = False,
        **kwargs,
    ) -> AsyncContextManager[ClientResponse]:
        self._request_info = {
            "method": method,
            "url": url,
            "data": kwargs.get("data"),
            "json": kwargs.get("json"),
            "files": kwargs.get("files"),
        }

        headers = kwargs.pop("headers", {})
        data = kwargs.pop("data", None)
        files = kwargs.pop("files", None)

        request_id = request_id_trace_context.get(None)
        if request_id:
            headers["requestid"] = request_id

        if files or is_multipart:
            form_data = FormData()

            for key, value in (data or {}).items():
                if isinstance(value, (dict, list)):
                    form_data.add_field(key, json.dumps(value), content_type="application/json")
                else:
                    form_data.add_field(key, str(value))

            if files:
                for key, file_info in files.items():
                    if isinstance(file_info, dict):
                        filename = file_info.get("filename", "file")
                        content = file_info.get("content", b"")
                        content_type = file_info.get("content_type", "application/octet-stream")
                        form_data.add_field(key, content, filename=filename, content_type=content_type)
                    elif isinstance(file_info, tuple) and len(file_info) >= 2:
                        filename = file_info[0]
                        content = file_info[1]
                        content_type = file_info[2] if len(file_info) > 2 else "application/octet-stream"
                        form_data.add_field(key, content, filename=filename, content_type=content_type)

            form_data_headers = form_data._gen_form_data().headers
            for key, value in form_data_headers.items():
                headers[key] = value

            data = form_data

        return client().request(
            method.upper(),
            url,
            raise_for_status=raise_for_status,
            headers=headers,
            data=data,
            **kwargs,
        )

    async def __execute(self) -> Request:
        self._response = None
        self._validated_data = None
        self._exception = None
        status = None

        try:
            async with self.request as client_response:
                status = client_response.status
                await self._parse_response(client_response)

                if 400 <= status:
                    client_response.raise_for_status()

                self._validate_response()

        except Exception:
            self._exception = self.error_class(
                detail={
                    "request": self._request_info,
                    "response": {
                        "status": status,
                        "data": self._response,
                    },
                }
            )

        return self

    async def _parse_response(self, client_response: ClientResponse) -> None:
        try:
            self._response = await client_response.json()
        except Exception:
            self._response = await client_response.text(errors="ignore")
            raise

    def _validate_response(self) -> None:
        response = self._response

        if self.validate_key:
            response = response[self.validate_key]

        if self.validation_function:
            self._validated_data = self.validation_function(response)
        elif self.validation_model:
            self._validated_data = self.validation_model.model_validate(response)
        else:
            self._validated_data = response

    def is_valid(self, raise_exception=False) -> bool:
        if self.has_exception():
            if raise_exception:
                self.raise_exception()
            return False
        return True

    def get_response(self) -> Union[Dict, None]:
        return self._response

    def get_validated_data(self) -> Any:
        return self._validated_data

    def get_exception(self) -> Union[Error, None]:
        return self._exception

    def has_exception(self) -> bool:
        return self._exception is not None

    def get_original_exception(self) -> Union[Exception, None]:
        return self._exception and self._exception.caught_exception

    def log_exception(self):
        logger.opt(exception=self._exception).error(self._exception.message)

    def raise_exception(self, detail: Dict = None, log: bool = True):
        if self._exception:
            if detail:
                self._exception.detail.update(detail)
            if log:
                self.log_exception()
            raise self.get_exception()

    def __await__(self):
        return self.__execute().__await__()