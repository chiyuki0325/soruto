class WashingMachineBaseError(Exception):
    api_name: str | None = None
    pass


class UserAlreadyLoggedInError(WashingMachineBaseError):
    pass


class QRCodeExpiredError(WashingMachineBaseError):
    pass


class UnknownWashingMachineError(WashingMachineBaseError):
    pass


class NotFoundError(WashingMachineBaseError):
    pass


class InternalServerError(WashingMachineBaseError):
    pass


class WashingMachineFatalError(Exception):
    pass


class DecryptFailedError(WashingMachineFatalError):
    pass


class IPBannedFatalError(WashingMachineFatalError):
    pass


class MaxRetriesExceededError(Exception):
    # 可以通过 e.e 获取原始异常
    def __init__(self, e):
        self.e = e
        super().__init__(e)
