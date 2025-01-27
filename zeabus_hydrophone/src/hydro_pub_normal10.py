#!/usr/bin/env python

import struct
import numpy
import math
import time
import serial
import numpy as np
import scipy.stats as stats
from zeabus_hydrophone.srv import hydro_info
from zeabus_hydrophone.msg import hydro_msg
import rospy
#ser = serial.Serial('/dev/ttyUSB0', 115200)
ser = serial.Serial('/dev/usb2serial/ftdi_AJ038YFU', 115200)
freq_s = 0
fre = 0
k = 0


def float_hex4(f):
	return ''.join(('%2.2x'%ord(c)) for c in struct.pack('<f', f))
def uint_hex4(I):
	return ''.join(('%2.2x'%ord(c)) for c in struct.pack('<I', I))
def set(mode,value):
	res = []
	res.append('\xff')
	res.append('\xff')
	#res.append(mode)
	if mode==0x00 or mode==0x01 or mode==0x04:
		print "uint32"
		if mode==0x00:
			res.append('\x00')
		elif mode==0x01:
			res.append('\x01')
		elif mode==0x04:
			res.append('\x04')
		tmp = uint_hex4(value)
		res.append(tmp[0:2].decode("hex"))
		res.append(tmp[2:4].decode("hex"))
		res.append(tmp[4:6].decode("hex"))
		res.append(tmp[6:8].decode("hex"))
	elif mode==0x02 or mode==0x03:
		print "float"
		if mode==0x02:
			res.append('\x02')
		elif mode==0x03:
			res.append('\x03')
		tmp = float_hex4(value)
		res.append(tmp[0:2].decode("hex"))
		res.append(tmp[2:4].decode("hex"))
		res.append(tmp[4:6].decode("hex"))
		res.append(tmp[6:8].decode("hex"))
	res.append('\x00')
	#print list(array.array('B', res).tostring())
	print res
	return ''.join(res)


class particleFilter:
    def __init__(self,N,x_min,x_max,f,h,simga_r):
        nx = x_min.shape[0]     #number of element 
        d = np.random.rand(nx,N) #random 3 to N
        rang_x = (x_max-x_min).reshape((nx,1)) 
        rang_x = np.repeat(rang_x,N,1)
        x_min = x_min.reshape((nx,1))
        x_min = np.repeat(x_min,N,1)
        state_x = d*rang_x+x_min
        self.N = N
        self.state_x = state_x
        self.weight = (1./float(N))*np.ones((N,))
        self.predict_function = f
        self.observation_function = h
        self.sigma_r = simga_r
        self.nx = nx
    def predict(self,v):
        state_x_km1 = self.state_x
        state_x_k = self.predict_function(state_x_km1,v)
        self.state_x = state_x_k

    def update_weight(self,z_obv):
        nx = self.nx
        ny = z_obv.shape[0]
        N = self.N
        state_x = self.state_x
        mu = self.observation_function(state_x)
        z= z_obv.reshape((ny,1))
        z = np.repeat(z,N,1)
        z = z -mu
        z2 = np.linalg.solve(self.sigma_r,z)
        e = 0.5*(z*z2).sum(0) + 0.5*np.log(np.linalg.det(self.sigma_r))
        prob = np.exp(-e)
        w = self.weight
        w = w*prob
        w = w/w.sum()
        self.weight = w

    def resampling(self):
        N = self.N
        w = self.weight
        nx = self.nx
        Neff = 1./(w**2).sum()
        if Neff < (2./3.)*N : # resampling
            w_cum = w.cumsum()
            d = np.random.rand(N,)
            x_new = np.zeros((nx,N))
            x_old = self.state_x
            self.weight = (1./float(N))*np.ones((N,))
            for k in range(N):
                dk = d[k]
                b = np.nonzero(w_cum>dk)
                b = b[0]
                b = b.min()
                x_new[:,k] = x_old[:,b]
            self.state_x = x_new

    def get_mmse(self):
        x = self.state_x
        w = self.weight
        xmmse = (w*x).sum(1)
        return xmmse
def fx(x):
    x[-1] = 0
    return x

def fx2(x,y):
    pi = np.pi
    z = x+y
    z[0] = z[0]#%(2*np.pi)
    z[0] = z[0]*(z[0]<= pi) +(z[0]-2*pi)*(z[0]>pi)
    z[0] = z[0]*(z[0]> -pi) +(z[0]+2*pi)*(z[0]<=-pi)
    z[1] = z[1]*(z[1]<= pi/2.0) +(pi-z[1])*(z[1]>pi/2.0)
    z[1] = z[1]*(z[1]>=0) +(-z[1])*(z[1]<0)
    z[2] = z[2]#%(2*np.pi)
    z[2] = z[2]*(z[2]<= pi) +(z[2]-2*pi)*(z[2]>pi)
    z[2] = z[2]*(z[2]> -pi) +(z[2]+2*pi)*(z[2]<=-pi)

    return z


def hx(x):
    global fre
    az = x[0]
    el = x[1]
    c  = x[2]
    if x.ndim > 1:
        nx,N = x.shape
    else:
        N = 1
    """if fre == 0:
        fre = 12000"""   #check error
    fs = fre/1000.0
    lamb = 1500.0/fs   #26C
    phase = np.array([np.cos(az)*np.sin(el),np.sin(az)*np.sin(el),c])
    ant = np.array([[10,10],[-10,10],[-10,-10],[10,-10]])     #np.array([[10,10],[-10,10],[-10,-10.],[10,-10]])
    ant_phase = ant*np.pi*2/lamb
    A = np.ones((4,3))
    A[:,:2] = ant_phase
    angles = np.dot(A,phase)
    cr = np.cos(angles)
    ci = np.sin(angles)
    if x.ndim > 1:
        c = np.zeros((8,N))
        c[:4,:] = cr
        c[4:,:] = ci
    else:
        c = np.zeros((8,))
        c[:4] = cr
        c[4:] = ci
    return c
class readdata:
    def __init__(self):
        self.az_t = 0
        self.elv_t = 0
    def getData(self):
        global fre
        global pf
        global k
        global freq_s
        print "Test"
        data = hydro_msg()
        count = 0
        x=0

        data.stop = False

        while True:
            #print '0'
            x = ser.read(1)
            #print '1'
            #print x
            if x=='\xff':
                x = ser.read(1)
                #print '2'
                count +=1
                #print x
                if x=='\xff':
                    x = ser.read(94)
                    #print "3"
                    count = 0
                    break
            if count  == 2:
                data.azi = self.az_t
                data.elv = self.elv_t
                data.stop = True
                count = 0
		print "===== Pulse Error ======"
                
        
        seq = struct.unpack("<H", ''.join(x[0:2]))[0]
        azi = struct.unpack("<f", ''.join(x[2:6]))[0]
        elv = struct.unpack("<f", ''.join(x[6:10]))[0]
        itv = struct.unpack("<H", ''.join(x[10:12]))[0]
        pct = struct.unpack("<H", ''.join(x[12:14]))[0]
        po1 = struct.unpack("<f", ''.join(x[14:18]))[0]
        po2 = struct.unpack("<f", ''.join(x[18:22]))[0]
        po3 = struct.unpack("<f", ''.join(x[22:26]))[0]
        po4 = struct.unpack("<f", ''.join(x[26:30]))[0]
        stt = struct.unpack("<c", ''.join(x[30:31]))[0]
        fre = struct.unpack("<I", ''.join(x[31:35]))[0]
        fthres = struct.unpack("<f", ''.join(x[35:39]))[0]
        pthres = struct.unpack("<f", ''.join(x[39:43]))[0]
        ph1 = struct.unpack("<f", ''.join(x[43:47]))[0]
        ph2 = struct.unpack("<f", ''.join(x[47:51]))[0]
        ph3 = struct.unpack("<f", ''.join(x[51:55]))[0]
        ph4 = struct.unpack("<f", ''.join(x[55:59]))[0]
        c0r = struct.unpack("<f", ''.join(x[59:63]))[0]
        c0i = struct.unpack("<f", ''.join(x[63:67]))[0]
        c1r = struct.unpack("<f", ''.join(x[67:71]))[0]
        c1i = struct.unpack("<f", ''.join(x[71:75]))[0]
        c2r = struct.unpack("<f", ''.join(x[75:79]))[0]
        c2i = struct.unpack("<f", ''.join(x[79:83]))[0]
        c3r = struct.unpack("<f", ''.join(x[83:87]))[0]
        c3i = struct.unpack("<f", ''.join(x[87:91]))[0]
        resb = struct.unpack("<c", ''.join(x[91:92]))[0]
        csm = struct.unpack("<H", ''.join(x[92:94]))[0]

        if k < 10 :
        	if k == 0 :
        		freq_s = fre
        		k+=1
        	elif freq_s == fre :
        		k +=1
        	else :
        		k = 0
        		data.azi = self.pre_azi
        		data.elv = self.pre_elv
        		data.distance = -999
			print "======ERROR======"
        		return data		 

        else :
        	if fre != freq_s :
        		data.azi = self.pre_azi
        		data.elv = self.pre_elv
        		data.distance = -999
                print "=====ERROR====="
        	else :
        		fre = freq_s
		

        c_obv = []
                        
        m1 = c0r+1j*c0i
        m2 = c1r+1j*c1i
        m3 = c2r+1j*c2i
        m4 = c3r+1j*c3i
        #print "Cs :", m1,m2,m3,m4
        print "c0r = %.6f, c0i = %.6f, c1r = %.6f, c1i = %.6f, c2r = %.6f, c2i = %.6f, c3r = %.6f, c3i = %.6f" % (c0r,c0i,c1r,c1i,c2r,c2i,c3r,c3i)
        print (((po1+po2+po3+po4)/4)*1000)
        #print po2
        #print po3
        #print po4
        #m_mx = max(max(np.abs(m1),np.abs(m2),max(np.abs(m3),np.abs(m4))))
        #if m_mx > 0:
        cp = np.array([c0r/np.abs(m1),c1r/np.abs(m2),c2r/np.abs(m3),c3r/np.abs(m4),c0i/np.abs(m1),c1i/np.abs(m2),c2i/np.abs(m3),c3i/np.abs(m4)])

        
        #c_obv.append(temp2)
            
        #print "Board"
        #print seq,azi,elv
        #print "C:", cp 
		#print "Ele :%.2f" % (elv)
		#th1 = np.arctan2(cp[4],cp[0])*180./np.pi
		#th2 = np.arctan2(cp[5],cp[1])*180./np.pi
		#th3 = np.arctan2(cp[6],cp[2])*180./np.pi
		#th4 = np.arctan2(cp[7],cp[3])*180./np.pi
		#print th1,th2,th3,th4
        #for cp in c_obv:
            #cp = hx(np.array(np.array([-pi*0.7,pi/4.,0])))+np.random.normal(0,np.sqrt(0.01),(8,))
        v = np.random.rand(3,N)*2.0-1.0
        v[0] = v[0]*pi/7.0 #16.0   #trace max speed 
        v[1] = v[1]*pi/9.4 #23-1507 
        v[2] = v[2]*pi/3.0
        pf.predict(v)
        pf.update_weight(cp)
        pf.resampling()
        xk = pf.get_mmse()
        self.az_t = xk[0]*180./pi
        self.elv_t = xk[1]*180./pi
        c = xk[2]
        print "Particle Filter Az: %.2f,Elv: %.2f,Ot: %.3f ,Freq : %.0f\n" % (self.az_t, self.elv_t,c,fre/1000)
   
        self.pre_azi = self.az_t
        self.pre_elv = self.elv_t

        data.azi = self.az_t
        data.elv = self.elv_t
        data.freq = fre 
        #if elv_t <= 20:
        #    data.stop = True

        
        return data


def greet():
    rospy.init_node('HYDROPHONE_2016')
    rospy.Publisher('hydro', hydro_msg, queue_size =  4)
    print "READY TO GET THE DATA"
    res = set(0x00,2000000)
    ser.write(res)
    #res = set(0x01,28000)
    #ser.write(res)
    res = set(0x02,0.3)
    ser.write(res)
    res = set(0x03,0.02)
    ser.write(res)
    res = set(0x04,1500)
    ser.write(res)
    rospy.spin()
    	
if __name__ == '__main__':
    global pf
    R = np.eye(8)*0.1
    pi = np.pi
    x_min = np.array([-pi,0,-pi])
    x_max = np.array([pi,pi/2.,pi])
    N= 1100
    pf = particleFilter(N,x_min,x_max,fx2,hx,R)
    rd = readdata()

    #r = rospy.Rate(10)
    rospy.init_node('HYDROPHONE_2016')
    pub = rospy.Publisher('hydro', hydro_msg, queue_size =  4)
    print "READY TO GET THE DATA"
    res = set(0x00,2000000)
    ser.write(res)
    #res = set(0x01,28000)
    #ser.write(res)
    res = set(0x02,0.3)
    ser.write(res)
    res = set(0x03,0.02)
    ser.write(res)
    res = set(0x04,1500)
    ser.write(res)
    while not rospy.is_shutdown() :
        d = rd.getData()
        pub.publish(d)
        #r.sleep()
