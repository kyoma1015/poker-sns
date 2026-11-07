// Separate finite preflop abstraction. Original native engines are untouched.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <numeric>
#include <random>
#include <stdexcept>
#include <vector>
using I=int64_t;using V=std::vector<I>;
static void require(bool b,const char*s){if(!b)throw std::invalid_argument(s);}
#include "rank_reused.h"
extern "C" uint64_t abstract_rank(const int*cs,int n){
 V cards(cs,cs+n);auto r=n==7?rank7(cards):five(cards);uint64_t out=0;
 for(int k=0;k<6;++k)out=out*15+(k<int(r.size())?r[k]:0);return out;
}
static bool strong(const V& hole,const V& board){V cs=hole;cs.insert(cs.end(),board.begin(),board.begin()+3);
 int suits[4]{};for(auto c:cs)++suits[c%4];return five(cs)[0]>=1||*std::max_element(suits,suits+4)>=4;}
static bool probe(const V& h,const V& board){return strong(h,board)||(h[0]/4>std::max({board[0]/4,board[1]/4,board[2]/4})&&h[1]/4>std::max({board[0]/4,board[1]/4,board[2]/4}));}
// A controller reads only its own holes and the public flop. Future cards only
// enter settlement. One half-pot bet, no raise; subsequent streets check through.
static double continuation(const V& sb,const V& bb,const V& board,int sign,int x){
 bool bb_bet=strong(bb,board),sb_call=strong(sb,board),sb_bet=probe(sb,board),bb_call=strong(bb,board);
 if(bb_bet&&!sb_call)return -x;if(!bb_bet&&sb_bet&&!bb_call)return x;
 int bet=bb_bet||sb_bet?std::min(x,100-x):0;return sign*(x+bet);
}
extern "C" int abstract_kernel(int n,const int*offset,const int*cards,int samples,int seed,double*mean,double*variance){
 if(n<1||n>169||samples<2)return -1;std::mt19937 rng(seed);int xs[4]{2,5,18,42};
 for(int i=0;i<n;++i)for(int j=i;j<n;++j){
  std::vector<std::array<int,4>> deals;
  for(int a=offset[i];a<offset[i+1];++a)for(int b=offset[j];b<offset[j+1];++b){int x=cards[2*a],y=cards[2*a+1],z=cards[2*b],w=cards[2*b+1];if(x!=z&&x!=w&&y!=z&&y!=w)deals.push_back({x,y,z,w});}
  if(deals.empty())return -2;double sum[2][5]{},sq[2][5]{};
  for(int s=0;s<samples;++s){auto deal=deals[std::uniform_int_distribution<size_t>(0,deals.size()-1)(rng)];
   V a{deal[0],deal[1]},b{deal[2],deal[3]},deck,board;
   for(int c=0;c<52;++c)if(std::find(deal.begin(),deal.end(),c)==deal.end())deck.push_back(c);
   for(int k=0;k<5;++k){int q=std::uniform_int_distribution<int>(k,47)(rng);std::swap(deck[k],deck[q]);board.push_back(deck[k]);}
   V ac=a,bc=b;ac.insert(ac.end(),board.begin(),board.end());bc.insert(bc.end(),board.begin(),board.end());
   auto ar=rank7(ac),br=rank7(bc);int sign=(ar>br)-(ar<br);double values[2][5]{};values[0][0]=100*sign;values[1][0]=-100*sign;
   for(int k=0;k<4;++k){values[0][k+1]=continuation(a,b,board,sign,xs[k]);values[1][k+1]=continuation(b,a,board,-sign,xs[k]);}
   for(int d=0;d<2;++d)for(int k=0;k<5;++k){double v=i==j?(values[0][k]+values[1][k])/2:values[d][k];sum[d][k]+=v;sq[d][k]+=v*v;}
  }
  for(int d=0;d<2;++d)for(int k=0;k<5;++k){int pos=k*n*n+(d?j*n+i:i*n+j);mean[pos]=sum[d][k]/samples;variance[pos]=std::max(0.,(sq[d][k]-sum[d][k]*sum[d][k]/samples)/(samples-1));}
 }return 0;
}
struct Game{
 int n,m;const int*actor,*count,*child;const double*p,*leaf;
 std::vector<double> regret,average,strategy;double*actionev;double*reachout;
 Game(int n_,int m_,const int*a,const int*c,const int*h,const double*p_,const double*l):n(n_),m(m_),actor(a),count(c),child(h),p(p_),leaf(l),regret(m*3*n),average(m*3*n),strategy(m*3*n){}
 int at(int node,int a,int h)const{return (node*3+a)*n+h;}
 void match(bool avg){for(int v=0;v<m;++v)if(actor[v]>=0)for(int h=0;h<n;++h){double z=0;for(int a=0;a<count[v];++a)z+=avg?average[at(v,a,h)]:std::max(0.,regret[at(v,a,h)]);for(int a=0;a<count[v];++a)strategy[at(v,a,h)]=z>0?(avg?average[at(v,a,h)]:std::max(0.,regret[at(v,a,h)]))/z:1./count[v];}}
 std::vector<double> walk(int v,const std::vector<double>&r0,const std::vector<double>&r1,bool train,int br=-1){
  if(actor[v]<0)return std::vector<double>(leaf+v*n*n,leaf+(v+1)*n*n);
  int player=actor[v],na=count[v];std::vector<std::vector<double>>q;std::vector<double>value(n*n),cf(na*n),denom(n);
  for(int a=0;a<na;++a){auto s0=r0,s1=r1;for(int h=0;h<n;++h)(player==0?s0:s1)[h]*=strategy[at(v,a,h)];q.push_back(walk(child[v*3+a],s0,s1,train,br));}
  for(int i=0;i<n;++i)for(int j=0;j<n;++j){int h=player==0?i:j;double w=p[i*n+j]*(player==0?r1[j]:r0[i]);denom[h]+=w;for(int a=0;a<na;++a)cf[a*n+h]+=w*q[a][i*n+j];}
  std::vector<int>best(n);for(int h=0;h<n;++h)for(int a=1;a<na;++a)if((player==0?1:-1)*cf[a*n+h]>(player==0?1:-1)*cf[best[h]*n+h])best[h]=a;
  for(int i=0;i<n;++i)for(int j=0;j<n;++j){int h=player==0?i:j;if(br==player)value[i*n+j]=q[best[h]][i*n+j];else for(int a=0;a<na;++a)value[i*n+j]+=strategy[at(v,a,h)]*q[a][i*n+j];}
  for(int h=0;h<n;++h){double expected=0;for(int a=0;a<na;++a)expected+=strategy[at(v,a,h)]*cf[a*n+h];
   if(train){for(int a=0;a<na;++a){regret[at(v,a,h)]+=(player==0?1:-1)*(cf[a*n+h]-expected);average[at(v,a,h)]+=(player==0?r0[h]:r1[h])*strategy[at(v,a,h)];}}
   else if(br<0){reachout[v*n+h]=denom[h]*(player==0?r0[h]:r1[h]);for(int a=0;a<na;++a)actionev[at(v,a,h)]=denom[h]>0?(player==0?1:-1)*cf[a*n+h]/denom[h]:0;}
  }return value;
 }
 double expectation(const std::vector<double>&v){double out=0;for(int k=0;k<n*n;++k)out+=p[k]*v[k];return out;}
};
extern "C" int abstract_solve(int n,int m,const int*actor,const int*count,const int*child,const double*p,const double*leaf,int iterations,double*out,double*ev,double*reach,double*metrics){
 if(n<1||m<1||iterations<1)return -1;Game g(n,m,actor,count,child,p,leaf);std::vector<double>ones(n,1.);g.actionev=ev;g.reachout=reach;
 for(int t=0;t<iterations;++t){g.match(false);g.walk(0,ones,ones,true);}
 g.match(true);std::copy(g.strategy.begin(),g.strategy.end(),out);metrics[0]=g.expectation(g.walk(0,ones,ones,false));metrics[1]=g.expectation(g.walk(0,ones,ones,false,0));metrics[2]=g.expectation(g.walk(0,ones,ones,false,1));metrics[3]=metrics[1]-metrics[2];return 0;
}
extern "C" int abstract_evaluate(int n,int m,const int*actor,const int*count,const int*child,const double*p,const double*leaf,const double*policy,double*ev,double*reach,double*metrics){
 Game g(n,m,actor,count,child,p,leaf);g.strategy.assign(policy,policy+m*3*n);g.actionev=ev;g.reachout=reach;std::vector<double>ones(n,1.);
 metrics[0]=g.expectation(g.walk(0,ones,ones,false));metrics[1]=g.expectation(g.walk(0,ones,ones,false,0));metrics[2]=g.expectation(g.walk(0,ones,ones,false,1));metrics[3]=metrics[1]-metrics[2];return 0;
}
