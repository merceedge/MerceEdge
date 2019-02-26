
class MockEdge:
    def __init__(self, package_config):
        self.user_config = package_config

    def wireload_emit_output_payload(self, 
                                    output_name, 
                                    mock_output_call, 
                                    output_payload):
        mock_output_call(output_name, output_payload)   