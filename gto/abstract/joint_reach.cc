// Synchronous CFR and information-constrained BR on explicit joint chance worlds.
// Policy indices encode OWN observations only. Chance is supplied without reaches.
#include <algorithm>
#include <cmath>
#include <vector>
extern "C" int joint_run(int N,int W,int S,int iterations,const int*actor,
 const int*counts,const int*children,const int*info,const int*width,
 const double*chance,const double*equity,const double*c0,const double*c1,
 double*regret,double*sum,double*policy,double*action_ev,double*out){
 if(N<1||W<1||S<1||iterations<0)return -1;
 const size_t size=(size_t)N*W;
 std::vector<double>r0(size),r1(size),value(size),p(S),adv(S),mass(S);
 auto match=[&](bool average){
  for(int k=0;k<S;){int n=width[k];if(n<1||n>4||k+n>S)return false;
   double z=0;for(int a=0;a<n;++a)z+=average?sum[k+a]:std::max(0.,regret[k+a]);
   for(int a=0;a<n;++a)p[k+a]=z?(average?sum[k+a]:std::max(0.,regret[k+a]))/z:1./n;
   k+=n;
  }return true;
 };
 auto reach=[&](int owner){ // owner=-1 => both; otherwise opponent-only.
  std::fill(r0.begin(),r0.end(),0.);std::fill(r1.begin(),r1.end(),0.);
  for(int w=0;w<W;++w)r0[w]=r1[w]=1.;
  for(int k=0;k<N;++k)if(actor[k]>=0)for(int a=0;a<counts[k];++a){
   int c=children[k*4+a];if(c<=k||c>=N)return false;
   for(int w=0;w<W;++w){size_t x=(size_t)k*W+w,y=(size_t)c*W+w;double q=p[info[x]+a];
    r0[y]=r0[x]*((actor[k]==0&&owner!=0)?q:1.);
    r1[y]=r1[x]*((actor[k]==1&&owner!=1)?q:1.);
   }
  }return true;
 };
 auto profile=[&](bool update){
  if(!reach(-1))return false;
  if(update)std::fill(adv.begin(),adv.end(),0.);
  std::fill(action_ev,action_ev+S,0.);std::fill(mass.begin(),mass.end(),0.);
  for(int k=N-1;k>=0;--k)for(int w=0;w<W;++w){size_t x=(size_t)k*W+w;
   if(actor[k]<0){value[x]=c0[k]+c1[k]*equity[w];continue;}
   int i=info[x];double base=0,opp=actor[k]==0?r1[x]:r0[x],own=actor[k]==0?r0[x]:r1[x];
   for(int a=0;a<counts[k];++a)base+=p[i+a]*value[(size_t)children[k*4+a]*W+w];
   value[x]=base;
   for(int a=0;a<counts[k];++a){double q=value[(size_t)children[k*4+a]*W+w]*(actor[k]==0?1.:-1.);
    action_ev[i+a]+=chance[w]*opp*q;mass[i+a]+=chance[w]*opp;
    if(update){adv[i+a]+=chance[w]*opp*(q-base*(actor[k]==0?1.:-1.));sum[i+a]+=chance[w]*own*p[i+a];}
   }
  }
  if(update)for(int i=0;i<S;++i)regret[i]+=adv[i];
  for(int i=0;i<S;++i)action_ev[i]=mass[i]>0?action_ev[i]/mass[i]:0.;
  return true;
 };
 for(int it=0;it<iterations;++it)if(!match(false)||!profile(true))return -2;
 if(!match(true)||!profile(false))return -3;
 std::copy(p.begin(),p.end(),policy);
 double ev=0,known=0,unknown=0;
 for(int w=0;w<W;++w)ev+=chance[w]*value[w];
 for(int k=0;k<N;++k)if(actor[k]<0)for(int w=0;w<W;++w){size_t x=(size_t)k*W+w;double z=chance[w]*r0[x]*r1[x];
  if(c1[k]>0&&c1[k]<100-1e-10)unknown+=z;else known+=z*value[x];
 }
 out[0]=ev;
 for(int owner=0;owner<2;++owner){
  if(!reach(owner))return -4;
  for(int k=N-1;k>=0;--k){
   if(actor[k]<0){for(int w=0;w<W;++w)value[(size_t)k*W+w]=(c0[k]+c1[k]*equity[w])*(owner==0?1.:-1.);continue;}
   if(actor[k]==owner){
    std::fill(adv.begin(),adv.end(),0.);
    for(int w=0;w<W;++w){size_t x=(size_t)k*W+w;double weight=chance[w]*(owner==0?r1[x]:r0[x]);
     for(int a=0;a<counts[k];++a)adv[info[x]+a]+=weight*value[(size_t)children[k*4+a]*W+w];
    }
    for(int w=0;w<W;++w){size_t x=(size_t)k*W+w;int a=0;for(int b=1;b<counts[k];++b)if(adv[info[x]+b]>adv[info[x]+a])a=b;value[x]=value[(size_t)children[k*4+a]*W+w];}
   }else for(int w=0;w<W;++w){size_t x=(size_t)k*W+w;double v=0;for(int a=0;a<counts[k];++a)v+=p[info[x]+a]*value[(size_t)children[k*4+a]*W+w];value[x]=v;}
  }
  out[1+owner]=0;for(int w=0;w<W;++w)out[1+owner]+=chance[w]*value[w];
 }
 out[3]=out[1]+out[2];out[4]=unknown;out[5]=known-50*unknown;out[6]=known+50*unknown;
 double bound=0;for(int i=0;i<S;){int n=width[i];double best=0;for(int a=0;a<n;++a)best=std::max(best,regret[i+a]);bound+=best;i+=n;}out[7]=bound;
 return 0;
}
