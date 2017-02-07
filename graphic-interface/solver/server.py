import json
import os
import sys

import tornado.web

from optimizedGPS import options

APP_NAME = os.getenv("APP_NAME")
PORT_NUMBER = os.getenv("%s_port" % APP_NAME)


class GetAllProblemsHandler(tornado.web.RequestHandler):
    def post(self):
        problems = {'data': options.KNOWN_PROBLEMS}
        self.write(json.dumps(problems))


class GetAllHeuristicsHandler(tornado.web.RequestHandler):
    def post(self):
        heuristics = {'data': options.KNOWN_HEURISTICS}
        self.write(json.dumps(heuristics))


if __name__ == "__main__":
    settings = {
        "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__"
    }

    app = tornado.web.Application(
        [
            (r"/get_all_problems", GetAllProblemsHandler),
            (r"/get_all_heuristics", GetAllHeuristicsHandler)
        ],
        **settings
    )
    app.listen(PORT_NUMBER)
    sys.stderr.write("server started on port %s...\n" % PORT_NUMBER)
    tornado.ioloop.IOLoop.current().start()
