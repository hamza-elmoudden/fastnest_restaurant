from fastnest.common.decorators import createParamDecorator

CurrentUser = createParamDecorator(
    lambda data, req: getattr(req.state, "user", None)
)
