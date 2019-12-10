import sentry_sdk
import logging


class Config:

    def __init__(self, *args, **kwargs):
        sentry_sdk.init(
            "https://878e280471064d3786d9bcd063e46ad7@sentry.io/1850943"
            )
