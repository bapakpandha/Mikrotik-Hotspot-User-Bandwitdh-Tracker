import os.path
import cherrypy
from cherrypy import tools
from cherrypy import expose
import persistence

class HelloWorld(object):
    @expose
    def index(self):
        raise cherrypy.HTTPRedirect("/html/index.html")

    @expose
    @cherrypy.tools.json_out()
    def detail(self):
        data = persistence.get_detail()
        cherrypy.response.status = 200
        return data
    
    @expose
    @cherrypy.tools.json_out()
    def weekly(self):
        return persistence.get_by_week()

    @expose
    @cherrypy.tools.json_out()
    def monthly(self):
        return persistence.get_by_month()

    @expose
    @cherrypy.tools.json_out()
    def total(self):
        return persistence.get_by_host()


    @expose
    def html(self):
        return """<html>
        <head>
                <title>CherryPy static</title>
                <link rel="stylesheet" type="text/css" href="css/style.css" type="text/css"></link>
                <script type="application/javascript" src="js/some.js"></script>
        </head>
        <body>
        <p>Static content</p>
        </body>
        </html>"""

def start():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    conf = {'/html': {  
        'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.join(current_dir, 'html'), },
        }
        
    cherrypy.tree.mount(HelloWorld(), '', conf)
    cherrypy.config.update({'server.socket_host': '127.0.0.7',})
    cherrypy.config.update({'server.socket_port': '8433',})
    #cherrypy.config.update(conf)
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()

def stop():
    cherrypy.engine.stop()

if __name__ == '__main__':
    start()
    cherrypy.engine.block()