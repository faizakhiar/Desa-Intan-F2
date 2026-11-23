import numpy as np, cv2
H,W=1920,1080
YY,XX=np.mgrid[0:H,0:W].astype(np.float32)
MUD=np.array([70,98,118],np.float32)  # BGR murky brown

def boundary(vp, a_left, roll=0.0):
    """y of the water boundary per column: wall waterline from (0,a_left) to vp, then horizon through vp."""
    vx,vy=vp
    xs=np.arange(W,dtype=np.float32)
    wall=a_left+(vy-a_left)*xs/max(vx,1)
    hor=vy+roll*(xs-vx)
    return np.where(xs<vx,wall,hor)

_rng=np.random.default_rng(7)
def _fbm(n=512):
    acc=np.zeros((n,n),np.float32); amp=1.0; tot=0
    for k in [8,16,32,64,128]:
        r=_rng.random((k,k)).astype(np.float32)
        r=cv2.resize(np.tile(r,(3,3)),(n*3,n*3),interpolation=cv2.INTER_CUBIC)[n:2*n,n:2*n]
        acc+=r*amp; tot+=amp; amp*=0.55
    return (acc/tot-0.5)*2
NOISE=_fbm()
NOISE2=_fbm()
def ripple(dy,t,vpx,kx=None,kdy=None):
    if kx is None: kx,kdy=XX,dy
    Z=1.0/(np.maximum(kdy,0)+45.0)  # ground-plane depth proxy (keyframe space)
    X=(kx-vpx)*Z                    # lateral ground coord
    n=NOISE.shape[0]
    u=(X*420.0+t*9.0)%n; v=(Z*38000.0+t*24.0)%n
    u2=(X*900.0-t*5.0)%n; v2=(Z*80000.0+t*41.0)%n
    h=cv2.remap(NOISE,u.astype(np.float32),v.astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_WRAP)
    h+=0.5*cv2.remap(NOISE2,u2.astype(np.float32),v2.astype(np.float32),cv2.INTER_LINEAR,borderMode=cv2.BORDER_WRAP)
    gx=np.gradient(h,axis=1); gy=np.gradient(h,axis=0)
    return h,gx,gy

def flood(img,yb,t,vpx,alpha=1.0,wet=1.0,kx=None,kdy=None,kvpx=None):
    img=img.astype(np.float32)
    ybf=yb[None,:].astype(np.float32)
    dy=YY-ybf
    under=dy>0
    h,gx,gy=ripple(np.maximum(dy,0),t,kvpx if kvpx is not None else vpx,kx,kdy)
    near=np.clip(dy/90.0,0,1)
    amp=(np.clip(dy,0,None)*0.05+1.5)*(0.35+0.65*near)
    sx=XX+gx*amp*9.0
    sy=ybf-dy*0.92+gy*amp*18.0
    sy=np.clip(sy,0,H-1)
    refl=cv2.remap(img,sx,sy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
    f=np.clip(0.64-dy/1100.0,0.2,0.64)[...,None]
    shade=(1.0-np.clip(dy/1800.0,0,0.35))[...,None]
    water=(refl*0.78*f+MUD*(1-f))*shade
    spec=(np.clip(gy*6.0,0.25,None)-0.25)*np.clip((dy-40)/160.0,0,1)
    water+=(spec*70.0*np.clip(1-dy/1200.0,0.2,1))[...,None]
    # soft edge with slight foam
    edge=np.clip(dy/3.0,0,1)[...,None]
    foam=np.exp(-np.abs(dy)/2.5)[...,None]*(0.5+0.5*np.sin(XX*0.35+t*4))[...,None]*55
    a=(edge*alpha)
    out=img*(1-a)+water*a+foam*alpha*(dy>-2)[...,None]
    # wet band on walls just above the line (left of vp)
    wb=((dy<0)&(dy>-26)&(XX<vpx))[...,None]*(1+dy/26.0)[...,None]
    out=out*(1-0.22*wb*wet*alpha)
    return np.clip(out,0,255).astype(np.uint8)
