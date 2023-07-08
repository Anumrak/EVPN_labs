# Настройка underlay сети в CLOS топологии из пяти устройств Cisco Nexus 9k. (VXLAN over eBGP EVPN L2 VPN version)
Цели
1) Включить нужные функции для evpn, vxlan и arp suppression на роутерах типа Leaf.
2) Включить нужные функции для evpn на роутерах типа Spine.
3) Настроить eBGP evpn семейство между overlay пирами Leaf и Spine.
4) Настроить VXLAN network identifier для нужного vlan.
5) Настроить evpn route distinguisher и route-target для нужного участника virtual network.
6) Настроить network virtualized interface (NVE) для инкапсуляции и терминации VXLAN трафика.
7) Проверить установление eBGP evpn соседства между Loopback адресами всех роутеров для VXLAN связности.
8) Проверить L2 связность между всеми тремя VPC клиента.
9) Проверить какие evpn маршруты стали известны на роутере Leaf и Spine.
10) Проверить как выглядит MAC таблица Leaf роутера.
11) Проверить как выглядит arp-suppression таблица.
# Целевая схема
![Снимок](https://github.com/Anumrak/EVPN_labs/assets/133969023/6207ac40-14de-454f-ac56-6adfd13a0d87)

Адресное пространство для link интерфейсов

> 172.16.0.0/24

Адресное пространство для loopback интерфейсов

> 10.0.0.0/24

Адресное пространство для L2 VPN сервиса клиента

> 192.168.0.0/24

Необходимые свойства Leaf роутера
```
nv overlay evpn
feature bgp
feature vn-segment-vlan-based
feature nv overlay
```
Для arp suppression сначала необходимо выделить место в TCAM таблице для arp записей
```
hardware access-list tcam region racl 512
hardware access-list tcam region arp-ether 256 double-wide
```
Необходимые свойства Spine роутера
```
nv overlay evpn
feature bgp
```
Конфигурация типового процесса ebgp evpn на примере роутера Leaf_1
```
router bgp 64086.59905
  router-id 10.0.0.1
  bestpath as-path multipath-relax
  reconnect-interval 5
  log-neighbor-changes
  address-family ipv4 unicast
    redistribute direct route-map rm_connected
    maximum-paths 64
  template peer Overlay
    remote-as 64086.59904
    update-source loopback0
    ebgp-multihop 2
  template peer Spines
    remote-as 64086.59904
    password 3 7b12be5a1d75eaf0
    timers 5 15
    address-family ipv4 unicast
  neighbor 10.0.0.4
    inherit peer Overlay
    description Spine_1_overlay
    address-family l2vpn evpn
      send-community
      send-community extended
  neighbor 10.0.0.5
    inherit peer Overlay
    description Spine_2_overlay
    address-family l2vpn evpn
      send-community
      send-community extended
  neighbor 172.16.0.1
    inherit peer Spines
    description Spine_1
  neighbor 172.16.0.3
    inherit peer Spines
    description Spine_2
```
Конфигурация типового процесса ebgp на примере роутера Spine_1
```
router bgp 64086.59904
  router-id 10.0.0.4
  bestpath as-path multipath-relax
  reconnect-interval 5
  log-neighbor-changes
  address-family ipv4 unicast
    redistribute direct route-map rm_connected
    maximum-paths 64
  address-family l2vpn evpn
    retain route-target all
  neighbor 10.0.0.0/30 remote-as route-map leafs
    update-source loopback0
    address-family l2vpn evpn
      send-community
      send-community extended
      route-map next-hop-unchanged out
  neighbor 172.16.0.0/28 remote-as route-map leafs
    password 3 7b12be5a1d75eaf0
    timers 5 15
    maximum-peers 3
    address-family ipv4 unicast
```
На спайн роутерах настроено две дополнительные функции для корректной обработки bgp обновлений от Leaf роутеров
1) Сохранять и передавать все принятые evpn маршруты, не смотря на то, что у Spine не настроен NVE интерфейс с совпадающими route-target для vn-segment, иначе они не установятся в BGP evpn таблицу маршрутов. Ведь пиринг у Leaf именно со Spine, а не с другими Leaf.
```
address-family l2vpn evpn
    retain route-target all
```
2) Изменить стандартное поведение между eBGP пирами (Spine и Leaf) на изменение next-hop атрибута, иначе обновление от Leaf роутера, транслированное от Spine, будет иметь next-hop Loopback адреса Spine роутера. Таким образом VXLAN туннель будет пытаться установить соединение именно со Spine, что закончится неудачей, ведь туннели нужны сквозные, только от Leaf до Leaf для успешной терминации VXLAN трафика.
```
route-map next-hop-unchanged permit 10
  set ip next-hop unchanged
```
```
neighbor 10.0.0.0/30 remote-as route-map leafs
    update-source loopback0
    address-family l2vpn evpn
      send-community
      send-community extended
      route-map next-hop-unchanged out
```
Создание vlan и добавление ему VXLAN Network Identifier (VNI)
```
vlan 100
  vn-segment 10100
```
Создание evpn route distinguisher и route-target для нужного VNI
```
evpn
  vni 10100 l2
    rd 10.0.0.1:100
    route-target import 10100:100
    route-target export 10100:100
```
Создание network virtualized interface (NVE) для инкапсуляции и терминации VXLAN трафика
```
interface nve1
  no shutdown
  host-reachability protocol bgp
  source-interface loopback0
  member vni 10100
    suppress-arp
    ingress-replication protocol bgp
```

### Проверка установления eBGP evpn соседства между Loopback адресами всех роутеров для VXLAN связности
```
Leaf_1# sh bgp l2vpn evpn summary
BGP summary information for VRF default, address family L2VPN EVPN
BGP router identifier 10.0.0.1, local AS number 4200000001
BGP table version is 315, L2VPN EVPN config peers 2, capable peers 2
15 network entries and 21 paths using 3660 bytes of memory
BGP attribute entries [8/1376], BGP AS path entries [2/20]
BGP community entries [0/0], BGP clusterlist entries [0/0]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
10.0.0.4        4 4200000000
                           1590    1545      315    0    0 08:51:57 6
10.0.0.5        4 4200000000
                           1579    1539      315    0    0 08:51:42 6
```
```
Leaf_2# sh bgp l2vpn evpn summary
BGP summary information for VRF default, address family L2VPN EVPN
BGP router identifier 10.0.0.2, local AS number 4200000002
BGP table version is 248, L2VPN EVPN config peers 2, capable peers 2
15 network entries and 21 paths using 3660 bytes of memory
BGP attribute entries [8/1376], BGP AS path entries [2/20]
BGP community entries [0/0], BGP clusterlist entries [0/0]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
10.0.0.4        4 4200000000
                           1535    1493      248    0    0 08:51:57 6
10.0.0.5        4 4200000000
                           1533    1493      248    0    0 08:51:47 6
```
```
Leaf_3# sh bgp l2vpn evpn summary
BGP summary information for VRF default, address family L2VPN EVPN
BGP router identifier 10.0.0.3, local AS number 4200000003
BGP table version is 287, L2VPN EVPN config peers 2, capable peers 2
15 network entries and 21 paths using 3660 bytes of memory
BGP attribute entries [8/1376], BGP AS path entries [2/20]
BGP community entries [0/0], BGP clusterlist entries [0/0]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
10.0.0.4        4 4200000000
                           1503    1441      287    0    0 08:51:57 6
10.0.0.5        4 4200000000
                           1494    1446      287    0    0 08:51:49 6
```
```
Spine_1# sh bgp l2vpn evpn summary
BGP summary information for VRF default, address family L2VPN EVPN
BGP router identifier 10.0.0.4, local AS number 4200000000
BGP table version is 365, L2VPN EVPN config peers 4, capable peers 3
9 network entries and 9 paths using 2196 bytes of memory
BGP attribute entries [6/1032], BGP AS path entries [3/18]
BGP community entries [0/0], BGP clusterlist entries [0/0]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
10.0.0.1        4 4200000001
                           1573    1543      365    0    0 08:52:06 3
10.0.0.2        4 4200000002
                           1510    1498      365    0    0 08:52:03 3
10.0.0.3        4 4200000003
                           1441    1445      365    0    0 08:52:00 3
```
```
Spine_2# sh bgp l2vpn evpn summary
BGP summary information for VRF default, address family L2VPN EVPN
BGP router identifier 10.0.0.5, local AS number 4200000000
BGP table version is 385, L2VPN EVPN config peers 4, capable peers 3
9 network entries and 9 paths using 2196 bytes of memory
BGP attribute entries [6/1032], BGP AS path entries [3/18]
BGP community entries [0/0], BGP clusterlist entries [0/0]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
10.0.0.1        4 4200000001
                           1493    1476      385    0    0 08:51:56 3
10.0.0.2        4 4200000002
                           1512    1499      385    0    0 08:51:57 3
10.0.0.3        4 4200000003
                           1445    1440      385    0    0 08:51:56 3
```
### Проверка L2 связности между всеми тремя VPC клиента
```
VPCS> ping 192.168.0.2

84 bytes from 192.168.0.2 icmp_seq=1 ttl=64 time=47.706 ms
84 bytes from 192.168.0.2 icmp_seq=2 ttl=64 time=24.557 ms
84 bytes from 192.168.0.2 icmp_seq=3 ttl=64 time=19.693 ms
84 bytes from 192.168.0.2 icmp_seq=4 ttl=64 time=27.038 ms
84 bytes from 192.168.0.2 icmp_seq=5 ttl=64 time=25.593 ms

VPCS> ping 192.168.0.3

84 bytes from 192.168.0.3 icmp_seq=1 ttl=64 time=33.583 ms
84 bytes from 192.168.0.3 icmp_seq=2 ttl=64 time=18.492 ms
84 bytes from 192.168.0.3 icmp_seq=3 ttl=64 time=23.969 ms
84 bytes from 192.168.0.3 icmp_seq=4 ttl=64 time=15.520 ms
84 bytes from 192.168.0.3 icmp_seq=5 ttl=64 time=97.714 ms

VPCS> sh arp

00:50:79:66:68:07  192.168.0.2 expires in 104 seconds
00:50:79:66:68:08  192.168.0.3 expires in 111 seconds
```
### Проверка evpn маршрутов на роутерах Leaf_1 и Spine_1 как примерных
```
Leaf_1# sh bgp l2vpn evpn
BGP routing table information for VRF default, address family L2VPN EVPN
BGP table version is 315, Local Router ID is 10.0.0.1
Status: s-suppressed, x-deleted, S-stale, d-dampened, h-history, *-valid, >-best
Path type: i-internal, e-external, c-confed, l-local, a-aggregate, r-redist, I-injected
Origin codes: i - IGP, e - EGP, ? - incomplete, | - multipath, & - backup, 2 - best2

   Network            Next Hop            Metric     LocPrf     Weight Path
Route Distinguisher: 10.0.0.1:100    (L2VNI 10100)
*>l[2]:[0]:[0]:[48]:[0050.7966.6806]:[0]:[0.0.0.0]/216
                      10.0.0.1                          100      32768 i
*>e[2]:[0]:[0]:[48]:[0050.7966.6807]:[0]:[0.0.0.0]/216
                      10.0.0.2                                       0 4200000000 4200000002 i
*>e[2]:[0]:[0]:[48]:[0050.7966.6808]:[0]:[0.0.0.0]/216
                      10.0.0.3                                       0 4200000000 4200000003 i
*>l[2]:[0]:[0]:[48]:[0050.7966.6806]:[32]:[192.168.0.1]/248
                      10.0.0.1                          100      32768 i
*>e[2]:[0]:[0]:[48]:[0050.7966.6807]:[32]:[192.168.0.2]/248
                      10.0.0.2                                       0 4200000000 4200000002 i
*>e[2]:[0]:[0]:[48]:[0050.7966.6808]:[32]:[192.168.0.3]/248
                      10.0.0.3                                       0 4200000000 4200000003 i
*>l[3]:[0]:[32]:[10.0.0.1]/88
                      10.0.0.1                          100      32768 i
*>e[3]:[0]:[32]:[10.0.0.2]/88
                      10.0.0.2                                       0 4200000000 4200000002 i
*>e[3]:[0]:[32]:[10.0.0.3]/88
                      10.0.0.3                                       0 4200000000 4200000003 i

Route Distinguisher: 10.0.0.2:100
*>e[2]:[0]:[0]:[48]:[0050.7966.6807]:[0]:[0.0.0.0]/216
                      10.0.0.2                                       0 4200000000 4200000002 i
* e                   10.0.0.2                                       0 4200000000 4200000002 i
* e[2]:[0]:[0]:[48]:[0050.7966.6807]:[32]:[192.168.0.2]/248
                      10.0.0.2                                       0 4200000000 4200000002 i
*>e                   10.0.0.2                                       0 4200000000 4200000002 i
* e[3]:[0]:[32]:[10.0.0.2]/88
                      10.0.0.2                                       0 4200000000 4200000002 i
*>e                   10.0.0.2                                       0 4200000000 4200000002 i

Route Distinguisher: 10.0.0.3:100
* e[2]:[0]:[0]:[48]:[0050.7966.6808]:[0]:[0.0.0.0]/216
                      10.0.0.3                                       0 4200000000 4200000003 i
*>e                   10.0.0.3                                       0 4200000000 4200000003 i
* e[2]:[0]:[0]:[48]:[0050.7966.6808]:[32]:[192.168.0.3]/248
                      10.0.0.3                                       0 4200000000 4200000003 i
*>e                   10.0.0.3                                       0 4200000000 4200000003 i
* e[3]:[0]:[32]:[10.0.0.3]/88
                      10.0.0.3                                       0 4200000000 4200000003 i
*>e                   10.0.0.3                                       0 4200000000 4200000003 i
```
```
Spine_1# sh bgp l2vpn evpn
BGP routing table information for VRF default, address family L2VPN EVPN
BGP table version is 365, Local Router ID is 10.0.0.4
Status: s-suppressed, x-deleted, S-stale, d-dampened, h-history, *-valid, >-best
Path type: i-internal, e-external, c-confed, l-local, a-aggregate, r-redist, I-injected
Origin codes: i - IGP, e - EGP, ? - incomplete, | - multipath, & - backup, 2 - best2

   Network            Next Hop            Metric     LocPrf     Weight Path
Route Distinguisher: 10.0.0.1:100
*>e[2]:[0]:[0]:[48]:[0050.7966.6806]:[0]:[0.0.0.0]/216
                      10.0.0.1                                       0 4200000001 i
*>e[2]:[0]:[0]:[48]:[0050.7966.6806]:[32]:[192.168.0.1]/248
                      10.0.0.1                                       0 4200000001 i
*>e[3]:[0]:[32]:[10.0.0.1]/88
                      10.0.0.1                                       0 4200000001 i

Route Distinguisher: 10.0.0.2:100
*>e[2]:[0]:[0]:[48]:[0050.7966.6807]:[0]:[0.0.0.0]/216
                      10.0.0.2                                       0 4200000002 i
*>e[2]:[0]:[0]:[48]:[0050.7966.6807]:[32]:[192.168.0.2]/248
                      10.0.0.2                                       0 4200000002 i
*>e[3]:[0]:[32]:[10.0.0.2]/88
                      10.0.0.2                                       0 4200000002 i

Route Distinguisher: 10.0.0.3:100
*>e[2]:[0]:[0]:[48]:[0050.7966.6808]:[0]:[0.0.0.0]/216
                      10.0.0.3                                       0 4200000003 i
*>e[2]:[0]:[0]:[48]:[0050.7966.6808]:[32]:[192.168.0.3]/248
                      10.0.0.3                                       0 4200000003 i
*>e[3]:[0]:[32]:[10.0.0.3]/88
                      10.0.0.3                                       0 4200000003 i
```
Видно, что Leaf получил по шесть маршрутов от каждого из Spine, а Spine получил по три маршрута от каждого Leaf. Все верно.

Первый маршрут, например от Route Distinguisher: 10.0.0.2:100
```
*>e[2]:[0]:[0]:[48]:[0050.7966.6807]:[0]:[0.0.0.0]/216
```
является маршрутом второго типа mac-ip, который сообщает MAC адрес, выученный от data plane во vlan id 100.
Второй маршрут, также типа mac-ip, но уже несет в себе и IP адрес хоста во vlan id 100, но выучен он уже благодаря функционалу arp suppression
включенном на nve интерфейсе в начале
```
* e[2]:[0]:[0]:[48]:[0050.7966.6807]:[32]:[192.168.0.2]/248
```
```
interface nve1
  no shutdown
  host-reachability protocol bgp
  source-interface loopback0
  member vni 10100
    suppress-arp
    ingress-replication protocol bgp
```
Последний маршрут, третьего типа Inclusive Multicast Ethernet Tag Route, или сокращенно imet, предназначен для рассылки broadcast, unknown unicast и multicast между VTEP адресами поверх VXLAN туннеля. Собственно, сначала используется именно этот тип маршрута, а потом уже маршрут второго типа.
```
* e[3]:[0]:[32]:[10.0.0.2]/88
```
### Проверка MAC таблицы Leaf роутера
```
Leaf_1# sh mac address-table
Legend:
        * - primary entry, G - Gateway MAC, (R) - Routed MAC, O - Overlay MAC
        age - seconds since last seen,+ - primary entry using vPC Peer-Link,
        (T) - True, (F) - False, C - ControlPlane MAC, ~ - vsan
   VLAN     MAC Address      Type      age     Secure NTFY Ports
---------+-----------------+--------+---------+------+----+------------------
*  100     0050.7966.6806   dynamic  0         F      F    Eth1/3
C  100     0050.7966.6807   dynamic  0         F      F    nve1(10.0.0.2)
C  100     0050.7966.6808   dynamic  0         F      F    nve1(10.0.0.3)
G    -     5001.0000.1b08   static   -         F      F    sup-eth1(R)
```
Флаг "C" указывает на то, что мак адрес был выучен из Control Plane, в нашем случае это eBGP evpn. Интерфейс, за которым он был выучен наш NVE интерфейс и адрес соответствующего VTEP.
### Проверка arp suppression таблицы
```
Leaf_1# sh ip arp suppression-cache detail

Flags: + - Adjacencies synced via CFSoE
       L - Local Adjacency
       R - Remote Adjacency
       L2 - Learnt over L2 interface
       PS - Added via L2RIB, Peer Sync
       RO - Dervied from L2RIB Peer Sync Entry

Ip Address      Age      Mac Address    Vlan Physical-ifindex    Flags    Remote Vtep Addrs

192.168.0.1     00:27:04 0050.7966.6806  100 Ethernet1/3         L2
192.168.0.3     00:40:38 0050.7966.6808  100 (null)              R        10.0.0.3
192.168.0.2     00:43:12 0050.7966.6807  100 (null)              R        10.0.0.2
```
Тут также видно, что удаленные ARP записи были выучены от VTEP адресов Leaf_2 и Leaf_3.

На последок прикладываю вид заголовка трафика с ICMP пакетом, снятым с интерфейса Ethernet 1/1 роутера Leaf_1 при запросе от его VPC клиента.
![vxlan icmp](https://github.com/Anumrak/EVPN_labs/assets/133969023/8c114b96-2315-4dd4-95fd-e6ddcfb3353f)
