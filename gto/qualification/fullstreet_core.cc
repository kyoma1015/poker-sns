// Offline same-game CF vectors. Future public/private suffixes are never infosets.
#include "../abstract/precision_native.cc"
#include <limits>
#include <numeric>
#include <cmath>
static int feature(const int*own,const int*board,int n){
 int count[15]{},suit[4]{};unsigned ranks=0;
 for(int k=0;k<n+2;++k){int c=k<2?own[k]:board[k-2];int r=c/4+2;++count[r];++suit[c%4];ranks|=1u<<r;}
 for(int r=2;r<15;++r)if(count[r]>=2)return 1;
 return *std::max_element(suit,suit+4)>=4||straight(ranks)>0;
}
extern "C" int fs_feature(const int*own,const int*board,int n){if(n!=3&&n!=4)return -1;return feature(own,board,n);}
extern "C" int fs_nuts(const int*own,const int*board){
 bool used[52]{};for(int k=0;k<2;++k)used[own[k]]=true;for(int k=0;k<5;++k)used[board[k]]=true;
 int a[7]{own[0],own[1],board[0],board[1],board[2],board[3],board[4]};auto rank=fast(a);
 for(int x=0;x<52;++x)if(!used[x])for(int y=x+1;y<52;++y)if(!used[y]){a[0]=x;a[1]=y;if(fast(a)>rank)return 0;}return 1;
}
extern "C" int fs_world(const int*board,int*holes,int*bits,int8_t*equity){
 bool used[52]{};for(int k=0;k<5;++k){if(board[k]<0||board[k]>=52||used[board[k]])return -1;used[board[k]]=true;}
 std::vector<uint64_t>masks,rank;
 for(int a=0;a<52;++a)if(!used[a])for(int b=a+1;b<52;++b)if(!used[b]){int h[2]{a,b};int i=masks.size();holes[2*i]=a;holes[2*i+1]=b;int cs[7]{a,b,board[0],board[1],board[2],board[3],board[4]};rank.push_back(fast(cs));masks.push_back((1ull<<a)|(1ull<<b));bits[i]=4*feature(h,board,3)+2*feature(h,board,4);}
 int N=masks.size();if(N!=1081)return -2;
 for(int i=0;i<N;++i){bool nuts=true;for(int j=0;j<N;++j){int8_t e=-1;if(!(masks[i]&masks[j])){e=rank[i]>rank[j]?2:rank[i]==rank[j]?1:0;if(rank[j]>rank[i])nuts=false;}equity[i*N+j]=e;}bits[i]+=nuts;}
 return N;
}
// offsets delimit each complete-board block's private types and dense pair law.
extern "C" int fs_eval(int N,int B,int C,int S,int owner,const int*actor,const int*cnt,
 const int*child,const int*round,const int*base,const int*prebase,const int*pub,const int*types,
 const int*code_offsets,const int*matrix_offsets,const int*codes,
 const double*M,const double*E,const double*c0,const double*c1,const double*pi,
 double*grad,double*avg,double*den,double*anum,double*aden,int P,double*out){
 if(N<1||B<1||C<1||S<1||owner<0||owner>1)return -1;
 std::vector<int>offset(B+1);size_t states=0;
 for(int b=0;b<B;++b){offset[b]=states;states+=(size_t)N*types[b];}offset[B]=states;
 if(states*8*5+(size_t)S*8*6>512ULL*1024*1024)return -2;
 auto ix=[&](int k,int b,int h){int r=round[k],n=cnt[k];int group=pub[b]>>(3-r);int obs=codes[code_offsets[b]+h]>>(3-r);return base[k]+(group*(C<<r)+obs)*n;};
 std::vector<double>reach0(states),reach1(states),v(states),br(states),mass(states);
 for(int b=0;b<B;++b){int T=types[b],off=offset[b];for(int h=0;h<T;++h)reach0[off+h]=reach1[off+h]=1.;
  for(int k=0;k<N;++k)if(actor[k]>=0){if(cnt[k]<1||cnt[k]>4||round[k]<0||round[k]>3)return -3;
   for(int a=0;a<cnt[k];++a){int c=child[k*4+a];if(c<=k||c>=N)return -3;
    for(int h=0;h<T;++h){int i=ix(k,b,h)+a;if(i<0||i>=S||!std::isfinite(pi[i])||pi[i]<0||pi[i]>1)return -4;auto x=off+(size_t)k*T+h,y=off+(size_t)c*T+h;reach0[y]=reach0[x]*(actor[k]==0?pi[i]:1.);reach1[y]=reach1[x]*(actor[k]==1?pi[i]:1.);}
   }
  }
 }
 std::fill(grad,grad+S,0.);std::fill(avg,avg+S,0.);std::fill(den,den+S,0.);std::fill(anum,anum+P,0.);std::fill(aden,aden+P,0.);
 std::vector<std::vector<double>>marg(B);
 for(int b=0;b<B;++b){int T=types[b],off=matrix_offsets[b];marg[b].resize(T);for(int h=0;h<T;++h)for(int o=0;o<T;++o)marg[b][h]+=M[off+(owner==0?(size_t)h*T+o:(size_t)o*T+h)];}
 for(int k=N-1;k>=0;--k){
  if(actor[k]<0){for(int b=0;b<B;++b){int T=types[b],off=offset[b],mo=matrix_offsets[b];
    for(int h=0;h<T;++h){double z=0.,pay=0.;for(int o=0;o<T;++o){auto p=mo+(owner==0?(size_t)h*T+o:(size_t)o*T+h);double r=owner==0?reach1[off+(size_t)k*T+o]:reach0[off+(size_t)k*T+o];z+=M[p]*r;pay+=M[p]*r*(c0[k]+c1[k]*E[p]);}auto x=off+(size_t)k*T+h;v[x]=br[x]=(owner==0?1.:-1.)*pay;mass[x]=z;}
   }continue;
  }
  int span=(1<<round[k])*(C<<round[k])*cnt[k];std::vector<double>scores(actor[k]==owner?span:0);
  if(actor[k]==owner)for(int b=0;b<B;++b){int T=types[b],off=offset[b];for(int h=0;h<T;++h){int i=ix(k,b,h)-base[k];for(int a=0;a<cnt[k];++a)scores[i+a]+=br[off+(size_t)child[k*4+a]*T+h];}}
  for(int b=0;b<B;++b){int T=types[b],off=offset[b];for(int h=0;h<T;++h){auto x=off+(size_t)k*T+h;int i=ix(k,b,h);double val=0.,z=0.,best=0.;
    if(actor[k]==owner){int aBest=0;for(int a=1;a<cnt[k];++a)if(scores[i-base[k]+a]>scores[i-base[k]+aBest])aBest=a;
     for(int a=0;a<cnt[k];++a){auto y=off+(size_t)child[k*4+a]*T+h;val+=pi[i+a]*v[y];z+=pi[i+a]*mass[y];}best=br[off+(size_t)child[k*4+aBest]*T+h];
     for(int a=0;a<cnt[k];++a){auto y=off+(size_t)child[k*4+a]*T+h;grad[i+a]+=v[y]-val;avg[i+a]+=marg[b][h]*(owner==0?reach0[x]:reach1[x])*pi[i+a];den[i+a]+=z;if(round[k]==0){int at=prebase[k]+(codes[code_offsets[b]+h]>>3)*cnt[k]+a;anum[at]+=v[y];aden[at]+=z;}}
    }else for(int a=0;a<cnt[k];++a){auto y=off+(size_t)child[k*4+a]*T+h;val+=v[y];z+=mass[y];best+=br[y];}
    v[x]=val;br[x]=best;mass[x]=z;
   }}
 }
 out[0]=out[1]=0.;for(int b=0;b<B;++b)for(int h=0;h<types[b];++h){out[0]+=v[offset[b]+h];out[1]+=br[offset[b]+h];}return 0;
}
