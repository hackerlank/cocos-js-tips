#!/bin/sh

PYTHON=/usr/bin/python
ROOTDIR=`cd $(dirname $0); pwd`

running() {
    case "$2" in
        start)
            nohup $PYTHON $ROOTDIR/runserver.py --plat=$1 --port=$PORT --settings=settings.$SETTING >> log &
            ;;
        stop)
            ps -ef | grep "port=$PORT" | grep -v "grep" | awk '{print $2}' | xargs kill -9
            ;;
        restart)
            ps -ef | grep "port=$PORT" | grep -v "grep" | awk '{print $2}' | xargs kill -9
            sleep 3
            nohup $PYTHON $ROOTDIR/runserver.py --plat=$1 --port=$PORT --settings=settings.$SETTING >> log &
            ;;
        *)
            echo $"Usage: {local|dev|prod} {ios|android|apple} {start|stop|restart}"
            exit 1
    esac
}

case "$1" in
    local)
        PORT=8000
        SETTING="local"
        running $2 $3
        ;;
    dev)
        PORT=8000
        SETTING="dev"
        cp cfgs/dev_storage.conf apps/configs/app_config/storage.conf
        running $2 $3
        ;;
    prod)
        PORT=80
        SETTING="prod"
        running $2 $3
        ;;
    *)
        echo $"Usage: {local|dev|prod} {ios|android|apple} {start|stop|restart}"
        exit 1
esac
