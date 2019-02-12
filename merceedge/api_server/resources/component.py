
import threading
import json
from flask import (
    current_app,
    abort
)
from flask_restful import (
    Resource,
    reqparse, 
    marshal_with, 
    fields
)
from merceedge.api_server.models import (
    ComponentDBModel,
    WireDBModel
)
from merceedge.api_server.extensions import db


component_parser = reqparse.RequestParser()
component_parser.add_argument('template_name', type=str)


class ComponentTemplateList(Resource):
    def get(self, template_name):
        pass
    # def post(self, instance_id):
    #     pass
    

class ComponentTemplate(Resource):
    def get(self, template_name):
        template = current_app.edge.component_templates.get(template_name, None)
        if template:
            return template
        else:
            abort(404)

"""
TODO
按照组件类型名称查询组件信息
"""
class ComponentList(Resource): 
    def __init__(self):
        # self._lock = threading.Lock()
        pass

    def get(self):
        """ Get All Component within a template
        """
        # TODO 
        pass
    
    def post(self):
        """ Create new component
        创建指定类型的组件实例
        """
        args = component_parser.parse_args()
        # with self._lock:
        new_component = current_app.edge._generate_component_instance(args['template_name'])
        new_db_component = ComponentDBModel(uuid=new_component.id,
                                                    template_name=args['template_name'])

        db.session.add(new_db_component)
        db.session.commit()
        return new_db_component.uuid, 201


class Component(Resource):
    def get(self, component_id):
        """ 按照组件id获取组件信息,以及相关联的wire信息（场景重构的时候调用）
        组件信息包括：组件基本信息，接口信息，连线信息
        
        """
        component_info = {"id": "", 
                        "template": "",
                        "vendor": "", 
                        "inputs": [],
                        "outputs":[]
                        }
        component = current_app.edge.components.get(component_id, None)
        if component:
            component_info["id"] = component_id
            component_info["template"] = component.model_template_config["component"]["name"]
            component_info["vendor"] = component.model_template_config["component"]["vendor"]
            component_info["inputs"] = component.model_template_config["component"].get("inputs", [])
            component_info["outputs"] = component.model_template_config["component"].get("outputs", [])
            # wires info 
            for input_info in component_info["inputs"]:
                name = input_info["name"]
                input_obj = component.inputs.get(name, None)
                if input_obj:
                    input_info["wires"] = input_obj.wires_info()
            
            for output_info in component_info["outputs"]:
                name = output_info["name"]
                output_obj = component.outputs.get(name, None)
                if output_obj:
                    output_info["wires"] = output_obj.wires_info()
            
            return component_info, 200
        else:
            abort(404) 

    
    def delete(self, component_id):
        pass
    
    def put(self, component_id):
        pass

