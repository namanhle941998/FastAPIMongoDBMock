from enum import Enum

def init():
    pass 

class Role(Enum):
    ADMIN = "Admin"
    USER = "User"
    GUEST = "Guest"
    MODERATOR = "Moderator"

class KafkaTopic(Enum):
    USER_ACTIVITY = "user_activity"


