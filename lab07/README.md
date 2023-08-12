# Настройка underlay сети в CLOS топологии из пяти устройств Cisco Nexus 9k. (VXLAN over MP-BGP EVPN vPC version)
Цели
1) Настроить port-channel интерфейс на Client_Router до Leaf_1 и Leaf_2.
2) Создать и vPC домен на свитчах Leaf_1 и Leaf_2.
3) Настроить vPC peer keepalive интерфейсы между Leaf_1 и Leaf_2.
4) Настроить vPC peer link между Leaf_1 и Leaf_2.
5) Настроить приоритет роли главного vPC свитча для Leaf_1.
6) Настроить IP связность между vPC keepalive интерфейсами.
7) Настроить синхронизацию ARP записей между vPC свитчами.
8) Настроить вторичный IP адрес на интерфейсе Loopback 0, одинаковый для Leaf_1 и Leaf_2, для успешной vPC связи между свитчами.
9) Проверить состояние vPC связи между Leaf_1 и Leaf_2.
10) Проверить состояние port-channel клиента Client_Router.
11) Проверить приоритет ролей между Leaf_1 и Leaf_2.
12) Настроить SVI интерфейс для роутинга трафика Client_Router.
13) Настроить BGP анонсирование evpn route-type 5 маршрута сети Client_Router для Leaf_3.
14) Проверить BGP обновление с evpn route-type 5 сети Client_Router на Spine от Anycast VTEP адреса vPC домена.
15) Проверить установку BGP обновления в L3RIB Leaf_3.
16) Проверить сетевую связность между клиентом Leaf_3 и Client_Router сетью.
# Целевая схема
![map](https://github.com/Anumrak/EVPN_labs/assets/133969023/f91aa432-414d-40db-9d06-ee10fe326178)



Адресное пространство для link интерфейсов

> 172.16.0.0/24

Адресное пространство для loopback интерфейсов

> 10.0.0.0/24

Адресное пространство для L2 VPN сервиса клиента

> 192.168.3.0/24

Адресное пространство для L3 VPN сервиса клиента

> 192.168.1.0/24
> 192.168.2.0/24

Адресное пространство для vPC Peer Keepalive интерфейсов

> 192.168.255.0/31

Адресное пространство для Client_Router

> 192.168.4.0/24

Необходимые свойства Leaf роутеров:

```
feature lacp
feature vpc
```

Конфигурация клиентского роутера Client_Router:

```
interface Ethernet0/1
 switchport trunk allowed vlan 400
 switchport trunk encapsulation dot1q
 switchport mode trunk
 channel-group 1 mode active
!
interface Ethernet0/2
 switchport trunk allowed vlan 400
 switchport trunk encapsulation dot1q
 switchport mode trunk
 channel-group 1 mode active
!
interface Port-channel1
 switchport trunk allowed vlan 400
 switchport trunk encapsulation dot1q
 switchport mode trunk
!
interface Vlan400
 ip address 192.168.4.1 255.255.255.0
!
ip route 192.168.1.0 255.255.255.0 192.168.4.254
ip route 192.168.2.0 255.255.255.0 192.168.4.254
```
Настройка vPC домена:
```
Leaf_1# sh run vpc
vpc domain 1
  role priority 1
  peer-keepalive destination 192.168.255.1 source 192.168.255.0 vrf Keepalive
  ip arp synchronize
```
```
Leaf_2# sh run vpc
vpc domain 1
  peer-keepalive destination 192.168.255.0 source 192.168.255.1 vrf Keepalive
  ip arp synchronize
```
