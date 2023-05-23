from prometheus_client import start_http_server, Gauge
import os
from subprocess import check_output,CalledProcessError 
from datetime import datetime
import time
from dateutil import parser

###directory with kubeconfigs
dir_path='/cluster-configs'
cluster_configs = os.listdir(dir_path)


##set values for metrics
def set_values():
    for i in cluster_configs:
            os.environ["KUBECONFIG"] = "/cluster-configs/%s" % (i)
            resources = secret_exist(i)
            for c in resources:
                if c == 'proxy-injector':
                    try:
                        end_date = check_output("kubectl -n proxy-injector get secret proxy-injector-certs -o yaml |  grep cert.pem |  sed 's/.*: //g' | base64 -d | /usr/bin/openssl x509 -enddate -noout | sed -n 's/ *notAfter= *//p'", shell='true').strip()
                        end_date_seconds = parser.parse(end_date).timestamp()
                        now_seconds = int(datetime.now().strftime("%s"))
                        days_to_expire = (end_date_seconds - now_seconds)/24/3600
                        metric_dict[f"{c.replace('-', '_')}_{i}"].set(days_to_expire)
                    except:
                        metric_dict[f"{c.replace('-', '_')}_{i}"].set(-1000)
                if c == 'vault-infra':
                    try:
                        end_date = check_output("kubectl -n vault-infra get secret vault-secrets-webhook-webhook-tls -o yaml |  grep tls.crt |  sed 's/.*: //g' | base64 -d | openssl x509 -enddate -noout | sed -n 's/ *notAfter= *//p'", shell='true').strip()
                        end_date_seconds = parser.parse(end_date).timestamp()
                        now_seconds = int(datetime.now().strftime("%s"))
                        days_to_expire = (end_date_seconds - now_seconds)/24/3600
                        metric_dict[f"{c.replace('-', '_')}_{i}"].set(days_to_expire)
                    except:
                        metric_dict[f"{c.replace('-', '_')}_{i}"].set(-1000)

###check which aap install in cluster
def secret_exist(cluster):
    os.environ["KUBECONFIG"] = "/cluster-configs/%s" % (cluster)
    try:
        secret_exist = str(check_output("kubectl get ns |  grep -E  'vault-infra|proxy-injector' |  awk '{print $1}'", shell='true')).strip('b').strip("'")
        secret_exist_lst = [x for x in secret_exist.split(r"\n") if len(x) > 2]
        print(cluster)
        print(secret_exist_lst)
        return secret_exist_lst
    except:
        return ['proxy-injector', 'vault-infra']


### define empty dict
metric_dict = {}

### create keys for dict (metrics)
def create_gauge_for_metric():
    for i in cluster_configs:
        for j in secret_exist(i):
            metric_name = f"{j.replace('-', '_')}_{i}"
            if metric_dict.get(metric_name) is None:
                metric_dict[metric_name] = Gauge(metric_name, f"days to expiry in cluster {i} - {j}")


def main():
    start_http_server(9999)

    while True:
       create_gauge_for_metric()
#       proxy_inj()
#       vault_webhook()
       set_values()
       time.sleep(86400)             ### one refresh in day 



if __name__ == "__main__":
        main()

