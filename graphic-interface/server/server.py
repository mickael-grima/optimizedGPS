import os
import sys
import tornado.web

import requests

APP_NAME = os.getenv("APP_NAME")
PORT_NUMBER = os.getenv("%s_port" % APP_NAME)
SOLVER = ("solver", os.getenv("solver_port"))


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        problems = requests.post(
            "http://%s:%s/get_all_problems" % SOLVER
        ).json()
        heuristics = requests.post(
            "http://%s:%s/get_all_heuristics" % SOLVER
        ).json()
        self.render("start.html", problems=problems['data'], heuristics=heuristics['data'], data={})


class StatsHandler(tornado.web.RequestHandler):
    def get(self):
        data = requests.post(
            "http://%s:%s/get_stats" % SOLVER,
            data=dict(
                data=self.request.arguments.get("data"),
                parameters=self.request.arguments.get("parameters", []),
                problems=self.request.arguments.get("problems", []),
                heuristics=self.request.arguments.get("heuristics", [])
            )
        ).json()
        import json
        self.write(json.dumps(data))
        # self.render("stats.html", data=data)


if __name__ == "__main__":
    settings = {
        "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__"
    }

    app = tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/stats", StatsHandler)
        ],
        template_path="/workspace/templates",
        static_path="/workspace/static",
        xsrf_cookies=False,
        **settings
    )
    app.listen(PORT_NUMBER)
    sys.stderr.write("server started on port %s...\n" % PORT_NUMBER)
    tornado.ioloop.IOLoop.current().start()
