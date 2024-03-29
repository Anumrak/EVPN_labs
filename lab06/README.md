# Настройка underlay сети в CLOS топологии из пяти устройств Cisco Nexus 9k. (VXLAN over MP-BGP EVPN L3 VPN version)
Цели
1) Настроить L2VNI связность между всеми участниками всех групп.
2) Настроить виртуальный шлюз (Host Mobility Manager) для участников групп HQ и Prod.
3) Настроить SVI для групп, которым потребуется локальная и удаленная маршрутизация и настроить на SVI anycast-gateway. 
4) Создать и настроить транзитный vrf для форвардинга трафика между подсетями.
5) Создать и настроить служебный SVI для форвардинга пакетов между VTEP.
6) Настроить NVE интерфейс для L2 и L3 VNI.
7) Дополнить секцию BGP для отправки обновлений с данными о vrf на Spine роутеры.
8) Дополнить секцию BGP Leaf_1 для отправки обновлений с маршрутом по умолчанию для Leaf_2 и Leaf_3.
9) Проверить наличие обновлений на Spine_1.
10) Проверить на Leaf_2 как примерном импорт route-type 2 и 5 в L3RIB.
11) Проверить сетевую связность между всеми группами.
# Целевая схема
![map](https://github.com/Anumrak/EVPN_labs/assets/133969023/f91aa432-414d-40db-9d06-ee10fe326178)

Группам HQ и Prod необходимо организовать связь между всеми их участниками как по L2, так и по L3 через фабрику. Группе Dev нужна связь только по L2.
Также нужно создать непрерывную arp связь до шлюза всем участникам групп HQ и Prod, в случае миграций ВМ клиента на другие Leaf.
Связь нужно организовать так, чтобы весь широковещательный трафик между группами HQ и Prod доходил только до своего ближайшего Leaf свитча.
Если хост другой группы расположен на своем Leaf, используем локальный шлюз для роутинга между vrf.
Если хост другой группы расположен на удаленном Leaf, используем L3VNI форвардинг.

Адресное пространство для link интерфейсов

> 172.16.0.0/24

Адресное пространство для loopback интерфейсов

> 10.0.0.0/24

Адресное пространство для L2 VPN сервиса клиента

> 192.168.3.0/24

Адресное пространство для L3 VPN сервиса клиента

> 192.168.1.0/24
> 192.168.2.0/24

Необходимые свойства Leaf роутера
```
nv overlay evpn
feature fabric forwarding
```
В lab05 мы уже разбирали механику L2VNI связи между Leaf свитчами. Для группы Dev этого будет достаточно.

RT MAC-IP для экспорта устанавливает mac/arp/hmm route из L2RIB в L2VPN EVPN route-type 2 маршрут.

RT MAC-IP для импорта устанавливает L2VPN EVPN route-type 2 маршруты в L2RIB.
```
evpn
  vni 10100 l2
    rd 10.0.0.1:100
    route-target import 10100:100
    route-target export 10100:100
  vni 10200 l2
    rd 10.0.0.1:200
    route-target import 10200:200
    route-target export 10200:200
  vni 10300 l2
    rd 10.0.0.1:300
    route-target import 10300:300
    route-target export 10300:300
```
Но дизайн расположения ресурсов клиента в группах HQ и Prod вынуждает нас использовать параллельные способы сетевой связности, как по L2VNI, так уже и по L3,
так как за каждым Leaf расположен каждый участник каждой группы.

Для мобильности хоста между одинаковыми шлюзами разных Leaf, хост должен иметь один и тот же мак адрес шлюза в своей ARP записи. Он будет виртуальным для каждого шлюза на всех Leaf.
Для этого нужно указать в глобальной конфигурации свитча
```
fabric forwarding anycast-gateway-mac 0000.0000.7777
```
MAC адрес взят для примера, он может быть любым. Главное, чтобы он был одинаковым.

Конфигурация клиентского SVI на примере Leaf_1
```
interface Vlan100
  description VPCS_1_GW
  no shutdown
  vrf member Leafs_L3VNI
  ip address 192.168.1.254/24
  fabric forwarding mode anycast-gateway
```
Как только клиент отправит ARP request в сеть, его перехватит Host Mobility Manager (HMM) и распределит эту информацию одновременно в L2RIB и L3RIB.
```
Leaf_1# sh fabric forwarding ip local-host-db vrf Leafs_L3VNI 192.168.1.1/32
HMM routing table information for VRF Leafs_L3VNI, address family IPv4
HMM routing table entry for 192.168.1.1/32
Hosts: (1 available)

  Host type: Local(Flags: 0x420201), in Rib
  mac: 0050.7966.6806, svi: Vlan100, bd: 100, phy_intf: Ethernet1/11
```
```
Leaf_1# sh ip route 192.168.1.1/32 vrf Leafs_L3VNI
IP Route Table for VRF "Leafs_L3VNI"
'*' denotes best ucast next-hop
'**' denotes best mcast next-hop
'[x/y]' denotes [preference/metric]
'%<string>' in via output denotes VRF <string>

192.168.1.1/32, ubest/mbest: 1/0, attached
    *via 192.168.1.1, Vlan100, [190/0], 00:24:53, hmm
```
Маршрут известный от "hmm" означает, что он импортировался в L3RIB от Host Mobility Manager при включенном и настроенном функционале:
```
feature fabric forwarding
fabric forwarding anycast-gateway-mac 0000.0000.7777
fabric forwarding mode anycast-gateway
```
Конфигурация L3VNI vrf на примере Leaf_1.

RT IP-VRF для экспорта устанавливает IPv4 префиксы в L2VPN EVPN route-type 5 маршрут.

RT IP-VRF для импорта устанавливает L2VPN EVPN route-type 5 маршруты в L3RIB.
```
vrf context Leafs_L3VNI
  vni 7777
  ip route 0.0.0.0/0 Null0 1
  rd 10.0.0.1:7777
  address-family ipv4 unicast
    route-target import 4200000001:7777 evpn
    route-target import 4200000002:7777 evpn
    route-target import 4200000003:7777 evpn
    route-target export 4200000001:7777 evpn
```
RT IP-VRF добавляется к RT MAC-IP для отправления обновления с маршрутом типа route-type 2. Также добавляется такое расширенное community как Router MAC.
С его помощью мы сообщаем настоящий MAC адрес шлюза, чтобы с другой стороны хост смог отправить нам ответ. Конечно перед ответом, другой Leaf должен отправить нам точно такое же зеркальное обновление. В таком обновлении будет присутствовать оба VNI. В route-type 2 экспортируются оба RT: из L2RIB и L3RIB. Это нужно для связи с этим хостом как с помощью L2VNI, так и с помощью L3VNI на другой стороне.
![L3VNI 192 168 1 1_painted](https://github.com/Anumrak/EVPN_labs/assets/133969023/8ea3b1cb-8737-4a28-a055-6a6cb58a2c93)


На Leaf_2 и Leaf_3 RD и RT настроены зеркально симметрично. Статический маршрут есть только у Leaf_1.

Конфигурация служебного SVI на примере Leaf_1. На интерфейсе нет IP адреса.
С помощью команды ip/ipv6 forward он служит только для форвардинга трафика через VXLAN vrf VNI
```
vlan 777
  vn-segment 7777

interface Vlan777
  description Leafs_L3VNI
  no shutdown
  vrf member Leafs_L3VNI
  no ip redirects
  ip forward
  ipv6 forward
  no ipv6 redirects
```
Конфигурация NVE интерфейса для L2 и L3 VNI
```
interface nve1
  no shutdown
  host-reachability protocol bgp
  source-interface loopback0
  member vni 7777 associate-vrf
  member vni 10100
    suppress-arp
    ingress-replication protocol bgp
  member vni 10200
    suppress-arp
    ingress-replication protocol bgp
  member vni 10300
    suppress-arp
    ingress-replication protocol bgp
```
```
Leaf_1# sh nve vni
Codes: CP - Control Plane        DP - Data Plane
       UC - Unconfigured         SA - Suppress ARP
       SU - Suppress Unknown Unicast
       Xconn - Crossconnect
       MS-IR - Multisite Ingress Replication

Interface VNI      Multicast-group   State Mode Type [BD/VRF]      Flags
--------- -------- ----------------- ----- ---- ------------------ -----
nve1      7777     n/a               Up    CP   L3 [Leafs_L3VNI]
nve1      10100    UnicastBGP        Up    CP   L2 [100]           SA
nve1      10200    UnicastBGP        Up    CP   L2 [200]           SA
nve1      10300    UnicastBGP        Up    CP   L2 [300]           SA
```
Конфигурация процесса ebgp evpn на примере роутера Leaf_1. В секции vrf распространяется маршрут 0.0.0.0/0 как route-type 5, так как vrf связан с L3VNI.
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
    address-family l2vpn evpn
      send-community
      send-community extended
  template peer Spines
    remote-as 64086.59904
    password 3 7b12be5a1d75eaf0
    timers 5 15
    address-family ipv4 unicast
  neighbor 10.0.0.4
    inherit peer Overlay
    description Spine_1_overlay
  neighbor 10.0.0.5
    inherit peer Overlay
    description Spine_2_overlay
  neighbor 172.16.0.1
    inherit peer Spines
    description Spine_1
  neighbor 172.16.0.3
    inherit peer Spines
    description Spine_2
  vrf Leafs_L3VNI
    address-family ipv4 unicast
      network 0.0.0.0/0
```
Конфигурация Spine роутеров не меняется, так как все что им нужно, это пересылка обновлений от Leaf к Leaf все в тех же расширенных community
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
### Проверка наличия обновлений на Spine_1
```
Spine_1# sh bgp l2vpn evpn
BGP routing table information for VRF default, address family L2VPN EVPN
BGP table version is 211, Local Router ID is 10.0.0.4
Status: s-suppressed, x-deleted, S-stale, d-dampened, h-history, *-valid, >-best
Path type: i-internal, e-external, c-confed, l-local, a-aggregate, r-redist, I-injected
Origin codes: i - IGP, e - EGP, ? - incomplete, | - multipath, & - backup, 2 - best2

   Network            Next Hop            Metric     LocPrf     Weight Path
Route Distinguisher: 10.0.0.1:100
*>e[2]:[0]:[0]:[48]:[0050.7966.6806]:[0]:[0.0.0.0]/216
                      10.0.0.1                                       0 4200000001 i
*>e[2]:[0]:[0]:[48]:[0200.0000.0a0a]:[0]:[0.0.0.0]/216
                      10.0.0.1                                       0 4200000001 i
*>e[2]:[0]:[0]:[48]:[0050.7966.6806]:[32]:[192.168.1.1]/272
                      10.0.0.1                                       0 4200000001 i
*>e[3]:[0]:[32]:[10.0.0.1]/88
                      10.0.0.1                                       0 4200000001 i

Route Distinguisher: 10.0.0.1:200
*>e[2]:[0]:[0]:[48]:[0050.7966.6809]:[0]:[0.0.0.0]/216
                      10.0.0.1                                       0 4200000001 i
*>e[2]:[0]:[0]:[48]:[0200.0000.0a0a]:[0]:[0.0.0.0]/216
                      10.0.0.1                                       0 4200000001 i
*>e[2]:[0]:[0]:[48]:[0050.7966.6809]:[32]:[192.168.2.1]/272
                      10.0.0.1                                       0 4200000001 i
*>e[3]:[0]:[32]:[10.0.0.1]/88
                      10.0.0.1                                       0 4200000001 i

Route Distinguisher: 10.0.0.1:300
*>e[2]:[0]:[0]:[48]:[0050.7966.680c]:[0]:[0.0.0.0]/216
                      10.0.0.1                                       0 4200000001 i
*>e[2]:[0]:[0]:[48]:[0050.7966.680c]:[32]:[192.168.3.1]/248
                      10.0.0.1                                       0 4200000001 i
*>e[3]:[0]:[32]:[10.0.0.1]/88
                      10.0.0.1                                       0 4200000001 i

Route Distinguisher: 10.0.0.1:7777
*>e[5]:[0]:[0]:[0]:[0.0.0.0]/224
                      10.0.0.1                                       0 4200000001 i

Route Distinguisher: 10.0.0.2:100
*>e[2]:[0]:[0]:[48]:[0050.7966.6807]:[0]:[0.0.0.0]/216
                      10.0.0.2                                       0 4200000002 i
*>e[2]:[0]:[0]:[48]:[0050.7966.6807]:[32]:[192.168.1.2]/272
                      10.0.0.2                                       0 4200000002 i
*>e[3]:[0]:[32]:[10.0.0.2]/88
                      10.0.0.2                                       0 4200000002 i

Route Distinguisher: 10.0.0.2:200
*>e[2]:[0]:[0]:[48]:[0050.7966.680a]:[0]:[0.0.0.0]/216
                      10.0.0.2                                       0 4200000002 i
*>e[2]:[0]:[0]:[48]:[0050.7966.680a]:[32]:[192.168.2.2]/272
                      10.0.0.2                                       0 4200000002 i
*>e[3]:[0]:[32]:[10.0.0.2]/88
                      10.0.0.2                                       0 4200000002 i

Route Distinguisher: 10.0.0.2:300
*>e[2]:[0]:[0]:[48]:[0050.7966.680d]:[0]:[0.0.0.0]/216
                      10.0.0.2                                       0 4200000002 i
*>e[2]:[0]:[0]:[48]:[0050.7966.680d]:[32]:[192.168.3.2]/248
                      10.0.0.2                                       0 4200000002 i
*>e[3]:[0]:[32]:[10.0.0.2]/88
                      10.0.0.2                                       0 4200000002 i

Route Distinguisher: 10.0.0.3:100
*>e[2]:[0]:[0]:[48]:[0050.7966.6808]:[0]:[0.0.0.0]/216
                      10.0.0.3                                       0 4200000003 i
*>e[2]:[0]:[0]:[48]:[0050.7966.6808]:[32]:[192.168.1.3]/272
                      10.0.0.3                                       0 4200000003 i
*>e[3]:[0]:[32]:[10.0.0.3]/88
                      10.0.0.3                                       0 4200000003 i

Route Distinguisher: 10.0.0.3:200
*>e[2]:[0]:[0]:[48]:[0050.7966.680b]:[0]:[0.0.0.0]/216
                      10.0.0.3                                       0 4200000003 i
*>e[2]:[0]:[0]:[48]:[0050.7966.680b]:[32]:[192.168.2.3]/272
                      10.0.0.3                                       0 4200000003 i
*>e[3]:[0]:[32]:[10.0.0.3]/88
                      10.0.0.3                                       0 4200000003 i

Route Distinguisher: 10.0.0.3:300
*>e[2]:[0]:[0]:[48]:[0050.7966.680e]:[0]:[0.0.0.0]/216
                      10.0.0.3                                       0 4200000003 i
*>e[2]:[0]:[0]:[48]:[0050.7966.680e]:[32]:[192.168.3.3]/248
                      10.0.0.3                                       0 4200000003 i
*>e[3]:[0]:[32]:[10.0.0.3]/88
                      10.0.0.3                                       0 4200000003 i
```
Вы могли заметить, что есть разница через слэш в EVPN маршрутах с RD 10.0.0.1:100 и 10.0.0.1:300.
/272, /248 это количество бит информации в поле NLRI (Network Layer Reachability Information) атрибута пути MP_REACH_NLRI BGP обновления, когда нужно сообщить о доступности новой маршрутной информации. Высчитывается следующими полями: RD - 8 байт (октетов), ESI - 10 байт, MAC адрес - 6 байт, IPv4 адрес - 4 байта, VNI - 3 байта.
На примере этого дампа можно увидеть, что разница только в количестве VNI - 3 байта. Но в route-type 2 маршруте без IP адреса мы вычитаем IPv4 поле и получаем 216 бит.
![L3VNI 192 168 1 1_bits](https://github.com/Anumrak/EVPN_labs/assets/133969023/ef69a114-6d3b-43b6-bdf2-b4531fa06849)

### Проверка импорта route-type 2 и 5 EVPN маршрутов в L2RIB и L3RIB Leaf_2
```
Leaf_2# sh bgp l2vpn evpn 192.168.1.1
BGP routing table information for VRF default, address family L2VPN EVPN
Route Distinguisher: 10.0.0.1:100
BGP routing table entry for [2]:[0]:[0]:[48]:[0050.7966.6806]:[32]:[192.168.1.1]/272, version 9422
Paths: (2 available, best #2)
Flags: (0x000202) (high32 00000000) on xmit-list, is not in l2rib/evpn, is not in HW

  Path type: external, path is valid, not best reason: newer EBGP path, no labeled nexthop
  AS-Path: 4200000000 4200000001 , path sourced external to AS
    10.0.0.1 (metric 0) from 10.0.0.5 (10.0.0.5)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 10100 7777
      Extcommunity: RT:10100:100 RT:4200000001:7777 ENCAP:8 Router MAC:5001.0000.1b08

  Advertised path-id 1
  Path type: external, path is valid, is best path, no labeled nexthop
             Imported to 3 destination(s)
             Imported paths list: Leafs_L3VNI L3-7777 L2-10100
  AS-Path: 4200000000 4200000001 , path sourced external to AS
    10.0.0.1 (metric 0) from 10.0.0.4 (10.0.0.4)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 10100 7777
      Extcommunity: RT:10100:100 RT:4200000001:7777 ENCAP:8 Router MAC:5001.0000.1b08

  Path-id 1 not advertised to any peer

Route Distinguisher: 10.0.0.2:100    (L2VNI 10100)
BGP routing table entry for [2]:[0]:[0]:[48]:[0050.7966.6806]:[32]:[192.168.1.1]/272, version 9420
Paths: (1 available, best #1)
Flags: (0x000212) (high32 00000000) on xmit-list, is in l2rib/evpn, is not in HW

  Advertised path-id 1
  Path type: external, path is valid, is best path, no labeled nexthop, in rib
             Imported from 10.0.0.1:100:[2]:[0]:[0]:[48]:[0050.7966.6806]:[32]:[192.168.1.1]/272
  AS-Path: 4200000000 4200000001 , path sourced external to AS
    10.0.0.1 (metric 0) from 10.0.0.4 (10.0.0.4)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 10100 7777
      Extcommunity: RT:10100:100 RT:4200000001:7777 ENCAP:8 Router MAC:5001.0000.1b08

  Path-id 1 not advertised to any peer

Route Distinguisher: 10.0.0.2:7777    (L3VNI 7777)
BGP routing table entry for [2]:[0]:[0]:[48]:[0050.7966.6806]:[32]:[192.168.1.1]/272, version 9421
Paths: (1 available, best #1)
Flags: (0x000202) (high32 00000000) on xmit-list, is not in l2rib/evpn, is not in HW

  Advertised path-id 1
  Path type: external, path is valid, is best path, no labeled nexthop
             Imported from 10.0.0.1:100:[2]:[0]:[0]:[48]:[0050.7966.6806]:[32]:[192.168.1.1]/272
  AS-Path: 4200000000 4200000001 , path sourced external to AS
    10.0.0.1 (metric 0) from 10.0.0.4 (10.0.0.4)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 10100 7777
      Extcommunity: RT:10100:100 RT:4200000001:7777 ENCAP:8 Router MAC:5001.0000.1b08

  Path-id 1 not advertised to any peer
```
```
Leaf_2# sh ip route 192.168.1.1 vrf Leafs_L3VNI
IP Route Table for VRF "Leafs_L3VNI"
'*' denotes best ucast next-hop
'**' denotes best mcast next-hop
'[x/y]' denotes [preference/metric]
'%<string>' in via output denotes VRF <string>

192.168.1.1/32, ubest/mbest: 1/0
    *via 10.0.0.1%default, [20/0], 00:04:44, bgp-64086.59906, external, tag 4200000000, segid: 7777
tunnelid: 0xa000001 encap: VXLAN
```
```
Leaf_2# sh ip arp suppression-cache detail

Flags: + - Adjacencies synced via CFSoE
       L - Local Adjacency
       R - Remote Adjacency
       L2 - Learnt over L2 interface
       PS - Added via L2RIB, Peer Sync
       RO - Dervied from L2RIB Peer Sync Entry

Ip Address      Age      Mac Address    Vlan Physical-ifindex    Flags    Remote Vtep Addrs

192.168.1.2     00:16:23 0050.7966.6807  100 Ethernet1/11        L
192.168.1.3     14:38:57 0050.7966.6808  100 (null)              R        10.0.0.3
192.168.1.1     14:48:14 0050.7966.6806  100 (null)              R        10.0.0.1
192.168.2.2     00:16:23 0050.7966.680a  200 Ethernet1/12        L
192.168.2.3     14:38:34 0050.7966.680b  200 (null)              R        10.0.0.3
192.168.2.1     14:38:51 0050.7966.6809  200 (null)              R        10.0.0.1
```
```
Leaf_2# sh bgp l2vpn evpn 0.0.0.0
BGP routing table information for VRF default, address family L2VPN EVPN
Route Distinguisher: 10.0.0.1:7777
BGP routing table entry for [5]:[0]:[0]:[0]:[0.0.0.0]/224, version 9401
Paths: (2 available, best #1)
Flags: (0x000002) (high32 00000000) on xmit-list, is not in l2rib/evpn, is not in HW

  Advertised path-id 1
  Path type: external, path is valid, is best path, no labeled nexthop
             Imported to 2 destination(s)
             Imported paths list: Leafs_L3VNI L3-7777
  Gateway IP: 0.0.0.0
  AS-Path: 4200000000 4200000001 , path sourced external to AS
    10.0.0.1 (metric 0) from 10.0.0.4 (10.0.0.4)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 7777
      Extcommunity: RT:4200000001:7777 ENCAP:8 Router MAC:5001.0000.1b08

  Path type: external, path is valid, not best reason: Router Id, no labeled nexthop
  Gateway IP: 0.0.0.0
  AS-Path: 4200000000 4200000001 , path sourced external to AS
    10.0.0.1 (metric 0) from 10.0.0.5 (10.0.0.5)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 7777
      Extcommunity: RT:4200000001:7777 ENCAP:8 Router MAC:5001.0000.1b08

  Path-id 1 not advertised to any peer

Route Distinguisher: 10.0.0.2:7777    (L3VNI 7777)
BGP routing table entry for [5]:[0]:[0]:[0]:[0.0.0.0]/224, version 9402
Paths: (1 available, best #1)
Flags: (0x000002) (high32 00000000) on xmit-list, is not in l2rib/evpn, is not in HW

  Advertised path-id 1
  Path type: external, path is valid, is best path, no labeled nexthop
             Imported from 10.0.0.1:7777:[5]:[0]:[0]:[0]:[0.0.0.0]/224
  Gateway IP: 0.0.0.0
  AS-Path: 4200000000 4200000001 , path sourced external to AS
    10.0.0.1 (metric 0) from 10.0.0.4 (10.0.0.4)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 7777
      Extcommunity: RT:4200000001:7777 ENCAP:8 Router MAC:5001.0000.1b08

  Path-id 1 not advertised to any peer
```
Так выглядит NLRI с EVPN route-type 5 в дампе
![route-type 5 default route](https://github.com/Anumrak/EVPN_labs/assets/133969023/48a4f078-51f3-416f-9229-fd3bfc5b0072)

```
Leaf_2# sh ip route 0.0.0.0 vrf Leafs_L3VNI
IP Route Table for VRF "Leafs_L3VNI"
'*' denotes best ucast next-hop
'**' denotes best mcast next-hop
'[x/y]' denotes [preference/metric]
'%<string>' in via output denotes VRF <string>

0.0.0.0/0, ubest/mbest: 1/0
    *via 10.0.0.1%default, [20/0], 01:17:20, bgp-64086.59906, external, tag 4200000000, segid: 7777
tunnelid: 0xa000001 encap: VXLAN
```
### Проверка связности HQ между другими HQ
```
NAME        : VPCS[1]
IP/MASK     : 192.168.1.1/24
GATEWAY     : 192.168.1.254
DNS         :
MAC         : 00:50:79:66:68:06
LPORT       : 20000
RHOST:PORT  : 127.0.0.1:30000
MTU         : 1500

VPCS> ping 192.168.1.2

84 bytes from 192.168.1.2 icmp_seq=1 ttl=64 time=17.323 ms
84 bytes from 192.168.1.2 icmp_seq=2 ttl=64 time=15.257 ms
84 bytes from 192.168.1.2 icmp_seq=3 ttl=64 time=13.295 ms
84 bytes from 192.168.1.2 icmp_seq=4 ttl=64 time=12.879 ms
84 bytes from 192.168.1.2 icmp_seq=5 ttl=64 time=14.304 ms

VPCS> ping 192.168.1.3

84 bytes from 192.168.1.3 icmp_seq=1 ttl=64 time=15.730 ms
84 bytes from 192.168.1.3 icmp_seq=2 ttl=64 time=15.957 ms
84 bytes from 192.168.1.3 icmp_seq=3 ttl=64 time=13.083 ms
84 bytes from 192.168.1.3 icmp_seq=4 ttl=64 time=15.090 ms
84 bytes from 192.168.1.3 icmp_seq=5 ttl=64 time=13.074 ms

VPCS> sh arp

00:50:79:66:68:07  192.168.1.2 expires in 103 seconds
00:50:79:66:68:08  192.168.1.3 expires in 110 seconds
```
### Проверка связности между HQ и всеми Prod
```
NAME        : VPCS[1]
IP/MASK     : 192.168.1.1/24
GATEWAY     : 192.168.1.254
DNS         :
MAC         : 00:50:79:66:68:06
LPORT       : 20000
RHOST:PORT  : 127.0.0.1:30000
MTU         : 1500

VPCS> ping 192.168.2.1

84 bytes from 192.168.2.1 icmp_seq=1 ttl=63 time=7.238 ms
84 bytes from 192.168.2.1 icmp_seq=2 ttl=63 time=6.188 ms
84 bytes from 192.168.2.1 icmp_seq=3 ttl=63 time=4.491 ms
84 bytes from 192.168.2.1 icmp_seq=4 ttl=63 time=4.669 ms
84 bytes from 192.168.2.1 icmp_seq=5 ttl=63 time=6.551 ms

VPCS> ping 192.168.2.2

84 bytes from 192.168.2.2 icmp_seq=1 ttl=62 time=16.824 ms
84 bytes from 192.168.2.2 icmp_seq=2 ttl=62 time=16.201 ms
84 bytes from 192.168.2.2 icmp_seq=3 ttl=62 time=18.584 ms
84 bytes from 192.168.2.2 icmp_seq=4 ttl=62 time=14.486 ms
84 bytes from 192.168.2.2 icmp_seq=5 ttl=62 time=16.368 ms

VPCS> ping 192.168.2.3

84 bytes from 192.168.2.3 icmp_seq=1 ttl=62 time=13.357 ms
84 bytes from 192.168.2.3 icmp_seq=2 ttl=62 time=13.438 ms
84 bytes from 192.168.2.3 icmp_seq=3 ttl=62 time=14.079 ms
84 bytes from 192.168.2.3 icmp_seq=4 ttl=62 time=15.760 ms
84 bytes from 192.168.2.3 icmp_seq=5 ttl=62 time=15.455 ms

VPCS> sh arp

00:50:79:66:68:07  192.168.1.2 expires in 89 seconds
00:50:79:66:68:08  192.168.1.3 expires in 92 seconds
00:00:00:00:77:77  192.168.1.254 expires in 34 seconds
```
В дампе трафика видно, что при обращении к другой подсети, в VXLAN заголовке устанавливается метка L3 VNI 7777
![L3VNI icmp](https://github.com/Anumrak/EVPN_labs/assets/133969023/e3803031-d674-4632-8010-ec4a8c8d90ce)

TTL снимается 2 раза, до хоста в другой подсети на локальном Leaf и обратно, потому что пакету приходится пройти только через свой шлюз в локальном vrf - мы получает ответ с TTL 63.

TTL снимается 4 раза, до хоста в другой подсети на удаленном Leaf и обратно, потому что пакет проходит через свой шлюз и через шлюз на удаленном Leaf - мы получаем ответ с TTL 62.

Cisco Nexus умеет форвардить трафик только в симметричном режиме (Symmetrical IRB (Integrated Routing and Bridging)), т.е. отправить трафик в другую подсеть без L3VNI на обоих Leaf не удастся. Это напрямую связано с тем, что Sender MAC адрес подменяется на anycast gateway MAC адрес SVI в ARP запросе. После получения такого запроса, целевой хост ответит, и такой ARP reply умрет прям на этом же Leaf, потому что anycast gateway MAC везде одинаковый. Происходит это потому, что Nexus свитчи выступают всегда как arp proxy, подменяя arp запросы своими MAC адресами. С L2VNI ситуацию спасает suppress-arp в секции member vni NVE интерфейса.

Похожая проблема описана тут

https://www.theasciiconstruct.com/post/nxos-evpn-symmetric-hybrid/#understanding-why-asymmetric-irb-does-not-work-on-nxos

Тут Cisco предлагает некий гибридный режим, который 9000v версией не поддерживается

https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/102x/configuration/vxlan/cisco-nexus-9000-series-nx-os-vxlan-configuration-guide-release-102x/m-evpn-hybrid-irb-mode.html

### Проверка связности внутри группы Dev
Так как группа Dev не имеет шлюза ни на одном из Leaf, то им будет доступна только L2 связность между всеми Leaf.
```
NAME        : VPCS[1]
IP/MASK     : 192.168.3.1/24
GATEWAY     : 192.168.3.254
DNS         :
MAC         : 00:50:79:66:68:0c
LPORT       : 20000
RHOST:PORT  : 127.0.0.1:30000
MTU         : 1500

VPCS> ping 192.168.3.2

84 bytes from 192.168.3.2 icmp_seq=1 ttl=64 time=12.697 ms
84 bytes from 192.168.3.2 icmp_seq=2 ttl=64 time=14.796 ms
84 bytes from 192.168.3.2 icmp_seq=3 ttl=64 time=14.164 ms
84 bytes from 192.168.3.2 icmp_seq=4 ttl=64 time=13.879 ms
84 bytes from 192.168.3.2 icmp_seq=5 ttl=64 time=10.407 ms

VPCS> ping 192.168.3.3

84 bytes from 192.168.3.3 icmp_seq=1 ttl=64 time=14.443 ms
84 bytes from 192.168.3.3 icmp_seq=2 ttl=64 time=14.042 ms
84 bytes from 192.168.3.3 icmp_seq=3 ttl=64 time=10.515 ms
84 bytes from 192.168.3.3 icmp_seq=4 ttl=64 time=13.719 ms
84 bytes from 192.168.3.3 icmp_seq=5 ttl=64 time=13.474 ms

VPCS> ping 192.168.1.1

host (192.168.3.254) not reachable

VPCS> ping 192.168.2.1

host (192.168.3.254) not reachable

VPCS> sh arp

00:50:79:66:68:0d  192.168.3.2 expires in 81 seconds
00:50:79:66:68:0e  192.168.3.3 expires in 86 seconds
```
