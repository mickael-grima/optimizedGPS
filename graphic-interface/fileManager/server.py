import sys
import os
import tornado.web

APP_NAME = os.getenv("APP_NAME")
PORT_NUMBER = os.getenv("%s_port" % APP_NAME)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        error, info, warning = "", "", ""
        self.render("base.html", error=error, warning=warning, info=info, active=self.get_argument("active", default=""))


if __name__ == "__main__":
    settings = {
        "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__"
    }

    app = tornado.web.Application(
        [
            (r"/", MainHandler),
        ],
        template_path="/workspace/templates",
        static_path="/workspace/static",
        xsrf_cookies=False,
        **settings
    )
    app.listen(PORT_NUMBER)
    sys.stderr.write("server started on port %s...\n" % PORT_NUMBER)
    tornado.ioloop.IOLoop.current().start()
