# coding: utf-8

class HttpErrorStatus:
    SystemError = (511, 'system error.')
    InvalidRequest = (512, 'invalid request.')
    WrongParams = (513, 'wrong params.')
    LackPrivilege = (513, 'lack privilege.')
    QueryToDbError = (510, 'query db failed.')
    InsertToDbError = (514, 'insert data to db failed.')
    DeleteFromDbError = (515, 'delete from db failed.')
    RemoteServerError = (520, 'call remote api error.')
    BadFileExtension = (521, 'bad file extension')
    TargetNotExist = (522, 'target not exist.')
    InvalidToken = (530, 'token is invalid.')
    InvalidRequestId = (531, 'request id is out of date or already used.')
    InvalidSign = (532, 'sign is invalid.')
    OldToken = (533, 'token is out of date.')
    ProcessHeaderError = (534, 'process header error.')


class ErrorCode:
    UserExist = 1001
    SendSMSFailed = 1002
    SendSMSOver = 1003
    IncorrectSMSCode = 1004
    IncorrectPassword = 1005
    UserNotExist = 1006
    UserBanned = 1007
    ServerError = 2000
    CacheError = 2001
    DatabaseError = 2002
    UnknownError = 2999
    InvalidParam = 3001
    InsufficientGold = 3002
    AlreadyLiked = 4001
    NotLiked = 4002
    InvalidLocationPair = 4003
    InvalidOperation = 4004
    InvalidFileExtension = 4005
    NotExist = 5001
    AlreadyExist = 5002
    LoginByOtherMachine = 5003
    InnerNetError = 5004
    ThirdPartyError = 5005
    LoginDataOutOfDate = 5006
    LiveAlreadyClosed = 5007
    GameFrozen = 5008
    OldVersion = 5009
    InternalError = 5010
    NotOnBetting = 6001
    ResourceError = 6002
    RPCError = 6003


class MoneyTag:
    RealMoney = 0
    FreeMoney = 1


class RewardType(object):
    NoReward = 0
    Charm = 1
    Credits = 2
    RealMoney = 3
    FreeMoney = 4


class TaskType(object):
    ShareLive = 0
    WinGame = 1
    RewardSomeone = 2  # 打赏某人
    PublishActive = 3
    CommentSomeone = 4
    ChatWithSomeone = 5
    WatchLive = 6
    Login = 7
    PlayGame = 8
    TypeNumber = 9
