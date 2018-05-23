import datetime

class normaliser():
    logLevel = "INFO"
    tailfile = '/var/log/nxlog/windows.log'
    
    corrlationFields = {
        'src_ip' : 'SourceAddress',
        'dst_ip' : 'DestAddress',
        'src_port' : 'SourcePort',
        'nproto': '%--function--%',
        'dst_port' : 'DestPort'
    }

    initialValues = {
        'type_winSecAudit' : 'True'
    }

    secondaryFields = {
        'timestamp' : '%--function--%',
        'process' : 'Application',
        'processID': 'ProcessID'
    }

    overwriteFields = set()

    appendingFields = set()

    def timestamp(self,log):

        return datetime.datetime.fromtimestamp(float(log['EventReceivedTime'])/1000).isoformat()

    def nproto(self,log):
        protoDict = {
            "1" : "icmp",
            "2" : "igmp",
            "6" : "tcp",
            "17" : "udp",
            "47" : "gre",
            "51" : "ah"
        }
        if log['Protocol'] in protoDict:
            return protoDict[log['Protocol']]
        else:
            raise ValueError
