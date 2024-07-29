import grpc
from lnd_grpc import LightningStub, ln, rpc_pb2 as lnrpc

def get_ln_stub():
    with open(CERT_PATH, 'rb') as f:
        cert = f.read()
    creds = grpc.ssl_channel_credentials(cert)
    auth_creds = grpc.metadata_call_credentials(lambda context, callback: callback([('macaroon', get_macaroon_hex())], None))
    combined_creds = grpc.composite_channel_credentials(creds, auth_creds)
    channel = grpc.secure_channel('localhost:10009', combined_creds)
    return LightningStub(channel)

def get_node_info():
    stub = get_ln_stub()
    response = stub.GetInfo(ln.GetInfoRequest())
    print(f"Alias: {response.alias}\nBlock Height: {response.block_height}")

