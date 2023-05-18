# Настройка underlay сети в CLOS топологии из пяти устройств Cisco Nexus 9k.
Цели
1) Поднять сетевые интерфейсы между всеми устройствами в рамках указанной топологии.
2) Создать и поднять loopback интерфейсы на всех устройствах.
3) Экономно распределить адресное пространство между всеми устройствами и их интерфейсами.
4) Включить все необходимые сервисы для работы в будущем, такие как ospf, isis, bgp, bfd.
5) В виде теста, включить и настроить ospfv2 между Leaf и Spine роутерами.
# Целевая схема
![Снимок](https://github.com/Anumrak/EVPN_labs/assets/133969023/6207ac40-14de-454f-ac56-6adfd13a0d87)

Адресное пространство для link интерфейсов

> 172.16.0.0/24

Адресное пространство для loopback интерфейсов

> 10.0.0.0/24

Конфигурация типового интерфейса на примере роутера Leaf_1
```
interface Ethernet1/1
  description -M- | Leaf_1 to Spine_1 | PTP
  no switchport
  mtu 9216
  no ip redirects
  ip address 172.16.0.0/31
  no ipv6 redirects
  ip ospf network point-to-point
  no ip ospf passive-interface
  ip router ospf 100 area 0.0.0.0
  no shutdown
```
Конфигурация типового процесса ospf на примере роутера Leaf_1
```
router ospf 100
  router-id 10.0.0.1
  log-adjacency-changes detail
  area 0.0.0.0 range 10.0.0.1/32
  area 0.0.0.0 range 172.16.0.0/31
  area 0.0.0.0 range 172.16.0.2/31
  passive-interface default
```
Конфигурация на Spine роутерах аналогична.

### Вывод ospf соседства между всеми устройствами и базы данных состояния каналов.
```
Leaf_1# sh ip ospf neighbors
 OSPF Process ID 100 VRF default
 Total number of neighbors: 2
 Neighbor ID     Pri State            Up Time  Address         Interface
 10.0.0.4          1 FULL/ -          02:23:56 172.16.0.1      Eth1/1
 10.0.0.5          1 FULL/ -          02:07:01 172.16.0.3      Eth1/2
Leaf_1# sh ip ospf database
        OSPF Router with ID (10.0.0.1) (Process ID 100 VRF default)

                Router Link States (Area 0.0.0.0)

Link ID         ADV Router      Age        Seq#       Checksum Link Count
10.0.0.1        10.0.0.1        1282       0x80000010 0xb181   5
10.0.0.2        10.0.0.2        531        0x8000000b 0xc75d   5
10.0.0.3        10.0.0.3        534        0x8000000b 0xd33e   5
10.0.0.4        10.0.0.4        845        0x8000000d 0x28ff   7
10.0.0.5        10.0.0.5        394        0x8000000b 0x5fbb   7
```
```
Leaf_2# sh ip ospf neighbors
 OSPF Process ID 100 VRF default
 Total number of neighbors: 2
 Neighbor ID     Pri State            Up Time  Address         Interface
 10.0.0.4          1 FULL/ -          02:14:46 172.16.0.5      Eth1/1
 10.0.0.5          1 FULL/ -          02:09:19 172.16.0.7      Eth1/2
Leaf_2# sh ip ospf database
        OSPF Router with ID (10.0.0.2) (Process ID 100 VRF default)

                Router Link States (Area 0.0.0.0)

Link ID         ADV Router      Age        Seq#       Checksum Link Count
10.0.0.1        10.0.0.1        1457       0x80000010 0xb181   5
10.0.0.2        10.0.0.2        703        0x8000000b 0xc75d   5
10.0.0.3        10.0.0.3        708        0x8000000b 0xd33e   5
10.0.0.4        10.0.0.4        1019       0x8000000d 0x28ff   7
10.0.0.5        10.0.0.5        567        0x8000000b 0x5fbb   7
```
```
Leaf_3# sh ip ospf neighbors
 OSPF Process ID 100 VRF default
 Total number of neighbors: 2
 Neighbor ID     Pri State            Up Time  Address         Interface
 10.0.0.4          1 FULL/ -          01:46:48 172.16.0.9      Eth1/1
 10.0.0.5          1 FULL/ -          01:41:23 172.16.0.11     Eth1/2
Leaf_3#
Leaf_3# sh ip ospf database
        OSPF Router with ID (10.0.0.3) (Process ID 100 VRF default)

                Router Link States (Area 0.0.0.0)

Link ID         ADV Router      Age        Seq#       Checksum Link Count
10.0.0.1        10.0.0.1        1522       0x80000010 0xb181   5
10.0.0.2        10.0.0.2        769        0x8000000b 0xc75d   5
10.0.0.3        10.0.0.3        770        0x8000000b 0xd33e   5
10.0.0.4        10.0.0.4        1083       0x8000000d 0x28ff   7
10.0.0.5        10.0.0.5        632        0x8000000b 0x5fbb   7
```
```
Spine_1# sh ip ospf neighbors
 OSPF Process ID 100 VRF default
 Total number of neighbors: 3
 Neighbor ID     Pri State            Up Time  Address         Interface
 10.0.0.1          1 FULL/ -          02:23:47 172.16.0.0      Eth1/1
 10.0.0.2          1 FULL/ -          02:14:33 172.16.0.4      Eth1/2
 10.0.0.3          1 FULL/ -          02:14:32 172.16.0.8      Eth1/3
Spine_1# sh ip ospf database
        OSPF Router with ID (10.0.0.4) (Process ID 100 VRF default)

                Router Link States (Area 0.0.0.0)

Link ID         ADV Router      Age        Seq#       Checksum Link Count
10.0.0.1        10.0.0.1        1539       0x80000010 0xb181   5
10.0.0.2        10.0.0.2        787        0x8000000b 0xc75d   5
10.0.0.3        10.0.0.3        790        0x8000000b 0xd33e   5
10.0.0.4        10.0.0.4        1101       0x8000000d 0x28ff   7
10.0.0.5        10.0.0.5        651        0x8000000b 0x5fbb   7
```
```
Spine_2# sh ip ospf neighbors
 OSPF Process ID 100 VRF default
 Total number of neighbors: 3
 Neighbor ID     Pri State            Up Time  Address         Interface
 10.0.0.1          1 FULL/ -          01:39:20 172.16.0.2      Eth1/1
 10.0.0.2          1 FULL/ -          01:41:35 172.16.0.6      Eth1/2
 10.0.0.3          1 FULL/ -          01:41:36 172.16.0.10     Eth1/3
Spine_2#
Spine_2# sh ip ospf database
        OSPF Router with ID (10.0.0.5) (Process ID 100 VRF default)

                Router Link States (Area 0.0.0.0)

Link ID         ADV Router      Age        Seq#       Checksum Link Count
10.0.0.1        10.0.0.1        1561       0x80000010 0xb181   5
10.0.0.2        10.0.0.2        808        0x8000000b 0xc75d   5
10.0.0.3        10.0.0.3        811        0x8000000b 0xd33e   5
10.0.0.4        10.0.0.4        1124       0x8000000d 0x28ff   7
10.0.0.5        10.0.0.5        671        0x8000000b 0x5fbb   7
```
### Вывод RIB на примере Leaf_1
```
Leaf_1#
Leaf_1# sh ip route
IP Route Table for VRF "default"
'*' denotes best ucast next-hop
'**' denotes best mcast next-hop
'[x/y]' denotes [preference/metric]
'%<string>' in via output denotes VRF <string>

10.0.0.1/32, ubest/mbest: 2/0, attached
    *via 10.0.0.1, Lo0, [0/0], 03:19:09, local
    *via 10.0.0.1, Lo0, [0/0], 03:19:08, direct
10.0.0.2/32, ubest/mbest: 2/0
    *via 172.16.0.1, Eth1/1, [110/81], 02:16:55, ospf-100, intra
    *via 172.16.0.3, Eth1/2, [110/81], 02:09:20, ospf-100, intra
10.0.0.3/32, ubest/mbest: 2/0
    *via 172.16.0.1, Eth1/1, [110/81], 02:16:54, ospf-100, intra
    *via 172.16.0.3, Eth1/2, [110/81], 02:09:20, ospf-100, intra
10.0.0.4/32, ubest/mbest: 1/0
    *via 172.16.0.1, Eth1/1, [110/41], 02:22:00, ospf-100, intra
10.0.0.5/32, ubest/mbest: 1/0
    *via 172.16.0.3, Eth1/2, [110/41], 02:09:20, ospf-100, intra
172.16.0.0/31, ubest/mbest: 1/0, attached
    *via 172.16.0.0, Eth1/1, [0/0], 02:31:21, direct
172.16.0.0/32, ubest/mbest: 1/0, attached
    *via 172.16.0.0, Eth1/1, [0/0], 02:31:21, local
172.16.0.2/31, ubest/mbest: 1/0, attached
    *via 172.16.0.2, Eth1/2, [0/0], 03:39:30, direct
172.16.0.2/32, ubest/mbest: 1/0, attached
    *via 172.16.0.2, Eth1/2, [0/0], 03:39:30, local
172.16.0.4/31, ubest/mbest: 1/0
    *via 172.16.0.1, Eth1/1, [110/80], 02:26:11, ospf-100, intra
172.16.0.6/31, ubest/mbest: 1/0
    *via 172.16.0.3, Eth1/2, [110/80], 02:09:20, ospf-100, intra
172.16.0.8/31, ubest/mbest: 1/0
    *via 172.16.0.1, Eth1/1, [110/80], 02:26:11, ospf-100, intra
172.16.0.10/31, ubest/mbest: 1/0
    *via 172.16.0.3, Eth1/2, [110/80], 02:09:20, ospf-100, intra
```
### Проверка сетевой связности между Loopback интерфейсами всех нод от Leaf_1
```
Leaf_1# ping 10.0.0.2
PING 10.0.0.2 (10.0.0.2): 56 data bytes
64 bytes from 10.0.0.2: icmp_seq=0 ttl=253 time=22.859 ms
64 bytes from 10.0.0.2: icmp_seq=1 ttl=253 time=16.309 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=253 time=20.209 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=253 time=18.856 ms
64 bytes from 10.0.0.2: icmp_seq=4 ttl=253 time=9.093 ms

--- 10.0.0.2 ping statistics ---
5 packets transmitted, 5 packets received, 0.00% packet loss
round-trip min/avg/max = 9.093/17.465/22.859 ms
Leaf_1# ping 10.0.0.3
PING 10.0.0.3 (10.0.0.3): 56 data bytes
64 bytes from 10.0.0.3: icmp_seq=0 ttl=253 time=10.375 ms
64 bytes from 10.0.0.3: icmp_seq=1 ttl=253 time=11.689 ms
64 bytes from 10.0.0.3: icmp_seq=2 ttl=253 time=10.54 ms
64 bytes from 10.0.0.3: icmp_seq=3 ttl=253 time=12.145 ms
64 bytes from 10.0.0.3: icmp_seq=4 ttl=253 time=16.138 ms

--- 10.0.0.3 ping statistics ---
5 packets transmitted, 5 packets received, 0.00% packet loss
round-trip min/avg/max = 10.375/12.177/16.138 ms
Leaf_1# ping 10.0.0.4
PING 10.0.0.4 (10.0.0.4): 56 data bytes
64 bytes from 10.0.0.4: icmp_seq=0 ttl=254 time=6.049 ms
64 bytes from 10.0.0.4: icmp_seq=1 ttl=254 time=6.116 ms
64 bytes from 10.0.0.4: icmp_seq=2 ttl=254 time=7.597 ms
64 bytes from 10.0.0.4: icmp_seq=3 ttl=254 time=6.125 ms
64 bytes from 10.0.0.4: icmp_seq=4 ttl=254 time=6.086 ms

--- 10.0.0.4 ping statistics ---
5 packets transmitted, 5 packets received, 0.00% packet loss
round-trip min/avg/max = 6.049/6.394/7.597 ms
Leaf_1# ping 10.0.0.5
PING 10.0.0.5 (10.0.0.5): 56 data bytes
64 bytes from 10.0.0.5: icmp_seq=0 ttl=254 time=4.914 ms
64 bytes from 10.0.0.5: icmp_seq=1 ttl=254 time=3.414 ms
64 bytes from 10.0.0.5: icmp_seq=2 ttl=254 time=5.48 ms
64 bytes from 10.0.0.5: icmp_seq=3 ttl=254 time=5.676 ms
64 bytes from 10.0.0.5: icmp_seq=4 ttl=254 time=6.697 ms

--- 10.0.0.5 ping statistics ---
5 packets transmitted, 5 packets received, 0.00% packet loss
round-trip min/avg/max = 3.414/5.236/6.697 ms
```

