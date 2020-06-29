import abc
import os

from pymongo import MongoClient


class Connection(metaclass=abc.ABCMeta):
    """
    The connetion interface that declares a client for a particular
    client.
    """
    @property
    @abc.abstractmethod
    def client(self):
        pass

    @client.setter
    @abc.abstractmethod
    def client(self, x):
        pass


class MongoConnection(Connection):
    """
    A concrete class that defines a MongoDB client
    """

    def __init__(self):
        self.host = os.environ['DATABASE_HOST']
        self.user = os.environ['MONGODB_USERNAME']
        self.password = os.environ['MONGODB_PASSWORD']
        self.db_name = os.environ['DATABASE_NAME']

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, x):
        if os.environ.get('DATABASE_HOST') is not None:
            self._client = MongoClient(
                host,
                username=user,
                password=password,
                authSource=db_name,
                authMechanism='SCRAM-SHA-1',
            )
        else:
            self._client = None
