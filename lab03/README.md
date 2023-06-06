# Настройка underlay сети в CLOS топологии из пяти устройств Cisco Nexus 9k. (iBGP version)
Цели
1) Очистить RIB от маршрутов известных ранее через протокол IS-IS, выключив его в корне настройки.
2) Создать и поднять протокол iBGP.
3) Настроить роутеры Spine_1 и Spine_2 как Route Reflector для своих Leaf роутеров.
4) Настроить опцию изменение следующего прыжка на Spine роутерах для своих Leaf соседей.
5) Проверить установление ibgp соседства между Leaf и Spine роутерами.
6) Проверить, что все Loopback адреса Leaf роутеров находятся в bgp таблице роутеров Spine_1 и Spine_2.
7) Проверить на Leaf_1 роутере как примерном, что адреса атрибута next-hop до Loopback адресов других Leaf роутеров изменились до Spine_1 и Spine_2.
8) Проверить RIB на Leaf_1 роутере как примерном на наличие всех Loopback адресов, полученных от Spine_1 RR и Spine_2 RR.
9) Убедиться, что балансировка до Loopback адреса Leaf роутера задействована.
10) Проверить сетевую связность между Loopback адресами Leaf и Spine роутеров.
# Целевая схема
![Снимок](https://github.com/Anumrak/EVPN_labs/assets/133969023/6207ac40-14de-454f-ac56-6adfd13a0d87)

Адресное пространство для link интерфейсов

> 172.16.0.0/24

Адресное пространство для loopback интерфейсов

> 10.0.0.0/24

### Отключение протокола IS-IS:
```
router isis 100
  shutdown
  net 49.0001.0100.0000.0001.00
  is-type level-1
  log-adjacency-changes
```
Конфигурация типового процесса ibgp на примере роутера Leaf_1
```
router bgp 64086.59904
  router-id 10.0.0.1
  reconnect-interval 5
  log-neighbor-changes
  address-family ipv4 unicast
    redistribute direct route-map rm_connected
    maximum-paths ibgp 64
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
Конфигурация типового процесса ibgp Route Reflector на примере роутера Spine_1
```
router bgp 64086.59904
  router-id 10.0.0.4
  reconnect-interval 5
  log-neighbor-changes
  address-family ipv4 unicast
    redistribute direct route-map rm_connected
    maximum-paths ibgp 64
  neighbor 172.16.0.0/28
    remote-as 64086.59904
    password 3 7b12be5a1d75eaf0
    timers 5 15
    maximum-peers 3
    address-family ipv4 unicast
      route-reflector-client
      next-hop-self all
```
### Проверка установления ibgp соседства между Leaf и Spine роутерами
```
Leaf_1# sh ip bgp summary
BGP summary information for VRF default, address family IPv4 Unicast
BGP router identifier 10.0.0.1, local AS number 4200000000
BGP table version is 51, IPv4 Unicast config peers 2, capable peers 2
5 network entries and 7 paths using 1460 bytes of memory
BGP attribute entries [6/1032], BGP AS path entries [0/0]
BGP community entries [0/0], BGP clusterlist entries [4/16]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
172.16.0.1      4 4200000000
                          10638   10596       51    0    0 13:56:38 3
172.16.0.3      4 4200000000
                          10652   10623       51    0    0 13:56:38 3
```
```
Leaf_2# sh ip bgp summary
BGP summary information for VRF default, address family IPv4 Unicast
BGP router identifier 10.0.0.2, local AS number 4200000000
BGP table version is 47, IPv4 Unicast config peers 2, capable peers 2
5 network entries and 7 paths using 1460 bytes of memory
BGP attribute entries [6/1032], BGP AS path entries [0/0]
BGP community entries [0/0], BGP clusterlist entries [4/16]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
172.16.0.5      4 4200000000
                          10480   10441       47    0    0 13:57:32 3
172.16.0.7      4 4200000000
                          10465   10436       47    0    0 13:57:33 3
```
```
Leaf_3# sh ip bgp summary
BGP summary information for VRF default, address family IPv4 Unicast
BGP router identifier 10.0.0.3, local AS number 4200000000
BGP table version is 41, IPv4 Unicast config peers 2, capable peers 2
5 network entries and 7 paths using 1460 bytes of memory
BGP attribute entries [6/1032], BGP AS path entries [0/0]
BGP community entries [0/0], BGP clusterlist entries [4/16]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
172.16.0.9      4 4200000000
                          10445   10403       41    0    0 13:58:06 3
172.16.0.11     4 4200000000
                          10428   10397       41    0    0 13:58:08 3
```
```
Spine_1# sh ip bgp summary
BGP summary information for VRF default, address family IPv4 Unicast
BGP router identifier 10.0.0.4, local AS number 4200000000
BGP table version is 68, IPv4 Unicast config peers 4, capable peers 3
4 network entries and 4 paths using 976 bytes of memory
BGP attribute entries [2/344], BGP AS path entries [0/0]
BGP community entries [0/0], BGP clusterlist entries [0/0]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
172.16.0.0      4 4200000000
                          10487   10491       68    0    0 13:58:26 1
172.16.0.4      4 4200000000
                          10454   10457       68    0    0 13:58:25 1
172.16.0.8      4 4200000000
                          10410   10415       68    0    0 13:58:24 1
```
```
Spine_2# sh ip bgp summary
BGP summary information for VRF default, address family IPv4 Unicast
BGP router identifier 10.0.0.5, local AS number 4200000000
BGP table version is 57, IPv4 Unicast config peers 4, capable peers 3
4 network entries and 4 paths using 976 bytes of memory
BGP attribute entries [2/344], BGP AS path entries [0/0]
BGP community entries [0/0], BGP clusterlist entries [0/0]

Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd
172.16.0.2      4 4200000000
                          10653   10655       57    0    0 13:58:53 1
172.16.0.6      4 4200000000
                          10455   10457       57    0    0 13:58:53 1
172.16.0.10     4 4200000000
                          10409   10413       57    0    0 13:58:52 1
```
### Проверка наличия Loopback адресов всех Leaf роутеров в bgp таблице на Spine_1 RR и Spine_2 RR
```
Spine_1# sh ip bgp
BGP routing table information for VRF default, address family IPv4 Unicast
BGP table version is 68, Local Router ID is 10.0.0.4
Status: s-suppressed, x-deleted, S-stale, d-dampened, h-history, *-valid, >-best
Path type: i-internal, e-external, c-confed, l-local, a-aggregate, r-redist, I-injected
Origin codes: i - IGP, e - EGP, ? - incomplete, | - multipath, & - backup, 2 - best2

   Network            Next Hop            Metric     LocPrf     Weight Path
*>i10.0.0.1/32        172.16.0.0               0        100          0 ?
*>i10.0.0.2/32        172.16.0.4               0        100          0 ?
*>i10.0.0.3/32        172.16.0.8               0        100          0 ?
*>r10.0.0.4/32        0.0.0.0                  0        100      32768 ?
```
```
Spine_2# sh ip bgp
BGP routing table information for VRF default, address family IPv4 Unicast
BGP table version is 57, Local Router ID is 10.0.0.5
Status: s-suppressed, x-deleted, S-stale, d-dampened, h-history, *-valid, >-best
Path type: i-internal, e-external, c-confed, l-local, a-aggregate, r-redist, I-injected
Origin codes: i - IGP, e - EGP, ? - incomplete, | - multipath, & - backup, 2 - best2

   Network            Next Hop            Metric     LocPrf     Weight Path
*>i10.0.0.1/32        172.16.0.2               0        100          0 ?
*>i10.0.0.2/32        172.16.0.6               0        100          0 ?
*>i10.0.0.3/32        172.16.0.10              0        100          0 ?
*>r10.0.0.5/32        0.0.0.0                  0        100      32768 ?
```
### Проверка изменения атрибута next-hop в bgp таблице Leaf_1 роутера до Loopback адресов других Leaf роутеров через Spine_1 и Spine_2
```
Leaf_1# sh ip bgp
BGP routing table information for VRF default, address family IPv4 Unicast
BGP table version is 51, Local Router ID is 10.0.0.1
Status: s-suppressed, x-deleted, S-stale, d-dampened, h-history, *-valid, >-best
Path type: i-internal, e-external, c-confed, l-local, a-aggregate, r-redist, I-injected
Origin codes: i - IGP, e - EGP, ? - incomplete, | - multipath, & - backup, 2 - best2

   Network            Next Hop            Metric     LocPrf     Weight Path
*>r10.0.0.1/32        0.0.0.0                  0        100      32768 ?
*|i10.0.0.2/32        172.16.0.3               0        100          0 ?
*>i                   172.16.0.1               0        100          0 ?
*|i10.0.0.3/32        172.16.0.3               0        100          0 ?
*>i                   172.16.0.1               0        100          0 ?
*>i10.0.0.4/32        172.16.0.1               0        100          0 ?
*>i10.0.0.5/32        172.16.0.3               0        100          0 ?
```
### Проверка RIB на Leaf_1 роутере как примерном на наличие всех Loopback адресов, полученных от Spine_1 RR и Spine_2 RR
```
Leaf_1# sh ip route bgp
IP Route Table for VRF "default"
'*' denotes best ucast next-hop
'**' denotes best mcast next-hop
'[x/y]' denotes [preference/metric]
'%<string>' in via output denotes VRF <string>

10.0.0.2/32, ubest/mbest: 2/0
    *via 172.16.0.1, [200/0], 14:09:00, bgp-64086.59904, internal, tag 4200000000
    *via 172.16.0.3, [200/0], 14:09:00, bgp-64086.59904, internal, tag 4200000000
10.0.0.3/32, ubest/mbest: 2/0
    *via 172.16.0.1, [200/0], 14:08:59, bgp-64086.59904, internal, tag 4200000000
    *via 172.16.0.3, [200/0], 14:08:59, bgp-64086.59904, internal, tag 4200000000
10.0.0.4/32, ubest/mbest: 1/0
    *via 172.16.0.1, [200/0], 14:09:01, bgp-64086.59904, internal, tag 4200000000
10.0.0.5/32, ubest/mbest: 1/0
    *via 172.16.0.3, [200/0], 14:09:01, bgp-64086.59904, internal, tag 4200000000
```
### Проверка работоспособности балансировки до Loopback адреса Leaf_2 роутера как примерного через Spine_1 RR и Spine_2 RR
```
Leaf_1# sh ip bgp 10.0.0.2/32
BGP routing table information for VRF default, address family IPv4 Unicast
BGP routing table entry for 10.0.0.2/32, version 50
Paths: (2 available, best #2)
Flags: (0x08001a) (high32 00000000) on xmit-list, is in urib, is best urib route, is in HW
Multipath: iBGP

  Path type: internal, path is valid, not best reason: Neighbor Address, multipath, no labeled nexthop, in rib
  AS-Path: NONE, path sourced internal to AS
    172.16.0.3 (metric 0) from 172.16.0.3 (10.0.0.5)
      Origin incomplete, MED 0, localpref 100, weight 0
      Originator: 10.0.0.2 Cluster list: 10.0.0.5

  Advertised path-id 1
  Path type: internal, path is valid, is best path, no labeled nexthop, in rib
  AS-Path: NONE, path sourced internal to AS
    172.16.0.1 (metric 0) from 172.16.0.1 (10.0.0.4)
      Origin incomplete, MED 0, localpref 100, weight 0
      Originator: 10.0.0.2 Cluster list: 10.0.0.4
```
```
Leaf_1# sh ip route 10.0.0.2/32 detail
IP Route Table for VRF "default"
'*' denotes best ucast next-hop
'**' denotes best mcast next-hop
'[x/y]' denotes [preference/metric]
'%<string>' in via output denotes VRF <string>

10.0.0.2/32, ubest/mbest: 2/0
    *via 172.16.0.1, [200/0], 14:12:09, bgp-64086.59904, internal, tag 4200000000
         client-specific data: 3
         recursive next hop: 172.16.0.1/32
         extended route information: BGP origin AS 4200000000 BGP peer AS 4200000000
    *via 172.16.0.3, [200/0], 14:12:09, bgp-64086.59904, internal, tag 4200000000
         client-specific data: 4
         recursive next hop: 172.16.0.3/32
         extended route information: BGP origin AS 4200000000 BGP peer AS 4200000000
```
### Проверка сетевой связности между Loopback адресами Leaf и Spine роутеров.
```
Leaf_1# ping 10.0.0.2 source 10.0.0.1
PING 10.0.0.2 (10.0.0.2) from 10.0.0.1: 56 data bytes
64 bytes from 10.0.0.2: icmp_seq=0 ttl=253 time=26.081 ms
64 bytes from 10.0.0.2: icmp_seq=1 ttl=253 time=15.166 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=253 time=24.061 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=253 time=19.009 ms
64 bytes from 10.0.0.2: icmp_seq=4 ttl=253 time=20.192 ms

--- 10.0.0.2 ping statistics ---
5 packets transmitted, 5 packets received, 0.00% packet loss
round-trip min/avg/max = 15.166/20.901/26.081 ms
Leaf_1# ping 10.0.0.3 source 10.0.0.1
PING 10.0.0.3 (10.0.0.3) from 10.0.0.1: 56 data bytes
64 bytes from 10.0.0.3: icmp_seq=0 ttl=253 time=47.852 ms
64 bytes from 10.0.0.3: icmp_seq=1 ttl=253 time=18.499 ms
64 bytes from 10.0.0.3: icmp_seq=2 ttl=253 time=24.648 ms
64 bytes from 10.0.0.3: icmp_seq=3 ttl=253 time=17.278 ms
64 bytes from 10.0.0.3: icmp_seq=4 ttl=253 time=62.508 ms

--- 10.0.0.3 ping statistics ---
5 packets transmitted, 5 packets received, 0.00% packet loss
round-trip min/avg/max = 17.278/34.156/62.508 ms
Leaf_1# ping 10.0.0.4 source 10.0.0.1
PING 10.0.0.4 (10.0.0.4) from 10.0.0.1: 56 data bytes
64 bytes from 10.0.0.4: icmp_seq=0 ttl=254 time=23.52 ms
64 bytes from 10.0.0.4: icmp_seq=1 ttl=254 time=20.92 ms
64 bytes from 10.0.0.4: icmp_seq=2 ttl=254 time=42.541 ms
64 bytes from 10.0.0.4: icmp_seq=3 ttl=254 time=16.513 ms
64 bytes from 10.0.0.4: icmp_seq=4 ttl=254 time=31.28 ms

--- 10.0.0.4 ping statistics ---
5 packets transmitted, 5 packets received, 0.00% packet loss
round-trip min/avg/max = 16.513/26.954/42.541 ms
Leaf_1# ping 10.0.0.5 source 10.0.0.1
PING 10.0.0.5 (10.0.0.5) from 10.0.0.1: 56 data bytes
64 bytes from 10.0.0.5: icmp_seq=0 ttl=254 time=11.092 ms
64 bytes from 10.0.0.5: icmp_seq=1 ttl=254 time=7.804 ms
64 bytes from 10.0.0.5: icmp_seq=2 ttl=254 time=12.178 ms
64 bytes from 10.0.0.5: icmp_seq=3 ttl=254 time=7.213 ms
64 bytes from 10.0.0.5: icmp_seq=4 ttl=254 time=10.117 ms

--- 10.0.0.5 ping statistics ---
5 packets transmitted, 5 packets received, 0.00% packet loss
round-trip min/avg/max = 7.213/9.68/12.178 ms
```
