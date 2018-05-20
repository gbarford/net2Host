import datetime

class normaliser():
    tailfile = '/var/log/bro/current/conn.log'
    
    corrlationFields = {
        'src_ip' : 'id.orig_h',
        'dst_ip' : 'id.resp_h',
        'src_port' : 'id.orig_p',
        'dst_port' : 'id.resp_p',
        'nproto': 'proto'
    }

    initialValues = {
        'type_broConn' : 'True'
    }

    secondaryFields = {
        'timestamp' : '%--function--%',
        'finished' : '%--function--%',
        'bro_uid' : 'uid',
        'service': 'service',
        'duration' : 'duration',
        'dst_bytes' : 'resp_bytes',
        'src_bytes' : 'orig_bytes',
        'bro_conn_state' : 'conn_state',
        'direction' : '%--function--%',
        'finished_time' : '%--function--%',
        'bro_missed_bytes' : 'missed_bytes',
        'src_packets' : 'orig_pkts',
        'dst_packets' : 'resp_pkts'
    }

    overwriteFields = set(['@timestamp','aproto','nproto','finished'])

    appendingFields = set()

    def timestamp(self,log):
        return datetime.datetime.fromtimestamp(float(log['ts'])).isoformat()

    def finished(self,log):
        if log['conn_state'] == u'S0' or log['conn_state'] == u'S1':
            return False
        else:
            if log['conn_state'] == u'OTH' or log['proto'] != 'tcp':
                return None
            else:
                return True

    def direction(self,log):
        if log['local_resp'] == True:
            return "inbound"
        else:
            return "outbound"

    def finished_time(self,log):
        if self.finished(log) and 'ts' in log and 'duration' in log:
            return datetime.datetime.fromtimestamp(float(log['ts'])+float(log['duration'])).isoformat()