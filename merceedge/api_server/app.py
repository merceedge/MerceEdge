
import threading
from flask import Flask
from flask_restful import Api, Resource

from merceedge.api_server.resources.component import (
    ComponentTemplateList,
    ComponentTemplate,
    ComponentList,
    Component,

)
from merceedge.api_server.resources.wire import (
    WireList,
    Wire
)
from merceedge.api_server.extensions import db


"""
REST API:
组件类型
  
/template/{template_name} 
----------
组件
/component  
/component/{component_id} 
----------
连线
/wire
/wire/{wire_id}
"""



def setup(edge, config=None):    
    flask_app_thread = threading.Thread(target=app_run, args=(edge, ))
    flask_app_thread.start()

   
    


class EdgeFlask(Flask):
    """MerceEdge Flask app class
    """
    def __init__(self, edge, import_name):
        super(EdgeFlask, self).__init__(import_name)
        self.edge = edge

def app_run(edge):
    app = EdgeFlask(edge, __name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
    with app.app_context():
        db.init_app(app)
        db.create_all(app=app)
        api = Api(app)

    # api.add_resource(ComponentTemplateList, '/template')
    api.add_resource(ComponentTemplate, '/template/<template_name>')
    api.add_resource(ComponentList, '/component')
    api.add_resource(Component, '/component/<component_id>')
    api.add_resource(WireList, '/wire')
    api.add_resource(Wire, '/wire/<wire_id>')

    with app.app_context():
        edge.restore_entities_from_db()

    app.run(debug=True, use_reloader=False, host= '0.0.0.0')



     

    












    


        


