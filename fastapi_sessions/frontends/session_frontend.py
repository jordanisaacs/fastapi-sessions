from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Union

from fastapi import Request, Response


class FrontendError(Exception):
    pass


ID = TypeVar("ID")


class SessionFrontend(ABC, Generic[ID]):
    @property
    @abstractmethod
    def identifier(self) -> str:
        raise NotImplementedError()

    # All frontends must have the __call__ function (the extractor).
    # Not in the abstract class as the arguments vary.
    #
    # def __call__(self, *args) -> Union[ID, FrontendError]:
    #     """Extract, attach to request, and return the session ID from the request."""
    #     raise NotImplementedError()

    @abstractmethod
    def attach_to_response(self, response: Response, session_id: ID) -> None:
        """Attach a response with the session ID attached."""
        raise NotImplementedError()

    @abstractmethod
    def delete_from_response(self, response: Response) -> None:
        """Delete the session from the response."""
        raise NotImplementedError()

    def attach_id_state(self, request: Request, session_id: Union[ID, FrontendError]):
        """Attach the extracted session id to the request."""
        try:
            request.state.session_ids[self.identifier] = session_id
        except Exception:
            request.state.session_ids = {}
            request.state.session_ids[self.identifier] = session_id
