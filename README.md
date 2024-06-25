# ds-project

Research on information dissemination methods in distributed systems.

## Команды для запуска

```bash
# BROADCAST, все значения по умолчанию
$ python3 ./disseminator.py broadcast
# INFO:root:total: 2 msgs, discarded: 0 msgs
# INFO:root:expected: 0.000000, actual: 0.000000
# INFO:root:SUCCEED in dissemination: (1/2000) rounds


# GOSSIP
# gossip-pull, число узлов в группе 5, всего узлов 100
$ python3 ./disseminator.py -n 100 gossip pull 5
# INFO:root:total: 941 msgs, discarded: 0 msgs
# INFO:root:expected: 0.000000, actual: 0.000000
# INFO:root:SUCCEED in dissemination: (2/2000) rounds

# gossip-push, число узлов в группе 5, всего узлов 100
$ python3 ./disseminator.py -n 100 gossip push 5
# INFO:root:total: 615 msgs, discarded: 0 msgs
# INFO:root:expected: 0.000000, actual: 0.000000
# INFO:root:SUCCEED in dissemination: (4/2000) rounds

# gossip-push-pull, число узлов в группе 5, всего узлов 100
$ python3 ./disseminator.py -n 100 gossip push-pull 5
# INFO:root:total: 758 msgs, discarded: 0 msgs
# INFO:root:expected: 0.000000, actual: 0.000000
# INFO:root:SUCCEED in dissemination: (3/2000) rounds


# MULTICAST, число узлов в группе 5, всего узлов 100
$ python3 ./disseminator.py -n 100 multicast 5
# INFO:root:total: 4850 msgs, discarded: 0 msgs
# INFO:root:expected: 0.000000, actual: 0.000000
# INFO:root:SUCCEED in dissemination: (20/2000) rounds


# SIGLECAST
$ python3 ./disseminator.py singlecast
# INFO:root:total: 3 msgs, discarded: 0 msgs
# INFO:root:expected: 0.000000, actual: 0.000000
# INFO:root:SUCCEED in dissemination: (2/2000) rounds
```

### Пример с ненулевой вероятностью потери сообщений

```bash
# GOSSIP: в режиме push-pull, 100 узлов, 90% вероятность потери, 5 узлов в push-группе, 10 узлов в pull-группе
$ python3 ./disseminator.py -n 100 -c 90 gossip push-pull 5 10
# INFO:root:total: 13968 msgs, discarded: 12524 msgs
# INFO:root:expected: 0.900000, actual: 0.896621
# INFO:root:SUCCEED in dissemination: (19/2000) rounds
```

## Вывод с опцией help

```bash
$ python3 ./disseminator.py --help
Usage: disseminator.py [OPTIONS] COMMAND [ARGS]...

Options:
  -n, --nodes INTEGER      Number of nodes  [default: 3]
  -l, --limit INTEGER      Maximum rounds of simulation  [default: 2000]
  -c, --loss-chance FLOAT  probability% of losing a message  [default: 0.0]
  -v, --verbose            Set verbosity level, default INFO
  --help                   Show this message and exit.

Commands:
  broadcast
  gossip
  multicast
  singlecast
```
