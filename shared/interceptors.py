import time
from fastnest.common.interfaces import NestInterceptor
from fastnest.common.logger import Logger


class LogInterceptor(NestInterceptor):
    def __init__(self):
        self.logger = Logger("HTTP")

    def intercept_before(self, req):
        req.state.t0 = time.time()

    def intercept_after(self, req, res):
        ms = (time.time() - req.state.t0) * 1000
        self.logger.info(f"{req.method} {req.url.path} {ms:.0f}ms")
        return res
