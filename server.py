import os.path
import cherrypy
from cherrypy import expose
import persistence


def stringify_datetime(data):
    for i in range(len(data)):
        data[i]['period'] = data[i]['period'].strftime('%Y-%m-%d %H:%M:%S')
    return data

class HelloWorld(object):
    @expose
    def index(self):
        current_path = cherrypy.request.script_name + cherrypy.request.path_info
        print((current_path))
        raise cherrypy.HTTPRedirect("index.html")

    @expose
    @cherrypy.tools.json_out()
    def detail(self):
        data = persistence.get_detail()
        data = stringify_datetime(data)
        return data
    
    @expose
    @cherrypy.tools.json_out()
    def daily(self):
        data = persistence.get_by_day()
        return data
    
    @expose
    @cherrypy.tools.json_out()
    def weekly(self):
        data = persistence.get_by_week()
        return data

    @expose
    @cherrypy.tools.json_out()
    def monthly(self):
        data = persistence.get_by_month()
        return data

    @expose
    @cherrypy.tools.json_out()
    def total(self):
        data = persistence.get_by_host()
        return data
        
    @expose
    @cherrypy.tools.json_out()
    @cherrypy.tools.allow(methods=['POST'])
    def monitor(self, user_id=None):
        try:
            user_id = int(user_id) if user_id is not None else 1
        except ValueError:
            user_id = 1
        data = persistence.get_real_time(user_id)
        data = stringify_datetime(data)
        return data
    
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
    
    @expose
    def shutdown(self):
        cherrypy.engine.stop()
    

def start():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    conf = {'/': {  
        'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.join(current_dir, 'html'), },
        }
        
    cherrypy.tree.mount(HelloWorld(), '', conf)
    cherrypy.config.update({'server.socket_host': '0.0.0.0',})
    cherrypy.config.update({'server.socket_port': 8433,})
    #cherrypy.config.update(conf)
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()

def stop():
    cherrypy.engine.stop()

if __name__ == '__main__':
    start()
    cherrypy.engine.block()