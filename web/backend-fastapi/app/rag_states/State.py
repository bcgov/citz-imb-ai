from abc import ABC, abstractmethod


class State(ABC):
    def __init__(self, tag, index="", query="", kwargs_key=""):
        self.__tag = tag
        self.__vector_index = index
        self.__vector_query = query
        self.__kwargs_key = kwargs_key

    def get_tag(self):
        return self.__tag

    def get_index(self):
        return self.__vector_index

    def get_vector_query(self):
        return self.__vector_query

    def get_kwargs_key(self):
        return self.__kwargs_key

    @abstractmethod
    def create_prompt(self, context_str, question, chat_history): ...

    @abstractmethod
    def query_similar(self, question, kg): ...
