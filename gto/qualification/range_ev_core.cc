// Existing exact card evaluator; frozen solver sources are unchanged.
#include "public_chance_core.cc"
#include <random>
extern "C" int range_equity(const int*own,const int*prefix,int K,const int*pairs,const double*cdf,int P,uint64_t n,uint64_t seed,double*out){
 if(P<1||n<1||K<0||K>5)return -1;
 bool used[52]{};for(int j=0;j<2;++j){int c=own[j];if(c<0||c>=52||used[c])return -2;used[c]=true;}for(int j=0;j<K;++j){int c=prefix[j];if(c<0||c>=52||used[c])return -2;used[c]=true;}
 std::vector<std::vector<int>> decks(P);double last=0.;
 for(int p=0;p<P;++p){int a=pairs[2*p],b=pairs[2*p+1];if(a<0||a>=52||b<0||b>=52||a==b||used[a]||used[b]||!std::isfinite(cdf[p])||cdf[p]<last||cdf[p]>1)return -3;last=cdf[p];for(int c=0;c<52;++c)if(!used[c]&&c!=a&&c!=b)decks[p].push_back(c);}
 if(cdf[P-1]!=1.)return -4;
 std::mt19937_64 rng(seed);double wins=0.;int a[7]{own[0],own[1]},b[7]{};
 for(int j=0;j<K;++j)a[j+2]=b[j+2]=prefix[j];
 for(uint64_t s=0;s<n;++s){double u=(rng()>>11)*0x1.0p-53;int p=std::upper_bound(cdf,cdf+P,u)-cdf;b[0]=pairs[2*p];b[1]=pairs[2*p+1];auto&deck=decks[p];int picked[5]{};std::uniform_int_distribution<int> choose(0,int(deck.size())-1);
  for(int j=0;j<5-K;++j){int ix;bool duplicate;do{ix=choose(rng);duplicate=false;for(int z=0;z<j;++z)if(picked[z]==ix)duplicate=true;}while(duplicate);picked[j]=ix;a[2+K+j]=b[2+K+j]=deck[ix];}
  auto x=fast(a),y=fast(b);wins+=x>y?1.:x==y?.5:0.;
 }
 *out=wins/double(n);return 0;
}
