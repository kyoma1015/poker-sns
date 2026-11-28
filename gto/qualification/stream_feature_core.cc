// Integer-only causal feature batching; frozen CF kernel is included unchanged.
#include "active_chance_core.cc"
extern "C" int stream_features(const int*own,const int*board,int n,int H,int*out){
 if(n<3||n>5||H<1)return -1;
 int ps[4]{};for(int j=0;j<n;++j)++ps[board[j]%4];int sorted[4];std::copy(ps,ps+4,sorted);std::sort(sorted,sorted+4);
 for(int h=0;h<H;++h){int cs[7]{own[2*h],own[2*h+1]};for(int j=0;j<n;++j)cs[j+2]=board[j];auto rank=prefix_fast(cs,n+2);
  int suit[4]{};unsigned mask=0;for(int j=0;j<n+2;++j){++suit[cs[j]%4];mask|=1u<<(cs[j]/4+2);}if(mask&(1u<<14))mask|=2;
  int potential=0;for(int lo=1;lo<=10;++lo)potential=std::max(potential,__builtin_popcount(mask&(31u<<lo)));
  int*o=out+13*h;o[0]=rank/759375;o[1]=(rank/50625)%15;o[2]=*std::max_element(suit,suit+4);o[3]=potential;std::copy(sorted,sorted+4,o+4);
  std::vector<std::pair<int,int>>block;for(int j=0;j<2;++j){int c=cs[j];if(ps[c%4]>=2)block.push_back({ps[c%4],c/4+2});}std::sort(block.begin(),block.end());o[8]=block.size();for(int j=9;j<13;++j)o[j]=0;for(size_t j=0;j<block.size();++j){o[9+2*j]=block[j].first;o[10+2*j]=block[j].second;}
 }return 0;
}
