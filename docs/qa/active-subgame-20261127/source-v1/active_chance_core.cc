// Active row indexing of the existing exact private-vector CFR kernel.
// Terminal/card-removal math is reused unchanged; actions remain CSR, not four slots.
#include "public_chance_core.cc"
extern "C" int active_eval(int N,int B,int C,int S,int owner,const int*actor,const int*cnt,
 const int*child,const int*round,const int*base,const int*prebase,const int*pub,const int*types,
 const int*code_offsets,const int*matrix_offsets,const int*codes,const int*active,const int*span_by_node,
 const int*holes,const int*ranks,const double*weights,const double*c0,const double*c1,const double*pi,
 double*grad,double*avg,double*den,double*anum,double*aden,int P,double*out){
 if(N<1||B<1||C<1||S<1||owner<0||owner>1)return -1;
 std::vector<int>offset(B+1);size_t states=0;
 for(int b=0;b<B;++b){offset[b]=states;states+=(size_t)N*types[b];}offset[B]=states;
 if(states*8*5+(size_t)S*8*6>512ULL*1024*1024)return -2;
 auto ix=[&](int k,int b,int h){return active[((size_t)b*N+k)*1081+h];};
 std::vector<double>reach0(states),reach1(states),v(states),br(states),mass(states);
 for(int b=0;b<B;++b){int T=types[b],off=offset[b];for(int h=0;h<T;++h)reach0[off+h]=reach1[off+h]=1.;
  for(int k=0;k<N;++k)if(actor[k]>=0){if(cnt[k+1]-cnt[k]<1||round[k]<0||round[k]>3)return -3;
   for(int a=0;a<cnt[k+1]-cnt[k];++a){int c=child[cnt[k]+a];if(c<=k||c>=N)return -3;
    for(int h=0;h<T;++h){int i=ix(k,b,h)+a;if(i<0||i>=S||!std::isfinite(pi[i])||pi[i]<0||pi[i]>1)return -4;auto x=off+(size_t)k*T+h,y=off+(size_t)c*T+h;reach0[y]=reach0[x]*(actor[k]==0?pi[i]:1.);reach1[y]=reach1[x]*(actor[k]==1?pi[i]:1.);}
   }
  }
 }
 std::fill(grad,grad+S,0.);std::fill(avg,avg+S,0.);std::fill(den,den+S,0.);std::fill(anum,anum+P,0.);std::fill(aden,aden+P,0.);
 std::vector<std::vector<double>>marg(B);
 for(int b=0;b<B;++b){int T=types[b];marg[b].assign(T,weights[b]/T);}
 for(int k=N-1;k>=0;--k){
  if(actor[k]<0){for(int b=0;b<B;++b){int T=types[b],off=offset[b];
    std::vector<double>m(T),w(T); const double*opp=owner==0?reach1.data():reach0.data();
    if(pcs_terminal(T,holes+2*code_offsets[b],ranks+code_offsets[b],opp+off+(size_t)k*T,m.data(),w.data()))return -5;
    double scale=weights[b]/((double)T*(T-91));
    for(int h=0;h<T;++h){auto x=off+(size_t)k*T+h;mass[x]=m[h]*scale;
     v[x]=br[x]=scale*(owner==0?c0[k]*m[h]+c1[k]*w[h]:-(c0[k]+c1[k])*m[h]+c1[k]*w[h]);}
   }continue;
  }
  int span=span_by_node[k];std::vector<double>scores(actor[k]==owner?span:0);
  if(actor[k]==owner)for(int b=0;b<B;++b){int T=types[b],off=offset[b];for(int h=0;h<T;++h){int i=ix(k,b,h)-base[k];for(int a=0;a<cnt[k+1]-cnt[k];++a)scores[i+a]+=br[off+(size_t)child[cnt[k]+a]*T+h];}}
  for(int b=0;b<B;++b){int T=types[b],off=offset[b];for(int h=0;h<T;++h){auto x=off+(size_t)k*T+h;int i=ix(k,b,h);double val=0.,z=0.,best=0.;
    if(actor[k]==owner){int aBest=0;for(int a=1;a<cnt[k+1]-cnt[k];++a)if(scores[i-base[k]+a]>scores[i-base[k]+aBest])aBest=a;
     for(int a=0;a<cnt[k+1]-cnt[k];++a){auto y=off+(size_t)child[cnt[k]+a]*T+h;val+=pi[i+a]*v[y];z+=pi[i+a]*mass[y];}best=br[off+(size_t)child[cnt[k]+aBest]*T+h];
     for(int a=0;a<cnt[k+1]-cnt[k];++a){auto y=off+(size_t)child[cnt[k]+a]*T+h;grad[i+a]+=v[y]-val;avg[i+a]+=marg[b][h]*(owner==0?reach0[x]:reach1[x])*pi[i+a];den[i+a]+=z;if(round[k]==0){int at=prebase[k]+(codes[code_offsets[b]+h]>>3)*(cnt[k+1]-cnt[k])+a;anum[at]+=v[y];aden[at]+=z;}}
    }else for(int a=0;a<cnt[k+1]-cnt[k];++a){auto y=off+(size_t)child[cnt[k]+a]*T+h;val+=v[y];z+=mass[y];best+=br[y];}
    v[x]=val;br[x]=best;mass[x]=z;
   }}
 }
 out[0]=out[1]=0.;for(int b=0;b<B;++b)for(int h=0;h<types[b];++h){out[0]+=v[offset[b]+h];out[1]+=br[offset[b]+h];}return 0;
}

static uint64_t prefix_fast(const int*cards,int n){
 int counts[15]{},suits[4]{};unsigned mask=0,sm[4]{};
 for(int k=0;k<n;++k){int r=cards[k]/4+2,s=cards[k]%4;++counts[r];++suits[s];mask|=1u<<r;sm[s]|=1u<<r;}
 int flush=-1;for(int s=0;s<4;++s)if(suits[s]>=5)flush=s;
 if(flush>=0){int st=straight(sm[flush]);if(st)return encode({8,st,0,0,0,0});}
 int quad=0,triple=0,pair=0;
 for(int r=14;r>=2;--r){if(counts[r]==4)quad=r;if(!triple&&counts[r]>=3)triple=r;}
 if(quad){int k=14;while(k==quad||!counts[k])--k;return encode({7,quad,k,0,0,0});}
 if(triple)for(int r=14;r>=2;--r)if(r!=triple&&counts[r]>=2){pair=r;break;}
 if(triple&&pair)return encode({6,triple,pair,0,0,0});
 if(flush>=0){std::array<int,6>out{5,0,0,0,0,0};int k=1;for(int r=14;r>=2&&k<6;--r)if(sm[flush]&(1u<<r))out[k++]=r;return encode(out);}
 int st=straight(mask);if(st)return encode({4,st,0,0,0,0});
 if(triple){std::array<int,6>out{3,triple,0,0,0,0};int k=2;for(int r=14;r>=2&&k<4;--r)if(r!=triple&&counts[r])out[k++]=r;return encode(out);}
 int p1=0,p2=0;for(int r=14;r>=2;--r)if(counts[r]>=2){if(!p1)p1=r;else if(!p2)p2=r;}
 if(p2){int k=14;while(k==p1||k==p2||!counts[k])--k;return encode({2,p1,p2,k,0,0});}
 if(p1){std::array<int,6>out{1,p1,0,0,0,0};int k=2;for(int r=14;r>=2&&k<5;--r)if(r!=p1&&counts[r])out[k++]=r;return encode(out);}
 std::array<int,6>out{};int k=1;for(int r=14;r>=2&&k<6;--r)if(counts[r])out[k++]=r;return encode(out);
}

extern "C" uint64_t active_rank(const int*cards,int n){return n>=5&&n<=7?prefix_fast(cards,n):0;}
