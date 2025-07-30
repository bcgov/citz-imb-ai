from abc import ABC, abstractmethod
from enum import Enum


class StateType(Enum):
    """
    Enum class used to define the different types of RAG states.
    """

    INTERNAL = "internal"
    EXTERNAL = "external"


class State(ABC):
    """
    An abtract class used as the base for all RAG states.
    """

    def __init__(self, tag, version, index, query, kwargs_key, description, top_k=10):
        self.__tag = tag
        self.__version = version
        self.__vector_index = index
        self.__vector_query = query
        self.__kwargs_key = kwargs_key
        self.__description = description
        self.__top_k = top_k

    @property
    def tag(self):
        return self.__tag

    @property
    def vector_index(self):
        return self.__vector_index

    @property
    def vector_query(self):
        return self.__vector_query

    @property
    def kwargs_key(self):
        return self.__kwargs_key

    @property
    def trulens_id(self):
        return self.__tag + "-" + self.__version

    @property
    def description(self):
        return self.__description

    @property
    def type(self):
        return StateType.INTERNAL

    @property
    def top_k(self):
        return self.__top_k

    @abstractmethod
    def create_prompt(self, context_str, question, chat_history): ...

    @abstractmethod
    def query_similar(self, question, kg): ...
