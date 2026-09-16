# gevent must patch ssl/socket before botocore imports them, otherwise
# documentservice's monkey.patch_all() at import time blows the stack.
from gevent import monkey

monkey.patch_all()
