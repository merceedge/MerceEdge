from merceedge.api_server.extensions import (
    db
)

class ComponentDBModel(db.Model):
    __tablename__ = 'components'
    uuid = db.Column(db.String, primary_key=True)
    template_name = db.Column(db.String, nullable=False)

    def __repr__(self):
        return 'Component {}-{}'.format(self.template_name, self.uuid)


class WireDBModel(db.Model):
    __tablename__ = 'wires'
    id = db.Column(db.String, primary_key=True)
    input_component_uuid = db.Column(db.String, nullable=False)
    input_name = db.Column(db.String(255), nullable=False)
    output_component_uuid = db.Column(db.String, nullable=False)
    output_name = db.Column(db.String(255), nullable=False)


