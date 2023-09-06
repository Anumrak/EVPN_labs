# Настройка underlay сети в CLOS топологии из пяти устройств Cisco Nexus 9k. (VXLAN over MP-BGP EVPN IPv6 version)
Цели
1) 
# Целевая схема
![Снимок](https://github.com/Anumrak/EVPN_labs/assets/133969023/090ab0fd-c540-4503-8934-4834c4fd1294)

Адресное пространство для link интерфейсов

> 172.16.0.0/24
111
Адресное пространство для loopback интерфейсов

> 10.0.0.0/24

Адресное пространство для L2 VPN сервиса клиента

> 192.168.3.0/24
> 2023:1eaf:300:0:192:168:3:0/64

Адресное пространство для L3 VPN сервиса клиента

> 192.168.1.0/24
> 2023:1eaf:100:0:192:168:1:0/64
> 192.168.2.0/24
> 2023:1eaf:200:0:192:168:2:0/64

Адресное пространство для vPC Peer Keepalive интерфейсов

> 192.168.255.0/31

Адресное пространство для eBGP пиринга между клиентом и vPC доменом

> 192.168.50.0/29
> FC00:2023::192:168:50:0/126

Адресное пространство клиентской сети за Client_Router

> 192.168.4.0/24
> 2023:A5E2:8C12:400::/64

Необходимые свойства Client_Router:
```
ipv6 unicast-routing
```
Все SVI интерфейсы сохраняют свое поведение anycast gateway через виртуальный мак адрес для IPv6 клиентов внутри фабрики
```
interface Vlan100
  description VPCS_HQ_GW
  no shutdown
  vrf member Leafs_L3VNI
  no ip redirects
  ip address 192.168.1.254/24
  ipv6 address 2023:1eaf:100:0:192:168:1:254/64
  no ipv6 redirects
  fabric forwarding mode anycast-gateway
```
```
VPCS> sh ipv6

NAME              : VPCS[1]
LINK-LOCAL SCOPE  : fe80::250:79ff:fe66:6806/64
GLOBAL SCOPE      : 2023:1eaf:100:0:192:168:1:1/64
DNS               :
ROUTER LINK-LAYER : 00:00:00:00:77:77
MAC               : 00:50:79:66:68:06
LPORT             : 20000
RHOST:PORT        : 127.0.0.1:30000
MTU:              : 1500
```
Настройка IPv6 адресации для пиринга через vPC линк с клиентом
```
interface Vlan400
  description -C- | Client_Router eBGP session Leaf_1 | Clients
  no shutdown
  vrf member Leafs_L3VNI
  no ip redirects
  ip address 192.168.50.1/29
  ipv6 address fc00:2023::192:168:50:1/126
  no ipv6 redirects
```
```
interface Vlan400
  description -C- | Client_Router eBGP session Leaf_2 | Clients
  no shutdown
  vrf member Leafs_L3VNI
  no ip redirects
  ip address 192.168.50.2/29
  ipv6 address fc00:2023::192:168:50:2/126
  no ipv6 redirects
```
```
interface Vlan400
 description eBGP peering
 ip address 192.168.50.3 255.255.255.248
 ipv6 address FC00:2023::192:168:50:3/126
end

Client_Router#
```
Типовая настройка eBGP для IPv6 через EVPN фабрику на примере Leaf_1
```
ipv6 prefix-list pl_client_ipv6 seq 5 permit 2000::/3
```
```
route-map rm_client_ipv6 permit 10
  match ipv6 address prefix-list pl_client_ipv6
```
```
vrf context Leafs_L3VNI
  vni 7777
  ip route 0.0.0.0/0 Null0
  ipv6 route 2000::/3 Null0
  rd 10.0.0.1:7777
  address-family ipv4 unicast
    route-target import 4200000001:7777 evpn
    route-target import 4200000002:7777 evpn
    route-target import 4200000003:7777 evpn
    route-target export 4200000001:7777 evpn
  address-family ipv6 unicast
    route-target import 4200000001:7777 evpn
    route-target import 4200000002:7777 evpn
    route-target import 4200000003:7777 evpn
    route-target export 4200000001:7777 evpn
```
```
vpc domain 1
  role priority 1
  peer-keepalive destination 192.168.255.1 source 192.168.255.0 vrf Keepalive
  peer-gateway
  layer3 peer-router
  ipv6 nd synchronize
  ip arp synchronize
```
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
    address-family ipv6 unicast
      network 2000::/3
    neighbor fc00:2023::192:168:50:3
      remote-as 64512
      address-family ipv6 unicast
        route-map rm_client_ipv6 out
    neighbor 192.168.50.3
      remote-as 64512
      address-family ipv4 unicast
        route-map rm_client out
```
Настройка IPv6 eBGP пиринга для клиента
```
ipv6 unicast-routing
ipv6 cef
```
```
interface Loopback400
 description Users Network
 ip address 192.168.4.1 255.255.255.0
 ipv6 address 2023:A5E2:8C12:400::1/64
```
```
router bgp 64512
 bgp router-id 10.100.100.100
 bgp log-neighbor-changes
 neighbor 192.168.50.1 remote-as 4200000001
 neighbor 192.168.50.2 remote-as 4200000002
 neighbor FC00:2023::192:168:50:1 remote-as 4200000001
 neighbor FC00:2023::192:168:50:2 remote-as 4200000002
 !
 address-family ipv4
  network 192.168.4.0
  neighbor 192.168.50.1 activate
  neighbor 192.168.50.2 activate
  no neighbor FC00:2023::192:168:50:1 activate
  no neighbor FC00:2023::192:168:50:2 activate
 exit-address-family
 !
 address-family ipv6
  network 2023:A5E2:8C12:400::/64
  neighbor FC00:2023::192:168:50:1 activate
  neighbor FC00:2023::192:168:50:2 activate
 exit-address-family
```
### Проверка состояния пиринга на Leaf_1 как примерном
```
Leaf_1# sh ipv6 bgp summary vrf Leafs_L3VNI
BGP summary information for VRF Leafs_L3VNI, address family IPv6 Unicast
BGP router identifier 192.168.1.254, local AS number 4200000001
BGP table version is 45, IPv6 Unicast config peers 1, capable peers 1
3 network entries and 3 paths using 648 bytes of memory
BGP attribute entries [3/516], BGP AS path entries [2/16]
BGP community entries [0/0], BGP clusterlist entries [0/0]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
fc00:2023::192:168:50:3
                4 64512    1295    1146       45    0    0 18:55:22 1
```
```
Leaf_1# sh ipv6 bgp vrf Leafs_L3VNI
BGP routing table information for VRF Leafs_L3VNI, address family IPv6 Unicast
BGP table version is 45, Local Router ID is 192.168.1.254
Status: s-suppressed, x-deleted, S-stale, d-dampened, h-history, *-valid, >-best
Path type: i-internal, e-external, c-confed, l-local, a-aggregate, r-redist, I-injected
Origin codes: i - IGP, e - EGP, ? - incomplete, | - multipath, & - backup, 2 - best2

   Network            Next Hop            Metric     LocPrf     Weight Path
*>l2000::/3           0::                               100      32768 i
*>e2023:a5e2:8c12:400::/64
                      fc00:2023::192:168:50:3
                                               0                     0 64512 i
```
### Проверка экспорта AF IPv6 в AF L2VPN SAFI EVPN как route-type 5
```
Leaf_1# sh bgp l2vpn evpn 2023:a5e2:8c12:400::
BGP routing table information for VRF default, address family L2VPN EVPN
Route Distinguisher: 10.0.0.1:7777    (L3VNI 7777)
BGP routing table entry for [5]:[0]:[0]:[64]:[2023:a5e2:8c12:400::]/416, version 1409
Paths: (1 available, best #1)
Flags: (0x000002) (high32 00000000) on xmit-list, is not in l2rib/evpn

  Advertised path-id 1
  Path type: local, path is valid, is best path, no labeled nexthop
  Gateway IP: 0.0.0.0
  AS-Path: 64512 , path sourced external to AS
    10.1.0.1 (metric 0) from 0.0.0.0 (10.0.0.1)
      Origin IGP, MED 0, localpref 100, weight 0
      Received label 7777
      Extcommunity: RT:4200000001:7777 ENCAP:8 Router MAC:5001.0000.1b08

  Path-id 1 advertised to peers:
    10.0.0.4           10.0.0.5
```
Как мы видим, next-hop используется в виде vPC Anycast адреса 10.1.0.1, значит этот префикс известен именно от vPC домена.
Как выглядит NLRI с этим префиксом в дампе

Картинка_1.

### Проверка route-type 5 от vPC домена на Spine_1 как примерном
```
Route Distinguisher: 10.0.0.1:7777
*>e[5]:[0]:[0]:[0]:[0.0.0.0]/224
                      10.1.0.1                                       0 4200000001 i
*>e[5]:[0]:[0]:[24]:[192.168.4.0]/224
                      10.1.0.1                 0                     0 4200000001 64512 i
*>e[5]:[0]:[0]:[3]:[2000::]/416
                      10.1.0.1                                       0 4200000001 i
*>e[5]:[0]:[0]:[64]:[2023:a5e2:8c12:400::]/416
                      10.1.0.1                 0                     0 4200000001 64512 i
```
Опять же, очень удобно, что на спайнах ничего настраивать не нужно, ведь эти IPv6 префиксы известны все также как SAFI EVPN в виде route-type 5.

### Проверка импорта EVPN route-type 5 маршрутов на Leaf_3
```
Route Distinguisher: 10.0.0.3:7777    (L3VNI 7777)
*>e[2]:[0]:[0]:[48]:[0050.7966.6806]:[32]:[192.168.1.1]/272
                      10.1.0.1                                       0 4200000000 4200000002 i
* e                   10.1.0.1                                       0 4200000000 4200000001 i
* e[2]:[0]:[0]:[48]:[0050.7966.6807]:[32]:[192.168.1.2]/272
                      10.1.0.1                                       0 4200000000 4200000001 i
*>e                   10.1.0.1                                       0 4200000000 4200000002 i
*>e[2]:[0]:[0]:[48]:[0050.7966.6809]:[32]:[192.168.2.1]/272
                      10.1.0.1                                       0 4200000000 4200000002 i
* e                   10.1.0.1                                       0 4200000000 4200000001 i
*>e[2]:[0]:[0]:[48]:[0050.7966.680a]:[32]:[192.168.2.2]/272
                      10.1.0.1                                       0 4200000000 4200000002 i
* e                   10.1.0.1                                       0 4200000000 4200000001 i
*>e[5]:[0]:[0]:[0]:[0.0.0.0]/224
                      10.1.0.1                                       0 4200000000 4200000002 i
* e                   10.1.0.1                                       0 4200000000 4200000001 i
* e[5]:[0]:[0]:[24]:[192.168.4.0]/224
                      10.1.0.1                                       0 4200000000 4200000001 64512 i
*>e                   10.1.0.1                                       0 4200000000 4200000002 64512 i
*>e[5]:[0]:[0]:[3]:[2000::]/416
                      10.1.0.1                                       0 4200000000 4200000002 i
* e                   10.1.0.1                                       0 4200000000 4200000001 i
* e[5]:[0]:[0]:[64]:[2023:a5e2:8c12:400::]/416
                      10.1.0.1                                       0 4200000000 4200000001 64512 i
*>e                   10.1.0.1                                       0 4200000000 4200000002 64512 i
```
```
Leaf_3# sh bgp l2vpn evpn 2023:a5e2:8c12:400::
BGP routing table information for VRF default, address family L2VPN EVPN
Route Distinguisher: 10.0.0.1:7777
BGP routing table entry for [5]:[0]:[0]:[64]:[2023:a5e2:8c12:400::]/416, version 2133
Paths: (2 available, best #2)
Flags: (0x000002) (high32 00000000) on xmit-list, is not in l2rib/evpn, is not in HW

  Path type: external, path is valid, not best reason: newer EBGP path, no labeled nexthop
  Gateway IP: 0.0.0.0
  AS-Path: 4200000000 4200000001 64512 , path sourced external to AS
    10.1.0.1 (metric 0) from 10.0.0.5 (10.0.0.5)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 7777
      Extcommunity: RT:4200000001:7777 ENCAP:8 Router MAC:5001.0000.1b08

  Advertised path-id 1
  Path type: external, path is valid, is best path, no labeled nexthop
             Imported to 2 destination(s)
             Imported paths list: L3-7777 Leafs_L3VNI
  Gateway IP: 0.0.0.0
  AS-Path: 4200000000 4200000001 64512 , path sourced external to AS
    10.1.0.1 (metric 0) from 10.0.0.4 (10.0.0.4)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 7777
      Extcommunity: RT:4200000001:7777 ENCAP:8 Router MAC:5001.0000.1b08

  Path-id 1 not advertised to any peer

Route Distinguisher: 10.0.0.2:7777
BGP routing table entry for [5]:[0]:[0]:[64]:[2023:a5e2:8c12:400::]/416, version 2115
Paths: (2 available, best #2)
Flags: (0x000002) (high32 00000000) on xmit-list, is not in l2rib/evpn, is not in HW

  Path type: external, path is valid, not best reason: newer EBGP path, no labeled nexthop
  Gateway IP: 0.0.0.0
  AS-Path: 4200000000 4200000002 64512 , path sourced external to AS
    10.1.0.1 (metric 0) from 10.0.0.5 (10.0.0.5)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 7777
      Extcommunity: RT:4200000002:7777 ENCAP:8 Router MAC:5002.0000.1b08

  Advertised path-id 1
  Path type: external, path is valid, is best path, no labeled nexthop
             Imported to 2 destination(s)
             Imported paths list: L3-7777 Leafs_L3VNI
  Gateway IP: 0.0.0.0
  AS-Path: 4200000000 4200000002 64512 , path sourced external to AS
    10.1.0.1 (metric 0) from 10.0.0.4 (10.0.0.4)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 7777
      Extcommunity: RT:4200000002:7777 ENCAP:8 Router MAC:5002.0000.1b08

  Path-id 1 not advertised to any peer

Route Distinguisher: 10.0.0.3:7777    (L3VNI 7777)
BGP routing table entry for [5]:[0]:[0]:[64]:[2023:a5e2:8c12:400::]/416, version 2096
Paths: (2 available, best #2)
Flags: (0x000002) (high32 00000000) on xmit-list, is not in l2rib/evpn, is not in HW

  Path type: external, path is valid, not best reason: newer EBGP path, no labeled nexthop
             Imported from 10.0.0.1:7777:[5]:[0]:[0]:[64]:[2023:a5e2:8c12:400::]/416
  Gateway IP: 0.0.0.0
  AS-Path: 4200000000 4200000001 64512 , path sourced external to AS
    10.1.0.1 (metric 0) from 10.0.0.4 (10.0.0.4)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 7777
      Extcommunity: RT:4200000001:7777 ENCAP:8 Router MAC:5001.0000.1b08

  Advertised path-id 1
  Path type: external, path is valid, is best path, no labeled nexthop
             Imported from 10.0.0.2:7777:[5]:[0]:[0]:[64]:[2023:a5e2:8c12:400::]/416
  Gateway IP: 0.0.0.0
  AS-Path: 4200000000 4200000002 64512 , path sourced external to AS
    10.1.0.1 (metric 0) from 10.0.0.4 (10.0.0.4)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 7777
      Extcommunity: RT:4200000002:7777 ENCAP:8 Router MAC:5002.0000.1b08
```
```
Leaf_3# sh ipv6 bgp vrf Leafs_L3VNI
BGP routing table information for VRF Leafs_L3VNI, address family IPv6 Unicast
BGP table version is 96, Local Router ID is 192.168.1.254
Status: s-suppressed, x-deleted, S-stale, d-dampened, h-history, *-valid, >-best
Path type: i-internal, e-external, c-confed, l-local, a-aggregate, r-redist, I-injected
Origin codes: i - IGP, e - EGP, ? - incomplete, | - multipath, & - backup, 2 - best2

   Network            Next Hop            Metric     LocPrf     Weight Path
*>e2000::/3           ::ffff:10.1.0.1                                0 4200000000 4200000002 i
* e                   ::ffff:10.1.0.1                                0 4200000000 4200000001 i
*>e2023:a5e2:8c12:400::/64
                      ::ffff:10.1.0.1                                0 4200000000 4200000002 64512 i
* e                   ::ffff:10.1.0.1                                0 4200000000 4200000001 64512 i
```
Next-Hop выглядит через ::ffff:10.1.0.1 потому, что у нас нет реального IPv6 адреса куда направить трафик, так как он доступен через VTEP адрес только после VXLAN инкапсуляции.
```
Leaf_3# sh ipv6 route 2000::/3 vrf Leafs_L3VNI
IPv6 Routing Table for VRF "Leafs_L3VNI"
'*' denotes best ucast next-hop
'**' denotes best mcast next-hop
'[x/y]' denotes [preference/metric]

2000::/3, ubest/mbest: 1/0
    *via ::ffff:10.1.0.1%default:IPv4, [20/0], 00:45:19, bgp-64086.59907, external, tag 4200000000,
segid 7777 tunnelid: 0xa010001 encap: VXLAN
```
Маршрут 2000::/3 сообщен в фабрику для того, чтобы хосты смогли ходить на все глобальные юникаст адреса в этом VRF. Это как строгий маршрут по умолчанию: только для глобально маршрутизируемых IPv6 префиксов.
```
Leaf_3# sh ipv6 route 2023:a5e2:8c12:400::/64 vrf Leafs_L3VNI
IPv6 Routing Table for VRF "Leafs_L3VNI"
'*' denotes best ucast next-hop
'**' denotes best mcast next-hop
'[x/y]' denotes [preference/metric]

2023:a5e2:8c12:400::/64, ubest/mbest: 1/0
    *via ::ffff:10.1.0.1%default:IPv4, [20/0], 00:45:33, bgp-64086.59907, external, tag 4200000000,
segid 7777 tunnelid: 0xa010001 encap: VXLAN
```
### Проверка доступности IPv6 хостов через EVPN фабрику от клиента Leaf_3 до клиента подсети Client_Router
```
VPCS> sh ipv6

NAME              : VPCS[1]
LINK-LOCAL SCOPE  : fe80::250:79ff:fe66:6808/64
GLOBAL SCOPE      : 2023:1eaf:100:0:192:168:1:3/64
DNS               :
ROUTER LINK-LAYER : 00:00:00:00:77:77
MAC               : 00:50:79:66:68:08
LPORT             : 20000
RHOST:PORT        : 127.0.0.1:30000
MTU:              : 1500

VPCS> ping 2023:A5E2:8C12:400::1

2023:A5E2:8C12:400::1 icmp6_seq=1 ttl=62 time=16.421 ms
2023:A5E2:8C12:400::1 icmp6_seq=2 ttl=62 time=14.432 ms
2023:A5E2:8C12:400::1 icmp6_seq=3 ttl=62 time=16.574 ms
2023:A5E2:8C12:400::1 icmp6_seq=4 ttl=62 time=14.354 ms
2023:A5E2:8C12:400::1 icmp6_seq=5 ttl=62 time=16.886 ms
```
Как это выглядит в дампе

Картинка_4

### Проверка обратного роутинга от публичного шлюза Client_Router до клиента фабрики
```
Client_Router#ping 2023:1eaf:100:0:192:168:1:3 source 2023:A5E2:8C12:400::1
Type escape sequence to abort.
Sending 5, 100-byte ICMP Echos to 2023:1EAF:100:0:192:168:1:3, timeout is 2 seconds:
Packet sent with a source address of 2023:A5E2:8C12:400::1
!!!!!
Success rate is 100 percent (5/5), round-trip min/avg/max = 17/22/32 ms
```
Кстати, обратно нам приходят ответы только потому, что vPC домен в курсе об обратном маршруте через full mac-ip route-type 2 через L3VNI форвардинг
```
2023:1eaf:100:0:192:168:1:3/128, ubest/mbest: 1/0
    *via ::ffff:10.0.0.3%default:IPv4, [20/0], 00:00:08, bgp-64086.59905, external, tag 4200000000,
segid 7777 tunnelid: 0xa000003 encap: VXLAN
```
```
Route Distinguisher: 10.0.0.3:100
BGP routing table entry for [2]:[0]:[0]:[48]:[0050.7966.6808]:[128]:[2023:1eaf:100:0:192:168:1:3]/36
8, version 1851
Paths: (2 available, best #1)
Flags: (0x000202) (high32 00000000) on xmit-list, is not in l2rib/evpn, is not in HW

  Advertised path-id 1
  Path type: external, path is valid, is best path, no labeled nexthop
             Imported to 3 destination(s)
             Imported paths list: Leafs_L3VNI L3-7777 L2-10100
  AS-Path: 4200000000 4200000003 , path sourced external to AS
    10.0.0.3 (metric 0) from 10.0.0.4 (10.0.0.4)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 10100 7777
      Extcommunity: RT:10100:100 RT:4200000003:7777 ENCAP:8 Router MAC:5003.0000.1b08

  Path type: external, path is valid, not best reason: Router Id, no labeled nexthop
  AS-Path: 4200000000 4200000003 , path sourced external to AS
    10.0.0.3 (metric 0) from 10.0.0.5 (10.0.0.5)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 10100 7777
      Extcommunity: RT:10100:100 RT:4200000003:7777 ENCAP:8 Router MAC:5003.0000.1b08
```
VPCS> trace 2023:A5E2:8C12:400::1

trace to 2023:A5E2:8C12:400::1, 64 hops max
 1 2023:1eaf:100:0:192:168:1:254   4.665 ms  3.319 ms  2.864 ms
 2 2023:1eaf:100:0:192:168:1:254   14.120 ms  13.708 ms  13.204 ms
 3 *fc00:2023::192:168:50:3   17.167 ms (ICMP type:1, code:4, Port unreachable)
```
В трассировке от 2023:1eaf:100:0:192:168:1:3 до 2023:A5E2:8C12:400::1 видно 2 anycast шлюза, а третий хоп, адрес которого принадлежит стыку eBGP пиринга с Leaf свитчами, отвечает нам "ICMP type:1, code:4, Port unreachable". Значит ли это, что на сети произошла ошибка? Нет. Дело в том, что трассировка в VPC машинах работает по умолчанию поверх UDP портов. При назначении TTL в Hop Limit = 3 в IPv6 заголовке с вышестоящим UDP заголовком, такой пакет успешно доходит до Client_Router интерфейса SVI 400, и так как там нет ни одного сервиса, слушающего UDP порт 36193, то SVI 400 должен что то ответить обратно. Но ведь и TTL не закончился. Именно поэтому он отвечает этим кодом. Он означает, что адрес назначения как раз доступен.
Что говорят об этом в RFC https://www.ietf.org/rfc/rfc2463.txt
```
A destination node SHOULD send a Destination Unreachable message with
   Code 4 in response to a packet for which the transport protocol
   (e.g., UDP) has no listener, if that transport protocol has no
   alternative means to inform the sender.

   Upper layer notification

   A node receiving the ICMPv6 Destination Unreachable message MUST
   notify the upper-layer process.
```
На роутере Client_Router нет вышестоящего UDP сервиса, поэтому такой ответ.

Картинка_2

Картинка_3

L2VPN функционал к сожалению не работает из-за все того же бага Cisco Nexus 9000v - перехват arp и nd запросов и подставлением своего системного мак адреса. Для IPv4 это лечилось suppress ARP функционалом на NVE интерфейсах, но supress ND не поддерживается 9000v. На реальном оборудовании, как широковещательный ARP трафик, так как мультикаст ND рассылка должна работать штатно, без suppress.