import threading
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


wire_parser = reqparse.RequestParser()
wire_parser.add_argument('input_component_uuid', type=str)
wire_parser.add_argument('input_name', type=str)
wire_parser.add_argument('output_component_uuid', type=str)
wire_parser.add_argument('output_name', type=str)


class WireList(Resource):
    def get(self):
        """ TODO 查询指定id组件相关的连线
        """
        pass
    
    def post(self):
        """添加组件接口连线
        """
        args = wire_parser.parse_args()
        new_wire = current_app.edge.connect_interface(
                        args['output_component_uuid'],
                        args['output_name'],
                        args['input_component_uuid'],
                        args['input_name'])
        new_db_wire = WireDBModel(id=new_wire.id, 
                        input_component_uuid=args['input_component_uuid'],
                        input_name=args['input_name'],
                        output_component_uuid=args['output_component_uuid'],
                        output_name=args['output_name'])
        db.session.add(new_db_wire)
        db.session.commit()
        return new_wire.id, 201

        
class Wire(Resource):
    def get(self, wire_id):
        pass
  
    def put(self, wire_id):
        pass
    
    def delete(self, wire_id):
        """ 删除连线
        """
        # Delete local object
        wire = current_app.edge.delete_wire(wire_id)
        if wire:
            WireDBModel.query.filter_by(id=wire_id).delete()
            db.session.commit()
            return wire_id, 200
            
        else:
            abort(404)
            
        pass