// Exact type-game chance aggregation and synchronous full-sweep regret matching.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <random>
#include <vector>
static_assert(std::numeric_limits<long double>::digits>=64,"extended sums required");
extern "C" int type_aggregate(int n,int bh,int bv,const int*holes,const int*labels,const int*hi,const int*vi,const uint16_t*w,const uint16_t*t,const double*hero,const double*villain,double*out){
 if(n<1||n>1176||bh<1||bv<1)return -1;std::vector<uint64_t>mask(n);std::vector<long double>s(bh*bv*2);
 for(int i=0;i<n;++i){if(hi[i]<0||hi[i]>=bh||vi[i]<0||vi[i]>=bv||labels[i]<0||labels[i]>=169)return -2;mask[i]=(1ull<<holes[2*i])|(1ull<<holes[2*i+1]);}
 long double mass=0;
 for(int i=0;i<n;++i)for(int j=0;j<n;++j)if(!(mask[i]&mask[j])){long double q=(long double)hero[labels[i]]*villain[labels[j]],e=((long double)w[i*n+j]+(long double)t[i*n+j]/2)/990;int k=(hi[i]*bv+vi[j])*2;s[k]+=q;s[k+1]+=q*e;mass+=q;}
 if(!(mass>0))return -3;for(int k=0;k<bh*bv*2;++k)out[k]=s[k]/mass;return 0;
}
extern "C" int type_solve(int bh,int bv,const double*a,int iterations,uint32_t seed,double*average,double*regrets){
 if(bh<1||bv<1||iterations<1)return -1;int nh=bh*4,nv=bv*4;std::vector<double>r(nh),s(nv),p(nh),q(nv),avg(nh+nv);std::mt19937 rng(seed);std::uniform_real_distribution<double>u(.1,1.1);
 auto match=[&](const std::vector<double>&rr,std::vector<double>&v,int types,bool first){for(int k=0;k<types;++k){double z=0;for(int b=0;b<4;++b){v[k*4+b]=first?u(rng):std::max(0.,rr[k*4+b]);z+=v[k*4+b];}for(int b=0;b<4;++b)v[k*4+b]=z?v[k*4+b]/z:.25;}};
 for(int it=0;it<iterations;++it){match(r,p,bh,it==0);match(s,q,bv,it==0);std::vector<double>ph(nh),pv(nv);
  for(int i=0;i<bh;++i)for(int j=0;j<bv;++j)for(int x=0;x<4;++x)for(int y=0;y<4;++y){double z=a[((i*bv+j)*4+x)*4+y];ph[i*4+x]+=z*q[j*4+y];pv[j*4+y]-=z*p[i*4+x];}
  for(int i=0;i<bh;++i){double base=0;for(int x=0;x<4;++x)base+=p[i*4+x]*ph[i*4+x];for(int x=0;x<4;++x){r[i*4+x]+=ph[i*4+x]-base;avg[i*4+x]+=p[i*4+x];}}
  for(int j=0;j<bv;++j){double base=0;for(int y=0;y<4;++y)base+=q[j*4+y]*pv[j*4+y];for(int y=0;y<4;++y){s[j*4+y]+=pv[j*4+y]-base;avg[nh+j*4+y]+=q[j*4+y];}}
 }
 for(int i=0;i<nh+nv;++i){average[i]=avg[i]/iterations;regrets[i]=i<nh?r[i]:s[i-nh];}return 0;
}
extern "C" int type_leaf(int n,int bh,int bv,const int*holes,const int*labels,const int*hi,const int*vi,const uint16_t*w,const uint16_t*t,const double*c0,const double*c1,double*out,int*counts){
 std::vector<uint64_t>mask(n);std::vector<long double>sum(169*169);std::fill(counts,counts+169*169,0);
 for(int i=0;i<n;++i)mask[i]=(1ull<<holes[2*i])|(1ull<<holes[2*i+1]);
 for(int i=0;i<n;++i)for(int j=0;j<n;++j)if(!(mask[i]&mask[j])){int k=hi[i]*bv+vi[j],pos=labels[i]*169+labels[j];long double e=((long double)w[i*n+j]+(long double)t[i*n+j]/2)/990;sum[pos]+=c0[k]+c1[k]*e;++counts[pos];}
 for(int k=0;k<169*169;++k)out[k]=counts[k]?sum[k]/counts[k]:0;return 0;
}
