import requests
import enum
import json
import validators
from datadog import initialize, statsd
import datetime
from time import sleep
status=[]
while True:
    accessible = True
    datadog_access=True

    # Connect to datadog
    while True: #try to connect mongodb
        try:
            options = {
                'statsd_host':'127.0.0.1',
                'statsd_port':8125
            }

            initialize(**options)
            break
        except:
            print("Error to connect datadog")
            datadog_access=False
            sleep(30)
            


    # Request method
    class Methods(enum.Enum):
        GET = 0
        POST = 1

    # Result of site status
    class Status(enum.Enum):
        Correct= 0
        Fail = 1

    def Check_Status(status_code : int, address : str):
        if status_code != 200:
            message = "{0} at {1} was inaccessible".format(address,datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            Send_Status(statsd.WARNING,message)

            if address not in status:
                statsd.event(message, 'Error message', alert_type='error', tags=['yourapp'])
                status.append(address)
        elif status_code==200 and address in status:
            status.remove(address)
            message = "{0} at {1} be accessible".format(address,datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
            statsd.event(message, 'Info message', alert_type='success', tags=['yourapp'])
        

    def Send_Status(state : str = "0", msg : str = "Application is OK"):
        try:
            statsd.service_check(
                check_name = "yourapp.health",
                status = state ,
                message = msg,
            )
        except:
            print("error send check")
            datadog_access = False


    while datadog_access:
        with open('services.txt','r') as f:
            services = f.readlines()

        services = list(set(services[1:]))

        # In situation that a address in status not in new servicess.txt
        if len(status) > 0:
            addresses=[]
            for service in services:
                addresses.append(service.strip().split(',')[0])
            tmp_status=[]            
            for st in status:
                if st in addresses:
                    tmp_status.append(st)
                else:
                    message = "{0} at {1} removed from list".format(st,datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
                    statsd.event(message, 'Info message', alert_type='info', tags=['yourapp'])
            
            status=tmp_status

        if len(status)==0:
            Send_Status()

        for service in services:
            address, method, data = service.strip().split(',')

            if validators.url(address):
                req = ''
                try:
                    if int(method) == Methods.GET.value:
                        req = requests.get(address)
                    
                    #for post requests
                    else:
                        data = json.load(data.replace('\n',''))
                        req = requests.post(address,data = data)
                    
                    Check_Status(req.status_code,address)
                except Exception as e:
                    print(str(e))

        sleep(2)
