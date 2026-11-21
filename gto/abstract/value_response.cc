// Separate bounded continuation research kernel. Never edits preflop CFR.
#include <algorithm>
#include <cmath>
#include <vector>
extern "C" int warm_response(int bh,int bv,const double*a,const double*prior,int iterations,double*average,double*regrets){
 if(bh<1||bv<1||iterations<1||iterations>10000000)return -1;
 int nh=bh*4,nv=bv*4;
 for(int i=0;i<bh*bv*16;++i)if(!std::isfinite(a[i]))return -2;
 for(int t=0;t<bh+bv;++t){double z=0;for(int x=0;x<4;++x){double v=prior[t*4+x];if(!std::isfinite(v)||v<0)return -3;z+=v;}if(std::abs(z-1)>1e-10)return -3;}
 std::vector<double>r(nh),s(nv),p(nh),q(nv),avg(nh+nv);
 auto match=[](const std::vector<double>&reg,std::vector<double>&v){for(int k=0;k<(int)v.size()/4;++k){double z=0;for(int x=0;x<4;++x){v[k*4+x]=std::max(0.,reg[k*4+x]);z+=v[k*4+x];}for(int x=0;x<4;++x)v[k*4+x]=z?v[k*4+x]/z:.25;}};
 for(int it=0;it<iterations;++it){
  if(it==0){std::copy(prior,prior+nh,p.begin());std::copy(prior+nh,prior+nh+nv,q.begin());}else{match(r,p);match(s,q);}
  std::vector<double>ph(nh),pv(nv);
  for(int i=0;i<bh;++i)for(int j=0;j<bv;++j)for(int x=0;x<4;++x)for(int y=0;y<4;++y){double v=a[((i*bv+j)*4+x)*4+y];ph[i*4+x]+=v*q[j*4+y];pv[j*4+y]-=v*p[i*4+x];}
  for(int i=0;i<bh;++i){double v=0;for(int x=0;x<4;++x)v+=p[i*4+x]*ph[i*4+x];for(int x=0;x<4;++x){r[i*4+x]+=ph[i*4+x]-v;avg[i*4+x]+=p[i*4+x];}}
  for(int j=0;j<bv;++j){double v=0;for(int y=0;y<4;++y)v+=q[j*4+y]*pv[j*4+y];for(int y=0;y<4;++y){s[j*4+y]+=pv[j*4+y]-v;avg[nh+j*4+y]+=q[j*4+y];}}
 }
 for(int i=0;i<nh+nv;++i){average[i]=avg[i]/iterations;regrets[i]=i<nh?r[i]:s[i-nh];}return 0;
}
