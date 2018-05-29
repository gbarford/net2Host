import datetime

class normaliser():
    logLevel = "INFO"
    tailfile = '/var/log/bro/current/http.log'
    
    corrlationFields = {
        'src_ip' : 'id.orig_h',
        'dst_ip' : 'id.resp_h',
        'src_port' : 'id.orig_p',
        'dst_port' : 'id.resp_p'
    }


    initialValues = {
        'type_broHTTP' : 'True',
        'nproto' : 'tcp',
        'aproto' : 'http'
    }

    secondaryFields = {
        'timestamp' : '%--function--%',
        'bro_uid' : 'uid',
        'request_method' : 'method',
        'host_server_name' : 'host',
        'request_uri' : 'uri',
        'response_status_code' : 'status_code',
        'request_user_agent' : 'user_agent',
        'http_version' : 'version'

    }

    overwriteFields = set(['aproto'])

    appendingFields = set(['request_method','request_uri','response_status_code'])

    def timestamp(self,log):
        return datetime.datetime.fromtimestamp(float(log['ts'])).isoformat()

