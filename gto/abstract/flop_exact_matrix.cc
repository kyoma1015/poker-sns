// Exact fixed-flop showdown: reuse precision_native.cc ranker, cache rank per
// own-hole/runout BEFORE comparing compatible opponents. No strategy changes.
#include "precision_native.cc"
#include <limits>
static_assert(std::numeric_limits<long double>::digits>=64,"extended sums required");
extern "C" int flop_matrix(int n,const int*holes,const int*flop,uint16_t*win,uint16_t*tie){
 if(n<1||n>1176)return -1;bool seen[52]{};for(int k=0;k<3;++k){int c=flop[k];if(c<0||c>=52||seen[c])return -2;seen[c]=true;}
 std::vector<uint64_t> masks(n);std::vector<int>deck;for(int c=0;c<52;++c)if(!seen[c])deck.push_back(c);
 for(int i=0;i<n;++i){int a=holes[2*i],b=holes[2*i+1];if(a<0||b<0||a>=52||b>=52||a==b||seen[a]||seen[b])return -3;masks[i]=(1ull<<a)|(1ull<<b);}
 std::vector<std::array<int,2>>runs;std::vector<uint64_t>rm;
 for(int i=0;i<49;++i)for(int j=i+1;j<49;++j){runs.push_back({deck[i],deck[j]});rm.push_back((1ull<<deck[i])|(1ull<<deck[j]));}
 int m=runs.size();std::vector<uint64_t>ranks(n*m);
 for(int i=0;i<n;++i)for(int t=0;t<m;++t)if(!(masks[i]&rm[t])){int cards[7]{holes[2*i],holes[2*i+1],flop[0],flop[1],flop[2],runs[t][0],runs[t][1]};ranks[i*m+t]=fast(cards);}
 std::fill(win,win+n*n,0);std::fill(tie,tie+n*n,0);
 for(int i=0;i<n;++i)for(int j=i+1;j<n;++j)if(!(masks[i]&masks[j])){
  unsigned w=0,d=0,count=0;auto mask=masks[i]|masks[j];
  for(int t=0;t<m;++t)if(!(mask&rm[t])){auto a=ranks[i*m+t],b=ranks[j*m+t];w+=a>b;d+=a==b;++count;}
  if(count!=990)return -4;win[i*n+j]=w;win[j*n+i]=990-w-d;tie[i*n+j]=tie[j*n+i]=d;
 }return 0;
}
extern "C" int flop_expectation(int n,const int*holes,const int*labels,const int*flop,const uint16_t*w,const uint16_t*t,const double*hero,const double*villain,int actor,int matched,int remaining,double*out){
 if(n<1||n>1176||actor<0||actor>1||matched<1||remaining<0||matched+remaining!=50)return -1;
 std::vector<uint64_t>masks(n);std::vector<bool>strength(n),probe(n);int top=std::max({flop[0]/4,flop[1]/4,flop[2]/4});
 for(int i=0;i<n;++i){if(labels[i]<0||labels[i]>=169)return -2;std::array<int,2>h{holes[2*i],holes[2*i+1]};std::array<int,3>f{flop[0],flop[1],flop[2]};masks[i]=(1ull<<h[0])|(1ull<<h[1]);strength[i]=strong5(h,f);probe[i]=strength[i]||(h[0]/4>top&&h[1]/4>top);}
 long double sums[169][5]{};
 for(int i=0;i<n;++i)for(int j=0;j<n;++j)if(!(masks[i]&masks[j])){
  int h=labels[i],v=labels[j];long double weight=(long double)hero[h]*villain[v];if(!weight)continue;
  long double e=((long double)w[i*n+j]+(long double)t[i*n+j]/2)/990;
  int sb=actor==0?i:j,bb=actor==0?j:i;long double old;
  if(strength[bb]&&!strength[sb])old=actor==0?-matched:matched;
  else if(!strength[bb]&&probe[sb])old=actor==0?matched:-matched;
  else old=(2*e-1)*(matched+((strength[bb]||probe[sb])?std::min(matched,remaining):0));
  long double newer=(2*e-1)*(matched+std::min(3*matched,remaining));
  sums[h][0]+=weight;sums[h][1]+=weight*e;sums[h][2]+=weight*old;sums[h][3]+=weight*newer;sums[h][4]+=weight*(newer-old);
 }
 for(int h=0;h<169;++h)for(int k=0;k<5;++k)out[h*5+k]=sums[h][k];return 0;
}
