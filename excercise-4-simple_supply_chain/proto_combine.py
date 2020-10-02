from glob import glob

from grpc.tools.protoc import main as _protoc

output_path = ['./processor/protobuf', './rest_api/protobuf']

for _output_path in output_path:
    _protoc(
        [
            '',
            '-I=./protos',
            f'--python_out={_output_path}',
        ]
        + glob('./protos/*.proto')
    )
