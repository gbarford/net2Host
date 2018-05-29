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
        'finished': '%--function--%',
        'bro_uid' : 'uid',
        'dns_qry' : 'query',
        'dns_code' : 'rcode',
        'dns_code_name' : 'rcode_name',
        'dns_qry_type' : 'qtype',
        'dns_qry_type_name' : 'qtype_name',
        'dns_class' : 'qclass',
        'dns_class_name' : 'qclass_name',
        'dns_response' : 'answers',
        'dns_auth_answ' : 'AA',
        'dns_mesg_trunc' : 'TC',
        'dns_rec_desir' : 'RD',
        'dns_rec_avail' : 'RA',
        'dns_TTLs' : 'TTLs'
    }

    overwriteFields = set()

    appendingFields = set(['dns_qry','dns_code','dns_class','dns_response_qry'])

    def timestamp(self,log):
        return datetime.datetime.fromtimestamp(float(log['ts'])).isoformat()

    def finished(self,log):
        if log['proto'] == 'udp':
            return True
        else:
            return None

