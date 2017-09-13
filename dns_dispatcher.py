# -*- coding:utf-8 -*-
from frame import config
from web import app

if __name__ == '__main__':
    app.run(port=config.APP_PORT, debug=config.DEBUG, host="0.0.0.0", threaded=True)
