// Public chance sampled fullstreet CFR kernel. Frozen fs_eval is unchanged.
#include "fullstreet_core.cc"
// Exact private-pair integration: rank prefixes minus both own-card blockers.
// T must be all C(47,2) hands on one complete board, sorted by hand rank.
extern "C" int pcs_terminal(int T,const int*holes,const int*ranks,const double*opp,double*mass,double*win){
 if(T!=1081)return -1;
 double total=0.,card[52]{},below=0.,before[52]{};
 for(int h=0;h<T;++h){if(!std::isfinite(opp[h])||opp[h]<0)return -2;total+=opp[h];card[holes[2*h]]+=opp[h];card[holes[2*h+1]]+=opp[h];}
 for(int i=0;i<T;){int j=i+1;while(j<T&&ranks[j]==ranks[i])++j;
  double tie=0.,tied[52]{};
  for(int h=i;h<j;++h){tie+=opp[h];tied[holes[2*h]]+=opp[h];tied[holes[2*h+1]]+=opp[h];}
  for(int h=i;h<j;++h){int a=holes[2*h],b=holes[2*h+1];mass[h]=total-card[a]-card[b]+opp[h];
   win[h]=below-before[a]-before[b]+.5*(tie-tied[a]-tied[b]+opp[h]);}
  below+=tie;for(int c=0;c<52;++c)before[c]+=tied[c];i=j;
 }return 0;
}
extern "C" int pcs_world(const int*board,int*holes,int*codes,int*ranks){
 bool used[52]{};for(int k=0;k<5;++k){if(board[k]<0||board[k]>=52||used[board[k]])return -1;used[board[k]]=true;}
 struct H{int a,b;uint64_t rank;};std::vector<H>hands;
 for(int a=0;a<52;++a)if(!used[a])for(int b=a+1;b<52;++b)if(!used[b]){int cs[7]{a,b,board[0],board[1],board[2],board[3],board[4]};hands.push_back({a,b,fast(cs)});}
 std::stable_sort(hands.begin(),hands.end(),[](const H&a,const H&b){return a.rank<b.rank;});
 int group=-1;uint64_t last=0;
 for(int i=0;i<1081;++i){auto h=hands[i];if(i==0||h.rank!=last)++group;last=h.rank;holes[2*i]=h.a;holes[2*i+1]=h.b;int own[2]{h.a,h.b};codes[i]=4*feature(own,board,3)+2*feature(own,board,4);ranks[i]=group;}
 // Exact nuts property includes card removal, rather than global top rank.
 for(int i=0;i<1081;++i){bool nuts=true;auto h=hands[i];for(int j=i+1;j<1081;++j)if(hands[j].rank>h.rank&&hands[j].a!=h.a&&hands[j].a!=h.b&&hands[j].b!=h.a&&hands[j].b!=h.b){nuts=false;break;}codes[i]+=nuts;}
 return 1081;
}
extern "C" int pcs_eval(int N,int B,int C,int S,int owner,const int*actor,const int*cnt,
 const int*child,const int*round,const int*base,const int*prebase,const int*pub,const int*types,
 const int*code_offsets,const int*matrix_offsets,const int*codes,
 const int*holes,const int*ranks,const double*weights,const double*c0,const double*c1,const double*pi,
 double*grad,double*avg,double*den,double*anum,double*aden,int P,double*out){
 if(N<1||B<1||C<1||S<1||owner<0||owner>1)return -1;
 std::vector<int>offset(B+1);size_t states=0;
 for(int b=0;b<B;++b){offset[b]=states;states+=(size_t)N*types[b];}offset[B]=states;
 if(states*8*5+(size_t)S*8*6>512ULL*1024*1024)return -2;
 auto ix=[&](int k,int b,int h){int r=round[k],n=cnt[k+1]-cnt[k];int group=pub[b]>>(3-r);int obs=codes[code_offsets[b]+h]>>(3-r);return base[k]+(group*(C<<r)+obs)*n;};
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
  int span=(1<<round[k])*(C<<round[k])*(cnt[k+1]-cnt[k]);std::vector<double>scores(actor[k]==owner?span:0);
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
