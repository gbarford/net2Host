import datetime

class normaliser():
    logLevel = "INFO"
    tailfile = '/var/log/nxlog/windows.log'
    
    corrlationFields = {
        'src_ip' : '%--function--%',
        'dst_ip' : '%--function--%',
        'src_port' : '%--function--%',
        'nproto': '%--function--%',
        'dst_port' : '%--function--%'
    }

    initialValues = {
        'type_winSecAudit' : 'True'
    }

    secondaryFields = {
        'timestamp' : '%--function--%',
        'src_process' : '%--function--%',
        'src_processID': '%--function--%',
        'dst_process': '%--function--%',
        'dst_processID': '%--function--%'
    }

    overwriteFields = set()

    appendingFields = set()

    def timestamp(self,log):

        return datetime.datetime.fromtimestamp(float(log['EventReceivedTime'])/1000).isoformat()

    def src_ip(self,log):
        if log['Direction'] == '%%14593':
            return log['SourceAddress']
        elif log['Direction'] == '%%14592':
            return log['DestAddress']
        else:
            return None

    def src_port(self,log):
        if log['Direction'] == '%%14593':
            return log['SourcePort']
        elif log['Direction'] == '%%14592':
            return log['DestPort']
        else:
            return None

    def dst_ip(self,log):
        if log['Direction'] == '%%14593':
            return log['DestAddress']
        elif log['Direction'] == '%%14592':
            return log['SourceAddress']
        else:
            return None

    def dst_port(self,log):
        if log['Direction'] == '%%14593':
            return log['DestPort']
        elif log['Direction'] == '%%14592':
            return log['SourcePort']
        else:
            return None

    def src_process(self,log):
        if log['Direction'] == '%%14593':
            return log['Application']
        return None

    def src_processID(self,log):
        if log['Direction'] == '%%14593':
            return log['ProcessID']
        return None

    def dst_process(self,log):
        if log['Direction'] == '%%14592':
            return log['Application']
        return None

    def dst_processID(self,log):
        if log['Direction'] == '%%14592':
            return log['ProcessID']
        return None

    def nproto(self,log):
        protoDict = {
            "1" : "icmp",
            "2" : "igmp",
            "6" : "tcp",
            "17" : "udp",
            "47" : "gre",
            "51" : "ah",
            "58" : "icmp"
        }
        if log['Protocol'] in protoDict:
            return protoDict[log['Protocol']]
        else:
            raise ValueError
