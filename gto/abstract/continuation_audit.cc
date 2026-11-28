// Independent continuation audit: same verified algorithm, stride12 for expanded legal sizes. Original untouched.
// Chance is joint private-type mass/equity, not independent hand marginals.
#include <algorithm>
#include <cmath>
#include <numeric>
#include <vector>
struct Street {
 int n,h,v;const int*actor,*count,*child;const double*M,*E;std::vector<int>off;const double*A,*B;
 Street(int nn,int hh,int vv,const int*a,const int*c,const int*d,const double*c0,const double*c1,const double*m,const double*e):n(nn),h(hh),v(vv),actor(a),count(c),child(d),M(m),E(e),off(nn+1),A(c0),B(c1){
  for(int k=0;k<n;++k){off[k+1]=off[k]+(actor[k]<0?0:(actor[k]==0?h:v)*count[k]);}
 }
 bool valid(const double*prior){
  if(n<1||h<1||v<1)return false;std::vector<int>parents(n);double mass=0;
  for(int i=0;i<h*v;++i){if(!std::isfinite(M[i]+E[i])||M[i]<-1e-12||E[i]<-1e-12||E[i]>M[i]+1e-12)return false;mass+=M[i];}if(std::abs(mass-1)>1e-10)return false;
  for(int k=0;k<n;++k){if(actor[k]<-1||actor[k]>1||count[k]!=(actor[k]<0?0:count[k])||count[k]>12||count[k]<0||actor[k]>=0&&count[k]<2)return false;for(int a=0;a<count[k];++a){int c=child[k*12+a];if(c<=k||c>=n)return false;++parents[c];}int types=actor[k]==0?h:v;if(actor[k]>=0)for(int t=0;t<types;++t){double z=0;for(int a=0;a<count[k];++a){double x=prior[off[k]+t*count[k]+a];if(!std::isfinite(x)||x<0)return false;z+=x;}if(std::abs(z-1)>1e-10)return false;}}
  for(int i=1;i<n;++i)if(parents[i]!=1)return false;return parents[0]==0;
 }
 double profile(const double*sigma,double*reg,double*sum,bool update){
  std::vector<double>rh(n*h),rv(n*v),uh(n*h),uv(n*v);std::fill(rh.begin(),rh.begin()+h,1.);std::fill(rv.begin(),rv.begin()+v,1.);
  for(int k=0;k<n;++k)if(actor[k]>=0){int types=actor[k]==0?h:v;for(int a=0;a<count[k];++a){int c=child[k*12+a];for(int i=0;i<h;++i)rh[c*h+i]=rh[k*h+i]*(actor[k]==0?sigma[off[k]+i*count[k]+a]:1.);for(int j=0;j<v;++j)rv[c*v+j]=rv[k*v+j]*(actor[k]==1?sigma[off[k]+j*count[k]+a]:1.);}if(update)for(int t=0;t<types;++t)for(int a=0;a<count[k];++a)sum[off[k]+t*count[k]+a]+=(actor[k]==0?rh[k*h+t]:rv[k*v+t])*sigma[off[k]+t*count[k]+a];}
  for(int k=n-1;k>=0;--k){
   if(actor[k]<0){for(int i=0;i<h;++i)for(int j=0;j<v;++j){double u=(A[k]*M[i*v+j]+B[k]*E[i*v+j]);uh[k*h+i]+=rv[k*v+j]*u;uv[k*v+j]-=rh[k*h+i]*u;}}
   else if(actor[k]==0){for(int i=0;i<h;++i){for(int a=0;a<count[k];++a)uh[k*h+i]+=sigma[off[k]+i*count[k]+a]*uh[child[k*12+a]*h+i];if(update)for(int a=0;a<count[k];++a)reg[off[k]+i*count[k]+a]+=uh[child[k*12+a]*h+i]-uh[k*h+i];}for(int j=0;j<v;++j)for(int a=0;a<count[k];++a)uv[k*v+j]+=uv[child[k*12+a]*v+j];}
   else {for(int i=0;i<h;++i)for(int a=0;a<count[k];++a)uh[k*h+i]+=uh[child[k*12+a]*h+i];for(int j=0;j<v;++j){for(int a=0;a<count[k];++a)uv[k*v+j]+=sigma[off[k]+j*count[k]+a]*uv[child[k*12+a]*v+j];if(update)for(int a=0;a<count[k];++a)reg[off[k]+j*count[k]+a]+=uv[child[k*12+a]*v+j]-uv[k*v+j];}}
  }
  return std::accumulate(uh.begin(),uh.begin()+h,0.);
 }
 double br(const double*sigma,int owner){
  int own=owner==0?h:v,opp=owner==0?v:h;std::vector<double>reach(n*opp),value(n*own);std::fill(reach.begin(),reach.begin()+opp,1.);
  for(int k=0;k<n;++k)if(actor[k]>=0)for(int a=0;a<count[k];++a){int c=child[k*12+a];for(int t=0;t<opp;++t)reach[c*opp+t]=reach[k*opp+t]*(actor[k]!=owner?sigma[off[k]+t*count[k]+a]:1.);}
  for(int k=n-1;k>=0;--k){if(actor[k]<0){for(int i=0;i<h;++i)for(int j=0;j<v;++j){double u=(A[k]*M[i*v+j]+B[k]*E[i*v+j]);if(owner==0)value[k*own+i]+=reach[k*opp+j]*u;else value[k*own+j]-=reach[k*opp+i]*u;}}
   else for(int t=0;t<own;++t){if(actor[k]==owner){value[k*own+t]=-1e300;for(int a=0;a<count[k];++a)value[k*own+t]=std::max(value[k*own+t],value[child[k*12+a]*own+t]);}else for(int a=0;a<count[k];++a)value[k*own+t]+=value[child[k*12+a]*own+t];}}
  return std::accumulate(value.begin(),value.begin()+own,0.);
 }
 void metrics(const double*sigma,double*out){out[0]=profile(sigma,nullptr,nullptr,false);out[1]=br(sigma,0);out[2]=-br(sigma,1);out[3]=out[1]-out[2];}
};
extern "C" int street_evaluate(int n,int h,int v,const int*a,const int*c,const int*d,const double*c0,const double*c1,const double*M,const double*E,const double*p,double*out){Street g(n,h,v,a,c,d,c0,c1,M,E);if(!g.valid(p))return -1;g.metrics(p,out);return 0;}
extern "C" int street_train(int n,int h,int v,const int*a,const int*c,const int*d,const double*c0,const double*c1,const double*M,const double*E,const double*prior,int start,int stop,double*reg,double*sum,double*average,double*out){
 Street g(n,h,v,a,c,d,c0,c1,M,E);if(!g.valid(prior)||start<0||stop<=start)return -1;std::vector<double>sigma(g.off[n]);
 for(int it=start;it<stop;++it){for(int k=0;k<n;++k)if(a[k]>=0){int types=a[k]==0?h:v;for(int t=0;t<types;++t){double z=0;int offset=g.off[k]+t*c[k];for(int b=0;b<c[k];++b){sigma[offset+b]=it==0?prior[offset+b]:std::max(0.,reg[offset+b]);z+=sigma[offset+b];}for(int b=0;b<c[k];++b)sigma[offset+b]=z?sigma[offset+b]/z:1./c[k];}}g.profile(sigma.data(),reg,sum,true);}
 double bound=0;for(int k=0;k<n;++k)if(a[k]>=0){int types=a[k]==0?h:v;for(int t=0;t<types;++t){int offset=g.off[k]+t*c[k];double z=0,best=0;for(int b=0;b<c[k];++b){z+=sum[offset+b];best=std::max(best,reg[offset+b]);}for(int b=0;b<c[k];++b)average[offset+b]=z?sum[offset+b]/z:prior[offset+b];bound+=best;}}
 g.metrics(average,out);out[4]=bound/stop;return 0;
}
