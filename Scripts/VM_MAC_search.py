import time
import json
import requests
import math
import getpass
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from concurrent.futures import ThreadPoolExecutor
def main():
    #подсчет времени выполнения программы и вызов основной функции
    start_time = time.time()
    NIC_VM()
    print('----------- %s seconds ---------' % (time.time() - start_time))

def NIC_VM():

    sbervcd = input('Enter VCD: ')
    sbervcd = sbervcd.replace('https','').replace('http','').replace(':','').replace('/','')
    organ = input(str('Enter tenant name: '))
    MAC_find = input(str('Enter MAC VM: '))

    # #sbervcd = input('Enter VCD: ')
    # #sbervcd = "vcd.sbercloud.ru"
    # sbervcd = 'vcd-site01.dzo.sbercloud.org'
    # #sbervcd = 'vcd11.msk.sbercloud.ru'
    # #sbervcd = 'vcd12.msk.sbercloud.ru'
    # #sbervcd = 'vcd-site01.sigma.sbrf.ru'

    #функция извлечения ресурсов по всем ОЦОД для МСК и НСК с заполнением в документ excel
    def vcd_res(sbervcd, MAC_find):
        try:
            class BearerAuth(requests.auth.AuthBase):
                token = None
                def __init__(self, token):
                    self.token = token
                def __call__(self, r):
                    r.headers["authorization"] = "Bearer " + self.token
                    return r

            #учетные данные для авторизации
            v_user = input('Enter your login: ') + '@system'
            v_pass = getpass.getpass(prompt="Enter secret password:")
            #v_pass = input('Enter password: ')
            url_session = f"https://{sbervcd}/api/sessions"
            url_admin = f"https://{sbervcd}/api/admin"

            #заголовок для формирования запросов
            headers = {"Accept": "application/*+json;version=35.2,application/json;version=35.2", "Authorization": "Basic"}

            # аутентификация
            auth = requests.post(url_session, headers=headers, verify=False, auth=(v_user, v_pass))

            # Получение токена для дальнейших http запросов
            session_token = auth.headers['X-VMWARE-VCLOUD-ACCESS-TOKEN']

            #выполнение API-запроса по url
            def url_inf(url):
                return requests.get(url, headers=headers, verify=False, auth=BearerAuth(session_token)).json()
            # Получение списка организаций
            jsonData = url_inf(url_admin)
            print('--------------------------------------------------------------')
            print('VM is being searched by MAC address... Please wait')
            print()
            for org in jsonData["organizationReferences"]["organizationReference"]:
                def org_info():
                    jsonOrg = url_inf(org['href'])
                    for vcd in jsonOrg["vdcs"]['vdc']:
                        # получение всей информации касательно ВЦОД
                        jsonVDC = url_inf(vcd["href"])
                        vapp_urls = []
                        try:
                            for vApp in jsonVDC['resourceEntities']['resourceEntity']:
                                    vapp_urls.append(vApp['href'])
                            def vap_inf(url):
                                jsonvApp = url_inf(url)
                                for vm in jsonvApp['children']['vm']:
                                    for NIC in vm['section'][3]['networkConnection']:
                                        if NIC['macAddress'] == MAC_find:
                                            print('VDC:', vcd["name"])
                                            print('VM:', vm["name"])
                                            print('NIC Index:', NIC["networkConnectionIndex"])
                                            print('IP address:', NIC["ipAddress"])
                                            print('MAC address:', NIC["macAddress"])
                            executor = ThreadPoolExecutor(max_workers=10)
                            executor.map(vap_inf, vapp_urls)
                            executor.shutdown()
                        except:
                            print(vcd['name'], 'Failed (пустой)')
                            pass
                if org['name'] in organ:
                    org_info()
        except KeyError as e:
            if str(e) == "'x-vmware-vcloud-access-token'":
                print(f'Failed autentification in {sbervcd}')
            else:
                print('Another error', e)
            pass
    # вызов функции для поиска VM по MAC
    vcd_res(sbervcd, MAC_find)
    input("Press Enter to continue...")
main()
