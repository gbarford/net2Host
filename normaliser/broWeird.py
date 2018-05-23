import datetime

class normaliser():
    logLevel = "INFO"
    tailfile = '/var/log/bro/current/dns.log'
    
    corrlationFields = {
        'src_ip' : 'id.orig_h',
        'dst_ip' : 'id.resp_h',
        'src_port' : 'id.orig_p',
        'dst_port' : 'id.resp_p',
        'nproto': 'proto'
    }

    initialValues = {
        'type_broDNS' : 'True',
        'service': 'dns'
    }

    secondaryFields = {
        'timestamp' : '%--function--%',
        'bro_uid' : 'uid',
        'dns_qry' : 'query',
        'dns_code' : 'rcode',
        'dns_class' : 'qclass',
        'dns_response' : 'answers'
    }

    overwriteFields = set()

    appendingFields = set(['dns_qry','dns_code','dns_class','dns_response_qry'])

    def timestamp(self,log):
        return datetime.datetime.fromtimestamp(float(log['ts'])).isoformat()

