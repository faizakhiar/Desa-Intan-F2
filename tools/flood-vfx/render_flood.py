import sys, subprocess, numpy as np, cv2
sys.path.insert(0, sys.argv[1]); import water
src, out = sys.argv[2], sys.argv[3]
W,H=1080,1920; FPS=30
raw=subprocess.run(["ffmpeg","-loglevel","error","-i",src,"-f","rawvideo","-pix_fmt","bgr24","-"],capture_output=True).stdout
frames=np.frombuffer(raw,np.uint8).reshape(-1,H,W,3); N=len(frames); K=120
orb=cv2.ORB_create(4000); bf=cv2.BFMatcher(cv2.NORM_HAMMING,crossCheck=True)
def homog(a,b):
    ga,gb=[cv2.cvtColor(x,cv2.COLOR_BGR2GRAY) for x in (a,b)]
    ka,da=orb.detectAndCompute(ga,None); kb,db=orb.detectAndCompute(gb,None)
    m=sorted(bf.match(da,db),key=lambda x:x.distance)[:1500]
    pa=np.float32([ka[x.queryIdx].pt for x in m]); pb=np.float32([kb[x.trainIdx].pt for x in m])
    Hm,_=cv2.findHomography(pa,pb,cv2.RANSAC,3.0); return Hm
Hs=[None]*N; Hs[K]=np.eye(3)
for i in range(K+1,N): Hs[i]=homog(frames[i-1],frames[i])@Hs[i-1]
for i in range(K-1,-1,-1): Hs[i]=homog(frames[i+1],frames[i])@Hs[i+1]
VP=(1090.0,940.0); BASE,TOP=1100.0,895.0
def ease(x): x=min(max(x,0),1); return x*x*(3-2*x)
xs_key=np.linspace(-2500,3500,600)
enc=subprocess.Popen(["ffmpeg","-loglevel","error","-y","-f","rawvideo","-pix_fmt","bgr24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
    "-c:v","libx264","-crf","16","-preset","medium","-pix_fmt","yuv420p","-g","10",out],stdin=subprocess.PIPE)
for i in range(N):
    t=i/FPS
    alpha=ease((t-2.9)/0.6); r=0.32*ease((t-3.5)/1.4)
    img=frames[i]
    if alpha<=0: enc.stdin.write(img.tobytes()); continue
    a=BASE-(BASE-TOP)*r
    lw=np.cross([0,a,1.0],[VP[0],VP[1],1.0]); lh=np.cross([0,VP[1],1.0],[VP[0],VP[1],1.0])
    Ht=np.linalg.inv(Hs[i]).T; lw=Ht@lw; lh=Ht@lh
    X=np.arange(W,dtype=np.float64)
    yw=-(lw[0]*X+lw[2])/lw[1]; yh=-(lh[0]*X+lh[2])/lh[1]
    yb=np.maximum(yw,yh)
    v=Hs[i]@np.array([VP[0],VP[1],1.0]); vpx=v[0]/v[2] if v[2]>0 else -1e5
    vpx=float(np.clip(vpx,-1500,2600))
    res=water.flood(img,yb.astype(np.float32),t,vpx,alpha=alpha,wet=ease((t-3.6)/1.0))
    enc.stdin.write(res.tobytes())
    if i%30==0: print("frame",i,"/",N,flush=True)
enc.stdin.close(); enc.wait(); print("done",N)
