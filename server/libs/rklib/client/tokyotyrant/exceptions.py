# -*- coding: utf-8 -*-

'''
If you know error code, use `get_for_code(code)` to retrieve exception instance.
'''

__all__ = ['Success', 'InvalidOperation', 'HostNotFound', 'ConnectionRefused',
           'SendError', 'ReceiveError', 'RecordExists', 'RecordNotFound',
           'MiscellaneousError', 'get_for_code']

class TyrantError(Exception):
    '''
    Tyrant error, socket and communication errors are not included here.
    '''
    pass

class TyrantServerDisconnected(TyrantError):
    '''
    Server disconnect error.
    '''
    pass

class IllegalServerExpresion(TyrantError):
    '''
    Server config error.
    '''
    pass

class Success(TyrantError):
    """
    Honestly copy from the Tyrant protocol!
    """
    pass

class InvalidOperation(TyrantError):
    pass

class HostNotFound(TyrantError):
    pass

class ConnectionRefused(TyrantError):
    pass

class SendError(TyrantError):
    pass

class ReceiveError(TyrantError):
    pass

class RecordExists(TyrantError):
    message = 'Record already exists'

class RecordNotFound(TyrantError):
    pass

class MiscellaneousError(TyrantError):
    pass


ERROR_CODE_TO_CLASS = {
    0: Success,
    1: InvalidOperation,
    2: HostNotFound,
    3: ConnectionRefused,
    4: SendError,
    5: ReceiveError,
    6: RecordExists,
    7: RecordNotFound,
    9999: MiscellaneousError,
}


def get_for_code(error_code, message=None):
    if type(error_code) != int:
        raise TypeError(u'Could not map error code to exception class: expected '
                        u'a number, got "%s"' % error_code)
    else:
        if ERROR_CODE_TO_CLASS.has_key(error_code):
            cls = ERROR_CODE_TO_CLASS[error_code]
            return cls(message) if message else cls()
        else:
            raise ValueError('Unknown error code "%d"' % error_code)
