# -*- coding: utf-8 -*-
'''
A client implementation of Tokyo Tyrant binary protocol.

Create by Ryan Zhou at Fre Mar/05/2010
Email: zhongrui.zhou@rekoo.com
'''
import math
import struct
import socket
import datetime

from . import exceptions
from .exceptions import TyrantServerDisconnected



# Table Types
DB_BTREE  = 'B+ tree'
DB_TABLE  = 'table'
DB_MEMORY = 'on-memory hash'
DB_HASH   = 'hash'

TABLE_COLUMN_SEP = '\x00'

class _Sock(object):
    '''
    Socket logic. We use this class as a wrapper to raw sockets.
    '''

    def __init__(self, host, port, timeout = None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock = None
        self.connect()

    def connect(self):
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.timeout:
                self._sock.settimeout(self.timeout)
            self._sock.connect((self.host, self.port))
            self._sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
        except socket.error:
            self.close()
            raise TyrantServerDisconnected('Tyrant server at %s:%i disconnected.'
                    % (self.host, self.port))

    def __del__(self):
        self._sock.close()

    def send(self, pack, sync = True):
        '''
        Send message to socket, then check for errors as needed.
        '''
        try:
            self._sock.sendall(pack)

            if not sync:
                return

            fail_code = ord(self.get_byte())
            if fail_code:
                raise exceptions.get_for_code(fail_code)
        except (socket.error, TyrantServerDisconnected):
            self.close()
            self.connect()
            self.send(pack, sync)

    def recv(self, bytes):
        '''
        Retrieves given number of bytes from the socket and returns them as
        string.
        '''
        data = ''
        while len(data) < bytes:
            d = self._sock.recv(min(8192, bytes - len(data)))
            if len(d) == 0:
                raise TyrantServerDisconnected
            data += d
        return data

    def get_byte(self):
        '''
        Retrieves one byte from the socket and returns it.
        '''
        return self.recv(1)

    def get_int(self):
        '''
        Retrieves an integer (4 bytes) from the socket and returns it.
        '''
        return struct.unpack('>I', self.recv(4))[0]

    def get_long(self):
        '''
        Retrieves a long integer (8 bytes) from the socket and returns it.
        '''
        return struct.unpack('>Q', self.recv(8))[0]

    def get_str(self):
        '''
        Retrieves a string (n bytes, which is an integer just before string)
        from the socket and returns it.
        '''
        return self.recv(self.get_int())

    def get_double(self):
        '''
        Retrieves two long integers (16 bytes) from the socket and returns them.
        '''
        intpart, fracpart = struct.unpack('>QQ', self.recv(16))
        return intpart + (fracpart * 1e-12)

    def get_strpair(self):
        '''
        Retrieves a pair of strings (n bytes, n bytes which are 2 integers just
        before the pair) and returns them as a tuple of strings.
        '''
        klen = self.get_int()
        vlen = self.get_int()
        return self.recv(klen), self.recv(vlen)

    def close(self):
        self._sock.close()

class TyrantClient(object):
    '''
    A straightforward implementation of the Tokyo Tyrant protocol. Provides all
    low level constants and operations. Provides a level of abstraction that is
    just enough to communicate with server from Python using Tyrant API.
    '''
    # encoding config
    _ENCODING = 'UTF-8'
    _ENCODING_ERROR_HANDLING = 'strict'    # set to 'replace' or 'ignore' if needed

    # magic number
    _MAGIC_NUMBER = 0xC8

    # TyrantClient commands

    PUT       = 0x10
    PUTKEEP   = 0x11
    PUTCAT    = 0x12
    PUTSHL    = 0x13
    PUTNR     = 0x18
    OUT       = 0x20
    GET       = 0x30
    MGET      = 0x31
    VSIZ      = 0x38
    ITERINIT  = 0x50
    ITERNEXT  = 0x51
    FWMKEYS   = 0x58
    ADDINT    = 0x60
    ADDDOUBLE = 0x61
    EXT       = 0x68
    SYNC      = 0x70
    OPTIMIZE  = 0x71
    VANISH    = 0x72
    COPY      = 0x73
    RESTORE   = 0x74
    SETMST    = 0x78
    RNUM      = 0x80
    SIZE      = 0x81
    STAT      = 0x88
    MISC      = 0x90

    # Query conditions

    RDBQCSTREQ   = 0     # string is equal to
    RDBQCSTRINC  = 1     # string is included in
    RDBQCSTRBW   = 2     # string begins with
    RDBQCSTREW   = 3     # string ends with
    RDBQCSTRAND  = 4     # string includes all tokens in
    RDBQCSTROR   = 5     # string includes at least one token in
    RDBQCSTROREQ = 6     # string is equal to at least one token in
    RDBQCSTRRX   = 7     # string matches regular expressions of
    RDBQCNUMEQ   = 8     # number is equal to
    RDBQCNUMGT   = 9     # number is greater than
    RDBQCNUMGE   = 10    # number is greater than or equal to
    RDBQCNUMLT   = 11    # number is less than
    RDBQCNUMLE   = 12    # number is less than or equal to
    RDBQCNUMBT   = 13    # number is between two tokens of
    RDBQCNUMOREQ = 14    # number is equal to at least one token in
    RDBQCFTSPH   = 15    # full-text search with the phrase of
    RDBQCFTSAND  = 16    # full-text search with all tokens in
    RDBQCFTSOR   = 17    # full-text search with at least one token in
    RDBQCFTSEX   = 18    # full-text search with the compound expression of

    RDBQCNEGATE  = 1 << 24    # negation flag
    RDBQCNOIDX   = 1 << 25    # no index flag

    # Order types

    RDBQOSTRASC  = 0    # string ascending
    RDBQOSTRDESC = 1    # string descending
    RDBQONUMASC  = 2    # number ascending
    RDBQONUMDESC = 3    # number descending

    # Operation types

    TDBMSUNION = 0    # union
    TDBMSISECT = 1    # intersection
    TDBMSDIFF  = 2    # difference

    # Miscellaneous operation options

    RDBMONOULOG = 1    # omission of update log

    # Scripting extension options

    RDBXOLCKREC = 1    # record locking
    RDBXOLCKGLB = 2    # global locking

    def __init__(self, host, port, timeout = None):
        self._sock = _Sock(host, port, timeout)

    def put(self, key, value):
        '''
        Unconditionally sets key to value.
        '''
        key = self._check_coding(key)
        value = self._check_coding(value)
        self._sock.send(struct.pack('>BBII', self._MAGIC_NUMBER, self.PUT,
                len(key), len(value)) + key + value)

    def putkeep(self, key, value):
        '''
        Sets key to value if key does not already exist.
        '''
        key = self._check_coding(key)
        value = self._check_coding(value)
        self._sock.send(struct.pack('>BBII', self._MAGIC_NUMBER, self.PUTKEEP,
                len(key), len(value)) + key + value)

    def putcat(self, key, value):
        '''
        key = self._check_coding(key)
        value = self._check_coding(value)
        Appends value to the existing value for key, or sets key to value if it
        does not already exist.
        '''
        self._sock.send(struct.pack('>BBII', self._MAGIC_NUMBER, self.PUTCAT,
                len(key), len(value)) + key + value)

    def putshl(self, key, value, width):
        '''
        Equivalent to:

            self.putcat(key, value)
            self.put(key, self.get(key)[-width:])
        '''
        key = self._check_coding(key)
        value = self._check_coding(value)
        self._sock.send(struct.pack('>BBIII', self._MAGIC_NUMBER, self.PUTSHL,
                len(key), len(value), width) + key + value)

    def putnr(self, key, value):
        '''
        Sets key to value without waiting for a server response.
        '''
        key = self._check_coding(key)
        value = self._check_coding(value)
        self._sock.send(struct.pack('>BBII',
                self._MAGIC_NUMBER, self.PUTNR, len(key), len(value)) + key + value, False)

    def out(self, key):
        '''
        Removes key from server.
        '''
        key = self._check_coding(key)
        self._sock.send(struct.pack('>BBI', self._MAGIC_NUMBER, self.OUT, len(key)) + key)

    def get(self, key, decode = False):
        '''
        Returns the value of `key` as stored on the server.
        '''
        key = self._check_coding(key)
        try:
            self._sock.send(struct.pack('>BBI', self._MAGIC_NUMBER, self.GET, len(key)) + key)
        except:
            return None
        result = self._sock.get_str()
        return result.decode(self._ENCODING, self._ENCODING_ERROR_HANDLING) if decode else result

    def getint(self, key):
        '''
        Returns an integer for given `key`. Value must be set by
        :meth:`~rkyrant.protocol.TyrantClient.addint`.
        '''
        return self.addint(key)

    def getdouble(self, key):
        '''
        Returns a double for given key. Value must be set by
        :meth:`~rkyrant.protocol.TyrantClient.adddouble`.
        '''
        return self.adddouble(key)

    def mget(self, klst):
        '''
        Returns key,value pairs from the server for the given list of keys.
        '''
        pack_str = struct.pack('>BBI', self._MAGIC_NUMBER, self.MGET, len(klst))
        for key in klst:
            key = self._check_coding(key)
            pack_str += struct.pack('>I', len(key)) + key
        self._sock.send(pack_str)
        numrecs = self._sock.get_int()
        return [self._sock.get_strpair() for i in xrange(numrecs)]

    def vsiz(self, key):
        '''
        Returns the size of a value for given key.
        '''
        key = self._check_coding(key)
        self._sock.send(struct.pack('>BBI', self._MAGIC_NUMBER, self.VSIZ, len(key)) + key)
        return self._sock.get_int()

    def iterinit(self):
        '''
        Begins iteration over all keys of the database.
        '''
        self._sock.send(chr(self._MAGIC_NUMBER) + chr(self.ITERINIT))

    def iternext(self):
        '''
        Returns the next key after ``iterinit`` call. Raises an exception which
        is subclass of :class:`~rkyrant.protocol.TyrantError` on iteration end.
        '''
        self._sock.send(chr(self._MAGIC_NUMBER) + chr(self.ITERNEXT))
        return self._sock.get_str().decode(self._ENCODING, self._ENCODING_ERROR_HANDLING)

    def fwmkeys(self, prefix, maxkeys = 4294967295):
        '''
        Get up to the first maxkeys starting with prefix
        '''
        prefix = self._check_coding(prefix)
        self._sock.send(struct.pack('>BBII', self._MAGIC_NUMBER,
                self.FWMKEYS, len(prefix), maxkeys) + prefix)
        numkeys = self._sock.get_int()
        return [self._sock.get_str().decode(self._ENCODING, self._ENCODING_ERROR_HANDLING)
                for i in xrange(numkeys)]

    def addint(self, key, num=0):
        '''
        Adds given integer to existing one. Stores and returns the sum.
        '''
        key = self._check_coding(key)
        value = self._check_coding(num)
        self._sock.send(struct.pack('>BBII', self._MAGIC_NUMBER, self.ADDINT, len(key), num) + key)
        return self._sock.get_int()

    def adddouble(self, key, num=0.0):
        '''
        Adds given double to existing one. Stores and returns the sum.
        '''
        key = self._check_coding(key)
        fracpart, intpart = math.modf(num)
        fracpart, intpart = int(fracpart * 1e12), int(intpart)
        self._sock.send(struct.pack('>BBIQQ', self._MAGIC_NUMBER,
                self.ADDDOUBLE, len(key), long(intpart), long(fracpart)) + key)
        return self._sock.get_double()

    def ext(self, func, opts, key, value):
        '''
        Calls ``func(key, value)`` with ``opts``.

        :param opts: a bitflag that can be `RDBXOLCKREC` for record locking
            and/or `RDBXOLCKGLB` for global locking.
        '''
        key = self._check_coding(key)
        value = self._check_coding(value)
        self._sock.send(struct.pack('>BBIIII', self._MAGIC_NUMBER, self.EXT, len(func),
                opts, len(key), len(value)) + func + key + value)
        return self._sock.get_str().decode(self._ENCODING, self._ENCODING_ERROR_HANDLING)

    def sync(self):
        '''
        Synchronizes the updated contents of the remote database object with the
        file and the device.
        '''
        self._sock.send(chr(self._MAGIC_NUMBER) + chr(self.SYNC))

    def optimize(self, parameter):
        '''
        Optimize the storage of a remove database object.
        '''
        self._sock.send(struct.pack('>BBI', self._MAGIC_NUMBER, self.OPTIMIZE, len(parameter)) \
                + parameter)

    def vanish(self):
        '''
        Removes all records from the database.
        '''
        self._sock.send(chr(self._MAGIC_NUMBER) + chr(self.VANISH))

    def copy(self, path):
        '''
        Hot-copies the database to given path.
        '''
        path = self._check_coding(path)
        self._sock.send(struct.pack('>BBI', self._MAGIC_NUMBER, self.COPY, len(path)) + path)

    def restore(self, path, msec, opts):
        '''
        Restores the database from `path` at given timestamp (in `msec`).
        '''
        path = self._check_coding(path)
        self._sock.send(struct.pack('>BBIQI', self._MAGIC_NUMBER, self.RESTORE,
                len(path), msec, opts) + path)

    def setmst(self, host, port):
        '''
        Sets master to `host`:`port`.
        '''
        self._sock.send(struct.pack('>BBII', self.SETMST, len(host), port) + host)

    def rnum(self):
        '''
        Returns the number of records in the database.
        '''
        self._sock.send(chr(self._MAGIC_NUMBER) + chr(self.RNUM))
        return self._sock.get_long()

    def size(self):
        '''
        Returns the size of the database in bytes.
        '''
        self._sock.send(chr(self._MAGIC_NUMBER) + chr(self.SIZE))
        return self._sock.get_long()

    def stat(self):
        '''
        Returns some statistics about the database.
        '''
        self._sock.send(chr(self._MAGIC_NUMBER) + chr(self.STAT))
        return self._sock.get_str().decode(self._ENCODING, self._ENCODING_ERROR_HANDLING)

    def search(self, conditions, limit=10, offset=0,
               order_type=0, order_column=None, opts=0,
               ms_conditions=None, ms_type=None, columns=None,
               out=False, count=False, hint=False):
        '''
        Returns list of keys for elements matching given ``conditions``.

        :param conditions: a list of tuples in the form ``(column, op, expr)``
            where `column` is name of a column and `op` is operation code (one of
            TyrantTyrantClient.RDBQC[...]). The conditions are implicitly combined
            with logical AND. See `ms_conditions` and `ms_type` for more complex
            operations.
        :param limit: integer. Defaults to 10.
        :param offset: integer. Defaults to 0.
        :param order_column: string; if defined, results are sorted by this
            column using default or custom ordering method.
        :param order_type: one of TyrantTyrantClient.RDBQO[...]; if defined along
            with `order_column`, results are sorted by the latter using given
            method. Default is RDBQOSTRASC.
        :param opts:
        :param ms_conditions: MetaSearch conditions.
        :param ms_type: MetaSearch operation type.
        :param columns: iterable; if not empty, returns only given columns for
            matched records.
        :param out: boolean; if True, all items that correspond to the query are
            deleted from the database when the query is executed.
        :param count: boolean; if True, the return value is the number of items
            that correspond to the query.
        :param hint: boolean; if True, the hint string is added to the return
            value.
        '''
        # sanity check
        assert limit  is None or 0 <= limit, 'wrong limit value "%s"' % limit
        assert offset is None or 0 <= offset, 'wrong offset value "%s"' % offset
        assert ms_type in (None, self.TDBMSUNION, self.TDBMSISECT, self.TDBMSDIFF)
        assert order_type in (self.RDBQOSTRASC, self.RDBQOSTRDESC,
                              self.RDBQONUMASC, self.RDBQONUMDESC)

        # conditions
        args = ['addcond\x00%s\x00%d\x00%s' % cond for cond in conditions]

        # MetaSearch support (multiple additional queries, one Boolean operation)
        if ms_type is not None and ms_conditions:
            args += ['mstype\x00%s' % ms_type]
            for conds in ms_conditions:
                args += ['next']
                args += ['addcond\x00%s\x00%d\x00%s' % cond for cond in conds]

        # return only selected columns
        if columns:
            args += ['get\x00%s' % '\x00'.join(columns)]

        # set order in query
        if order_column:
            args += ['setorder\x00%s\x00%d' % (order_column, order_type)]

        # set limit and offset
        if limit:   # and 0 <= offset:
            args += ['setlimit\x00%d\x00%d' % (limit, offset)]

        # drop all records yielded by the query
        if out:
            args += ['out']

        if count:
            args += ['count']

        if hint:
            args += ['hint']

        return self.misc('search', args, opts)

    def misc(self, func, args, opts=0):
        '''
        Executes custom function.

        :param func: the function name (see below)
        :param opts: a bitflag (see below)

        Functions supported by all databases:

        * `putlist` stores records. It receives keys and values one after
          the other, and returns an empty list.
        * `outlist` removes records. It receives keys, and returns
          an empty list.
        * `getlist` retrieves records. It receives keys, and returns values.

        Functions supported by the table database (in addition to mentioned above):

        * `setindex`
        * `search`
        * `genuid`.

        Possible options:

        * :const:`TyrantClient.RDBMONOULOG` to prevent writing to the update log.
        '''
        buf = ''
        if isinstance(args, (list, tuple)):
            for item in args:
                item = self._check_coding(item)
                buf += struct.pack(">I", len(item)) + item
        try:
            self._sock.send(struct.pack('>BBIII', self._MAGIC_NUMBER, self.MISC,
                    len(func), opts, len(args)) + func + buf)
        finally:
            numrecs = self._sock.get_int()

        return [self._sock.get_str().decode(self._ENCODING, self._ENCODING_ERROR_HANDLING)
                for i in xrange(numrecs)]

    def _check_coding(self, expr):
        if isinstance(expr, unicode):
            return expr.encode(self._ENCODING)
        elif isinstance(expr, str):
            return expr
        else:
            raise ValueError('"%s" cannt be a valible key or value in Tyrant.' % repr(expr))

    def reconnect(self):
        self._sock.connect()

    def close(self):
        self._sock.close()

