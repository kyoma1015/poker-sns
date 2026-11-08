// One exact conditional-board block. No preflop BR maximization here.
#include <algorithm>
#include <cmath>
#include <vector>
extern "C" int stream_train_block(int N,int W,int S,int B,const int*actor,const int*cnt,
 const int*child,const int*base,const int*street,const int*boundary,
 const int*hc,const int*vc,const int*ht,const int*vt,
 const double*chance,const double*equity,const double*c0,const double*c1,
 const double*pi,double*grad,double*avg,double*leaf,double*metrics,double*anum,double*aden){
 if(N<1||W<1||S<1||B<1)return -1;
 size_t size=(size_t)N*W;
 std::vector<double>r0(size),r1(size),val(size),tot(S);
 auto ix=[&](int k,int w){int t=actor[k]==0?(street[k]?ht[w]:hc[w]):(street[k]?vt[w]:vc[w]);return base[k]+t*cnt[k];};
 auto reach=[&](int owner){
  std::fill(r0.begin(),r0.end(),0.);std::fill(r1.begin(),r1.end(),0.);
  for(int w=0;w<W;++w)r0[w]=r1[w]=1.;
  for(int k=0;k<N;++k)if(actor[k]>=0)for(int a=0;a<cnt[k];++a){int c=child[k*4+a];if(c<=k||c>=N)return false;
   for(int w=0;w<W;++w){size_t x=(size_t)k*W+w,y=(size_t)c*W+w;double p=pi[ix(k,w)+a];r0[y]=r0[x]*((actor[k]==0&&owner!=0)?p:1.);r1[y]=r1[x]*((actor[k]==1&&owner!=1)?p:1.);}
  }return true;
 };
 if(!reach(-1))return -2;
 std::fill(grad,grad+S,0.);std::fill(avg,avg+S,0.);std::fill(anum,anum+S,0.);std::fill(aden,aden+S,0.);std::fill(leaf,leaf+2*B*169,0.);std::fill(metrics,metrics+3,0.);
 for(int k=N-1;k>=0;--k)for(int w=0;w<W;++w){size_t x=(size_t)k*W+w;
  if(actor[k]<0){val[x]=c0[k]+c1[k]*equity[w];double z=chance[w]*r0[x]*r1[x];if(c1[k]>0&&c1[k]<100-1e-10)metrics[2]+=z;else metrics[1]+=z*val[x];continue;}
  int i=ix(k,w);double v=0;for(int a=0;a<cnt[k];++a)v+=pi[i+a]*val[(size_t)child[k*4+a]*W+w];val[x]=v;
  double opp=actor[k]==0?r1[x]:r0[x],own=actor[k]==0?r0[x]:r1[x],sign=actor[k]==0?1.:-1.;
  for(int a=0;a<cnt[k];++a){double q=sign*val[(size_t)child[k*4+a]*W+w];grad[i+a]+=chance[w]*opp*(q-sign*v);avg[i+a]+=chance[w]*own*pi[i+a];anum[i+a]+=chance[w]*opp*q;aden[i+a]+=chance[w]*opp;}
 }
 for(int w=0;w<W;++w)metrics[0]+=chance[w]*val[w];
 return 0;
}
