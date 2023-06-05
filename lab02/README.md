# Настройка underlay сети в CLOS топологии из пяти устройств Cisco Nexus 9k. (IS-IS version)
Цели
1) Очистить RIB от маршрутов известных ранее через протокол OSPF, выключив его в корне настройки.
2) Создать и поднять протокол IS-IS.
3) Корректно указать system-id для протокола IS-IS исходя из установки идентификатора "net".
4) Проверить отображение ожидаемых loopback адресов средствами протокола IS-IS.
5) Проверить сетевую связность до всех Loopback адресов.
# Целевая схема
![Снимок](https://github.com/Anumrak/EVPN_labs/assets/133969023/6207ac40-14de-454f-ac56-6adfd13a0d87)

Адресное пространство для link интерфейсов

> 172.16.0.0/24

Адресное пространство для loopback интерфейсов

> 10.0.0.0/24

### Отключение протокола OSPF:
```
router ospf 100
  router-id 10.0.0.1
  log-adjacency-changes detail
  area 0.0.0.0 range 10.0.0.1/32
  area 0.0.0.0 range 172.16.0.0/31
  area 0.0.0.0 range 172.16.0.2/31
  shutdown
  passive-interface default
```
Конфигурация типового интерфейса на примере роутера Leaf_1
```
interface Ethernet1/1
  description -M- | Leaf_1 to Spine_1 | PTP
  no switchport
  mtu 9216
  no ip redirects
  ip address 172.16.0.0/31
  no ipv6 redirects
  no isis hello-padding always
  isis network point-to-point
  ip router isis 100
  ip ospf network point-to-point
  no ip ospf passive-interface
  ip router ospf 100 area 0.0.0.0
  no shutdown
```
Команда "no isis hello-padding always" нужна для того, чтобы запретить отправлять с интерфейса hello пакеты с полным mtu, и начать отправлять пакеты с минимально необходимым размером, например всего в 72 байта, для служебной информации работы протокола.

Конфигурация типового процесса isis на примере роутера Leaf_1
```
router isis 100
  net 49.0001.0100.0000.0001.00
  is-type level-1
  log-adjacency-changes
```
На Spine роутерах конфигурация отличается выбором зоны уровня 1-2, потому что они должны иметь и пересылать все базы данных о маршрутах, как 1го атк и 2го уровней всем.
По умолчанию, isis процесс работает на уровне 1-2, поэтому этой строчки в конфиге не видно.

```
router isis 100
  net 49.0001.0100.0000.0004.00
  log-adjacency-changes
```
### Вывод isis соседства между всеми устройствами и топологии соседств в RIB от LSB 1го уровня.
```
Leaf_1# sh isis 100 adjacency
IS-IS process: 100 VRF: default
IS-IS adjacency database:
Legend: '!': No AF level connectivity in given topology
System ID       SNPA            Level  State  Hold Time  Interface
Spine_1         N/A             1      UP     00:00:26   Ethernet1/1
Spine_2         N/A             1      UP     00:00:27   Ethernet1/2

Leaf_1# sh isis 100 topology
IS-IS process: 100
VRF: default
Topology ID: 0

IS-IS Level-1 IS routing table
Leaf_2.00, Instance 0x0000001A
   *via Spine_1, Ethernet1/1, metric 80
   *via Spine_2, Ethernet1/2, metric 80
Leaf_3.00, Instance 0x0000001A
   *via Spine_1, Ethernet1/1, metric 80
   *via Spine_2, Ethernet1/2, metric 80
Spine_1.00, Instance 0x0000001A
   *via Spine_1, Ethernet1/1, metric 40
Spine_2.00, Instance 0x0000001A
   *via Spine_2, Ethernet1/2, metric 40
```
```
Leaf_2# sh isis 100 adjacency
IS-IS process: 100 VRF: default
IS-IS adjacency database:
Legend: '!': No AF level connectivity in given topology
System ID       SNPA            Level  State  Hold Time  Interface
Spine_1         N/A             1      UP     00:00:26   Ethernet1/1
Spine_2         N/A             1      UP     00:00:26   Ethernet1/2

Leaf_2# sh isis 100 topology
IS-IS process: 100
VRF: default
Topology ID: 0

IS-IS Level-1 IS routing table
Leaf_1.00, Instance 0x00000018
   *via Spine_1, Ethernet1/1, metric 80
   *via Spine_2, Ethernet1/2, metric 80
Leaf_3.00, Instance 0x00000018
   *via Spine_1, Ethernet1/1, metric 80
   *via Spine_2, Ethernet1/2, metric 80
Spine_1.00, Instance 0x00000018
   *via Spine_1, Ethernet1/1, metric 40
Spine_2.00, Instance 0x00000018
   *via Spine_2, Ethernet1/2, metric 40
```
```
Leaf_3# sh isis 100 adjacency
IS-IS process: 100 VRF: default
IS-IS adjacency database:
Legend: '!': No AF level connectivity in given topology
System ID       SNPA            Level  State  Hold Time  Interface
Spine_1         N/A             1      UP     00:00:27   Ethernet1/1
Spine_2         N/A             1      UP     00:00:29   Ethernet1/2

Leaf_3# sh isis 100 topology
IS-IS process: 100
VRF: default
Topology ID: 0

IS-IS Level-1 IS routing table
Leaf_1.00, Instance 0x00000014
   *via Spine_1, Ethernet1/1, metric 80
   *via Spine_2, Ethernet1/2, metric 80
Leaf_2.00, Instance 0x00000014
   *via Spine_1, Ethernet1/1, metric 80
   *via Spine_2, Ethernet1/2, metric 80
Spine_1.00, Instance 0x00000014
   *via Spine_1, Ethernet1/1, metric 40
Spine_2.00, Instance 0x00000014
   *via Spine_2, Ethernet1/2, metric 40
```
```
Spine_1# sh isis 100 adjacency
IS-IS process: 100 VRF: default
IS-IS adjacency database:
Legend: '!': No AF level connectivity in given topology
System ID       SNPA            Level  State  Hold Time  Interface
Leaf_1          N/A             1      UP     00:00:31   Ethernet1/1
Leaf_2          N/A             1      UP     00:00:26   Ethernet1/2
Leaf_3          N/A             1      UP     00:00:22   Ethernet1/3

Spine_1# sh isis 100 topology
IS-IS process: 100
VRF: default
Topology ID: 0

IS-IS Level-1 IS routing table
Leaf_1.00, Instance 0x0000001C
   *via Leaf_1, Ethernet1/1, metric 40
Leaf_2.00, Instance 0x0000001C
   *via Leaf_2, Ethernet1/2, metric 40
Leaf_3.00, Instance 0x0000001C
   *via Leaf_3, Ethernet1/3, metric 40
Spine_2.00, Instance 0x0000001C
   *via Leaf_1, Ethernet1/1, metric 80
   *via Leaf_2, Ethernet1/2, metric 80
   *via Leaf_3, Ethernet1/3, metric 80
```
```
Spine_2# sh isis 100 adjacency
IS-IS process: 100 VRF: default
IS-IS adjacency database:
Legend: '!': No AF level connectivity in given topology
System ID       SNPA            Level  State  Hold Time  Interface
Leaf_1          N/A             1      UP     00:00:25   Ethernet1/1
Leaf_2          N/A             1      UP     00:00:21   Ethernet1/2
Leaf_3          N/A             1      UP     00:00:28   Ethernet1/3

Spine_2# sh isis 100 topology
IS-IS process: 100
VRF: default
Topology ID: 0

IS-IS Level-1 IS routing table
Leaf_1.00, Instance 0x0000000F
   *via Leaf_1, Ethernet1/1, metric 40
Leaf_2.00, Instance 0x0000000F
   *via Leaf_2, Ethernet1/2, metric 40
Leaf_3.00, Instance 0x0000000F
   *via Leaf_3, Ethernet1/3, metric 40
Spine_1.00, Instance 0x0000000F
   *via Leaf_1, Ethernet1/1, metric 80
   *via Leaf_2, Ethernet1/2, metric 80
   *via Leaf_3, Ethernet1/3, metric 80
```
### Вывод RIB на примере Leaf_1
```
Leaf_1# sh ip route isis
IP Route Table for VRF "default"
'*' denotes best ucast next-hop
'**' denotes best mcast next-hop
'[x/y]' denotes [preference/metric]
'%<string>' in via output denotes VRF <string>

10.0.0.2/32, ubest/mbest: 2/0
    *via 172.16.0.1, Eth1/1, [115/81], 00:53:38, isis-100, L1
    *via 172.16.0.3, Eth1/2, [115/81], 00:51:55, isis-100, L1
10.0.0.3/32, ubest/mbest: 2/0
    *via 172.16.0.1, Eth1/1, [115/81], 00:53:25, isis-100, L1
    *via 172.16.0.3, Eth1/2, [115/81], 00:51:45, isis-100, L1
10.0.0.4/32, ubest/mbest: 1/0
    *via 172.16.0.1, Eth1/1, [115/41], 00:53:27, isis-100, L1
10.0.0.5/32, ubest/mbest: 1/0
    *via 172.16.0.3, Eth1/2, [115/41], 00:51:47, isis-100, L1
172.16.0.4/31, ubest/mbest: 1/0
    *via 172.16.0.1, Eth1/1, [115/80], 00:53:51, isis-100, L1
172.16.0.6/31, ubest/mbest: 1/0
    *via 172.16.0.3, Eth1/2, [115/80], 00:52:05, isis-100, L1
172.16.0.8/31, ubest/mbest: 1/0
    *via 172.16.0.1, Eth1/1, [115/80], 00:53:37, isis-100, L1
172.16.0.10/31, ubest/mbest: 1/0
    *via 172.16.0.3, Eth1/2, [115/80], 00:51:57, isis-100, L1
```
### Проверка router-id соседей в LSDB на примере роутера Leaf_01:
```
Leaf_1# sh isis 100 database router-id 10.0.0.4
IS-IS Process: 100 LSP database VRF: default
IS-IS Level-1 Link State Database
  LSPID                 Seq Number   Checksum  Lifetime   A/P/O/T
  Spine_1.00-00         0x0000000E   0x68D0    760        0/0/0/3

IS-IS Level-2 Link State Database
  LSPID                 Seq Number   Checksum  Lifetime   A/P/O/T

Leaf_1# sh isis 100 database detail 0100.0000.0004.00-00
IS-IS Process: 100 LSP database VRF: default
IS-IS Level-1 Link State Database
  LSPID                 Seq Number   Checksum  Lifetime   A/P/O/T
  Spine_1.00-00         0x00000010   0x64D2    930        0/0/0/3
    Instance      :  0x0000000E
    Area Address  :  49.0001
    NLPID         :  0xCC
    Router ID     :  10.0.0.4
    IP Address    :  10.0.0.4
    Hostname      :  Spine_1            Length : 7
    Extended IS   :  Leaf_3.00          Metric : 40
      Interface IP Address :  172.16.0.9
      IP Neighbor Address :  172.16.0.8
    Extended IS   :  Leaf_2.00          Metric : 40
      Interface IP Address :  172.16.0.5
      IP Neighbor Address :  172.16.0.4
    Extended IS   :  Leaf_1.00          Metric : 40
      Interface IP Address :  172.16.0.1
      IP Neighbor Address :  172.16.0.0
    Extended IP   :        10.0.0.4/32  Metric : 1           (U)
    Extended IP   :      172.16.0.8/31  Metric : 40          (U)
    Extended IP   :      172.16.0.4/31  Metric : 40          (U)
    Extended IP   :      172.16.0.0/31  Metric : 40          (U)
    Digest Offset :  0
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