import datetime

class normaliser():
    logLevel = "INFO"
    tailfile = '/var/log/bro/current/ssl.log'
    
    corrlationFields = {
        'src_ip' : 'id.orig_h',
        'dst_ip' : 'id.resp_h',
        'src_port' : 'id.orig_p',
        'dst_port' : 'id.resp_p'
    }

    initialValues = {
        'nproto' : 'tcp',
        'aproto' : 'ssl',
        'type_broSSL' : 'True',
        'finished' : False
    }

    secondaryFields = {
        'timestamp' : '%--function--%',
        'bro_uid' : 'uid',
        'version': 'version',
        'cipher' : 'cipher',
        'curve' : 'curve',
        'host_server_name' : 'server_name',
        'resumed' : 'resumed',
        'next_protocol' : 'next_protocol',
        'established' : 'established',
        'subject' : 'subject',
        'issuer' : 'issuer',
        'ja3' : 'ja3',
        'cert_chain_fuids' : 'cert_chain_fuids',
        'client_cert_chain_fuids' : 'client_cert_chain_fuids'
    }

    overwriteFields = set(['aproto','nproto'])

    appendingFields = set()

    def timestamp(self,log):
        return datetime.datetime.fromtimestamp(float(log['ts'])).isoformat()
