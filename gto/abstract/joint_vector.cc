// Exact counterfactual vectors: integrate opponent private chance at terminals.
// Same public tree/information sets as stream_block, no sampled or pruned worlds.
#include <algorithm>
#include <cmath>
#include <vector>
extern "C" int stream_block(int N,int W,int S,int B,const int*actor,const int*cnt,
 const int*child,const int*base,const int*street,const int*boundary,
 const int*hc,const int*vc,const int*ht,const int*vt,
 const double*chance,const double*equity,const double*c0,const double*c1,
 const double*pi,double*grad,double*avg,double*leaf,double*metrics,double*anum,double*aden){
 if(N<1||W<1||S<1||B<1)return -1;
 int T=0;std::vector<int>types(N);
 for(int k=0;k<N;++k)if(actor[k]>=0){
  if(actor[k]>1||cnt[k]<1||cnt[k]>4||base[k]<0)return -2;
  for(int a=0;a<cnt[k];++a)if(child[k*4+a]<=k||child[k*4+a]>=N)return -2;
  int end=S;for(int j=0;j<N;++j)if(base[j]>base[k])end=std::min(end,base[j]);types[k]=(end-base[k])/cnt[k];if(types[k]<1||(end-base[k])%cnt[k])return -2;
  if(street[k]){if(T&&T!=types[k])return -2;T=types[k];}
  for(int t=0;t<types[k];++t){double sum=0.;for(int a=0;a<cnt[k];++a){double p=pi[base[k]+t*cnt[k]+a];if(!std::isfinite(p)||p<0||p>1)return -2;sum+=p;}if(std::abs(sum-1.)>1e-10)return -2;}
 }
 if(T==0){for(int w=0;w<W;++w)T=std::max(T,std::max(ht[w],vt[w])+1);}
 if(T<1||T>1352)return -2;
 if((size_t)N*T*8*6+(size_t)T*T*8*2>2ULL*1024*1024*1024)return -2;
 std::vector<double>M((size_t)T*T),E(M.size());std::vector<int>classes[2];classes[0].resize(T);classes[1].resize(T);
 for(int w=0;w<W;++w){if(ht[w]<0||ht[w]>=T||vt[w]<0||vt[w]>=T||hc[w]<0||hc[w]>=169||vc[w]<0||vc[w]>=169||!std::isfinite(chance[w])||chance[w]<0||!std::isfinite(equity[w])||equity[w]<0||equity[w]>1)return -2;size_t i=(size_t)ht[w]*T+vt[w];M[i]+=chance[w];E[i]+=chance[w]*equity[w];classes[0][ht[w]]=hc[w];classes[1][vt[w]]=vc[w];}
 auto index=[&](int k,int h){return base[k]+(street[k]?h:classes[actor[k]][h])*cnt[k];};
 std::vector<double>reach[2];reach[0].resize((size_t)N*T);reach[1].resize((size_t)N*T);
 for(int p=0;p<2;++p){for(int h=0;h<T;++h)reach[p][h]=1.;for(int k=0;k<N;++k)if(actor[k]>=0)for(int a=0;a<cnt[k];++a)for(int h=0;h<T;++h){int i=base[k]+(street[k]?h:classes[p][h])*cnt[k]+a;if(i<0||i>=S)return -2;reach[p][(size_t)child[k*4+a]*T+h]=reach[p][(size_t)k*T+h]*(actor[k]==p?pi[i]:1.);}}
 std::fill(grad,grad+S,0.);std::fill(avg,avg+S,0.);std::fill(anum,anum+S,0.);std::fill(aden,aden+S,0.);std::fill(leaf,leaf+2*B*169,0.);std::fill(metrics,metrics+3,0.);
 for(int owner=0;owner<2;++owner){
  std::vector<double>v((size_t)N*T),br((size_t)N*T),cmass((size_t)N*T),marginal(T),mass(T),pay(T);
  for(int h=0;h<T;++h)for(int o=0;o<T;++o)marginal[h]+=M[owner==0?(size_t)h*T+o:(size_t)o*T+h];
  auto integrate=[&](int k,bool payoff){for(int h=0;h<T;++h){double z=0.,e=0.;for(int o=0;o<T;++o){size_t i=owner==0?(size_t)h*T+o:(size_t)o*T+h;double r=reach[1-owner][(size_t)k*T+o];z+=M[i]*r;if(payoff)e+=E[i]*r;}mass[h]=z;pay[h]=(owner==0?1.:-1.)*(c0[k]*z+c1[k]*e);}};
  for(int k=N-1;k>=0;--k){
   if(actor[k]<0){integrate(k,true);for(int h=0;h<T;++h){size_t i=(size_t)k*T+h;v[i]=br[i]=pay[h];cmass[i]=mass[h];if(owner==0){double own=reach[0][i];if(c1[k]>0&&c1[k]<100-1e-10)metrics[2]+=own*mass[h];else metrics[1]+=own*pay[h];}}}
   else if(actor[k]==owner){
    for(int h=0;h<T;++h){int i=index(k,h);double value=0.,prob=0.,best=-1e300;for(int a=0;a<cnt[k];++a){size_t c=(size_t)child[k*4+a]*T+h;value+=pi[i+a]*v[c];prob+=pi[i+a]*cmass[c];if(street[k])best=std::max(best,br[c]);}v[(size_t)k*T+h]=value;cmass[(size_t)k*T+h]=prob;if(street[k])br[(size_t)k*T+h]=best;
     for(int a=0;a<cnt[k];++a){double q=v[(size_t)child[k*4+a]*T+h];grad[i+a]+=q-value;avg[i+a]+=marginal[h]*reach[owner][(size_t)k*T+h]*pi[i+a];anum[i+a]+=q;aden[i+a]+=prob;}
    }
   }else for(int h=0;h<T;++h){double value=0.,prob=0.,best=0.;for(int a=0;a<cnt[k];++a){size_t c=(size_t)child[k*4+a]*T+h;value+=v[c];prob+=cmass[c];if(street[k])best+=br[c];}v[(size_t)k*T+h]=value;cmass[(size_t)k*T+h]=prob;if(street[k])br[(size_t)k*T+h]=best;}
   if(boundary[k]>=0){int b=boundary[k];if(b>=B)return -4;for(int h=0;h<T;++h)leaf[(owner*B+b)*169+classes[owner][h]]+=br[(size_t)k*T+h];}
  }
  if(owner==0)for(int h=0;h<T;++h)metrics[0]+=v[h];
 }
 return 0;
}
