
class InvalidChatroom(BaseException):
    def __init__(self, m):
        pass
        self.message = m
    
    def __str__(self):
        return self.message


class NotChannelError(Exception):
    def __init__(self, m):
        pass
        self.message = m
    
    def __str__(self):
        return self.message


class NotGroupError(Exception):
    def __init__(self, m):
        pass
        self.message = m
    
    def __str__(self):
        return self.message


class NotDirectChatError(Exception):
    def __init__(self, m):
        pass
        self.message = m
    
    def __str__(self):
        return self.message


class AlreadyExistsInChatroom(Exception):
    def __init__(self, m):
        pass
        self.message = m
    
    def __str__(self):
        return self.message


class ChatRoomExistsError(Exception):
    def __init__(self, m):
        pass
        self.message = m
    
    def __str__(self):
        return self.message


class InvalidRole(Exception):
    def __init__(self, m):
        pass
        self.message = m
    
    def __str__(self):
        return self.message