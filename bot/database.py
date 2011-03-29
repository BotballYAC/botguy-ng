import sqlite3
try:
    import cPickle as pickle
except:
    import pickle
import atexit
import abc
from . import botguy_config

pickle_protocol = botguy_config.pickle_protocol

try: # python 2
    buffer
    blob = lambda x: buffer(pickle.dumps(x, pickle_protocol))
except: # python 3
    blob = lambda x: bytes(pickle.dumps(x, pickle_protocol))

try: # python 3
    bytes
    unblob = lambda x: pickle.loads(bytes(x))
except: # python 2
    unblob = lambda x: pickle.loads(str(x))

class Database(object):
    
    _plugin_db_codecs = {}
    
    def __init__(self, file_name, atexit_close=False):
        super(Database, self).__init__()
        self.connection = sqlite3.connect(file_name)
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS plugin_db(plugin TEXT, data BLOB)")
        self.__closed = False
        self._db_handlers = {}
        if atexit_close:
            atexit.register(self.close)
    
    def sync(self):
        assert not self.__closed
        self.connection.commit()
    
    def close(self):
        if not self.__closed:
            self.sync()
            self.connection.close()
            del self.connection
    
    def get_cursor(self):
        return self.connection.cursor()
    
    cursor = property(get_cursor)
    
    @classmethod
    def register_storage_format(cls, name, codec):
        cls._plugin_db_codecs[name] = codec
    
    def register_plugin(self, name, db_type, *args, **kwargs):
        h = self._plugin_db_codecs[db_type](name, self.cursor, *args, **kwargs)
        self._db_handlers[name] = h
        return h
    
    def get_handler(self, name):
        return self._db_handlers[name]

class DatabaseCodec(object):
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, name, cursor, writeback=False):
        self.__name = name
        self._cursor = cursor
        self._writeback = writeback
        self.__closed = False
        self.__value = None
    
    def get_name(self):
        return self.__name
    
    name = property(get_name)
    
    @abc.abstractmethod
    def _base_get_data(self):
        pass
    
    def get_data(self):
        v = self._base_get_data()
        if self._writeback:
            self.__value = v
        return v
    
    @abc.abstractmethod
    def _base_set_data(self):
        pass
    
    def set_data(self, obj):
        self._base_set_data(obj)
        if self._writeback:
            self.__value = obj
    
    @abc.abstractmethod
    def _base_del_data(self):
        pass
    
    def del_data(self):
        self._base_del_data()
        if self._writeback:
            self.__value = None
    
    data = property(get_data, set_data, del_data)
    
    def sync(self):
        self._base_set_data(self.__value)
    
    def close(self):
        self.sync()
        self._cursor.close()
        self.__closed = True
    
    def get_is_closed(self):
        return __closed
    
    is_closed = property(get_is_closed)

class PickleCodec(DatabaseCodec):
    def __init__(self, *args, **kwargs):
        super(PickleCodec, self).__init__(*args, **kwargs)
        self._cursor.execute(
            "INSERT OR IGNORE INTO plugin_db VALUES(?, NULL)", self.name
        )
    
    def _base_get_data(self):
        self._cursor.execute("SELECT data FROM plugin_db WHERE plugin=?",
                             (self.name, ))
        data = self._cursor.fetchone()[0]
        if data is None: return None
        return unblob(data)
    
    def _base_set_data(self, obj):
        self._cursor.execute(
            "UPDATE plugin_db SET data=? WHERE plugin=?",
            (blob(obj), self.name)
        )
    
    def _base_del_data(self):
        self._cursor.execute("DELETE FROM plugin_db WHERE plugin=?", self.name)

class SqlTableCodec(DatabaseCodec):
    """Warning: This class provides some lower-level access to the table, and
    therefore should only be used by trusted sources. It is vulnerable to sql
    injection, not to mention it returns a cursor to the data. That is not to
    say however, that one couldn't make a wrapper for this class and make its
    usage safe."""
    
    def __init__(self, name, cursor, table_args):
        super(SqlTableCodec, self).__init__(name, cursor, writeback=False)
        self._table = "plugin_db_%s" % name
        self._cursor.execute(
            "CREATE TABLE IF NOT EXISTS ?(?)", (self._table, table_args)
        )
    
    def _base_get_data(self):
        """Returns a tuple composed of a cursor to the sql table and the name of
        the table that contains this plugin's info"""
        return (self._cursor, self._table)
    
    def _base_set_data(self, obj):
        raise AttributeError("One cannot simply set sql_table data, they " +
                             "must do so through mutatable means!")
    
    def _base_del_data(self):
        self._cursor.execute("DROP TABLE ?", (self._table, ))
    
    def sync(self):
        pass

class DatabaseDict(DatabaseCodec):
    def __init__(self, name, cursor, writeback=False):
        super(DatabaseDict, self).__init__(name, cursor, writeback=False)
        self._table = "plugin_db_%s" % name
        self._cursor.execute(
            "CREATE TABLE IF NOT EXISTS %s(key TEXT UNIQUE, value BLOB)"
            % self._table
        )
        self.__cached_values = {}
        self._writeback = writeback
    
    def _base_get_data(self):
        raise AttributeError("Not yet implemented")
    
    def _base_set_data(self, obj):
        raise AttributeError("Not yet implemented")
    
    def _base_del_data(self):
        raise AttributeError("Not yet implemented")
    
    def __iter__(self):
        for i in self._cursor.execute("SELECT key FROM %s" % self._table):
            yield i[0];
    
    def __contains__(self, key):
        return (self._writeback and key in self.__cached_values) or \
               self._cursor.execute(
                   "SELECT * FROM %s WHERE key=?" % self._table, (key, )
               ).fetchone() is not None
    
    def __getitem__(self, key):
        try:
            return self.__cached_values[key]
        except:
            return unblob(
                self._cursor.execute(
                    "SELECT value FROM %s WHERE key=?" % self._table, (key, )
                ).fetchone()[0]
            )
    
    def __setitem__(self, key, value):
        if self._writeback:
            self.__cached_values[key] = value
        self._cursor.execute(
            "INSERT OR REPLACE INTO %s VALUES(?, ?)" % self._table,
            (key, blob(value))
        )
    
    def __delitem__(self, key):
        if self._writeback:
            del self.__cached_values[key]
        self._cursor.execute("DELETE FROM %s WHERE key=?" % self._table, (key,))
    
    def sync(self):
        for i in self.__cached_values:
            self._cursor.execute(
                "INSERT OR REPLACE INTO %s VALUES(?, ?)" % self._table,
                (key, blob(i))
            )
        self.__cached_values = {}

Database.register_storage_format("pickled", PickleCodec)
Database.register_storage_format("sql_table", SqlTableCodec)
Database.register_storage_format("shelf", DatabaseDict)
