# Настройка underlay сети в CLOS топологии из пяти устройств Cisco Nexus 9k. (eBGP version)
Цели
1) Создать и поднять протокол eBGP на всех узлах.
2) Настроить роутеры Spine_1 и Spine_2 в AS 64086.59904.
3) Настроить условие установления соседства с Leaf роутерами только с AS 64086.59905, 64086.59906, 64086.59907, соответственно.
4) Проверить установление ebgp соседства между Leaf и Spine роутерами.
5) Проверить, что все Loopback адреса Leaf роутеров находятся в bgp таблице роутеров Spine_1 и Spine_2.
6) Проверить RIB на Leaf_1 роутере как примерном на наличие всех Loopback адресов, полученных от Spine_1 и Spine_2.
7) Убедиться, что балансировка до Loopback адреса Leaf роутера задействована.
8) Проверить сетевую связность между Loopback адресами Leaf и Spine роутеров.
# Целевая схема
![Снимок](https://github.com/Anumrak/EVPN_labs/assets/133969023/6207ac40-14de-454f-ac56-6adfd13a0d87)

Адресное пространство для link интерфейсов

> 172.16.0.0/24

Адресное пространство для loopback интерфейсов

> 10.0.0.0/24

Конфигурация типового процесса ebgp на примере роутера Leaf_1
```
router bgp 64086.59905
  router-id 10.0.0.1
  bestpath as-path multipath-relax
  reconnect-interval 5
  log-neighbor-changes
  address-family ipv4 unicast
    redistribute direct route-map rm_connected
    maximum-paths 64
  template peer Spines
    remote-as 64086.59904
    password 3 7b12be5a1d75eaf0
    timers 5 15
    address-family ipv4 unicast
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
  neighbor 172.16.0.0/28 remote-as route-map leafs
    password 3 7b12be5a1d75eaf0
    timers 5 15
    maximum-peers 3
    address-family ipv4 unicast
```
Конфигурация карты маршрута для ограничения установления соседств от Leaf роутеров по номеру AS
```
route-map leafs permit 10
  match as-number 4200000001-4200000003
```
### Проверка установления ebgp соседства между Leaf и Spine роутерами
```
Leaf_1# sh ip bgp summary
BGP summary information for VRF default, address family IPv4 Unicast
BGP router identifier 10.0.0.1, local AS number 4200000001
BGP table version is 18, IPv4 Unicast config peers 2, capable peers 2
5 network entries and 7 paths using 1460 bytes of memory
BGP attribute entries [4/688], BGP AS path entries [3/26]
BGP community entries [0/0], BGP clusterlist entries [0/0]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
172.16.0.1      4 4200000000
                            525     581       18    0    0 00:18:22 3
172.16.0.3      4 4200000000
                            520     594       18    0    0 00:18:22 3
```
```
Leaf_2# sh ip bgp summary
BGP summary information for VRF default, address family IPv4 Unicast
BGP router identifier 10.0.0.2, local AS number 4200000002
BGP table version is 17, IPv4 Unicast config peers 2, capable peers 2
5 network entries and 7 paths using 1460 bytes of memory
BGP attribute entries [4/688], BGP AS path entries [3/26]
BGP community entries [0/0], BGP clusterlist entries [0/0]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
172.16.0.5      4 4200000000
                            495     490       17    0    0 00:18:48 3
172.16.0.7      4 4200000000
                            495     490       17    0    0 00:18:50 3
```
```
Leaf_3# sh ip bgp summary
BGP summary information for VRF default, address family IPv4 Unicast
BGP router identifier 10.0.0.3, local AS number 4200000003
BGP table version is 19, IPv4 Unicast config peers 2, capable peers 2
5 network entries and 7 paths using 1460 bytes of memory
BGP attribute entries [4/688], BGP AS path entries [3/26]
BGP community entries [0/0], BGP clusterlist entries [0/0]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
172.16.0.9      4 4200000000
                            488     485       19    0    0 00:19:19 3
172.16.0.11     4 4200000000
                            488     483       19    0    0 00:19:21 3
```
```
Spine_1# sh ip bgp summary
BGP summary information for VRF default, address family IPv4 Unicast
BGP router identifier 10.0.0.4, local AS number 4200000000
BGP table version is 18, IPv4 Unicast config peers 4, capable peers 3
4 network entries and 4 paths using 976 bytes of memory
BGP attribute entries [4/688], BGP AS path entries [3/18]
BGP community entries [0/0], BGP clusterlist entries [0/0]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
172.16.0.0      4 4200000001
                            540     536       18    0    0 00:19:44 1
172.16.0.4      4 4200000002
                            502     499       18    0    0 00:19:42 1
172.16.0.8      4 4200000003
                            491     486       18    0    0 00:19:41 1
```
```
Spine_2# sh ip bgp summary
BGP summary information for VRF default, address family IPv4 Unicast
BGP router identifier 10.0.0.5, local AS number 4200000000
BGP table version is 19, IPv4 Unicast config peers 4, capable peers 3
4 network entries and 4 paths using 976 bytes of memory
BGP attribute entries [4/688], BGP AS path entries [3/18]
BGP community entries [0/0], BGP clusterlist entries [0/0]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
172.16.0.2      4 4200000001
                            540     536       19    0    0 00:20:12 1
172.16.0.6      4 4200000002
                            508     505       19    0    0 00:20:11 1
172.16.0.10     4 4200000003
                            495     492       19    0    0 00:20:10 1
```
### Проверка наличия Loopback адресов всех Leaf роутеров в bgp таблице на Spine_1 и Spine_2
```
Spine_1# sh ip bgp
BGP routing table information for VRF default, address family IPv4 Unicast
BGP table version is 18, Local Router ID is 10.0.0.4
Status: s-suppressed, x-deleted, S-stale, d-dampened, h-history, *-valid, >-best
Path type: i-internal, e-external, c-confed, l-local, a-aggregate, r-redist, I-injected
Origin codes: i - IGP, e - EGP, ? - incomplete, | - multipath, & - backup, 2 - best2

   Network            Next Hop            Metric     LocPrf     Weight Path
*>e10.0.0.1/32        172.16.0.0               0                     0 4200000001 ?
*>e10.0.0.2/32        172.16.0.4               0                     0 4200000002 ?
*>e10.0.0.3/32        172.16.0.8               0                     0 4200000003 ?
*>r10.0.0.4/32        0.0.0.0                  0        100      32768 ?
```
```
Spine_2# sh ip bgp
BGP routing table information for VRF default, address family IPv4 Unicast
BGP table version is 19, Local Router ID is 10.0.0.5
Status: s-suppressed, x-deleted, S-stale, d-dampened, h-history, *-valid, >-best
Path type: i-internal, e-external, c-confed, l-local, a-aggregate, r-redist, I-injected
Origin codes: i - IGP, e - EGP, ? - incomplete, | - multipath, & - backup, 2 - best2

   Network            Next Hop            Metric     LocPrf     Weight Path
*>e10.0.0.1/32        172.16.0.2               0                     0 4200000001 ?
*>e10.0.0.2/32        172.16.0.6               0                     0 4200000002 ?
*>e10.0.0.3/32        172.16.0.10              0                     0 4200000003 ?
*>r10.0.0.5/32        0.0.0.0                  0        100      32768 ?
```
### Проверка RIB на Leaf_1 роутере как примерном на наличие всех Loopback адресов, полученных от Spine_1 и Spine_2
```
Leaf_1# sh ip route bgp
IP Route Table for VRF "default"
'*' denotes best ucast next-hop
'**' denotes best mcast next-hop
'[x/y]' denotes [preference/metric]
'%<string>' in via output denotes VRF <string>

10.0.0.2/32, ubest/mbest: 2/0
    *via 172.16.0.1, [20/0], 00:22:56, bgp-64086.59905, external, tag 4200000000
    *via 172.16.0.3, [20/0], 00:22:56, bgp-64086.59905, external, tag 4200000000
10.0.0.3/32, ubest/mbest: 2/0
    *via 172.16.0.1, [20/0], 00:22:56, bgp-64086.59905, external, tag 4200000000
    *via 172.16.0.3, [20/0], 00:22:56, bgp-64086.59905, external, tag 4200000000
10.0.0.4/32, ubest/mbest: 1/0
    *via 172.16.0.1, [20/0], 00:22:59, bgp-64086.59905, external, tag 4200000000
10.0.0.5/32, ubest/mbest: 1/0
    *via 172.16.0.3, [20/0], 00:22:59, bgp-64086.59905, external, tag 4200000000
```
### Проверка работоспособности балансировки до Loopback адреса Leaf_2 роутера как примерного через Spine_1 и Spine_2
```
Leaf_1# sh ip bgp 10.0.0.2/32
BGP routing table information for VRF default, address family IPv4 Unicast
BGP routing table entry for 10.0.0.2/32, version 16
Paths: (2 available, best #2)
Flags: (0x8008001a) (high32 00000000) on xmit-list, is in urib, is best urib rou
te, is in HW
Multipath: eBGP

  Path type: external, path is valid, not best reason: newer EBGP path, multipat
h, no labeled nexthop, in rib
  AS-Path: 4200000000 4200000002 , path sourced external to AS
    172.16.0.3 (metric 0) from 172.16.0.3 (10.0.0.5)
      Origin incomplete, MED not set, localpref 100, weight 0

  Advertised path-id 1
  Path type: external, path is valid, is best path, no labeled nexthop, in rib
  AS-Path: 4200000000 4200000002 , path sourced external to AS
    172.16.0.1 (metric 0) from 172.16.0.1 (10.0.0.4)
      Origin incomplete, MED not set, localpref 100, weight 0
```
```
Leaf_1# sh ip route 10.0.0.2/32 detail
IP Route Table for VRF "default"
'*' denotes best ucast next-hop
'**' denotes best mcast next-hop
'[x/y]' denotes [preference/metric]
'%<string>' in via output denotes VRF <string>

10.0.0.2/32, ubest/mbest: 2/0
    *via 172.16.0.1, [20/0], 00:25:36, bgp-64086.59905, external, tag 4200000000
         client-specific data: 3
         recursive next hop: 172.16.0.1/32
         extended route information: BGP origin AS 4200000002 BGP peer AS 420000
0000
    *via 172.16.0.3, [20/0], 00:25:36, bgp-64086.59905, external, tag 4200000000
         client-specific data: 3
         recursive next hop: 172.16.0.3/32
         extended route information: BGP origin AS 4200000002 BGP peer AS 420000
```
### Проверка сетевой связности между Loopback адресами Leaf и Spine роутеров.
```
Leaf_1# ping 10.0.0.2 source 10.0.0.1
PING 10.0.0.2 (10.0.0.2) from 10.0.0.1: 56 data bytes
64 bytes from 10.0.0.2: icmp_seq=0 ttl=253 time=33.847 ms
64 bytes from 10.0.0.2: icmp_seq=1 ttl=253 time=14.591 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=253 time=19.806 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=253 time=21.444 ms
64 bytes from 10.0.0.2: icmp_seq=4 ttl=253 time=18.507 ms

--- 10.0.0.2 ping statistics ---
5 packets transmitted, 5 packets received, 0.00% packet loss
round-trip min/avg/max = 14.591/21.639/33.847 ms
Leaf_1# ping 10.0.0.3 source 10.0.0.1
PING 10.0.0.3 (10.0.0.3) from 10.0.0.1: 56 data bytes
64 bytes from 10.0.0.3: icmp_seq=0 ttl=253 time=35.881 ms
64 bytes from 10.0.0.3: icmp_seq=1 ttl=253 time=16.252 ms
64 bytes from 10.0.0.3: icmp_seq=2 ttl=253 time=26.973 ms
64 bytes from 10.0.0.3: icmp_seq=3 ttl=253 time=21.85 ms
64 bytes from 10.0.0.3: icmp_seq=4 ttl=253 time=14.91 ms

--- 10.0.0.3 ping statistics ---
5 packets transmitted, 5 packets received, 0.00% packet loss
round-trip min/avg/max = 14.91/23.173/35.881 ms
Leaf_1# ping 10.0.0.4 source 10.0.0.1
PING 10.0.0.4 (10.0.0.4) from 10.0.0.1: 56 data bytes
64 bytes from 10.0.0.4: icmp_seq=0 ttl=254 time=22.31 ms
64 bytes from 10.0.0.4: icmp_seq=1 ttl=254 time=10.723 ms
64 bytes from 10.0.0.4: icmp_seq=2 ttl=254 time=5.461 ms
64 bytes from 10.0.0.4: icmp_seq=3 ttl=254 time=9.65 ms
64 bytes from 10.0.0.4: icmp_seq=4 ttl=254 time=4.683 ms

--- 10.0.0.4 ping statistics ---
5 packets transmitted, 5 packets received, 0.00% packet loss
round-trip min/avg/max = 4.683/10.565/22.31 ms
Leaf_1# ping 10.0.0.5 source 10.0.0.1
PING 10.0.0.5 (10.0.0.5) from 10.0.0.1: 56 data bytes
64 bytes from 10.0.0.5: icmp_seq=0 ttl=254 time=9.192 ms
64 bytes from 10.0.0.5: icmp_seq=1 ttl=254 time=8.825 ms
64 bytes from 10.0.0.5: icmp_seq=2 ttl=254 time=9.734 ms
64 bytes from 10.0.0.5: icmp_seq=3 ttl=254 time=14.073 ms
64 bytes from 10.0.0.5: icmp_seq=4 ttl=254 time=10.368 ms

--- 10.0.0.5 ping statistics ---
5 packets transmitted, 5 packets received, 0.00% packet loss
round-trip min/avg/max = 8.825/10.438/14.073 ms
```
