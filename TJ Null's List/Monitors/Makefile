obj-m +=reverse-shell.o
all:
	make -C /lib/modules/6.6.15-amd64/build M=$(pwd) modules
clean:
	make -C /lib/modules/6.6.15-amd64/build M=$(pwd) clean
