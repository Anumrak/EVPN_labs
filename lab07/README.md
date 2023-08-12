# Настройка underlay сети в CLOS топологии из пяти устройств Cisco Nexus 9k. (VXLAN over MP-BGP EVPN vPC version)
Цели
1) Настроить port-channel интерфейс на Client_Router до Leaf_1 и Leaf_2.
2) Создать и vPC домен на свитчах Leaf_1 и Leaf_2.
3) Настроить vPC peer keepalive интерфейсы между Leaf_1 и Leaf_2.
4) Настроить vPC peer link между Leaf_1 и Leaf_2.
5) Настройка port-channel до клиентского роутера Client_Router.
6) Настроить вторичный IP адрес на интерфейсе Loopback 0 (Anycast vPC SVI IP), одинаковый для Leaf_1 и Leaf_2, для успешной vPC связи между свитчами.
7) Настроить SVI интерфейс для роутинга трафика Client_Router.
8) Проверить состояние vPC связи между Leaf_1 и Leaf_2.
9) Проверить приоритет ролей между Leaf_1 и Leaf_2.
10) Проверить состояние port-channel клиента Client_Router.
11) Настроить BGP анонсирование evpn route-type 5 маршрута сети Client_Router для Leaf_3.
12) Проверить BGP обновление с evpn route-type 5 сети Client_Router на Spine от Anycast VTEP адреса vPC домена.
13) Проверить установку BGP обновления в L3RIB Leaf_3.
14) Проверить сетевую связность между клиентом Leaf_3 и Client_Router сетью.
# Целевая схема
![Снимок](https://github.com/Anumrak/EVPN_labs/assets/133969023/090ab0fd-c540-4503-8934-4834c4fd1294)

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
Настройка peer keepalive линка на примере Leaf_1
```
vrf context Keepalive
```
```
interface Ethernet1/10
  no switchport
  vrf member Keepalive
  ip address 192.168.255.0/31
  no shutdown
```
Настройка peer link между Leaf_1 и Leaf_2 на примере Leaf_1
```
interface Ethernet1/14
  switchport mode trunk
  channel-group 99 mode active

interface Ethernet1/15
  switchport mode trunk
  channel-group 99 mode active

interface port-channel99
  switchport mode trunk
  spanning-tree port type network
  vpc peer-link
```
Настройка port-channel до Client_Router на примере Leaf_1
```
interface Ethernet1/7
  description -C- | Client_Router eth 0/1 | Clients
  switchport mode trunk
  switchport trunk allowed vlan 400
  channel-group 7 mode active

interface port-channel7
  description -C- | Client_Router port 1 | Clients
  switchport mode trunk
  switchport trunk allowed vlan 400
  vpc 7
```
Настройка Anycast адреса для vPC SVI на примере Leaf_1
```
ip prefix-list pl_connected seq 5 permit 10.0.0.1/32
ip prefix-list pl_connected seq 10 permit 10.1.0.1/32
route-map rm_connected permit 10
  match ip address prefix-list pl_connected

interface loopback0
  description -L- | Router ID | Loopback
  ip address 10.0.0.1/32
  ip address 10.1.0.1/32 secondary
```
Настройка SVI интерфейса для роутинга трафика Client_Router на примере Leaf_1
```
interface Vlan400
  description Client_Router_GW
  no shutdown
  vrf member Leafs_L3VNI
  no ip redirects
  ip address 192.168.4.254/24
  no ipv6 redirects
  fabric forwarding mode anycast-gateway
```
### Проверка состояния vPC связи между Leaf_1 и Leaf_2
```
Leaf_1# sh vpc
Legend:
                (*) - local vPC is down, forwarding via vPC peer-link

vPC domain id                     : 1
Peer status                       : peer adjacency formed ok
vPC keep-alive status             : peer is alive
Configuration consistency status  : success
Per-vlan consistency status       : success
Type-2 consistency status         : success
vPC role                          : primary
Number of vPCs configured         : 1
Peer Gateway                      : Disabled
Dual-active excluded VLANs        : -
Graceful Consistency Check        : Enabled
Auto-recovery status              : Disabled
Delay-restore status              : Timer is off.(timeout = 30s)
Delay-restore SVI status          : Timer is off.(timeout = 10s)
Operational Layer3 Peer-router    : Disabled
Virtual-peerlink mode             : Disabled

vPC Peer-link status
---------------------------------------------------------------------
id    Port   Status Active vlans
--    ----   ------ -------------------------------------------------
1     Po99   up     1,100,200,300,400,777

vPC status
----------------------------------------------------------------------------
Id    Port          Status Consistency Reason                Active vlans
--    ------------  ------ ----------- ------                ---------------
7     Po7           up     success     success               400
```
```
Leaf_2# sh vpc
Legend:
                (*) - local vPC is down, forwarding via vPC peer-link

vPC domain id                     : 1
Peer status                       : peer adjacency formed ok
vPC keep-alive status             : peer is alive
Configuration consistency status  : success
Per-vlan consistency status       : success
Type-2 consistency status         : success
vPC role                          : secondary
Number of vPCs configured         : 1
Peer Gateway                      : Disabled
Dual-active excluded VLANs        : -
Graceful Consistency Check        : Enabled
Auto-recovery status              : Disabled
Delay-restore status              : Timer is off.(timeout = 30s)
Delay-restore SVI status          : Timer is off.(timeout = 10s)
Operational Layer3 Peer-router    : Disabled
Virtual-peerlink mode             : Disabled

vPC Peer-link status
---------------------------------------------------------------------
id    Port   Status Active vlans
--    ----   ------ -------------------------------------------------
1     Po99   up     1,100,200,300,400,777

vPC status
----------------------------------------------------------------------------
Id    Port          Status Consistency Reason                Active vlans
--    ------------  ------ ----------- ------                ---------------
7     Po7           up     success     success               400
```
### Проверка приоритета ролей между Leaf_1 и Leaf_2
```
Leaf_1# sh vpc role

vPC Role status
----------------------------------------------------
vPC role                        : primary
Dual Active Detection Status    : 0
vPC system-mac                  : 00:23:04:ee:be:01
vPC system-priority             : 32667
vPC local system-mac            : 50:01:00:00:1b:08
vPC local role-priority         : 1
vPC local config role-priority  : 1
vPC peer system-mac             : 50:02:00:00:1b:08
vPC peer role-priority          : 32667
vPC peer config role-priority   : 32667
```
```
Leaf_2# sh vpc role

vPC Role status
----------------------------------------------------
vPC role                        : secondary
Dual Active Detection Status    : 0
vPC system-mac                  : 00:23:04:ee:be:01
vPC system-priority             : 32667
vPC local system-mac            : 50:02:00:00:1b:08
vPC local role-priority         : 32667
vPC local config role-priority  : 32667
vPC peer system-mac             : 50:01:00:00:1b:08
vPC peer role-priority          : 1
vPC peer config role-priority   : 1
```
### Проверка состояния port-channel клиента Client_Router
```
Client_Router#sh int port 1
Port-channel1 is up, line protocol is up (connected)
  Hardware is EtherChannel, address is aabb.cc00.f020 (bia aabb.cc00.f020)
  Description: -M- | Leaf_1/Leaf_2 port 7 | Channel

Client_Router#sh lacp 1 neighbor
Flags:  S - Device is requesting Slow LACPDUs
        F - Device is requesting Fast LACPDUs
        A - Device is in Active mode       P - Device is in Passive mode

Channel group 1 neighbors

Partner's information:

                  LACP port                        Admin  Oper   Port    Port
Port      Flags   Priority  Dev ID          Age    key    Key    Number  State
Et0/1     SA      32768     0023.04ee.be01  16s    0x0    0x8007 0x107   0x3D
Et0/2     SA      32768     0023.04ee.be01   5s    0x0    0x8007 0x4107  0x3D
```
Настройка BGP анонсирования evpn route-type 5 маршрута сети Client_Router для Leaf_3 на примере Leaf_1
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
      network 192.168.4.0/24
```
### Проверка BGP обновления с evpn route-type 5 сети Client_Router на Spine от Anycast VTEP адреса vPC домена
```
Route Distinguisher: 10.0.0.1:7777
*>e[5]:[0]:[0]:[0]:[0.0.0.0]/224
                      10.1.0.1                                       0 4200000001 i
*>e[5]:[0]:[0]:[24]:[192.168.4.0]/224
                      10.1.0.1                                       0 4200000001 i
```
```
Spine_1# sh bgp l2vpn evpn 192.168.4.0
BGP routing table information for VRF default, address family L2VPN EVPN
Route Distinguisher: 10.0.0.1:7777
BGP routing table entry for [5]:[0]:[0]:[24]:[192.168.4.0]/224, version 8104
Paths: (1 available, best #1)
Flags: (0x000002) (high32 00000000) on xmit-list, is not in l2rib/evpn, is not in HW

  Advertised path-id 1
  Path type: external, path is valid, is best path, no labeled nexthop
  Gateway IP: 0.0.0.0
  AS-Path: 4200000001 , path sourced external to AS
    10.1.0.1 (metric 0) from 10.0.0.1 (10.0.0.1)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 7777
      Extcommunity: RT:4200000001:7777 ENCAP:8 Router MAC:5001.0000.1b08

  Path-id 1 advertised to peers:
    10.0.0.2           10.0.0.3

Route Distinguisher: 10.0.0.2:7777
BGP routing table entry for [5]:[0]:[0]:[24]:[192.168.4.0]/224, version 8113
Paths: (1 available, best #1)
Flags: (0x000002) (high32 00000000) on xmit-list, is not in l2rib/evpn, is not in HW

  Advertised path-id 1
  Path type: external, path is valid, is best path, no labeled nexthop
  Gateway IP: 0.0.0.0
  AS-Path: 4200000002 , path sourced external to AS
    10.1.0.1 (metric 0) from 10.0.0.2 (10.0.0.2)
      Origin IGP, MED not set, localpref 100, weight 0
      Received label 7777
      Extcommunity: RT:4200000002:7777 ENCAP:8 Router MAC:5002.0000.1b08

  Path-id 1 advertised to peers:
    10.0.0.1           10.0.0.3
```
### Проверка установки BGP обновления в L3RIB Leaf_3
```
192.168.4.0/24, ubest/mbest: 1/0
    *via 10.1.0.1%default, [20/0], 03:05:09, bgp-64086.59907, external, tag 4200000000, segid: 7777
tunnelid: 0xa010001 encap: VXLAN
```
### Проверка сетевой связности между клиентом Leaf_3 и Client_Router сетью
```
VPCS> sh ip

NAME        : VPCS[1]
IP/MASK     : 192.168.1.3/24
GATEWAY     : 192.168.1.254
DNS         :
MAC         : 00:50:79:66:68:08
LPORT       : 20000
RHOST:PORT  : 127.0.0.1:30000
MTU         : 1500

VPCS> ping 192.168.4.1

84 bytes from 192.168.4.1 icmp_seq=1 ttl=253 time=21.655 ms
84 bytes from 192.168.4.1 icmp_seq=2 ttl=253 time=16.560 ms
84 bytes from 192.168.4.1 icmp_seq=3 ttl=253 time=18.160 ms
84 bytes from 192.168.4.1 icmp_seq=4 ttl=253 time=16.794 ms
84 bytes from 192.168.4.1 icmp_seq=5 ttl=253 time=17.643 ms
```