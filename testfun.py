from multiprocessing import Pool
import os,time,random

def run(name):
    print("子进程启动")


if __name__ == "__main__":
    print("父进程启动")
    pp = Pool(2)
    for i in range(5):
        pp.apply_async(run,args = (i,))
    pp.close()
    pp.join()
    print("父进程结束")